"""Constants for the Meme Stock Insight integration."""
from datetime import timedelta

# Integration domain
DOMAIN = "meme_stock_insight"

# Version
VERSION = "0.0.3"

# Update intervals
DEFAULT_SCAN_INTERVAL = timedelta(minutes=30)

# Default configuration
DEFAULT_SUBREDDITS = ["wallstreetbets", "stocks", "investing", "SecurityAnalysis", "ValueInvesting"]
DEFAULT_STOCK_SYMBOLS = ["GME", "AMC", "TSLA", "AAPL", "NVDA", "MSFT", "SPY", "QQQ"]
DEFAULT_SCAN_LIMIT = 100

# Reddit configuration
REDDIT_USER_AGENT_TEMPLATE = "homeassistant:meme_stock_insight:v{version} (by /u/{username})"
REDDIT_RATE_LIMIT_SECONDS = 5

# Sensor configuration
SENSOR_TYPES = {
    "mentions": {
        "name": "Meme Stock Mentions",
        "icon": "mdi:chart-line",
        "unit": "mentions",
    },
    "sentiment": {
        "name": "Meme Stock Sentiment",
        "icon": "mdi:emoticon-happy",
        "unit": "score",
    },
    "trending": {
        "name": "Trending Meme Stocks",
        "icon": "mdi:trending-up",
        "unit": "stocks",
    }
}

# False positive filtering - Common words that aren't stock symbols
FALSE_POSITIVE_FILTERS = {
    "common_words": [
        "A", "I", "BE", "GO", "IT", "AT", "OR", "SO", "US", "UP", "TO", "ON", "IN", "IS", "IF", "OF", "MY", "BY", 
        "DO", "AM", "AN", "AS", "WE", "NO", "ME", "ALL", "ANY", "CAN", "GET", "GOT", "HAD", "HAS", "HER", "HIM", 
        "HIS", "HOW", "ITS", "MAY", "NEW", "NOW", "OLD", "OUR", "OUT", "SEE", "THE", "TOP", "TWO", "WAY", "WHO", 
        "BOY", "DID", "EAT", "FAR", "FOR", "FUN", "GUY", "JOB", "LOT", "MAN", "NEW", "NOW", "OFF", "OLD", "ONE", 
        "OWN", "PUT", "RUN", "SAY", "SHE", "SIT", "TRY", "USE", "WIN", "YES", "YET", "YOU", "BAD", "BAG", "BED", 
        "BIG", "BIT", "BOX", "BUS", "BUT", "BUY", "CAR", "CAT", "CUP", "CUT", "DAY", "DOG", "EAR", "END", "EYE", 
        "FAR", "FEW", "GOD", "GUN", "HAD", "HIT", "HOT", "LAW", "LEG", "LET", "LOT", "MAN", "MAP", "NET", "NOT", 
        "OIL", "PAN", "PAY", "PEN", "PET", "PIG", "POT", "RED", "RUN", "SUN", "TAX", "TEA", "TOY", "VAN", "WAR", 
        "WET", "WIN", "WON", "ARM", "ART", "ASK", "BAD", "BAG", "BAR", "BAT", "BED", "BET", "BIG", "BIT", "BOX", 
        "BUS", "BUT", "BUY", "CAR", "CAT", "COW", "CRY", "CUP", "CUT", "DAD", "DAY", "DIG", "DOG", "EAR", "EAT", 
        "EGG", "END", "EYE", "FAD", "FAR", "FAT", "FEW", "FLY", "FOR", "FUN", "GOD", "GOT", "GUN", "HAD", "HAT", 
        "HIT", "HOT", "HUG", "JOB", "LAW", "LEG", "LET", "LOT", "MAN", "MAP", "NET", "NOT", "OIL", "PAN", "PAY", 
        "PEN", "PET", "PIG", "POT", "RED", "RUN", "SUN", "TAX", "TEA", "TOY", "VAN", "WAR", "WET", "WIN", "WON",
        "AND", "ARE", "BUT", "CAN", "FOR", "HAD", "HAS", "HER", "HIM", "HIS", "NOT", "ONE", "OUR", "OUT", "SHE", 
        "THE", "WAS", "WHY", "WITH", "WILL", "WHAT", "WHEN", "WHERE", "BEEN", "HAVE", "THEY", "THEM", "THAN", "THAT", 
        "THIS", "THERE", "THEIR", "THESE", "THOSE", "WOULD", "COULD", "SHOULD", "AFTER", "BEFORE", "DURING", "THROUGH"
    ],
    "reddit_slang": [
        "DD", "YOLO", "FD", "WSB", "HODL", "DRS", "GME", "APE", "MOON", "DIAMOND", "HANDS", "PAPER", "ROCKET", 
        "TENDIES", "RETARD", "AUTIST", "SMOOTH", "BRAIN", "WRINKLE", "BANANA", "CRAYON", "WIFE", "BOYFRIEND", 
        "LOSS", "PORN", "GAIN", "PORN", "MEME", "STONK", "STONKS", "CALLS", "PUTS", "FD", "CHAD", "VIRGIN"
    ]
}

# Minimum configuration requirements
MIN_SUBREDDITS = 1
MAX_SUBREDDITS = 10
MIN_SCAN_LIMIT = 10
MAX_SCAN_LIMIT = 1000

# Error messages
ERROR_REDDIT_AUTH = "Failed to authenticate with Reddit. Ensure your app is created as 'script' type."
ERROR_REDDIT_WRONG_APP = "Reddit app must be created as a 'script' application."
ERROR_API_CONNECTION = "Error connecting to external APIs. Please check your internet connection."
ERROR_UNKNOWN = "An unknown error occurred. Please check the logs for more details."