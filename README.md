# Meme Stock Insight for Home Assistant

[![Version](https://img.shields.io/badge/version-0.0.3-blue.svg)](https://github.com/BestMasterChief/meme_stock_insight)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2023.7%2B-blue.svg)](https://www.home-assistant.io/)

A Home Assistant custom integration that monitors Reddit and other social platforms to identify trending "meme stocks" and provides comprehensive sentiment analysis and trading insights.

## Features

### 🔍 Real-time Social Sentiment Analysis
- Monitors multiple subreddits (wallstreetbets, stocks, investing, etc.)
- Advanced sentiment analysis using VADER sentiment analyzer
- Filters posts by karma threshold to ensure quality
- Extracts stock tickers automatically from post content

### 📊 Comprehensive Stock Metrics
- **Impact Score**: Composite score based on volume, sentiment, momentum, and short interest
- **Meme Likelihood**: Bayesian probability of being a trending meme stock
- **Stage Detection**: Identifies current meme stock phase (Initiation, Up-Ramp, Tipping Point, Do Not Invest)
- **Volume Score**: Normalized posting volume compared to historical patterns
- **Sentiment Score**: Aggregated positive/negative sentiment analysis
- **Momentum Score**: Price movement analysis integration
- **Short Interest**: Short selling availability and interest data

### 🔗 API Integrations
- **Reddit API**: Primary data source for social sentiment
- **Polygon.io** (Optional): Real-time market data and price information
- **Trading212** (Optional): Short selling availability data

### 🏠 Home Assistant Integration
- Individual sensors for each detected stock ticker
- Real-time updates with configurable intervals
- Rich device information and attributes
- Lovelace dashboard compatible
- Options flow for easy reconfiguration

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"  
3. Click the three dots menu and select "Custom repositories"
4. Add `https://github.com/BestMasterChief/meme_stock_insight` as an Integration
5. Find "Meme Stock Insight" in the list and install it
6. Restart Home Assistant

### Manual Installation

1. Download the `meme_stock_insight` folder from this repository
2. Copy it to your `custom_components` directory in your Home Assistant configuration
3. Restart Home Assistant

## Configuration

### Reddit API Setup (Required)

1. Go to [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click "Create another app..." 
3. **Important**: Select "script" as the application type
4. Fill in the details:
   - **Name**: `meme_stock_insight` (or any name you prefer)
   - **Type**: **script** (this is crucial!)
   - **Redirect URI**: `http://localhost` (required field, not used)
5. Note down:
   - **Client ID**: The 14-character string under the app name
   - **Client Secret**: The "secret" string shown
6. Ensure the Reddit username you'll use in Home Assistant is the same as the one that owns the app

### Integration Setup

1. Go to Home Assistant Settings → Devices & Services
2. Click "Add Integration" and search for "Meme Stock Insight"
3. Enter your configuration:
   - **Reddit Client ID**: From your Reddit app
   - **Reddit Client Secret**: From your Reddit app  
   - **Reddit Username**: Your Reddit username (must own the app)
   - **Reddit Password**: Your Reddit password
   - **Polygon.io API Key** (Optional): For real market data
   - **Trading212 API Key** (Optional): For short selling data
   - **Subreddits**: Comma-separated list of subreddits to monitor
   - **Update Interval**: How often to fetch new data (1-24 hours)
   - **Minimum Posts**: Minimum posts required to track a stock
   - **Minimum Karma**: Minimum karma threshold for post consideration

## Troubleshooting

### Reddit Authentication Issues

If you encounter authentication errors:

1. **Verify App Type**: Ensure your Reddit app is created as "script" type, not "installed" or "web"
2. **Check Credentials**: Verify client ID, secret, username, and password are correct
3. **Username Match**: The Reddit username in config must be the same as the app owner
4. **2FA**: This integration bypasses 2FA when using password flow
5. **Rate Limiting**: The integration includes polite rate limiting (5 second intervals)

### Common Error Messages

- **"OAuth refused"**: Check app type (must be script), client ID/secret, and user agent
- **"Reddit API refused connection"**: Network connectivity or Reddit API issues  
- **"Credentials accepted but read-only"**: App is not script type or wrong user

### File Structure

```
custom_components/meme_stock_insight/
├── __init__.py              # Main integration setup
├── config_flow.py           # Configuration flow
├── const.py                 # Constants and configuration
├── coordinator.py           # Data update coordinator
├── sensor.py                # Sensor platform
├── manifest.json            # Integration manifest
├── strings.json             # Localization strings
├── hacs.json                # HACS configuration
└── README.md                # This file
```

## Sensors Created

For each detected stock ticker, the integration creates:

- `sensor.{ticker}_impact_score` - Overall impact score (0-100%)
- `sensor.{ticker}_meme_likelihood` - Probability of being a meme stock (0-100%)
- `sensor.{ticker}_days_active` - Days since first detection
- `sensor.{ticker}_stage` - Current meme stock stage
- `sensor.{ticker}_shortable` - Whether stock can be shorted
- `sensor.{ticker}_decline_flag` - Warning flag for declining interest
- `sensor.{ticker}_volume_score` - Social volume score (0-100%)
- `sensor.{ticker}_sentiment_score` - Sentiment analysis score (0-100%)
- `sensor.{ticker}_momentum_score` - Price momentum score (0-100%)  
- `sensor.{ticker}_short_interest` - Short interest percentage

## Advanced Configuration

### Weighting Factors

The impact score calculation uses these default weights (customizable via options):

- **Volume Weight**: 40% - Social media posting volume
- **Sentiment Weight**: 30% - Positive sentiment analysis  
- **Momentum Weight**: 20% - Price movement momentum
- **Short Interest Weight**: 10% - Short selling interest

### Subreddit Selection

Default monitored subreddits:
- wallstreetbets
- stocks  
- SecurityAnalysis
- investing

You can customize this list during setup or via integration options.

## Example Lovelace Configuration

```yaml
type: entities
title: Meme Stock Monitor
entities:
  - sensor.gme_impact_score
  - sensor.gme_meme_likelihood
  - sensor.gme_stage
  - sensor.amc_impact_score
  - sensor.amc_meme_likelihood
  - sensor.amc_stage
show_header_toggle: false
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This integration is for informational purposes only and should not be considered financial advice. Always do your own research before making investment decisions.

## Support

- [Issues](https://github.com/BestMasterChief/meme_stock_insight/issues)
- [Discussions](https://github.com/BestMasterChief/meme_stock_insight/discussions)

## Changelog

### v0.0.3
- Fixed Reddit authentication issues with proper OAuth handling
- Improved error messages and validation
- Added proper user agent formatting
- Enhanced exception handling for prawcore errors
- Updated to support latest Home Assistant versions
- Improved documentation and setup instructions

### v0.0.2
- Initial HACS release
- Basic Reddit sentiment analysis
- Multi-subreddit support

### v0.0.1
- Initial development version