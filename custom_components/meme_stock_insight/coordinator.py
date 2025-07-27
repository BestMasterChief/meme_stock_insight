"""Data update coordinator for Meme Stock Insight - Optimized for fast startup."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any

import praw
import prawcore
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    MEME_STOCK_SYMBOLS,
    FALSE_POSITIVE_KEYWORDS,
    SENTIMENT_KEYWORDS_POSITIVE,
    SENTIMENT_KEYWORDS_NEGATIVE,
)

_LOGGER = logging.getLogger(__name__)

class MemeStockInsightCoordinator(DataUpdateCoordinator):
    """Coordinator to manage fetching data from Reddit."""

    def __init__(
        self,
        hass: HomeAssistant,
        client_id: str,
        client_secret: str,
        username: str,
        password: str,
        subreddits: str,
        update_interval: int,
    ) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.client_id = client_id
        self.client_secret = client_secret
        self.username = username
        self.password = password
        self.subreddits = subreddits.split(",")
        self.reddit = None
        self._initialization_count = 0

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            self._initialization_count += 1
            
            # First call: Just return minimal data, don't even setup Reddit
            if self._initialization_count == 1:
                _LOGGER.debug("First refresh - returning minimal data structure")
                return self._get_minimal_startup_data()
            
            # Second call: Setup Reddit connection
            if self._initialization_count == 2:
                _LOGGER.debug("Second refresh - setting up Reddit connection")
                await self._async_setup_reddit()
                return self._get_connection_established_data()
            
            # Third call and beyond: Fetch real data
            _LOGGER.debug("Regular refresh - fetching Reddit data")
            return await self._async_fetch_data_with_timeout()

        except Exception as exc:
            _LOGGER.error("Error in coordinator update: %s", exc)
            # Return fallback data instead of raising to prevent integration failure
            return self._get_error_fallback_data(str(exc))

    def _get_minimal_startup_data(self) -> dict[str, Any]:
        """Return absolute minimal data for first startup."""
        return {
            "total_mentions": 0,
            "average_sentiment": 0.0,
            "trending_count": 0,
            "stock_mentions": {},
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "trending_stocks": [],
            "last_updated": datetime.now().isoformat(),
            "status": "starting"
        }

    def _get_connection_established_data(self) -> dict[str, Any]:
        """Return data after connection is established."""
        return {
            "total_mentions": 0,
            "average_sentiment": 0.0,
            "trending_count": 0,
            "stock_mentions": {},
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "trending_stocks": [],
            "last_updated": datetime.now().isoformat(),
            "status": "connected"
        }

    async def _async_setup_reddit(self) -> None:
        """Set up Reddit client in executor thread with aggressive timeout."""
        def _quick_setup():
            """Quick Reddit setup with minimal validation."""
            try:
                reddit = praw.Reddit(
                    client_id=self.client_id.strip(),
                    client_secret=self.client_secret.strip() or None,
                    user_agent=f"homeassistant:meme_stock_insight:v0.0.3 (by /u/{self.username.strip()})",
                    username=self.username.strip(),
                    password=self.password,
                    ratelimit_seconds=5,
                    check_for_updates=False,
                    check_for_async=False,
                    timeout=15,  # Short timeout
                )
                
                # Very quick validation - just try to access user info with timeout
                try:
                    me = reddit.user.me()
                    if me is None:
                        raise ValueError("Authentication failed")
                    _LOGGER.debug(f"Reddit authentication successful for user: {me.name}")
                except Exception as e:
                    _LOGGER.warning(f"Reddit user validation failed, but continuing: {e}")
                    # Continue anyway - the connection might still work for data fetching
                
                return reddit
                
            except Exception as exc:
                _LOGGER.error(f"Reddit setup failed: {exc}")
                raise

        try:
            # Very short timeout for setup
            self.reddit = await asyncio.wait_for(
                self.hass.async_add_executor_job(_quick_setup),
                timeout=10  # Only 10 seconds for setup
            )
            _LOGGER.debug("Reddit client setup completed")
            
        except asyncio.TimeoutError:
            _LOGGER.error("Reddit setup timed out after 10 seconds")
            raise UpdateFailed("Reddit setup timeout - will retry on next update")
        except Exception as exc:
            _LOGGER.error(f"Reddit setup failed: {exc}")
            raise UpdateFailed(f"Reddit setup failed: {exc}")

    async def _async_fetch_data_with_timeout(self) -> dict[str, Any]:
        """Fetch Reddit data with timeout protection."""
        if self.reddit is None:
            _LOGGER.warning("Reddit client not initialized, setting up now")
            await self._async_setup_reddit()
        
        try:
            # Aggressive timeout for data fetching
            data = await asyncio.wait_for(
                self.hass.async_add_executor_job(self._fetch_reddit_data_fast),
                timeout=45  # 45 second timeout
            )
            return data
            
        except asyncio.TimeoutError:
            _LOGGER.warning("Reddit data fetch timed out, returning cached data")
            return self.data or self._get_timeout_fallback_data()
        except Exception as exc:
            _LOGGER.error(f"Reddit data fetch failed: {exc}")
            return self._get_error_fallback_data(str(exc))

    def _fetch_reddit_data_fast(self) -> dict[str, Any]:
        """Fast Reddit data fetch with minimal processing."""
        try:
            stock_mentions = {}
            sentiment_scores = []
            processed_posts = 0
            max_posts_per_subreddit = 10  # Very limited for speed
            max_comments_per_post = 5     # Very limited for speed
            
            for subreddit_name in self.subreddits[:2]:  # Only process first 2 subreddits
                try:
                    subreddit = self.reddit.subreddit(subreddit_name.strip())
                    
                    # Very limited hot posts
                    posts = list(subreddit.hot(limit=max_posts_per_subreddit))
                    
                    for submission in posts:
                        if processed_posts >= 20:  # Hard limit on total posts
                            break
                            
                        # Process title quickly
                        self._process_text_fast(submission.title, stock_mentions, sentiment_scores)
                        processed_posts += 1
                        
                        # Skip comments if we're running behind
                        if processed_posts < 15:
                            try:
                                # Very minimal comment processing
                                submission.comments.replace_more(limit=0)
                                for comment in submission.comments[:max_comments_per_post]:
                                    if hasattr(comment, 'body') and len(comment.body) < 500:
                                        self._process_text_fast(comment.body, stock_mentions, sentiment_scores)
                            except Exception:
                                continue  # Skip problematic comments
                                
                except Exception as e:
                    _LOGGER.debug(f"Error processing subreddit {subreddit_name}: {e}")
                    continue

            # Quick metrics calculation
            total_mentions = sum(stock_mentions.values())
            average_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            trending_stocks = sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Simple sentiment distribution
            positive = sum(1 for s in sentiment_scores if s > 0.1)
            negative = sum(1 for s in sentiment_scores if s < -0.1)
            neutral = len(sentiment_scores) - positive - negative
            
            return {
                "total_mentions": total_mentions,
                "average_sentiment": round(average_sentiment, 3),
                "trending_count": len([s for s, c in stock_mentions.items() if c >= 2]),
                "stock_mentions": dict(trending_stocks),
                "sentiment_distribution": {"positive": positive, "neutral": neutral, "negative": negative},
                "trending_stocks": [{"symbol": s, "mentions": c} for s, c in trending_stocks],
                "last_updated": datetime.now().isoformat(),
                "status": "success",
                "posts_processed": processed_posts
            }
            
        except Exception as exc:
            _LOGGER.error(f"Fast Reddit data fetch failed: {exc}")
            raise

    def _process_text_fast(self, text: str, stock_mentions: dict, sentiment_scores: list) -> None:
        """Ultra-fast text processing."""
        if not text or len(text) > 500:  # Skip long texts
            return
            
        # Quick regex for stock symbols
        words = re.findall(r'\b[A-Z]{2,5}\b', text.upper())
        
        for word in words:
            if word in MEME_STOCK_SYMBOLS:
                # Minimal false positive check
                if word in ["IT", "A", "AM", "GO"] and word.lower() in text.lower():
                    continue
                stock_mentions[word] = stock_mentions.get(word, 0) + 1
        
        # Quick sentiment check
        text_lower = text.lower()
        positive_words = ["moon", "rocket", "bullish", "buy", "gains"]
        negative_words = ["crash", "dump", "bearish", "sell", "loss"]
        
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        if pos_count > neg_count:
            sentiment_scores.append(0.5)
        elif neg_count > pos_count:
            sentiment_scores.append(-0.5)

    def _get_timeout_fallback_data(self) -> dict[str, Any]:
        """Return fallback data for timeout scenarios."""
        return {
            "total_mentions": 0,
            "average_sentiment": 0.0,
            "trending_count": 0,
            "stock_mentions": {},
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "trending_stocks": [],
            "last_updated": datetime.now().isoformat(),
            "status": "timeout_fallback"
        }

    def _get_error_fallback_data(self, error_msg: str) -> dict[str, Any]:
        """Return fallback data for error scenarios."""
        return {
            "total_mentions": 0,
            "average_sentiment": 0.0,
            "trending_count": 0,
            "stock_mentions": {},
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "trending_stocks": [],
            "last_updated": datetime.now().isoformat(),
            "status": f"error: {error_msg[:100]}"  # Truncate long errors
        }