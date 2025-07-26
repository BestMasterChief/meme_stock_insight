"""Data update coordinator for Meme Stock Insight."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
import numpy as np
import praw
import prawcore
from scipy import stats
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
    VERSION,
    DEFAULT_SUBREDDITS,
    DEFAULT_MIN_POSTS,
    DEFAULT_MIN_KARMA,
    STAGE_INITIATION,
    STAGE_UPRAMP,
    STAGE_TIPPING,
    STAGE_DO_NOT_INVEST,
    WEIGHT_VOLUME,
    WEIGHT_SENTIMENT,
    WEIGHT_MOMENTUM,
    WEIGHT_SHORT_INTEREST,
    USER_AGENT_TEMPLATE,
    REDDIT_RATE_LIMIT_SECONDS,
    FALSE_POSITIVE_TICKERS,
)

_LOGGER = logging.getLogger(__name__)

class MemeStockDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching meme stock data."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        name: str,
        update_interval: timedelta,
        session: aiohttp.ClientSession,
        config: Dict[str, Any],
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(hass, logger, name=name, update_interval=update_interval)
        self.session = session
        self.config = config
        self.sentiment_analyzer = SentimentIntensityAnalyzer()
        self.storage = Store(hass, 1, f"{DOMAIN}_cache")
        self.historical_data: Dict[str, List[Dict]] = {}

        # Reddit setup with improved authentication
        username = config.get("reddit_username", "anonymous")
        self.reddit = praw.Reddit(
            client_id=config.get("reddit_client_id"),
            client_secret=config.get("reddit_client_secret"),
            user_agent=USER_AGENT_TEMPLATE.format(version=VERSION, username=username),
            username=username,
            password=config.get("reddit_password"),
            ratelimit_seconds=REDDIT_RATE_LIMIT_SECONDS,
        )

        # Verify Reddit authentication during initialization
        try:
            if self.reddit.user.me() is None:
                raise RuntimeError("Reddit login unexpectedly read-only")
        except Exception as exc:
            raise UpdateFailed(f"Reddit auth failed: {exc}") from exc

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from Reddit and other sources."""
        try:
            # Fetch social sentiment data
            sentiment_data = await self._fetch_social_sentiment()

            # Fetch market data
            market_data = await self._fetch_market_data(list(sentiment_data.keys()))

            # Fetch Trading212 shortable stocks
            shortable_stocks = await self._fetch_trading212_shortable()

            # Process and combine data
            processed_data = await self._process_meme_stocks(
                sentiment_data, market_data, shortable_stocks
            )

            return processed_data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}")

    async def _fetch_social_sentiment(self) -> Dict[str, Dict[str, Any]]:
        """Fetch sentiment data from Reddit and other social platforms."""
        sentiment_data = {}
        subreddits = self.config.get("subreddits", DEFAULT_SUBREDDITS)
        min_karma = self.config.get("min_karma", DEFAULT_MIN_KARMA)

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get hot posts from the last 24 hours
                for submission in subreddit.hot(limit=100):
                    # Skip posts with insufficient karma
                    if submission.score < min_karma:
                        continue

                    # Extract stock tickers from title and content
                    text_content = submission.title + " " + (submission.selftext or "")
                    tickers = self._extract_tickers(text_content)

                    if not tickers:
                        continue

                    # Analyze sentiment
                    sentiment_score = self.sentiment_analyzer.polarity_scores(text_content)

                    # Process each ticker mentioned
                    for ticker in tickers:
                        if ticker not in sentiment_data:
                            sentiment_data[ticker] = {
                                "posts": [],
                                "total_karma": 0,
                                "avg_sentiment": 0,
                                "post_count": 0,
                            }

                        # Add post data
                        post_data = {
                            "timestamp": datetime.fromtimestamp(submission.created_utc),
                            "karma": submission.score,
                            "sentiment": sentiment_score["compound"],
                            "subreddit": subreddit_name,
                            "title": submission.title[:100],  # Truncate for storage
                        }

                        sentiment_data[ticker]["posts"].append(post_data)
                        sentiment_data[ticker]["total_karma"] += submission.score
                        sentiment_data[ticker]["post_count"] += 1

            except prawcore.exceptions.ResponseException as e:
                _LOGGER.warning(f"Reddit API error for r/{subreddit_name}: {e}")
            except Exception as e:
                _LOGGER.warning(f"Error fetching from r/{subreddit_name}: {e}")

        # Calculate average sentiment for each ticker
        for ticker_data in sentiment_data.values():
            if ticker_data["posts"]:
                ticker_data["avg_sentiment"] = np.mean([
                    post["sentiment"] for post in ticker_data["posts"]
                ])

        return sentiment_data

    async def _fetch_market_data(self, tickers: List[str]) -> Dict[str, Dict[str, Any]]:
        """Fetch market data for given tickers."""
        market_data = {}
        polygon_api_key = self.config.get("polygon_api_key")

        # If Polygon API key is provided, fetch real market data
        if polygon_api_key:
            for ticker in tickers:
                try:
                    # This is a placeholder for Polygon.io integration
                    # You would implement actual API calls here
                    market_data[ticker] = {
                        "current_price": 0.0,
                        "price_change_24h": 0.0,
                        "price_change_3d": 0.0,
                        "volume": 0,
                        "short_interest": 0.0,
                        "company_name": ticker,
                    }
                except Exception as e:
                    _LOGGER.warning(f"Error fetching market data for {ticker}: {e}")
        else:
            # Use placeholder data structure
            for ticker in tickers:
                market_data[ticker] = {
                    "current_price": 0.0,
                    "price_change_24h": 0.0,
                    "price_change_3d": 0.0,
                    "volume": 0,
                    "short_interest": 0.0,
                    "company_name": ticker,
                }

        return market_data

    async def _fetch_trading212_shortable(self) -> List[str]:
        """Fetch list of stocks that can be shorted on Trading212."""
        trading212_api_key = self.config.get("trading212_api_key")
        
        if trading212_api_key:
            try:
                # This is a placeholder for Trading212 API integration
                # You would implement actual API calls here
                return ["GME", "AMC", "TSLA", "AAPL", "MSFT", "NVDA"]
            except Exception as e:
                _LOGGER.warning(f"Error fetching Trading212 shortable stocks: {e}")
        
        # Return common shortable stocks as fallback
        return ["GME", "AMC", "TSLA", "AAPL", "MSFT", "NVDA"]

    def _extract_tickers(self, text: str) -> List[str]:
        """Extract stock tickers from text using regex patterns."""
        # Pattern to match $TICKER or TICKER: format
        pattern = r'\$([A-Z]{1,5})\b|\b([A-Z]{2,5})(?=\s*:)'
        matches = re.findall(pattern, text.upper())
        
        # Flatten the matches and filter common false positives
        tickers = [match[0] or match[1] for match in matches]
        
        # Filter out common false positives and ensure minimum length
        return [
            ticker for ticker in tickers 
            if ticker not in FALSE_POSITIVE_TICKERS and len(ticker) >= 2
        ]

    async def _process_meme_stocks(
        self,
        sentiment_data: Dict[str, Dict[str, Any]],
        market_data: Dict[str, Dict[str, Any]],
        shortable_stocks: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Process and combine all data to create meme stock insights."""
        processed_stocks = {}
        min_posts = self.config.get("min_posts", DEFAULT_MIN_POSTS)

        for ticker in sentiment_data.keys():
            if sentiment_data[ticker]["post_count"] < min_posts:
                continue

            # Calculate various scores
            volume_score = self._calculate_volume_score(ticker, sentiment_data[ticker])
            sentiment_score = sentiment_data[ticker]["avg_sentiment"]
            momentum_score = self._calculate_momentum_score(ticker, market_data.get(ticker, {}))
            short_interest_score = market_data.get(ticker, {}).get("short_interest", 0) / 100

            # Calculate composite impact score
            impact_score = (
                WEIGHT_VOLUME * volume_score +
                WEIGHT_SENTIMENT * max(0, sentiment_score) +  # Only positive sentiment contributes
                WEIGHT_MOMENTUM * momentum_score +
                WEIGHT_SHORT_INTEREST * short_interest_score
            ) * 100

            # Calculate meme likelihood
            meme_likelihood = self._calculate_meme_likelihood(
                volume_score, sentiment_score, momentum_score
            )

            # Determine stage
            stage = self._determine_meme_stage(
                sentiment_score, momentum_score, sentiment_data[ticker]["posts"]
            )

            # Calculate days active
            days_active = self._calculate_days_active(ticker, sentiment_data[ticker]["posts"])

            # Check if stock can be shorted
            is_shortable = ticker in shortable_stocks

            # Check decline flag
            decline_flag = self._check_decline_flag(sentiment_score, momentum_score)

            processed_stocks[ticker] = {
                "ticker": ticker,
                "name": market_data.get(ticker, {}).get("company_name", ticker),
                "impact_score": round(impact_score, 2),
                "meme_likelihood": round(meme_likelihood, 2),
                "days_active": days_active,
                "stage": stage,
                "shortable": is_shortable,
                "decline_flag": decline_flag,
                "volume_score": round(volume_score * 100, 2),
                "sentiment_score": round(sentiment_score * 100, 2),
                "momentum_score": round(momentum_score * 100, 2),
                "short_interest": market_data.get(ticker, {}).get("short_interest", 0),
                "post_count": sentiment_data[ticker]["post_count"],
                "total_karma": sentiment_data[ticker]["total_karma"],
            }

        return processed_stocks

    def _calculate_volume_score(self, ticker: str, sentiment_data: Dict[str, Any]) -> float:
        """Calculate normalized volume score based on historical data."""
        current_posts = sentiment_data["post_count"]

        # Get historical data for this ticker
        if ticker not in self.historical_data:
            self.historical_data[ticker] = []

        # Add current data point
        today = datetime.now().date()
        self.historical_data[ticker].append({
            "date": today,
            "post_count": current_posts
        })

        # Keep only last 30 days
        cutoff_date = today - timedelta(days=30)
        self.historical_data[ticker] = [
            data for data in self.historical_data[ticker]
            if data["date"] > cutoff_date
        ]

        # Calculate z-score
        if len(self.historical_data[ticker]) < 7:  # Need at least a week of data
            return min(current_posts / 10, 1.0)  # Simple scaling for new tickers

        historical_counts = [data["post_count"] for data in self.historical_data[ticker][:-1]]
        if not historical_counts:
            return 0.5

        mean_count = np.mean(historical_counts)
        std_count = np.std(historical_counts)
        if std_count == 0:
            return 0.5

        z_score = (current_posts - mean_count) / std_count

        # Normalize z-score to 0-1 range using sigmoid
        return 1 / (1 + np.exp(-z_score))

    def _calculate_momentum_score(self, ticker: str, market_data: Dict[str, Any]) -> float:
        """Calculate price momentum score."""
        price_change_3d = market_data.get("price_change_3d", 0)
        
        # Normalize to 0-1 range, with 0.5 being neutral
        return max(0, min(1, (price_change_3d + 10) / 20))  # Assumes max ±10% change

    def _calculate_meme_likelihood(
        self, volume_score: float, sentiment_score: float, momentum_score: float
    ) -> float:
        """Calculate likelihood of being a meme stock using Bayesian approach."""
        # Simple Bayesian calculation based on multiple factors
        base_probability = 0.1  # 10% base rate for meme stocks

        # Likelihood factors
        volume_factor = volume_score * 0.4
        sentiment_factor = max(0, sentiment_score) * 0.4
        momentum_factor = momentum_score * 0.2

        combined_likelihood = base_probability + (volume_factor + sentiment_factor + momentum_factor) * 0.9

        return min(100, max(0, combined_likelihood * 100))

    def _determine_meme_stage(
        self, sentiment_score: float, momentum_score: float, posts: List[Dict[str, Any]]
    ) -> str:
        """Determine the current stage of the meme stock."""
        # Analyze sentiment trend over recent posts
        recent_posts = sorted(posts, key=lambda x: x["timestamp"], reverse=True)[:10]
        
        if len(recent_posts) < 3:
            return STAGE_INITIATION

        # Calculate sentiment trend
        recent_sentiments = [post["sentiment"] for post in recent_posts]
        if len(recent_sentiments) >= 2:
            # Simple trend calculation
            early_sentiment = np.mean(recent_sentiments[len(recent_sentiments)//2:])
            late_sentiment = np.mean(recent_sentiments[:len(recent_sentiments)//2])
            sentiment_trend = late_sentiment - early_sentiment
        else:
            sentiment_trend = 0

        # Determine stage based on sentiment level, trend, and momentum
        if sentiment_score > 0.5 and sentiment_trend > 0.1 and momentum_score > 0.6:
            return STAGE_UPRAMP
        elif sentiment_score > 0.3 and sentiment_trend < -0.1:
            return STAGE_DO_NOT_INVEST
        elif sentiment_score > 0.4 and momentum_score > 0.7:
            return STAGE_TIPPING
        else:
            return STAGE_INITIATION

    def _calculate_days_active(self, ticker: str, posts: List[Dict[str, Any]]) -> int:
        """Calculate how many days the ticker has been active as a meme stock."""
        if not posts:
            return 0

        # Find the earliest post date
        earliest_post = min(posts, key=lambda x: x["timestamp"])
        days_active = (datetime.now() - earliest_post["timestamp"]).days

        return max(1, days_active)  # At least 1 day

    def _check_decline_flag(self, sentiment_score: float, momentum_score: float) -> bool:
        """Check if the stock is in decline phase."""
        return sentiment_score < 0 and momentum_score < 0.4