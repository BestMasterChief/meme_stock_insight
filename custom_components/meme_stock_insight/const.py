"""Constants for the Meme Stock Insight integration - Enhanced Version."""

DOMAIN = "meme_stock_insight"
VERSION = "0.0.4"

# Configuration constants
CONF_CLIENT_ID = "client_id"
CONF_CLIENT_SECRET = "client_secret"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_SUBREDDITS = "subreddits"
CONF_UPDATE_INTERVAL = "update_interval"

# Default values
DEFAULT_UPDATE_INTERVAL = 300  # 5 minutes
DEFAULT_SUBREDDITS = "wallstreetbets,stocks,investing"

# Attribution
ATTRIBUTION = "Data provided by Reddit API and Yahoo Finance"

# Popular meme stock symbols to track
MEME_STOCK_SYMBOLS = {
    "GME", "AMC", "BBBY", "NOK", "BB", "SNDL", "PLTR", "WISH", "CLOV", "SOFI",
    "TSLA", "NVDA", "AMD", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "DIS",
    "SPY", "QQQ", "IWM", "VTI", "ARKK", "TQQQ", "SQQQ", "UVXY", "VIX", "GLD",
    "BTC-USD", "ETH-USD", "DOGE-USD", "SHIB-USD", "ADA-USD", "DOT-USD", "LINK-USD", 
    "UNI-USD", "AVAX-USD", "MATIC-USD",
    "BABA", "NIO", "XPEV", "LI", "RIVN", "LCID", "F", "GM", "HOOD", "COIN",
    "ZM", "PTON", "BYND", "SPCE", "NKLA", "TLRY", "ACB", "CGC", "HEXO", "SAVA",
    "CRSR", "RKT", "UWMC", "PSFE", "UPST", "AFRM", "SQ", "PYPL", "V", "MA"
}

# Company name mappings for major meme stocks (fallback for when API fails)
STOCK_NAME_MAPPING = {
    "GME": "GameStop Corp",
    "AMC": "AMC Entertainment Holdings Inc",
    "TSLA": "Tesla Inc",
    "META": "Meta Platforms Inc",
    "AAPL": "Apple Inc",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc",
    "AMZN": "Amazon.com Inc",
    "NVDA": "NVIDIA Corporation",
    "AMD": "Advanced Micro Devices Inc",
    "PLTR": "Palantir Technologies Inc",
    "HOOD": "Robinhood Markets Inc",
    "COIN": "Coinbase Global Inc",
    "SOFI": "SoFi Technologies Inc",
    "BB": "BlackBerry Limited",
    "NOK": "Nokia Corporation",
    "NFLX": "Netflix Inc",
    "DIS": "The Walt Disney Company",
    "RIVN": "Rivian Automotive Inc",
    "LCID": "Lucid Group Inc",
    "F": "Ford Motor Company",
    "GM": "General Motors Company"
}

# Keywords that might indicate false positives for certain symbols
FALSE_POSITIVE_KEYWORDS = {
    "AM": ["morning", "am i", "i am", "am not", "am going", "am here"],
    "A": ["a stock", "a share", "a good", "a bad", "a lot", "a few", "a day"],
    "IT": ["it is", "it was", "it will", "it would", "it could", "it should"],
    "GO": ["go to", "go up", "go down", "go long", "go short", "let's go"],
    "AI": ["ai technology", "artificial intelligence"],
    "TV": ["television", "tv show", "tv series"],
    "DD": ["due diligence", "deep dive"],
    "CEO": ["chief executive"],
    "ATH": ["all time high"],
    "ATL": ["all time low"],
    "ER": ["earnings report", "emergency room"],
    "PE": ["price to earnings", "physical education"],
    "EV": ["electric vehicle", "enterprise value"],
    "IPO": ["initial public offering"],
    "NYSE": ["new york stock exchange"],
    "FDA": ["food and drug administration"],
    "SEC": ["securities and exchange commission"],
    "FED": ["federal reserve"],
    "GDP": ["gross domestic product"],
    "CPI": ["consumer price index"],
    "ETF": ["exchange traded fund"],
    "IPO": ["initial public offering"],
    "RSI": ["relative strength index"],
    "MACD": ["moving average convergence divergence"]
}

# Positive sentiment keywords
SENTIMENT_KEYWORDS_POSITIVE = {
    "moon", "rocket", "bullish", "buy", "calls", "green", "gains", "profit",
    "diamond hands", "hold", "hodl", "strong", "support", "breakout", "rally",
    "squeeze", "pump", "bull", "uptrend", "momentum", "catalyst", "golden",
    "explosion", "surge", "spike", "soar", "rise", "climb", "jump", "boost",
    "positive", "optimistic", "confident", "excited", "potential", "opportunity",
    "winner", "success", "victory", "target", "breakthrough", "promising"
}

# Negative sentiment keywords 
SENTIMENT_KEYWORDS_NEGATIVE = {
    "crash", "dump", "bearish", "sell", "puts", "red", "loss", "bear",
    "downtrend", "decline", "drop", "fall", "plunge", "tank", "collapse",
    "weak", "resistance", "bagholding", "rip", "dead", "over", "done",
    "disaster", "terrible", "awful", "worried", "concerned", "doubt",
    "negative", "pessimistic", "fear", "panic", "scary", "risky", "danger",
    "warning", "caution", "avoid", "stay away", "trap", "scam", "fraud"
}

# Meme stock lifecycle stages
MEME_STOCK_STAGES = {
    "start": "Start",
    "rising_interest": "Rising Interest", 
    "stock_rising": "Stock Rising",
    "estimated_peak": "Within Estimated Peak",
    "do_not_buy": "DO NOT BUY",
    "dropping": "Dropping"
}

# Stage analysis thresholds
STAGE_THRESHOLDS = {
    "volume_spike_threshold": 1.5,  # 50% above average volume
    "price_change_1d_rising": 0.02,  # 2% daily change for rising
    "price_change_1d_peak": 0.05,   # 5% daily change for peak detection
    "price_change_7d_declining": -0.10,  # -10% weekly change for declining
    "sentiment_positive_threshold": 0.1,  # Positive sentiment threshold
    "sentiment_negative_threshold": -0.1,  # Negative sentiment threshold
    "mentions_spike_threshold": 2.0,  # 2x increase in mentions
    "rsi_overbought": 70,  # RSI overbought level
    "rsi_oversold": 30,   # RSI oversold level
}

# Enhanced sensor types
SENSOR_TYPES = {
    "mentions": {
        "name": "Stock Mentions",
        "icon": "mdi:chart-line",
        "unit": "mentions",
        "device_class": None,
    },
    "sentiment": {
        "name": "Market Sentiment", 
        "icon": "mdi:emoticon-happy-outline",
        "unit": "score",
        "device_class": None,
    },
    "trending": {
        "name": "Trending Stocks",
        "icon": "mdi:trending-up",
        "unit": "stocks",
        "device_class": None,
    },
    "meme_1": {
        "name": "Meme Stock #1",
        "icon": "mdi:trophy",
        "unit": None,
        "device_class": None,
    },
    "meme_2": {
        "name": "Meme Stock #2", 
        "icon": "mdi:medal",
        "unit": None,
        "device_class": None,
    },
    "meme_3": {
        "name": "Meme Stock #3",
        "icon": "mdi:podium-bronze", 
        "unit": None,
        "device_class": None,
    },
    "stage": {
        "name": "Meme Stock Stage",
        "icon": "mdi:chart-timeline-variant",
        "unit": None,
        "device_class": None,
    }
}

# Stage icons for different phases
STAGE_ICONS = {
    "start": "mdi:seedling",
    "rising_interest": "mdi:trending-up", 
    "stock_rising": "mdi:rocket-launch",
    "estimated_peak": "mdi:mountain",
    "do_not_buy": "mdi:alert-octagon",
    "dropping": "mdi:trending-down"
}

# Stage colors for UI representation
STAGE_COLORS = {
    "start": "#4CAF50",  # Green
    "rising_interest": "#2196F3",  # Blue
    "stock_rising": "#FF9800",  # Orange  
    "estimated_peak": "#9C27B0",  # Purple
    "do_not_buy": "#F44336",  # Red
    "dropping": "#607D8B"  # Blue Grey
}