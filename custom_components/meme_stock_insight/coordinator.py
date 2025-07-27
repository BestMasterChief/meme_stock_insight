"""Data update coordinator for Meme Stock Insight - Balanced approach."""
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
        self.subreddits = [s.strip() for s in subreddits.split(",")]
        self.reddit = None
        self._setup_complete = False

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Setup Reddit client if not already done
            if not self._setup_complete:
                await self._async_setup_reddit()
                self._setup_complete = True
                _LOGGER.info("Reddit client setup completed")

            # Fetch data from Reddit with timeout protection
            data = await asyncio.wait_for(
                self.hass.async_add_executor_job(self._fetch_reddit_data),
                timeout=90  # 90 second timeout for data fetching
            )
            
            _LOGGER.debug(f"Fetched data: {data.get('total_mentions', 0)} mentions, "
                         f"{data.get('posts_processed', 0)} posts processed")
            return data

        except asyncio.TimeoutError:
            _LOGGER.warning("Reddit data fetch timed out, returning fallback data")
            return self._get_fallback_data("timeout")
        except Exception as exc:
            _LOGGER.error(f"Error fetching Reddit data: {exc}")
            return self._get_fallback_data(f"error: {str(exc)[:50]}")

    async def _async_setup_reddit(self) -> None:
        """Set up Reddit client in executor thread."""
        def _setup_reddit():
            """Setup Reddit client with proper configuration."""
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
                    timeout=30,
                )
                
                # Validate authentication
                me = reddit.user.me()
                if me is None:
                    raise ValueError("Authentication failed - ensure app is script type")
                
                _LOGGER.info(f"Reddit authentication successful for user: {me.name}")
                return reddit
                
            except Exception as exc:
                _LOGGER.error(f"Reddit setup failed: {exc}")
                raise UpdateFailed(f"Reddit setup failed: {exc}")

        try:
            self.reddit = await asyncio.wait_for(
                self.hass.async_add_executor_job(_setup_reddit),
                timeout=45  # 45 second timeout for setup
            )
        except asyncio.TimeoutError:
            raise UpdateFailed("Reddit setup timed out")

    def _fetch_reddit_data(self) -> dict[str, Any]:
        """Fetch Reddit data with reasonable limits."""
        try:
            stock_mentions = {}
            sentiment_scores = []
            processed_posts = 0
            
            # Process up to 5 subreddits, 30 posts each
            max_subreddits = min(5, len(self.subreddits))
            max_posts_per_subreddit = 30
            max_comments_per_post = 10
            
            for subreddit_name in self.subreddits[:max_subreddits]:
                try:
                    _LOGGER.debug(f"Processing subreddit: {subreddit_name}")
                    subreddit = self.reddit.subreddit(subreddit_name.strip())
                    
                    # Get hot posts
                    posts = list(subreddit.hot(limit=max_posts_per_subreddit))
                    
                    for submission in posts:
                        if processed_posts >= 100:  # Maximum total posts
                            break
                        
                        # Process submission title and text
                        self._process_text(submission.title, stock_mentions, sentiment_scores)
                        if hasattr(submission, 'selftext') and submission.selftext:
                            self._process_text(submission.selftext[:1000], stock_mentions, sentiment_scores)
                        
                        processed_posts += 1
                        
                        # Process comments (limited)
                        try:
                            submission.comments.replace_more(limit=1)
                            comment_count = 0
                            for comment in submission.comments:
                                if comment_count >= max_comments_per_post:
                                    break
                                if hasattr(comment, 'body') and len(comment.body) < 1000:
                                    self._process_text(comment.body, stock_mentions, sentiment_scores)
                                    comment_count += 1
                        except Exception as e:
                            _LOGGER.debug(f"Error processing comments: {e}")
                            continue
                            
                except prawcore.exceptions.Forbidden:
                    _LOGGER.warning(f"Access forbidden to subreddit: {subreddit_name}")
                    continue
                except Exception as e:
                    _LOGGER.warning(f"Error processing subreddit {subreddit_name}: {e}")
                    continue

            # Calculate final metrics
            total_mentions = sum(stock_mentions.values())
            average_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0.0
            
            # Get trending stocks (stocks with 2+ mentions)
            trending_stocks = [
                {"symbol": symbol, "mentions": count}
                for symbol, count in sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)
                if count >= 2
            ]
            
            # Sentiment distribution
            positive = sum(1 for s in sentiment_scores if s > 0.1)
            negative = sum(1 for s in sentiment_scores if s < -0.1)
            neutral = len(sentiment_scores) - positive - negative
            
            return {
                "total_mentions": total_mentions,
                "average_sentiment": round(average_sentiment, 3),
                "trending_count": len(trending_stocks),
                "stock_mentions": dict(sorted(stock_mentions.items(), key=lambda x: x[1], reverse=True)[:20]),
                "sentiment_distribution": {
                    "positive": positive,
                    "neutral": neutral,
                    "negative": negative
                },
                "trending_stocks": trending_stocks[:15],
                "last_updated": datetime.now().isoformat(),
                "status": "success",
                "posts_processed": processed_posts,
                "subreddits_processed": [s for s in self.subreddits[:max_subreddits]]
            }
            
        except Exception as exc:
            _LOGGER.error(f"Reddit data fetch failed: {exc}")
            raise

    def _process_text(self, text: str, stock_mentions: dict, sentiment_scores: list) -> None:
        """Process text for stock mentions and sentiment."""
        if not text or len(text) > 2000:  # Skip very long texts
            return
            
        # Find stock symbols (2-5 capital letters)
        words = re.findall(r'\b[A-Z]{2,5}\b', text.upper())
        
        for word in words[:50]:  # Limit words processed per text
            if word in MEME_STOCK_SYMBOLS:
                # Check for false positives
                if word in FALSE_POSITIVE_KEYWORDS:
                    text_lower = text.lower()
                    if any(fp_word in text_lower for fp_word in FALSE_POSITIVE_KEYWORDS[word][:5]):
                        continue
                
                stock_mentions[word] = stock_mentions.get(word, 0) + 1
        
        # Sentiment analysis
        text_lower = text.lower()
        
        # Count positive and negative keywords
        positive_count = sum(1 for word in SENTIMENT_KEYWORDS_POSITIVE if word in text_lower)
        negative_count = sum(1 for word in SENTIMENT_KEYWORDS_NEGATIVE if word in text_lower)
        
        # Calculate sentiment score
        if positive_count > 0 or negative_count > 0:
            total_sentiment_words = positive_count + negative_count
            sentiment_score = (positive_count - negative_count) / total_sentiment_words
            sentiment_scores.append(sentiment_score)

    def _get_fallback_data(self, status: str) -> dict[str, Any]:
        """Return fallback data when fetch fails."""
        return {
            "total_mentions": 0,
            "average_sentiment": 0.0,
            "trending_count": 0,
            "stock_mentions": {},
            "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0},
            "trending_stocks": [],
            "last_updated": datetime.now().isoformat(),
            "status": status,
            "posts_processed": 0,
            "subreddits_processed": []
        }