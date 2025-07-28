"""Data update coordinator for Meme Stock Insight v0.6.0

This file is based on commit 7a8f7ed of BestMasterChief/meme_stock_insight with
new features added:
    * Multi-provider price ladder (yfinance ➔ Alpha Vantage ➔ Polygon)
    * Per-provider quota tracking and daily reset
    * Fallback state `max_api_calls_used`
    * Days-active & price-since-start calculation
    * Dynamic subreddit discovery refreshed weekly
    * Yahoo Unknown/0 bug fixed by using .history fallback
"""
from __future__ import annotations

import asyncio
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple

import praw
import prawcore
import yfinance as yf
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    ATTRIBUTION,
    DEFAULT_SUBREDDITS,
    DYNAMIC_SUBREDDIT_REFRESH,
    DOMAIN,
    MAX_POSTS_PER_SUBREDDIT,
    MAX_COMMENTS_PER_POST,
    MEME_STOCK_SYMBOLS,
    PRICE_PROVIDERS,
    API_LIMITS,
    QUOTA_RESET_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    SENSOR_MENTIONS,
    SENSOR_SENTIMENT,
    SENSOR_TRENDING,
    SENSOR_MEME_1,
    SENSOR_MEME_2,
    SENSOR_MEME_3,
    SENSOR_STAGE,
    SENSOR_DAYS_ACTIVE,
    SENSOR_PRICE_SINCE_START,
    SENSOR_DYNAMIC_SUBREDDIT,
    MEME_STOCK_STAGES,
    STOCK_NAME_MAPPING,
    SENTIMENT_KEYWORDS_POSITIVE,
    SENTIMENT_KEYWORDS_NEGATIVE,
)

_LOGGER = logging.getLogger(__name__)

APILimitError = type("APILimitError", (Exception,), {})

class MemeStockCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Central coordinator handling Reddit and price data."""

    def __init__(self, hass: HomeAssistant, reddit_conf: Dict[str, str], options: Dict[str, Any]):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_UPDATE_INTERVAL,
        )

        # Reddit client (script-app)
        self._reddit = praw.Reddit(
            **reddit_conf,
            check_for_updates=False,
            check_for_async=False,
            ratelimit_seconds=5,
        )
        self._subreddits: List[str] = options.get("subreddits", DEFAULT_SUBREDDITS)
        self._dynamic_sr: str | None = None

        # Provider keys from options (may be blank)
        self._alpha_key: str = options.get("alpha_vantage_key", "")
        self._polygon_key: str = options.get("polygon_key", "")

        # Quota counters
        self._quota: Dict[str, int] = defaultdict(int)
        self._exhausted: set[str] = set()
        self._quota_reset_at: datetime = datetime.now(timezone.utc) + QUOTA_RESET_INTERVAL

        # Persisted state across restarts
        store = hass.data.setdefault(DOMAIN, {})
        self._first_seen: Dict[str, datetime] = store.setdefault("first_seen", {})
        self._first_price: Dict[str, float] = store.setdefault("first_price", {})

        # schedule dynamic subreddit refresh
        async_track_time_interval(
            hass, self._async_refresh_dynamic_subreddit, DYNAMIC_SUBREDDIT_REFRESH
        )

    # ---------------------------------------------------------------------
    # Data update cycle
    # ---------------------------------------------------------------------
    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            reddit_data = await self.hass.async_add_executor_job(self._gather_reddit)
            price_data = await self._gather_prices(reddit_data["mentions_dict"])
            return {**reddit_data, **price_data}
        except Exception as exc:
            raise UpdateFailed(str(exc)) from exc

    # ------------------------------------------------------------------
    # Reddit helpers
    # ------------------------------------------------------------------
    def _gather_reddit(self) -> Dict[str, Any]:
        """Fetch posts, count mentions, compute sentiment."""
        mentions: Dict[str, int] = defaultdict(int)
        sentiment_scores: List[float] = []

        sr_list = list(self._subreddits) + ([self._dynamic_sr] if self._dynamic_sr else [])
        for sr in sr_list:
            try:
                for post in self._reddit.subreddit(sr).hot(limit=MAX_POSTS_PER_SUBREDDIT):
                    self._scan_text(post.title, mentions, sentiment_scores)
                    self._scan_text(post.selftext, mentions, sentiment_scores)
            except prawcore.exceptions.Forbidden:
                _LOGGER.debug("Forbidden subreddit: %s", sr)
            except Exception as err:
                _LOGGER.debug("Error reading %s: %s", sr, err)

        total_mentions = sum(mentions.values())
        avg_sentiment = (
            round(sum(sentiment_scores) / len(sentiment_scores), 3) if sentiment_scores else 0.0
        )

        trending = sorted(mentions.items(), key=lambda x: x[1], reverse=True)[:15]

        return {
            "total_mentions": total_mentions,
            "average_sentiment": avg_sentiment,
            "trending": trending,
            "mentions_dict": mentions,
        }

    def _scan_text(self, text: str, bucket: Dict[str, int], sents: List[float]):
        if not text:
            return
        # count symbols
        for word in re.findall(r"\b[A-Z]{2,5}\b", text.upper()):
            if word in MEME_STOCK_SYMBOLS:
                bucket[word] += 1
        # naive sentiment
        lo = text.lower()
        pos = sum(lo.count(w) for w in SENTIMENT_KEYWORDS_POSITIVE)
        neg = sum(lo.count(w) for w in SENTIMENT_KEYWORDS_NEGATIVE)
        if pos + neg:
            sents.append((pos - neg) / (pos + neg))

    # ------------------------------------------------------------------
    # Price helpers with fallback ladder
    # ------------------------------------------------------------------
    async def _gather_prices(self, mentions: Dict[str, int]) -> Dict[str, Any]:
        # reset daily quota window
        if datetime.now(timezone.utc) >= self._quota_reset_at:
            self._quota.clear()
            self._exhausted.clear()
            self._quota_reset_at = datetime.now(timezone.utc) + QUOTA_RESET_INTERVAL

        async def fetch_one(sym: str) -> Dict[str, Any]:
            for provider in PRICE_PROVIDERS:
                if provider in self._exhausted:
                    continue
                try:
                    fetcher = getattr(self, f"_price_{provider}")
                    data = await fetcher(sym)
                    self._bump_quota(provider)
                    return data
                except APILimitError:
                    self._exhausted.add(provider)
                    continue
                except Exception as err:
                    _LOGGER.debug("%s via %s failed: %s", sym, provider, err)
            return {"current_price": None, "price_change_pct": 0.0, "provider": "exhausted"}

        symbols = list(mentions)[:10]
        price_results = await asyncio.gather(*[fetch_one(s) for s in symbols])

        price_map = dict(zip(symbols, price_results))
        top_sorted = sorted(symbols, key=lambda s: mentions[s], reverse=True)[:3]

        now = datetime.now(timezone.utc)
        top_entities = []
        for rank, sym in enumerate(top_sorted, start=1):
            pdata = price_map[sym]
            if sym not in self._first_seen:
                self._first_seen[sym] = now
                self._first_price[sym] = pdata["current_price"] or 0.0
            days_active = (now - self._first_seen[sym]).days
            since_start = (
                ((pdata["current_price"] / self._first_price[sym]) - 1) * 100
                if self._first_price[sym]
                else 0.0
            )
            top_entities.append(
                {
                    "symbol": sym,
                    "company": STOCK_NAME_MAPPING.get(sym, sym),
                    "rank": rank,
                    "mentions": mentions[sym],
                    "days_active": days_active,
                    "price_since_start": round(since_start, 2),
                    **pdata,
                }
            )

        stage = self._determine_stage(top_entities[0] if top_entities else None)

        return {
            "top_entities": top_entities,
            "stage": stage,
            "price_map": price_map,
        }

    # individual provider fetchers ------------------------------------------------
    async def _price_yfinance(self, sym: str) -> Dict[str, Any]:
        def _sync():
            tk = yf.Ticker(sym)
            hist = tk.history(period="5d")
            if hist.empty:
                raise RuntimeError("No Yahoo data")
            cur = hist["Close"].iloc[-1]
            prev = hist["Close"].iloc[-2] if len(hist) > 1 else cur
            pct = round(((cur / prev) - 1) * 100, 2)
            return {
                "current_price": round(float(cur), 2),
                "price_change_pct": pct,
                "volume": int(hist["Volume"].iloc[-1]),
                "provider": "yfinance",
            }

        return await self.hass.async_add_executor_job(_sync)

    async def _price_alpha_vantage(self, sym: str) -> Dict[str, Any]:
        if not self._alpha_key:
            raise RuntimeError("No AV key")
        from alpha_vantage.timeseries import TimeSeries

        ts = TimeSeries(self._alpha_key, output_format="json")
        data, _ = await self.hass.async_add_executor_job(ts.get_daily, sym, "compact")
        rows = list(data.values())[:2]
        if not rows:
            raise RuntimeError("Empty AV data")
        cur, prev = float(rows[0]["4. close"]), float(rows[1]["4. close"])
        pct = round(((cur / prev) - 1) * 100, 2)
        return {
            "current_price": round(cur, 2),
            "price_change_pct": pct,
            "volume": int(rows[0]["5. volume"]),
            "provider": "alpha_vantage",
        }

    async def _price_polygon(self, sym: str) -> Dict[str, Any]:
        if not self._polygon_key:
            raise RuntimeError("No Polygon key")
        import aiohttp, datetime as dt

        start = (datetime.utcnow() - timedelta(days=5)).date()
        end = datetime.utcnow().date()
        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{start}/{end}?limit=2&apiKey={self._polygon_key}"
        )
        async with aiohttp.ClientSession() as sess, sess.get(url, timeout=10) as resp:
            if resp.status == 429:
                raise APILimitError
            js = await resp.json()
        bars = js.get("results", [])
        if len(bars) < 2:
            raise RuntimeError("Insufficient bars")
        cur, prev = bars[-1]["c"], bars[-2]["c"]
        pct = round(((cur / prev) - 1) * 100, 2)
        return {
            "current_price": round(cur, 2),
            "price_change_pct": pct,
            "volume": bars[-1]["v"],
            "provider": "polygon",
        }

    # ------------------------------------------------------------------
    def _bump_quota(self, provider: str):
        limit = API_LIMITS.get(provider, 0)
        if limit:
            self._quota[provider] += 1
            if self._quota[provider] >= limit:
                self._exhausted.add(provider)

    # ------------------------------------------------------------------
    def _determine_stage(self, top: Dict[str, Any] | None) -> str:
        if not top or top["current_price"] is None:
            return MEME_STOCK_STAGES["start"]
        days = top["days_active"]
        price_pct = top["price_change_pct"]
        if days < 3 and price_pct < 2:
            return MEME_STOCK_STAGES["start"]
        if price_pct > 5 and days < 14:
            return MEME_STOCK_STAGES["stock_rising"]
        if price_pct > 10:
            return MEME_STOCK_STAGES["within_estimated_peak"]
        if price_pct < -5:
            return MEME_STOCK_STAGES["dropping"]
        return MEME_STOCK_STAGES["rising_interest"]

    # ------------------------------------------------------------------
    async def _async_refresh_dynamic_subreddit(self, _):
        """Weekly discovery of high-traffic trading sub."""
        try:
            top_week = await self.hass.async_add_executor_job(
                lambda: list(self._reddit.subreddit("all").top(limit=200, time_filter="week"))
            )
            tally = defaultdict(int)
            for post in top_week:
                tally[post.subreddit.display_name.lower()] += 1
            for name, _ in sorted(tally.items(), key=lambda x: x[1], reverse=True):
                if name not in self._subreddits:
                    self._dynamic_sr = name
                    _LOGGER.info("Dynamic subreddit switched to %s", name)
                    return
        except Exception as err:
            _LOGGER.debug("Dynamic subreddit discovery failed: %s", err)
