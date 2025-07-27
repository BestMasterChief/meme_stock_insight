"""Constants for the Meme Stock Insight integration."""

DOMAIN = "meme_stock_insight"
VERSION = "0.0.3"

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

# Popular meme stock symbols to track
MEME_STOCK_SYMBOLS = {
    "GME", "AMC", "BBBY", "NOK", "BB", "SNDL", "PLTR", "WISH", "CLOV", "SOFI",
    "TSLA", "NVDA", "AMD", "AAPL", "MSFT", "GOOGL", "AMZN", "META", "NFLX", "DIS",
    "SPY", "QQQ", "IWM", "VTI", "ARKK", "TQQQ", "SQQQ", "UVXY", "VIX", "GLD",
    "BTC", "ETH", "DOGE", "SHIB", "ADA", "DOT", "LINK", "UNI", "AVAX", "MATIC",
    "BABA", "NIO", "XPEV", "LI", "RIVN", "LCID", "F", "GM", "HOOD", "COIN",
    "ZM", "PTON", "BYND", "SPCE", "NKLA", "TLRY", "ACB", "CGC", "HEXO", "SAVA",
    "CRSR", "RKT", "UWMC", "PSFE", "UPST", "AFRM", "SQ", "PYPL", "V", "MA"
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
    "SEC": ["securities and exchange"],
    "FED": ["federal reserve"],
    "GDP": ["gross domestic product"],
    "CPI": ["consumer price index"],
    "PPI": ["producer price index"]
}

# Sentiment analysis keywords
SENTIMENT_KEYWORDS_POSITIVE = [
    "moon", "rocket", "bullish", "bull", "buy", "long", "hold", "hodl", "diamond hands",
    "to the moon", "squeeze", "gamma squeeze", "short squeeze", "tendies", "gains",
    "profit", "green", "up", "rise", "surge", "breakout", "rally", "pump", "strong",
    "good", "great", "excellent", "amazing", "love", "like", "positive", "optimistic",
    "calls", "yolo", "all in", "loading", "accumulate", "dip buying", "buying opportunity"
]

SENTIMENT_KEYWORDS_NEGATIVE = [
    "crash", "dump", "bearish", "bear", "sell", "short", "puts", "red", "down",
    "fall", "drop", "decline", "dip", "loss", "losses", "baghold", "bagholder",
    "dead", "rip", "rug pull", "scam", "overvalued", "bubble", "bad", "terrible",
    "awful", "hate", "dislike", "negative", "pessimistic", "fear", "panic", "avoid",
    "exit", "cut losses", "stop loss", "weakness", "support broken", "resistance"
]

# Sensor types
SENSOR_TYPES = {
    "mentions": {
        "name": "Stock Mentions",
        "icon": "mdi:trending-up",
        "unit": "mentions",
    },
    "sentiment": {
        "name": "Market Sentiment",
        "icon": "mdi:emoticon-happy",
        "unit": "score",
    },
    "trending": {
        "name": "Trending Stocks",
        "icon": "mdi:fire",
        "unit": "stocks",
    },
}

# Attribution
ATTRIBUTION = "Data from Reddit via PRAW"
