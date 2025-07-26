# Meme Stock Insight - Home Assistant Integration

A Home Assistant custom integration that monitors Reddit and social media platforms to identify emerging meme stocks and provide actionable insights for trading decisions.

## Features

- **Real-time Social Sentiment Analysis**: Monitors r/wallstreetbets, r/stocks, and other configured subreddits
- **Meme Stock Detection**: Uses AI to identify stocks gaining social media traction
- **Trading212 Integration**: Checks if stocks can be shorted on your Trading212 account
- **Comprehensive Metrics**: Impact scores, meme likelihood, stage analysis, and decline flags
- **Home Assistant Native**: Full integration with HA's automation and dashboard systems
- **HACS Compatible**: Easy installation and updates through HACS

## Installation

### Prerequisites

1. **Reddit API Credentials**: Create a Reddit application at https://www.reddit.com/prefs/apps
   - Choose "script" type application
   - Note down your client ID and client secret
   - You'll need your Reddit username and password

2. **Optional APIs**:
   - Polygon.io API key for enhanced market data
   - Trading212 API key for short availability checking

### HACS Installation (Recommended)

1. Open HACS in your Home Assistant
2. Go to "Integrations"
3. Click the three dots menu and select "Custom repositories"
4. Add your repository URL with category "Integration"
5. Install "Meme Stock Insight"
6. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/meme_stock_insight` folder to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration → Integrations → Add Integration
4. Search for "Meme Stock Insight" and follow the setup

## Configuration

### Initial Setup

1. Go to Configuration → Integrations → Add Integration
2. Search for "Meme Stock Insight"
3. Enter your Reddit API credentials:
   - Client ID and Secret from your Reddit app
   - Your Reddit username and password
4. Optionally configure:
   - Additional subreddits to monitor
   - Update interval (default: 12 hours)
   - Minimum posts/karma thresholds
   - Polygon.io and Trading212 API keys

### Options

You can adjust settings after installation:
- Subreddits to monitor
- Update frequency
- Weighting factors for impact score calculation
- Minimum thresholds for detection

## Entities

For each detected meme stock, the integration creates the following sensors:

| Sensor | Description | Unit |
|--------|-------------|------|
| `[ticker]_impact_score` | Composite impact score (0-100%) | % |
| `[ticker]_meme_likelihood` | Probability of being a meme stock | % |
| `[ticker]_days_active` | Days since meme activity started | days |
| `[ticker]_stage` | Current meme stage | enum |
| `[ticker]_shortable` | Can be shorted on Trading212 | bool |
| `[ticker]_decline_flag` | Stock is in decline phase | bool |
| `[ticker]_volume_score` | Social volume score | % |
| `[ticker]_sentiment_score` | Average sentiment score | % |
| `[ticker]_momentum_score` | Price momentum score | % |
| `[ticker]_short_interest` | Short interest percentage | % |

### Meme Stock Stages

- **Initiation**: Early stage, limited social activity
- **Up-Ramp**: Growing momentum and positive sentiment
- **Tipping Point**: Peak activity, high risk/reward
- **Do Not Invest**: Declining sentiment, avoid entry

## Services

### `meme_stock_insight.refresh_now`
Manually refresh data for all or specific stocks.

### `meme_stock_insight.set_weighting`
Adjust the weighting factors for impact score calculation:
- Volume Weight (default: 40%)
- Sentiment Weight (default: 30%)
- Momentum Weight (default: 20%)
- Short Interest Weight (default: 10%)

### `meme_stock_insight.force_update_cache`
Force update the Trading212 and exchange instrument cache.

### `meme_stock_insight.clear_historical_data`
Clear stored historical data for all tickers.

## Automation Examples

### Buy Alert for High-Potential Meme Stocks

```yaml
automation:
  - alias: "Meme Stock Buy Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.gme_impact_score
        above: 75
    condition:
      - condition: state
        entity_id: sensor.gme_stage
        state: "Up-Ramp"
      - condition: state
        entity_id: sensor.gme_decline_flag
        state: "off"
    action:
      - service: notify.mobile_app
        data:
          title: "🚀 Meme Stock Alert"
          message: "GME showing strong meme potential ({{ states('sensor.gme_impact_score') }}% impact)"
```

### Short Alert for Declining Stocks

```yaml
automation:
  - alias: "Meme Stock Short Alert"
    trigger:
      - platform: state
        entity_id: sensor.amc_decline_flag
        to: "on"
    condition:
      - condition: state
        entity_id: sensor.amc_shortable
        state: "on"
      - condition: numeric_state
        entity_id: sensor.amc_meme_likelihood
        below: 30
    action:
      - service: notify.mobile_app
        data:
          title: "📉 Short Opportunity"
          message: "AMC showing decline signals and is shortable on Trading212"
```

### Dashboard Card Example

```yaml
type: entities
title: Meme Stock Monitor
entities:
  - entity: sensor.gme_impact_score
    name: "GME Impact"
    icon: mdi:trending-up
  - entity: sensor.gme_stage
    name: "GME Stage"
  - entity: sensor.gme_shortable
    name: "GME Shortable"
  - entity: sensor.amc_impact_score
    name: "AMC Impact"
  - entity: sensor.amc_decline_flag
    name: "AMC Declining"
```

## Impact Score Calculation

The impact score is a weighted composite of four factors:

```
Impact = (40% × Volume) + (30% × Sentiment) + (20% × Momentum) + (10% × Short Interest)
```

- **Volume**: Z-scored post volume vs 30-day baseline
- **Sentiment**: Average VADER sentiment (-1 to +1)
- **Momentum**: 3-day price change momentum
- **Short Interest**: Percentage of float shorted

## Troubleshooting

### Common Issues

**Reddit Authentication Failed**
- Verify your Reddit app is set to "script" type
- Check client ID and secret are correct
- Ensure username/password are correct

**No Stocks Detected**
- Lower the minimum posts threshold
- Check subreddit names are spelled correctly
- Verify Reddit API is accessible

**Trading212 Integration Not Working**
- Ensure you have a Trading212 account
- Check API key is valid and has read permissions
- Some features require a margin account

### Logs

Enable debug logging to troubleshoot issues:

```yaml
logger:
  default: info
  logs:
    custom_components.meme_stock_insight: debug
```

## Privacy & Security

- Reddit credentials are stored securely in Home Assistant
- API keys are encrypted in the Home Assistant configuration
- No trading data is transmitted externally
- Social media data is processed locally

## Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with tests
4. Follow Home Assistant development guidelines

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This integration is for informational purposes only. It does not constitute financial advice. Always conduct your own research and consider your risk tolerance before making investment decisions. Past performance does not guarantee future results.

The authors are not responsible for any financial losses incurred through the use of this software.
