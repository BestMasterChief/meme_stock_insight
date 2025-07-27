"""Data update coordinator for Meme Stock Insight."""
from __future__ import annotations

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

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Initialize Reddit client if not already done
            if self.reddit is None:
                await self._async_setup_reddit()

            # Fetch data from Reddit in executor
            data = await self.hass.async_add_executor_job(self._fetch_reddit_data)
            return data

        except Exception as exc:
            raise UpdateFailed(f"Error communicating with Reddit API: {exc}") from exc

    async def _async_setup_reddit(self) -> None:
        """Set up Reddit client in executor thread."""
        def _setup_reddit():
            """Set up Reddit client with proper configuration."""
            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=f"homeassistant:meme_stock_insight:v0.0.3 (by /u/{self.username})",
                username=self.username,
                password=self.password,
                ratelimit_seconds=5,
                check_for_updates=False,  # Disable update check to prevent blocking calls
                check_for_async=False,    # Disable async check since we're in executor
            )

            # Verify authentication works
            try:
                me = reddit.user.me()
                if me is None:
                    raise RuntimeError("Reddit login unexpectedly read-only")
                _LOGGER.info("Successfully authenticated with Reddit as %s", me.name)
            except Exception as exc:
                raise RuntimeError(f"Reddit auth failed: {exc}") from exc

            return reddit

        try:
            self.reddit = await self.hass.async_add_executor_job(_setup_reddit)
        except Exception as exc:
            raise UpdateFailed(f"Failed to initialize Reddit client: {exc}") from exc

    def _fetch_reddit_data(self) -> dict[str, Any]:
        """Fetch data from Reddit (runs in executor thread)."""
        mentions = {}
        sentiment_scores = {}
        trending_stocks = []
        total_mentions = 0

        try:
            for subreddit_name in self.subreddits:
                subreddit_name = subreddit_name.strip()
                _LOGGER.debug("Processing subreddit: %s", subreddit_name)

                try:
                    subreddit = self.reddit.subreddit(subreddit_name)

                    # Get hot posts from the last 24 hours
                    for submission in subreddit.hot(limit=50):
                        # Process submission title and text
                        text_content = f"{submission.title} {getattr(submission, 'selftext', '')}"

                        # Extract stock mentions
                        found_stocks = self._extract_stock_mentions(text_content)

                        for stock in found_stocks:
                            mentions[stock] = mentions.get(stock, 0) + 1
                            total_mentions += 1

                            # Calculate sentiment
                            sentiment = self._calculate_sentiment(text_content)
                            sentiment_scores[stock] = sentiment_scores.get(stock, []) + [sentiment]

                        # Process top comments
                        submission.comments.replace_more(limit=5)
                        for comment in submission.comments.list()[:20]:
                            if hasattr(comment, 'body'):
                                comment_stocks = self._extract_stock_mentions(comment.body)

                                for stock in comment_stocks:
                                    mentions[stock] = mentions.get(stock, 0) + 1
                                    total_mentions += 1

                                    sentiment = self._calculate_sentiment(comment.body)
                                    sentiment_scores[stock] = sentiment_scores.get(stock, []) + [sentiment]

                except prawcore.exceptions.NotFound:
                    _LOGGER.warning("Subreddit %s not found or private", subreddit_name)
                    continue
                except Exception as exc:
                    _LOGGER.warning("Error processing subreddit %s: %s", subreddit_name, exc)
                    continue

            # Calculate average sentiment scores
            avg_sentiment = {}
            for stock, scores in sentiment_scores.items():
                if scores:
                    avg_sentiment[stock] = sum(scores) / len(scores)
                else:
                    avg_sentiment[stock] = 0.0

            # Determine trending stocks (top mentioned)
            sorted_mentions = sorted(mentions.items(), key=lambda x: x[1], reverse=True)
            trending_stocks = [{"symbol": stock, "mentions": count} for stock, count in sorted_mentions[:10]]

            return {
                "mentions": mentions,
                "sentiment": avg_sentiment,
                "trending": trending_stocks,
                "total_mentions": total_mentions,
                "last_update": datetime.now().isoformat(),
            }

        except Exception as exc:
            _LOGGER.error("Error fetching Reddit data: %s", exc)
            raise

    def _extract_stock_mentions(self, text: str) -> set[str]:
        """Extract stock symbol mentions from text."""
        if not text:
            return set()

        text = text.upper()
        found_stocks = set()

        # Look for stock symbols in the text
        for symbol in MEME_STOCK_SYMBOLS:
            # Use word boundaries to avoid partial matches
            pattern = rf"\b{re.escape(symbol)}\b"
            if re.search(pattern, text):
                # Check for false positives
                if not self._is_false_positive(text, symbol):
                    found_stocks.add(symbol)

        # Also look for $SYMBOL format
        dollar_pattern = r"\$([A-Z]{1,5})\b"
        dollar_matches = re.findall(dollar_pattern, text)
        for match in dollar_matches:
            if match in MEME_STOCK_SYMBOLS and not self._is_false_positive(text, match):
                found_stocks.add(match)

        return found_stocks

    def _is_false_positive(self, text: str, symbol: str) -> bool:
        """Check if a stock mention is likely a false positive."""
        text_lower = text.lower()

        for keyword in FALSE_POSITIVE_KEYWORDS.get(symbol, []):
            if keyword.lower() in text_lower:
                return True

        return False

    def _calculate_sentiment(self, text: str) -> float:
        """Calculate basic sentiment score for text."""
        if not text:
            return 0.0

        text_lower = text.lower()
        positive_score = 0
        negative_score = 0

        # Count positive sentiment keywords
        for keyword in SENTIMENT_KEYWORDS_POSITIVE:
            positive_score += text_lower.count(keyword)

        # Count negative sentiment keywords
        for keyword in SENTIMENT_KEYWORDS_NEGATIVE:
            negative_score += text_lower.count(keyword)

        # Calculate sentiment score (-1 to 1)
        total_sentiment_words = positive_score + negative_score
        if total_sentiment_words == 0:
            return 0.0

        return (positive_score - negative_score) / total_sentiment_words
