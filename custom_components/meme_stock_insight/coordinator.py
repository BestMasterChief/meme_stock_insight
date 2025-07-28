"""Enhanced Data update coordinator for Meme Stock Insight with stock price analysis."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import statistics

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
    STOCK_NAME_MAPPING,
    MEME_STOCK_STAGES,
    STAGE_THRESHOLDS,
    STAGE_ICONS,
)

_LOGGER = logging.getLogger(__name__)

class MemeStockInsightCoordinator(DataUpdateCoordinator):
    """Enhanced coordinator to manage fetching data from Reddit and stock prices."""

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
        self._stock_cache = {}  # Cache stock data to avoid API limits
        self._price_history = {}  # Store price history for trend analysis

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
            reddit_data = await asyncio.wait_for(
                self.hass.async_add_executor_job(self._fetch_reddit_data),
                timeout=90  # 90 second timeout for data fetching
            )
            
            # Fetch stock price data for top mentioned stocks
            stock_data = await self._fetch_stock_data(reddit_data.get('stock_mentions', {}))
            
            # Analyze meme stock stages
            stage_analysis = await self._analyze_meme_stock_stages(reddit_data, stock_data)
            
            # Combine all data
            combined_data = {
                **reddit_data,
                **stock_data,
                **stage_analysis
            }
            
            _LOGGER.debug(f"Fetched combined data: {combined_data.get('total_mentions', 0)} mentions, "
                         f"{len(combined_data.get('top_stocks', []))} top stocks with prices")
            return combined_data

        except asyncio.TimeoutError:
            _LOGGER.warning("Reddit data fetch timed out, returning fallback data")
            return self._get_fallback_data("timeout")
        except Exception as exc:
            _LOGGER.error(f"Error fetching data: {exc}")
            return self._get_fallback_data(f"error: {str(exc)[:50]}")

    async def _async_setup_reddit(self) -> None:
        """Set up Reddit client in executor thread."""
        def _setup_reddit():
            """Setup Reddit client with proper configuration."""
            try:
                reddit = praw.Reddit(
                    client_id=self.client_id.strip(),
                    client_secret=self.client_secret.strip() or None,
                    user_agent=f"homeassistant:meme_stock_insight:v0.0.4 (by /u/{self.username.strip()})",
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

    async def _fetch_stock_data(self, stock_mentions: Dict[str, int]) -> Dict[str, Any]:
        """Fetch stock price data for top mentioned stocks."""
        def _get_stock_prices():
            """Get stock prices using yfinance (can be replaced with Alpha Vantage)."""
            try:
                # Import yfinance here to avoid blocking
                import yfinance as yf
                
                # Get top 10 mentioned stocks
                top_stocks = list(stock_mentions.keys())[:10]
                stock_data = {}
                
                for symbol in top_stocks:
                    try:
                        # Clean symbol for crypto (remove -USD suffix for yfinance)
                        yf_symbol = symbol.replace('-USD', '-USD') if '-USD' in symbol else symbol
                        
                        ticker = yf.Ticker(yf_symbol)
                        info = ticker.info
                        hist = ticker.history(period="5d")  # Get 5 days of history
                        
                        if not hist.empty and info:
                            current_price = hist['Close'].iloc[-1] if len(hist) > 0 else None
                            prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                            
                            # Calculate price change
                            price_change = ((current_price - prev_close) / prev_close * 100) if prev_close and current_price else 0
                            
                            # Get company name
                            company_name = info.get('longName') or info.get('shortName') or STOCK_NAME_MAPPING.get(symbol, symbol)
                            
                            stock_data[symbol] = {
                                'current_price': round(float(current_price), 2) if current_price else None,
                                'price_change_pct': round(price_change, 2),
                                'volume': info.get('volume', 0),
                                'avg_volume': info.get('averageVolume', 0),
                                'company_name': company_name,
                                'market_cap': info.get('marketCap', 0),
                                'mentions': stock_mentions[symbol],
                                'price_history': hist['Close'].tolist()[-5:] if len(hist) >= 5 else []
                            }
                            
                            # Store in cache for stage analysis
                            self._stock_cache[symbol] = stock_data[symbol]
                            
                    except Exception as e:
                        _LOGGER.debug(f"Error fetching data for {symbol}: {e}")
                        # Use cached data or fallback
                        if symbol in self._stock_cache:
                            stock_data[symbol] = self._stock_cache[symbol]
                        else:
                            stock_data[symbol] = {
                                'current_price': None,
                                'price_change_pct': 0,
                                'volume': 0,
                                'avg_volume': 0,
                                'company_name': STOCK_NAME_MAPPING.get(symbol, symbol),
                                'market_cap': 0,
                                'mentions': stock_mentions[symbol],
                                'price_history': []
                            }
                
                return stock_data
                
            except ImportError:
                _LOGGER.error("yfinance not installed. Install with: pip install yfinance")
                return {}
            except Exception as exc:
                _LOGGER.error(f"Error fetching stock prices: {exc}")
                return {}
        
        try:
            stock_data = await asyncio.wait_for(
                self.hass.async_add_executor_job(_get_stock_prices),
                timeout=60  # 60 second timeout for stock data
            )
            
            # Create top stocks list with full information
            top_stocks = []
            for symbol, data in stock_data.items():
                top_stocks.append({
                    'symbol': symbol,
                    'company_name': data['company_name'],
                    'mentions': data['mentions'],
                    'current_price': data['current_price'],
                    'price_change_pct': data['price_change_pct'],
                    'display_name': f"{symbol} - {data['company_name']}"
                })
            
            # Sort by mentions
            top_stocks.sort(key=lambda x: x['mentions'], reverse=True)
            
            return {
                'top_stocks': top_stocks,
                'stock_prices': stock_data
            }
            
        except asyncio.TimeoutError:
            _LOGGER.warning("Stock price fetch timed out")
            return {'top_stocks': [], 'stock_prices': {}}
        except Exception as exc:
            _LOGGER.error(f"Error in stock data fetch: {exc}")
            return {'top_stocks': [], 'stock_prices': {}}

    async def _analyze_meme_stock_stages(self, reddit_data: Dict, stock_data: Dict) -> Dict[str, Any]:
        """Analyze meme stock lifecycle stages."""
        def _calculate_stage():
            """Calculate the current meme stock stage based on multiple factors."""
            try:
                top_stocks = stock_data.get('top_stocks', [])
                if not top_stocks:
                    return "start", "No active meme stocks detected"
                
                # Analyze the top meme stock
                top_stock = top_stocks[0]
                symbol = top_stock['symbol']
                mentions = top_stock['mentions']
                price_change = top_stock.get('price_change_pct', 0)
                
                # Get additional data from stock_prices
                stock_info = stock_data.get('stock_prices', {}).get(symbol, {})
                volume = stock_info.get('volume', 0)
                avg_volume = stock_info.get('avg_volume', 1)
                price_history = stock_info.get('price_history', [])
                
                # Get sentiment data
                sentiment = reddit_data.get('average_sentiment', 0)
                
                # Calculate volume ratio
                volume_ratio = volume / avg_volume if avg_volume > 0 else 1
                
                # Calculate price momentum (if we have history)
                price_momentum = 0
                if len(price_history) >= 3:
                    recent_avg = statistics.mean(price_history[-3:])
                    older_avg = statistics.mean(price_history[:-3]) if len(price_history) > 3 else recent_avg
                    price_momentum = (recent_avg - older_avg) / older_avg * 100 if older_avg > 0 else 0
                
                # Stage decision logic based on multiple factors
                stage_info = {
                    'mentions': mentions,
                    'price_change_1d': price_change,
                    'volume_ratio': volume_ratio,
                    'sentiment': sentiment,
                    'price_momentum': price_momentum,
                    'symbol': symbol
                }
                
                # Determine stage based on thresholds
                if mentions < 5:
                    stage = "start"
                    reason = f"Low mention count ({mentions})"
                elif (mentions >= 5 and volume_ratio > STAGE_THRESHOLDS['volume_spike_threshold'] 
                      and sentiment > 0):
                    if price_change > STAGE_THRESHOLDS['price_change_1d_peak']:
                        if price_momentum > 10:  # Very high momentum
                            stage = "estimated_peak"
                            reason = f"High price change ({price_change:.1f}%) with strong momentum"
                        else:
                            stage = "stock_rising"
                            reason = f"Strong price movement ({price_change:.1f}%)"
                    elif price_change > STAGE_THRESHOLDS['price_change_1d_rising']:
                        stage = "rising_interest"
                        reason = f"Growing interest with {mentions} mentions"
                    else:
                        stage = "rising_interest"  
                        reason = f"Increased volume and mentions ({mentions})"
                elif sentiment < STAGE_THRESHOLDS['sentiment_negative_threshold'] or price_change < -5:
                    if price_change < -15:  # Major drop
                        stage = "do_not_buy"
                        reason = f"Major price decline ({price_change:.1f}%)"
                    else:
                        stage = "dropping"
                        reason = f"Negative sentiment or declining price ({price_change:.1f}%)"
                elif mentions > 15 and price_change > 5:
                    stage = "estimated_peak"
                    reason = f"High activity ({mentions} mentions, {price_change:.1f}% change)"
                else:
                    stage = "rising_interest"
                    reason = f"Moderate activity with {mentions} mentions"
                
                return stage, reason, stage_info
                
            except Exception as exc:
                _LOGGER.error(f"Error calculating stage: {exc}")
                return "start", "Error in stage calculation", {}
        
        try:
            stage, reason, stage_info = await self.hass.async_add_executor_job(_calculate_stage)
            
            return {
                'meme_stage': MEME_STOCK_STAGES.get(stage, stage),
                'meme_stage_key': stage,
                'stage_reason': reason,
                'stage_analysis': stage_info,
                'stage_icon': STAGE_ICONS.get(stage, 'mdi:help-circle')
            }
            
        except Exception as exc:
            _LOGGER.error(f"Error in stage analysis: {exc}")
            return {
                'meme_stage': 'Start',
                'meme_stage_key': 'start',
                'stage_reason': 'Analysis error',
                'stage_analysis': {},
                'stage_icon': 'mdi:help-circle'
            }

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
            "top_stocks": [],
            "stock_prices": {},
            "meme_stage": "Start",
            "meme_stage_key": "start", 
            "stage_reason": "No data available",
            "stage_analysis": {},
            "stage_icon": "mdi:help-circle",
            "last_updated": datetime.now().isoformat(),
            "status": status,
            "posts_processed": 0,
            "subreddits_processed": []
        }