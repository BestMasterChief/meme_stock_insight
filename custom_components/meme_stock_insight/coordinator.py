"""Data-update coordinator – v0.6.0: multi-provider prices, quotas, dynamic SR."""
from __future__ import annotations

import asyncio, logging, re, statistics
from collections import defaultdict
from datetime import datetime, timedelta, UTC
from typing import Any, Dict, List

import praw, prawcore
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN, DEFAULT_SUBREDDITS, DYNAMIC_SUBREDDIT_REFRESH, SUBREDDIT_REFRESH,
    PROVIDERS, API_LIMITS, QUOTA_RESET,
    SENSOR_DAYS_ACTIVE, SENSOR_SINCE_START,
    MEME_STOCK_SYMBOLS, FALSE_POSITIVE_KEYWORDS,
    SENTIMENT_KEYWORDS_POSITIVE, SENTIMENT_KEYWORDS_NEGATIVE,
    STOCK_NAME_MAPPING, MEME_STOCK_STAGES, STAGE_THRESHOLDS,
)

_LOGGER = logging.getLogger(__name__)


class _APILimitError(Exception):
    """Raised when free-tier quota is exhausted."""


class MemeStockCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Central engine fetching Reddit + price data."""

    def __init__(self, hass: HomeAssistant, reddit_conf: dict, options: dict) -> None:
        super().__init__(
            hass, _LOGGER, name=DOMAIN, update_interval=SUBREDDIT_REFRESH
        )
        # ───── Reddit ─────
        self._reddit_conf   = reddit_conf
        self._subreddits    = options.get("subreddits", DEFAULT_SUBREDDITS)
        self._dynamic_sr: str | None = None

        # ───── Price provider keys ─────
        self._alpha_key   = options.get("alpha_vantage_key", "")
        self._polygon_key = options.get("polygon_key", "")

        # ───── Quota bookkeeping ─────
        self._quota: dict[str, int] = defaultdict(int)
        self._exhausted: set[str]   = set()
        self._quota_reset_at        = datetime.now(tz=UTC) + QUOTA_RESET

        # ───── Persistence across restarts ─────
        mem    = hass.data.setdefault(DOMAIN, {})
        self._first_seen  = mem.setdefault("first_seen",  {})   # {SYM: datetime}
        self._first_price = mem.setdefault("first_price", {})   # {SYM: float}
        self._stock_cache: dict[str, dict] = {}                 # last good price struct

        # schedule weekly subreddit rotation
        async_track_time_interval(
            hass, self._async_refresh_dynamic_sr, DYNAMIC_SUBREDDIT_REFRESH
        )

    # ──────────────────────────  update loop  ──────────────────────────
    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            if not getattr(self, "_reddit", None):
                await self._async_setup_reddit()

            reddit_data = await self.hass.async_add_executor_job(self._fetch_reddit)
            price_data  = await self._price_wrapper(reddit_data["stock_mentions"])
            stage_data  = await self._stage_wrapper(reddit_data, price_data)

            return {**reddit_data, **price_data, **stage_data}

        except Exception as err:
            _LOGGER.error("Coordinator error: %s", err)
            return self._fallback(str(err)[:48])

    # ──────────────────────  Reddit client bootstrap  ──────────────────
    async def _async_setup_reddit(self) -> None:
        def _build():
            return praw.Reddit(
                check_for_updates=False, check_for_async=False, ratelimit_seconds=5,
                **self._reddit_conf
            )
        self._reddit = await self.hass.async_add_executor_job(_build)
        if not self._reddit.user.me():
            raise UpdateFailed("Reddit script-app authentication failed")

    # ──────────────────────  Reddit scraping  ──────────────────────────
    def _fetch_reddit(self) -> dict:
        stock_mentions: dict[str, int] = defaultdict(int)
        sent_scores:   list[float]     = []
        posts_limit = 100

        for sr in (self._subreddits + ([self._dynamic_sr] if self._dynamic_sr else []))[:5]:
            try:
                for post in self._reddit.subreddit(sr).hot(limit=30):
                    if posts_limit <= 0:
                        break
                    self._scan_text(post.title,     stock_mentions, sent_scores)
                    self._scan_text(post.selftext,  stock_mentions, sent_scores)
                    posts_limit -= 1
            except prawcore.exceptions.Forbidden:
                _LOGGER.debug("Forbidden SR %s", sr)
            except Exception as e:
                _LOGGER.debug("SR %s error: %s", sr, e)

        total = sum(stock_mentions.values())
        sentiment = round(sum(sent_scores)/len(sent_scores), 3) if sent_scores else 0

        trending = sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)
        trending = [{"symbol": s, "mentions": m} for s, m in trending if m >= 2][:15]

        pos = sum(1 for s in sent_scores if s > 0.1)
        neg = sum(1 for s in sent_scores if s < -0.1)
        neu = len(sent_scores) - pos - neg

        return {
            "total_mentions": total,
            "average_sentiment": sentiment,
            "trending_count": len(trending),
            "stock_mentions": dict(sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)[:20]),
            "trending_stocks": trending,
            "sentiment_distribution": {"positive": pos, "neutral": neu, "negative": neg},
        }

    def _scan_text(self, text: str, bucket: dict, sents: list) -> None:
        if not text:
            return
        symbols = re.findall(r"\b[A-Z]{2,5}\b", text.upper())[:50]
        for tag in symbols:
            if tag not in MEME_STOCK_SYMBOLS:
                continue
            # quick false-positive filter
            if tag in FALSE_POSITIVE_KEYWORDS and any(
                k in text.lower() for k in FALSE_POSITIVE_KEYWORDS[tag][:5]
            ):
                continue
            bucket[tag] += 1

        # tiny lexicon sentiment
        lo = text.lower()
        pc = sum(1 for w in SENTIMENT_KEYWORDS_POSITIVE if w in lo)
        nc = sum(1 for w in SENTIMENT_KEYWORDS_NEGATIVE if w in lo)
        if pc or nc:
            sents.append((pc - nc) / (pc + nc))

    # ──────────────────────  price ladder & quotas  ─────────────────────
    async def _price_wrapper(self, mentions: dict) -> dict:
        # reset quota daily
        if datetime.now(tz=UTC) >= self._quota_reset_at:
            self._quota.clear(); self._exhausted.clear()
            self._quota_reset_at = datetime.now(tz=UTC) + QUOTA_RESET

        async def _loop(sym: str) -> dict:
            for provider in PROVIDERS:
                if provider in self._exhausted:
                    continue
                try:
                    data = await getattr(self, f"_price_{provider}")(sym)
                    self._inc_quota(provider)
                    return data
                except _APILimitError:
                    self._exhausted.add(provider)
                except Exception as e:
                    _LOGGER.debug("%s %s failed: %s", sym, provider, e)
            raise RuntimeError("all providers exhausted")

        tasks = {sym: _loop(sym) for sym in list(mentions)[:10]}
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)

        stock_prices, top = {}, []
        for sym, res in zip(tasks, results):
            if isinstance(res, Exception):
                res = self._stock_cache.get(sym, {
                    "current_price": None, "price_change_pct": 0,
                    "volume": 0, "avg_volume": 0, "market_cap": 0,
                    "price_history": [], "mentions": mentions[sym],
                    "company_name": STOCK_NAME_MAPPING.get(sym, sym),
                })
            stock_prices[sym] = res
            self._stock_cache[sym] = res  # memoise
            # days-active / since-start
            now = datetime.now(tz=UTC)
            if sym not in self._first_seen:
                self._first_seen[sym]  = now
                self._first_price[sym] = res["current_price"] or 0
            days = (now - self._first_seen[sym]).days
            since = (
                ((res["current_price"] / self._first_price[sym]) - 1) * 100
                if self._first_price[sym] else 0
            )
            top.append({
                "symbol": sym,
                "company_name": res["company_name"],
                "mentions": mentions[sym],
                "current_price": res["current_price"],
                "price_change_pct": res["price_change_pct"],
                "display_name": f"{sym} - {res['company_name']}",
                SENSOR_DAYS_ACTIVE: days,
                SENSOR_SINCE_START: round(since, 2),
            })

        top.sort(key=lambda x: x["mentions"], reverse=True)
        return {"stock_prices": stock_prices, "top_stocks": top}

    # helpers
    def _inc_quota(self, provider):
        if API_LIMITS[provider]:
            self._quota[provider] += 1
            if self._quota[provider] >= API_LIMITS[provider]:
                self._exhausted.add(provider)

    async def _price_yfinance(self, sym: str) -> dict:
        import yfinance as yf
        def _sync():
            tk   = yf.Ticker(sym.replace("-USD", "-USD"))
            hist = tk.history(period="5d")
            if hist.empty:
                raise RuntimeError("no data")
            cur, prev = hist["Close"].iloc[-1], hist["Close"].iloc[-2]
            pct = round(((cur / prev) - 1)*100, 2)
            return {
                "current_price": round(float(cur), 2),
                "price_change_pct": pct,
                "volume": int(hist["Volume"].iloc[-1]),
                "avg_volume": int(hist["Volume"].mean()),
                "market_cap": tk.info.get("marketCap", 0),
                "price_history": [round(float(v), 2) for v in hist["Close"].tolist()],
                "company_name": tk.info.get("longName") or STOCK_NAME_MAPPING.get(sym, sym),
                "mentions": 0,  # patch later
            }
        return await self.hass.async_add_executor_job(_sync)

    async def _price_alpha_vantage(self, sym: str) -> dict:
        from alpha_vantage.timeseries import TimeSeries
        if not self._alpha_key:
            raise RuntimeError("no alpha key")
        ts = TimeSeries(self._alpha_key, output_format="json")
        data, _ = await self.hass.async_add_executor_job(ts.get_daily, sym, "compact")
        rows = list(data.values())[:5]
        if not rows:
            raise RuntimeError("no rows")
        cur, prev = float(rows[0]["4. close"]), float(rows[1]["4. close"])
        pct = round(((cur / prev) - 1)*100, 2)
        return {
            "current_price": round(cur, 2), "price_change_pct": pct,
            "volume": int(rows[0]["5. volume"]),
            "avg_volume": int(sum(int(r["5. volume"]) for r in rows)/len(rows)),
            "market_cap": 0, "price_history": [round(float(r["4. close"]), 2) for r in rows[::-1]],
            "company_name": STOCK_NAME_MAPPING.get(sym, sym), "mentions": 0,
        }

    async def _price_polygon(self, sym: str) -> dict:
        import aiohttp, datetime as _dt
        if not self._polygon_key:
            raise RuntimeError("no polygon key")
        start = _dt.date.today() - _dt.timedelta(days=5)
        url = (f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/{start}/{_dt.date.today()}"
               f"?limit=5&apiKey={self._polygon_key}")
        async with aiohttp.ClientSession() as s, s.get(url, timeout=10) as r:
            if r.status == 429:
                raise _APILimitError
            js = await r.json()
        bars = js.get("results", [])[-5:]
        if not bars:
            raise RuntimeError("no bars")
        cur, prev = bars[-1]["c"], bars[-2]["c"]
        pct = round(((cur / prev) - 1)*100, 2)
        return {
            "current_price": round(cur, 2), "price_change_pct": pct,
            "volume": bars[-1]["v"], "avg_volume": int(sum(b["v"] for b in bars)/len(bars)),
            "market_cap": 0, "price_history": [round(b["c"], 2) for b in bars],
            "company_name": STOCK_NAME_MAPPING.get(sym, sym), "mentions": 0,
        }

    # ─────────────────────────  stage modeller  ────────────────────────
    async def _stage_wrapper(self, r: dict, p: dict) -> dict:
        def _calc():
            if not p["top_stocks"]:
                return "start", "no meme candidates"
            top = p["top_stocks"][0]
            mentions = top["mentions"]
            price_pct = top["price_change_pct"] or 0
            days = top[SENSOR_DAYS_ACTIVE]
            if mentions < 5:
                return "start", f"{mentions} mentions"
            if price_pct > 5 and days <= 21:
                return "stock_rising", f"{price_pct:+.1f}% today"
            if days > 21 and price_pct < -5:
                return "dropping", f"{price_pct:+.1f}% today"
            return "rising_interest", f"{mentions} mentions"
        stage, reason = await self.hass.async_add_executor_job(_calc)
        return {
            "meme_stage_key": stage,
            "meme_stage": MEME_STOCK_STAGES.get(stage, stage),
            "stage_reason": reason,
        }

    # ─────────────────────────  dynamic subreddit  ─────────────────────
    async def _async_refresh_dynamic_sr(self, _now):
        try:
            posts = await self.hass.async_add_executor_job(
                lambda: list(self._reddit.subreddit("all").top(time_filter="week", limit=200))
            )
            tally = defaultdict(int)
            for p in posts:
                tally[p.subreddit.display_name.lower()] += 1
            for name, _ in sorted(tally.items(), key=lambda x: x[1], reverse=True):
                if name not in self._subreddits:
                    self._dynamic_sr = name
                    _LOGGER.info("Dynamic subreddit set → %s", name)
                    return
        except Exception:
            pass

    # ───────────────────────────── fallback ───────────────────────────
    def _fallback(self, status="error") -> dict:
        return {
            "total_mentions": 0, "average_sentiment": 0, "trending_count": 0,
            "stock_mentions": {}, "trending_stocks": [],
            "stock_prices": {}, "top_stocks": [],
            "meme_stage": "Start", "meme_stage_key": "start", "stage_reason": "",
            "status": status, "last_updated": datetime.now().isoformat(),
        }
