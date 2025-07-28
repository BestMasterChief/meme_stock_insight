"""Constants for Meme Stock Insight - v0.6.0"""
from datetime import timedelta

DOMAIN = "meme_stock_insight"
VERSION = "0.6.0"
ATTRIBUTION = "Data provided by Reddit API and Yahoo Finance"

# Update intervals
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=5)
DYNAMIC_SUBREDDIT_REFRESH = timedelta(days=7)

# Reddit configuration
DEFAULT_SUBREDDITS = ["wallstreetbets", "stocks", "investing"]
MAX_POSTS_PER_SUBREDDIT = 30
MAX_COMMENTS_PER_POST = 10

# Price provider configuration
PRICE_PROVIDERS = ["yfinance", "alpha_vantage", "polygon"]
API_LIMITS = {
    "yfinance": 0,  # Unlimited for free tier
    "alpha_vantage": 500,  # Free tier daily limit
    "polygon": 5000,  # Free tier daily limit
}
QUOTA_RESET_INTERVAL = timedelta(days=1)

# Sensor configurations
SENSOR_MENTIONS = "stock_mentions"
SENSOR_SENTIMENT = "market_sentiment" 
SENSOR_TRENDING = "trending_stocks"
SENSOR_MEME_1 = "meme_stock_1"
SENSOR_MEME_2 = "meme_stock_2"
SENSOR_MEME_3 = "meme_stock_3"
SENSOR_STAGE = "meme_stock_stage"
SENSOR_DAYS_ACTIVE = "days_active"
SENSOR_PRICE_SINCE_START = "price_since_start"
SENSOR_DYNAMIC_SUBREDDIT = "dynamic_subreddit"

# Tracked stock symbols
MEME_STOCK_SYMBOLS = [
    "GME", "AMC", "TSLA", "META", "NVDA", "AMD", "AAPL", "MSFT", "GOOGL", "AMZN",
    "PLTR", "HOOD", "COIN", "SOFI", "CLOV", "WISH", "SNDL", "NOK", "BB", "EXPR",
    "KOSS", "NAKD", "SIRI", "DOGE-USD", "BTC-USD", "ETH-USD", "SHIB-USD", "ADA-USD",
    "SPY", "QQQ", "IWM", "VIX", "DIA", "TLT", "GLD", "SLV", "OIL", "GAS",
    "BABA", "NIO", "XPEV", "LI", "RIVN", "LCID", "F", "GM", "NKLA", "RIDE",
    "SPCE", "ARKK", "ARKF", "ARKG", "MVIS", "SENS", "BNGO", "OCGN", "PROG", "BBIG"
]

# Company name mapping
STOCK_NAME_MAPPING = {
    "GME": "GameStop Corp",
    "AMC": "AMC Entertainment Holdings Inc",
    "TSLA": "Tesla Inc",
    "META": "Meta Platforms Inc",
    "NVDA": "NVIDIA Corporation",
    "AMD": "Advanced Micro Devices Inc",
    "AAPL": "Apple Inc",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc",
    "AMZN": "Amazon.com Inc",
    "PLTR": "Palantir Technologies Inc",
    "HOOD": "Robinhood Markets Inc",
    "COIN": "Coinbase Global Inc",
    "SOFI": "SoFi Technologies Inc",
    "CLOV": "Clover Health Investments Corp",
    "WISH": "ContextLogic Inc",
    "SNDL": "Sundial Growers Inc",
    "NOK": "Nokia Corporation",
    "BB": "BlackBerry Limited",
    "EXPR": "Express Inc",
    "KOSS": "Koss Corporation",
    "NAKD": "Naked Brand Group Limited",
    "SIRI": "Sirius XM Holdings Inc",
    "DOGE-USD": "Dogecoin",
    "BTC-USD": "Bitcoin",
    "ETH-USD": "Ethereum",
    "SHIB-USD": "Shiba Inu",
    "ADA-USD": "Cardano",
    "SPY": "SPDR S&P 500 ETF Trust",
    "QQQ": "Invesco QQQ Trust",
    "IWM": "iShares Russell 2000 ETF",
    "VIX": "CBOE Volatility Index",
    "DIA": "SPDR Dow Jones Industrial Average ETF Trust",
    "TLT": "iShares 20+ Year Treasury Bond ETF",
    "GLD": "SPDR Gold Shares",
    "SLV": "iShares Silver Trust",
    "OIL": "United States Oil Fund",
    "GAS": "United States Gasoline Fund",
    "BABA": "Alibaba Group Holding Limited",
    "NIO": "NIO Inc",
    "XPEV": "XPeng Inc",
    "LI": "Li Auto Inc",
    "RIVN": "Rivian Automotive Inc",
    "LCID": "Lucid Group Inc",
    "F": "Ford Motor Company",
    "GM": "General Motors Company",
    "NKLA": "Nikola Corporation",
    "RIDE": "Lordstown Motors Corp",
    "SPCE": "Virgin Galactic Holdings Inc",
    "ARKK": "ARK Innovation ETF",
    "ARKF": "ARK Fintech Innovation ETF",
    "ARKG": "ARK Genomics Revolution ETF",
    "MVIS": "MicroVision Inc",
    "SENS": "Senseonics Holdings Inc",
    "BNGO": "Bionano Genomics Inc",
    "OCGN": "Ocugen Inc",
    "PROG": "Progenity Inc",
    "BBIG": "Vinco Ventures Inc"
}

# Sentiment analysis keywords
SENTIMENT_KEYWORDS_POSITIVE = [
    "buy", "bullish", "moon", "rocket", "diamond", "hands", "hold", "hodl",
    "squeeze", "gain", "profit", "up", "rise", "call", "calls", "long",
    "pump", "rally", "breakout", "momentum", "strong", "support", "bull"
]

SENTIMENT_KEYWORDS_NEGATIVE = [
    "sell", "bearish", "crash", "drop", "fall", "puts", "put", "short",
    "dump", "loss", "down", "bear", "red", "baghold", "panic", "fear",
    "resistance", "weak", "dip", "correction", "bubble", "overvalued"
]

# False positive filters
FALSE_POSITIVE_KEYWORDS = {
    "AM": ["morning", "am", "a.m.", "time"],
    "PM": ["evening", "pm", "p.m.", "time"],
    "IT": ["information", "technology", "tech"],
    "AI": ["artificial", "intelligence"],
    "DD": ["due", "diligence"],
    "CEO": ["chief", "executive", "officer"],
    "CFO": ["chief", "financial", "officer"],
    "IPO": ["initial", "public", "offering"],
    "SEC": ["securities", "exchange", "commission"],
    "FDA": ["food", "drug", "administration"],
    "US": ["united", "states", "america"],
    "UK": ["united", "kingdom", "britain"],
    "EU": ["european", "union"],
    "NY": ["new", "york"],
    "CA": ["california"],
    "LA": ["los", "angeles"],
    "TV": ["television"],
    "PC": ["personal", "computer"],
    "PR": ["public", "relations"],
    "HR": ["human", "resources"],
    "IR": ["investor", "relations"],
    "RE": ["real", "estate"],
    "PE": ["private", "equity"],
    "VC": ["venture", "capital"],
    "M&A": ["merger", "acquisition"],
    "ROI": ["return", "investment"],
    "P/E": ["price", "earnings"],
    "EPS": ["earnings", "per", "share"],
    "EBITDA": ["earnings", "before", "interest"],
    "CAPEX": ["capital", "expenditure"],
    "OPEX": ["operating", "expenditure"]
}

# Meme stock lifecycle stages
MEME_STOCK_STAGES = {
    "start": "Start",
    "rising_interest": "Rising Interest", 
    "stock_rising": "Stock Rising",
    "within_estimated_peak": "Within Estimated Peak",
    "do_not_buy": "DO NOT BUY",
    "dropping": "Dropping"
}

# Stage determination thresholds
STAGE_THRESHOLDS = {
    "mentions_low": 5,
    "mentions_medium": 15,
    "mentions_high": 30,
    "price_change_low": 2.0,
    "price_change_medium": 5.0,
    "price_change_high": 10.0,
    "sentiment_negative": -0.3,
    "sentiment_neutral": 0.1,
    "sentiment_positive": 0.3,
    "days_early": 7,
    "days_mid": 21,
    "volume_spike": 1.5
}

# Error messages
ERROR_REDDIT_AUTH = "reddit_auth_failed"
ERROR_API_LIMIT = "max_api_calls_used"
ERROR_TIMEOUT = "timeout"
ERROR_INVALID_CONFIG = "invalid_config"