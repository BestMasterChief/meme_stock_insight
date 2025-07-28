"""Constants for Meme Stock Insight ― v0.6.0."""

from datetime import timedelta

DOMAIN = "meme_stock_insight"
VERSION = "0.6.0"

# ──────────────────────────────────── Reddit ───────────────────────────────────
DEFAULT_SUBREDDITS = ["wallstreetbets", "stocks", "investing"]
DYNAMIC_SUBREDDIT_REFRESH = timedelta(days=7)          # “floating” SR cadence
SUBREDDIT_REFRESH        = timedelta(minutes=5)        # coordinator frequency

# ───────────────────────────────── Price Providers ─────────────────────────────
PROVIDERS   = ("yfinance", "alpha_vantage", "polygon")
API_LIMITS  = {        # free-tier daily ceilings (0 = unlimited)
    "yfinance":       0,
    "alpha_vantage":  500,
    "polygon":        5_000,
}
QUOTA_RESET = timedelta(days=1)

# ─────────────────────────────────── Sensors ───────────────────────────────────
SENSOR_MENTIONS      = "mentions"
SENSOR_SENTIMENT     = "sentiment"
SENSOR_TRENDING      = "trending"
SENSOR_TOP_N         = ("meme_1", "meme_2", "meme_3")
SENSOR_STAGE         = "stage"
SENSOR_DAYS_ACTIVE   = "days_active"
SENSOR_SINCE_START   = "price_since_start"
SENSOR_DYNAMIC_SR    = "dynamic_subreddit"

ALL_SENSORS = (
    SENSOR_MENTIONS, SENSOR_SENTIMENT, SENSOR_TRENDING,
    *SENSOR_TOP_N, SENSOR_STAGE,
    SENSOR_DAYS_ACTIVE, SENSOR_SINCE_START, SENSOR_DYNAMIC_SR,
)

# ──────────────────────────  UI metadata (icons / units) ──────────────────────
SENSOR_TYPES = {
    SENSOR_MENTIONS:      {"name": "Stock Mentions",          "icon": "mdi:chart-line",      "unit": "mentions"},
    SENSOR_SENTIMENT:     {"name": "Market Sentiment",        "icon": "mdi:emoticon-happy",  "unit": None},
    SENSOR_TRENDING:      {"name": "Trending Stocks",         "icon": "mdi:trending-up",     "unit": "stocks"},
    "meme_1":             {"name": "Meme Stock #1",           "icon": "mdi:trophy",          "unit": None},
    "meme_2":             {"name": "Meme Stock #2",           "icon": "mdi:medal",           "unit": None},
    "meme_3":             {"name": "Meme Stock #3",           "icon": "mdi:podium-bronze",   "unit": None},
    SENSOR_STAGE:         {"name": "Meme Stock Stage",        "icon": "mdi:chart-timeline",  "unit": None},
    SENSOR_DAYS_ACTIVE:   {"name": "Days Active",             "icon": "mdi:calendar-clock",  "unit": "d"},
    SENSOR_SINCE_START:   {"name": "Price Since Start",       "icon": "mdi:cash-plus",       "unit": "%"},
    SENSOR_DYNAMIC_SR:    {"name": "Dynamic Subreddit",       "icon": "mdi:reddit",          "unit": None},
}

# (Truncated: keep MEME_STOCK_SYMBOLS, SENTIMENT lexicons, STAGE_* dicts
# exactly as they exist in your current repo to avoid merge churn.)
