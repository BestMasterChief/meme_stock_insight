"""Data update coordinator for Meme Stock Insight integration."""
from __future__ import annotations

import asyncio
import logging
import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

import praw
import prawcore
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    FALSE_POSITIVE_FILTERS,
    REDDIT_RATE_LIMIT_SECONDS,
    REDDIT_USER_AGENT_TEMPLATE,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

class MemeStockInsightCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from Reddit API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        
        self.entry = entry
        self.config = entry.data
        
        # Initialize Reddit client
        self.reddit = self._initialize_reddit_client()
        
        # Configuration
        self.subreddits = [s.strip() for s in self.config["subreddits"].split(",")]
        self.stock_symbols = [s.strip().upper() for s in self.config["stock_symbols"].split(",")]
        self.scan_limit = self.config.get("scan_limit", 100)
        
        # Compile regex patterns for stock detection
        self._compile_stock_patterns()

    def _initialize_reddit_client(self) -> praw.Reddit:
        """Initialize and validate Reddit client."""
        try:
            reddit = praw.Reddit(
                client_id=self.config["reddit_client_id"].strip(),
                client_secret=self.config["reddit_client_secret"].strip(),
                user_agent=REDDIT_USER_AGENT_TEMPLATE.format(
                    version=VERSION,
                    username=self.config["reddit_username"]
                ),
                username=self.config["reddit_username"].strip(),
                password=self.config["reddit_password"],
                ratelimit_seconds=REDDIT_RATE_LIMIT_SECONDS,
            )
            
            # Test authentication
            me = reddit.user.me()
            if me is None:
                raise UpdateFailed("Reddit login unexpectedly read-only")
                
            _LOGGER.info("Successfully initialized Reddit client for user: %s", me.name)
            return reddit
            
        except prawcore.exceptions.OAuthException as err:
            raise UpdateFailed(f"Reddit OAuth failed: {err}") from err
        except prawcore.exceptions.ResponseException as err:
            raise UpdateFailed(f"Reddit API error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Reddit client initialization failed: {err}") from err

    def _compile_stock_patterns(self) -> None:
        """Compile regex patterns for stock symbol detection."""
        # Create pattern for configured stock symbols
        symbol_pattern = r'\b(?:' + '|'.join(re.escape(symbol) for symbol in self.stock_symbols) + r')\b'
        self.stock_pattern = re.compile(symbol_pattern, re.IGNORECASE)
        
        # General stock symbol pattern (1-5 uppercase letters)
        self.general_stock_pattern = re.compile(r'\b[A-Z]{1,5}\b')
        
        # False positive filters
        false_positives = set()
        for filter_list in FALSE_POSITIVE_FILTERS.values():
            false_positives.update(word.upper() for word in filter_list)
        self.false_positives = false_positives

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from Reddit API."""
        try:
            _LOGGER.debug("Starting Reddit data fetch")
            
            all_mentions = Counter()
            sentiment_scores = defaultdict(list)
            post_count = 0
            
            for subreddit_name in self.subreddits:
                try:
                    subreddit = self.reddit.subreddit(subreddit_name)
                    
                    # Get hot posts from subreddit
                    posts = list(subreddit.hot(limit=self.scan_limit // len(self.subreddits)))
                    
                    for post in posts:
                        post_count += 1
                        
                        # Analyze post title and content
                        text = f"{post.title} {post.selftext}".upper()
                        
                        # Find stock mentions
                        mentioned_stocks = self._extract_stock_symbols(text)
                        
                        # Calculate sentiment score (simple implementation)
                        sentiment = self._calculate_sentiment(text)
                        
                        # Update counters
                        for stock in mentioned_stocks:
                            all_mentions[stock] += 1
                            sentiment_scores[stock].append(sentiment)
                        
                        # Rate limiting
                        await asyncio.sleep(0.1)
                        
                except prawcore.exceptions.NotFound:
                    _LOGGER.warning("Subreddit not found: %s", subreddit_name)
                    continue
                except prawcore.exceptions.Forbidden:
                    _LOGGER.warning("Access forbidden to subreddit: %s", subreddit_name)
                    continue
                except Exception as err:
                    _LOGGER.error("Error processing subreddit %s: %s", subreddit_name, err)
                    continue
            
            # Calculate average sentiment scores
            avg_sentiment = {}
            for stock, scores in sentiment_scores.items():
                avg_sentiment[stock] = sum(scores) / len(scores) if scores else 0
            
            # Get trending stocks (top 10 by mentions)
            trending_stocks = dict(all_mentions.most_common(10))
            
            # Calculate overall sentiment
            overall_sentiment = (
                sum(avg_sentiment.values()) / len(avg_sentiment) 
                if avg_sentiment else 0
            )
            
            data = {
                "mentions": dict(all_mentions),
                "sentiment_scores": avg_sentiment,
                "trending_stocks": trending_stocks,
                "overall_sentiment": overall_sentiment,
                "total_posts_analyzed": post_count,
                "last_updated": datetime.now().isoformat(),
                "subreddits_scanned": self.subreddits,
            }
            
            _LOGGER.info(
                "Successfully fetched Reddit data: %d mentions across %d posts",
                sum(all_mentions.values()),
                post_count
            )
            
            return data
            
        except prawcore.exceptions.ResponseException as err:
            raise UpdateFailed(f"Reddit API error: {err}") from err
        except Exception as err:
            _LOGGER.exception("Unexpected error during data update")
            raise UpdateFailed(f"Failed to update data: {err}") from err

    def _extract_stock_symbols(self, text: str) -> set[str]:
        """Extract stock symbols from text."""
        symbols = set()
        
        # Find matches using general pattern
        matches = self.general_stock_pattern.findall(text)
        
        for match in matches:
            symbol = match.upper()
            
            # Filter out false positives
            if symbol not in self.false_positives:
                symbols.add(symbol)
        
        # Also check for configured stock symbols specifically
        configured_matches = self.stock_pattern.findall(text)
        symbols.update(match.upper() for match in configured_matches)
        
        return symbols

    def _calculate_sentiment(self, text: str) -> float:
        """Calculate simple sentiment score for text."""
        # Simple keyword-based sentiment analysis
        positive_words = [
            "BULLISH", "MOON", "ROCKET", "DIAMOND", "HANDS", "BUY", "HODL", 
            "SQUEEZE", "TENDIES", "UP", "RISE", "GAIN", "PROFIT", "WIN"
        ]
        
        negative_words = [
            "BEARISH", "CRASH", "DROP", "FALL", "DOWN", "LOSS", "SELL", 
            "PAPER", "HANDS", "DUMP", "RED", "BLEED", "DEAD"
        ]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        # Return normalized sentiment score (-1 to 1)
        total_words = len(text.split())
        if total_words == 0:
            return 0
            
        sentiment = (positive_count - negative_count) / total_words
        return max(-1, min(1, sentiment * 10))  # Scale and clamp