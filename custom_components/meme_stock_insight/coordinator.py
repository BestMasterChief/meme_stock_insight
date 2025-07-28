"""Data update coordinator for Meme Stock Insight v0.6.0"""
from __future__ import annotations

import asyncio
import logging
import re
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

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
    DEFAULT_SUBREDDITS,
    DYNAMIC_SUBREDDIT_REFRESH,
    DOMAIN,
    MAX_POSTS_PER_SUBREDDIT,
    MEME_STOCK_SYMBOLS,
    PRICE_PROVIDERS,
    API_LIMITS,
    QUOTA_RESET_INTERVAL,
    DEFAULT_UPDATE_INTERVAL,
    MEME_STOCK_STAGES,
    STOCK_NAME_MAPPING,
    SENTIMENT_KEYWORDS_POSITIVE,
    SENTIMENT_KEYWORDS_NEGATIVE,
)

_LOGGER = logging.getLogger(__name__)

class APILimitError(Exception):
    """Raised when API limit is exceeded."""


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
        self._reddit = None
        self._reddit_conf = reddit_conf
        self._subreddits: List[str] = options.get("subreddits", DEFAULT_SUBREDDITS)
        if isinstance(self._subreddits, str):
            self._subreddits = [s.strip() for s in self._subreddits.split(",")]
        
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

        # Schedule dynamic subreddit refresh
        async_track_time_interval(
            hass, self._async_refresh_dynamic_subreddit, DYNAMIC_SUBREDDIT_REFRESH
        )

    async def _async_setup_reddit(self):
        """Set up Reddit client."""
        if self._reddit is None:
            def _create_reddit():
                return praw.Reddit(
                    **self._reddit_conf,
                    check_for_updates=False,
                    check_for_async=False,
                    ratelimit_seconds=5,
                )
            
            self._reddit = await self.hass.async_add_executor_job(_create_reddit)
            
            # Verify authentication
            def _test_auth():
                user = self._reddit.user.me()
                if user is None:
                    raise UpdateFailed("Reddit authentication failed - read-only mode")
                return user.name
            
            username = await self.hass.async_add_executor_job(_test_auth)
            _LOGGER.info("Reddit authentication successful for user: %s", username)

    # -------------------------------------------------------------------------
    # Data update cycle
    # -------------------------------------------------------------------------
    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            # Ensure Reddit client is set up
            await self._async_setup_reddit()
            
            reddit_data = await self.hass.async_add_executor_job(self._gather_reddit)
            price_data = await self._gather_prices(reddit_data["mentions_dict"])
            return {**reddit_data, **price_data}
        except Exception as exc:
            _LOGGER.error("Update failed: %s", exc)
            raise UpdateFailed(str(exc)) from exc

    # -------------------------------------------------------------------------
    # Reddit helpers
    # -------------------------------------------------------------------------
    def _gather_reddit(self) -> Dict[str, Any]:
        """Fetch posts, count mentions, compute sentiment."""
        mentions: Dict[str, int] = defaultdict(int)
        sentiment_scores: List[float] = []

        sr_list = list(self._subreddits) + ([self._dynamic_sr] if self._dynamic_sr else [])
        for sr in sr_list[:5]:  # Limit to 5 subreddits
            try:
                subreddit = self._reddit.subreddit(sr)
                posts = list(subreddit.hot(limit=MAX_POSTS_PER_SUBREDDIT))
                for post in posts:
                    self._scan_text(post.title, mentions, sentiment_scores)
                    if hasattr(post, 'selftext') and post.selftext:
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
        """Scan text for stock symbols and sentiment."""
        if not text:
            return
        
        # Count symbols
        words = re.findall(r"\b[A-Z]{2,5}\b", text.upper())
        for word in words:
            if word in MEME_STOCK_SYMBOLS:
                bucket[word] += 1
        
        # Simple sentiment analysis
        text_lower = text.lower()
        pos = sum(text_lower.count(w) for w in SENTIMENT_KEYWORDS_POSITIVE)
        neg = sum(text_lower.count(w) for w in SENTIMENT_KEYWORDS_NEGATIVE)
        if pos + neg > 0:
            sents.append((pos - neg) / (pos + neg))

    # -------------------------------------------------------------------------
    # Price helpers with fallback ladder
    # -------------------------------------------------------------------------
    async def _gather_prices(self, mentions: Dict[str, int]) -> Dict[str, Any]:
        """Gather price data for top mentioned stocks."""
        # Reset daily quota window
        if datetime.now(timezone.utc) >= self._quota_reset_at:
            self._quota.clear()
            self._exhausted.clear()
            self._quota_reset_at = datetime.now(timezone.utc) + QUOTA_RESET_INTERVAL

        async def fetch_one(sym: str) -> Dict[str, Any]:
            """Fetch price data for one symbol with provider fallback."""
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
            
            # All providers failed or exhausted
            return {
                "current_price": None, 
                "price_change_pct": 0.0, 
                "volume": 0,
                "provider": "exhausted"
            }

        symbols = list(mentions)[:10]  # Limit to top 10 mentioned
        price_results = await asyncio.gather(*[fetch_one(s) for s in symbols], return_exceptions=True)

        # Handle any exceptions from gather
        for i, result in enumerate(price_results):
            if isinstance(result, Exception):
                _LOGGER.debug("Price fetch failed for %s: %s", symbols[i], result)
                price_results[i] = {
                    "current_price": None,
                    "price_change_pct": 0.0,
                    "volume": 0,
                    "provider": "error"
                }

        price_map = dict(zip(symbols, price_results))
        top_sorted = sorted(symbols, key=lambda s: mentions[s], reverse=True)[:3]

        now = datetime.now(timezone.utc)
        top_entities = []
        for rank, sym in enumerate(top_sorted, start=1):
            pdata = price_map[sym]
            
            # Track first seen
            if sym not in self._first_seen:
                self._first_seen[sym] = now
                self._first_price[sym] = pdata["current_price"] or 0.0
            
            days_active = (now - self._first_seen[sym]).days
            since_start = 0.0
            if self._first_price[sym] and pdata["current_price"]:
                since_start = ((pdata["current_price"] / self._first_price[sym]) - 1) * 100
            
            top_entities.append({
                "symbol": sym,
                "company": STOCK_NAME_MAPPING.get(sym, sym),
                "rank": rank,
                "mentions": mentions[sym],
                "days_active": days_active,
                "price_since_start": round(since_start, 2),
                **pdata,
            })

        stage = self._determine_stage(top_entities[0] if top_entities else None)

        return {
            "top_entities": top_entities,
            "stage": stage,
            "price_map": price_map,
        }

    # Individual provider fetchers
    async def _price_yfinance(self, sym: str) -> Dict[str, Any]:
        """Fetch price from Yahoo Finance."""
        def _sync():
            try:
                ticker = yf.Ticker(sym)
                hist = ticker.history(period="5d")
                if hist.empty:
                    raise RuntimeError("No Yahoo data")
                
                current = hist["Close"].iloc[-1]
                previous = hist["Close"].iloc[-2] if len(hist) > 1 else current
                change_pct = round(((current / previous) - 1) * 100, 2) if previous else 0.0
                
                return {
                    "current_price": round(float(current), 2),
                    "price_change_pct": change_pct,
                    "volume": int(hist["Volume"].iloc[-1]) if not hist["Volume"].empty else 0,
                    "provider": "yfinance",
                }
            except Exception as e:
                _LOGGER.debug("Yahoo Finance error for %s: %s", sym, e)
                raise

        return await self.hass.async_add_executor_job(_sync)

    async def _price_alpha_vantage(self, sym: str) -> Dict[str, Any]:
        """Fetch price from Alpha Vantage (if key provided)."""
        if not self._alpha_key:
            raise RuntimeError("No Alpha Vantage key")
        
        def _sync():
            try:
                from alpha_vantage.timeseries import TimeSeries
                ts = TimeSeries(self._alpha_key, output_format="json")
                data, _ = ts.get_daily(sym, "compact")
                
                rows = list(data.values())[:2]
                if not rows:
                    raise RuntimeError("Empty Alpha Vantage data")
                
                current = float(rows[0]["4. close"])
                previous = float(rows[1]["4. close"]) if len(rows) > 1 else current
                change_pct = round(((current / previous) - 1) * 100, 2) if previous else 0.0
                
                return {
                    "current_price": round(current, 2),
                    "price_change_pct": change_pct,
                    "volume": int(rows[0]["5. volume"]),
                    "provider": "alpha_vantage",
                }
            except Exception as e:
                if "call frequency" in str(e).lower():
                    raise APILimitError("Alpha Vantage rate limit")
                raise

        return await self.hass.async_add_executor_job(_sync)

    async def _price_polygon(self, sym: str) -> Dict[str, Any]:
        """Fetch price from Polygon (if key provided)."""
        if not self._polygon_key:
            raise RuntimeError("No Polygon key")
        
        import aiohttp
        from datetime import date, timedelta as td
        
        start_date = date.today() - td(days=5)
        end_date = date.today()
        
        url = (
            f"https://api.polygon.io/v2/aggs/ticker/{sym}/range/1/day/"
            f"{start_date}/{end_date}?limit=2&apiKey={self._polygon_key}"
        )
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 429:
                    raise APILimitError("Polygon rate limit")
                
                data = await response.json()
                bars = data.get("results", [])
                
                if len(bars) < 1:
                    raise RuntimeError("Insufficient Polygon data")
                
                current = bars[-1]["c"]
                previous = bars[-2]["c"] if len(bars) > 1 else current
                change_pct = round(((current / previous) - 1) * 100, 2) if previous else 0.0
                
                return {
                    "current_price": round(current, 2),
                    "price_change_pct": change_pct,
                    "volume": bars[-1]["v"],
                    "provider": "polygon",
                }

    def _bump_quota(self, provider: str):
        """Increment quota counter for provider."""
        limit = API_LIMITS.get(provider, 0)
        if limit:
            self._quota[provider] += 1
            if self._quota[provider] >= limit:
                self._exhausted.add(provider)

    def _determine_stage(self, top: Dict[str, Any] | None) -> str:
        """Determine current meme stock stage."""
        if not top or top["current_price"] is None:
            return MEME_STOCK_STAGES["start"]
        
        days = top["days_active"]
        price_pct = top["price_change_pct"]
        mentions = top["mentions"]
        
        if mentions < 5:
            return MEME_STOCK_STAGES["start"]
        elif price_pct > 10:
            return MEME_STOCK_STAGES["within_estimated_peak"]
        elif price_pct > 5 and days < 14:
            return MEME_STOCK_STAGES["stock_rising"]
        elif price_pct < -5:
            return MEME_STOCK_STAGES["dropping"]
        else:
            return MEME_STOCK_STAGES["rising_interest"]

    async def _async_refresh_dynamic_subreddit(self, _):
        """Weekly discovery of high-traffic trading subreddit."""
        if not self._reddit:
            return
            
        try:
            def _get_top_posts():
                return list(self._reddit.subreddit("all").top(limit=200, time_filter="week"))
            
            top_week = await self.hass.async_add_executor_job(_get_top_posts)
            tally = defaultdict(int)
            
            for post in top_week:
                sr_name = post.subreddit.display_name.lower()
                tally[sr_name] += 1
            
            # Find highest scoring subreddit not already in our list
            for name, _ in sorted(tally.items(), key=lambda x: x[1], reverse=True):
                if name not in [sr.lower() for sr in self._subreddits]:
                    self._dynamic_sr = name
                    _LOGGER.info("Dynamic subreddit switched to %s", name)
                    return
                    
        except Exception as err:
            _LOGGER.debug("Dynamic subreddit discovery failed: %s", err)