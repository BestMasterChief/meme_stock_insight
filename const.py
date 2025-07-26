"""Constants for the Meme Stock Insight integration."""

DOMAIN = "meme_stock_insight"

# Default configuration values
DEFAULT_UPDATE_INTERVAL = 12  # hours
DEFAULT_CACHE_DURATION = 72   # hours for instrument cache
DEFAULT_SUBREDDITS = ["wallstreetbets", "stocks", "SecurityAnalysis", "investing"]
DEFAULT_MIN_POSTS = 5  # Minimum posts to consider a stock
DEFAULT_MIN_KARMA = 100  # Minimum karma for post consideration

# API endpoints
REDDIT_BASE_URL = "https://www.reddit.com"
POLYGON_BASE_URL = "https://api.polygon.io"
TRADING212_BASE_URL = "https://live.trading212.com/api/v0"

# Entity attributes
ATTR_TICKER = "ticker"
ATTR_NAME = "name"
ATTR_IMPACT_SCORE = "impact_score"
ATTR_MEME_LIKELIHOOD = "meme_likelihood"
ATTR_DAYS_ACTIVE = "days_active"
ATTR_STAGE = "stage"
ATTR_SHORTABLE = "shortable"
ATTR_DECLINE_FLAG = "decline_flag"
ATTR_VOLUME_SCORE = "volume_score"
ATTR_SENTIMENT_SCORE = "sentiment_score"
ATTR_MOMENTUM_SCORE = "momentum_score"
ATTR_SHORT_INTEREST = "short_interest"

# Meme stock stages
STAGE_INITIATION = "Initiation"
STAGE_UPRAMP = "Up-Ramp"
STAGE_TIPPING = "Tipping Point"
STAGE_DO_NOT_INVEST = "Do Not Invest"

# Weighting factors for impact score (must sum to 1.0)
WEIGHT_VOLUME = 0.40
WEIGHT_SENTIMENT = 0.30
WEIGHT_MOMENTUM = 0.20
WEIGHT_SHORT_INTEREST = 0.10
