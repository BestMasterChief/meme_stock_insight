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

# Attribution
ATTRIBUTION = "Data provided by Reddit API"

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

# Sensor types and their configuration
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
}