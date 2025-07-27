# Meme Stock Insight v0.0.3 - Reddit Authentication Fix

**Fixed Version**: This version specifically addresses the "blocking call in event loop" error that was preventing the integration from working with Home Assistant.

## What Was Fixed

### The Problem
The previous version was causing this error:
```
RuntimeError: Caught blocking call to putrequest with args... inside the event loop
```

This happened because PRAW (Python Reddit API Wrapper) was making synchronous HTTP requests during initialization to check for updates from PyPI, which violates Home Assistant's async requirements.

### The Solution
**Version 0.0.3 implements two key fixes:**

1. **Disabled PRAW Update Checks**: Added `check_for_updates=False` to prevent blocking PyPI update checks
2. **Executor Thread Execution**: Used `hass.async_add_executor_job()` to run PRAW initialization in a separate thread

### Key Code Changes

In `config_flow.py`:
```python
reddit = praw.Reddit(
    client_id=client_id.strip(),
    client_secret=client_secret.strip() or None,
    user_agent=f"homeassistant:meme_stock_insight:v0.0.3 (by /u/{username.strip()})",
    username=username.strip(),
    password=password,
    ratelimit_seconds=5,
    check_for_updates=False,  # ✅ FIXED: Disable update check
    check_for_async=False,    # ✅ FIXED: Disable async check
)

# ✅ FIXED: Run in executor thread
await hass.async_add_executor_job(
    _validate_reddit_credentials,
    data["client_id"],
    data["client_secret"], 
    data["username"],
    data["password"]
)
```

## Installation Instructions

### 1. Reddit API Setup (Critical Steps)
1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. **IMPORTANT**: Select "script" as the application type
4. Fill in details:
   - Name: `meme_stock_insight`
   - Type: **script** (crucial!)
   - Redirect URI: `http://localhost`
5. Copy the 14-character Client ID and the Client Secret
6. Ensure the Reddit username matches the app owner

### 2. HACS Installation
1. Add this repository to HACS as a custom repository
2. Install "Meme Stock Insight" 
3. Restart Home Assistant

### 3. Home Assistant Setup
1. Go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Meme Stock Insight"
4. Enter your Reddit credentials

## File Structure

```
custom_components/
└── meme_stock_insight/
    ├── __init__.py          # Integration entry point
    ├── config_flow.py       # ✅ FIXED: Async-safe credential validation
    ├── const.py             # Constants and stock symbols
    ├── coordinator.py       # ✅ FIXED: Async-safe data coordinator  
    ├── sensor.py            # Sensor entities
    ├── manifest.json        # Integration manifest
    ├── strings.json         # Localization strings
    └── translations/
        └── en.json          # English translations
```

## Features

### Sensors Created
- **Stock Mentions**: Total mentions across tracked subreddits
- **Market Sentiment**: Average sentiment score (-1 to 1) 
- **Trending Stocks**: Number of currently trending stocks

### Tracked Data
- **60+ Popular Stocks**: GME, AMC, TSLA, NVDA, and more meme/popular stocks
- **Multiple Subreddits**: wallstreetbets, stocks, investing (configurable)
- **Sentiment Analysis**: Positive/negative keyword detection
- **False Positive Filtering**: Intelligent filtering of common false matches

## Troubleshooting

### If You Still Get Blocking Call Errors
1. Ensure you're using version 0.0.3 or later
2. Restart Home Assistant completely after installation
3. Remove and re-add the integration if issues persist

### Reddit Authentication Issues
1. **Verify app type**: Must be "script", not "web" or "installed"
2. **Check credentials**: Client ID (14 chars), Client Secret, Username, Password
3. **Username ownership**: The username must own the Reddit app
4. **User agent**: Integration uses proper format automatically

### HACS Issues
1. Ensure `hacs.json` is in repository root
2. Check that domain in `manifest.json` matches folder name
3. Verify all required files are present

## Version History

- **v0.0.3**: Fixed blocking call in event loop error, improved error handling
- **v0.0.2**: Enhanced sentiment analysis, added trending stocks
- **v0.0.1**: Initial release

## Contributing

Report issues at: https://github.com/yourusername/meme_stock_insight/issues

## License

MIT License - see LICENSE file for details.
