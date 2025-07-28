# 🚀 Meme Stock Insight v0.5.0 - Home Assistant Integration

*Transform your Home Assistant into a meme stock command center. Because why check Reddit manually when your smart home can do it for you?*

---

## ⚠️ DISCLAIMER

**This integration is for entertainment and educational purposes only.**  
Nothing here constitutes financial advice. Past performance of meme stocks does not guarantee future diamond hands. Please consult with a financial advisor before YOLOing your life savings. We are not responsible for any tendies lost or gained. **To the moon** only if the stars align, the apes unite, and the hedgies cry. 🚀

---

## 🦍 What This Integration Does

Meme Stock Insight brings the chaotic energy of r/wallstreetbets directly into your Home Assistant dashboard. It monitors Reddit discussions, tracks stock prices, and provides **intelligent analysis of meme stock lifecycle stages**—so you can make informed decisions about when to hold the line and when to take profits (or at least when to order more crayons).

---

## 🎯 Key Features

- **Reddit Mention Tracking:** Scans multiple subreddits for stock mentions and sentiment (because apes know best)
- **Individual Stock Tracking:** Get dedicated entities for the **top 3 meme stocks** with full company names—no more guessing what “GME” stands for
- **Lifecycle Stage Analysis:** Know when stocks are rising, peaking, or heading **to the moon** (or straight back to Valhalla)
- **Live Stock Prices:** Real-time price data, volume analysis, and market cap information—no more refreshing Yahoo Finance
- **Sentiment Analysis:** Measures the collective emotional state of retail investors (apes together strong)
- **Diamond Hands Detection:** Advanced algorithms to detect optimal entry and exit points (because paper hands never win)

---

## 📊 Sensors You'll Get

### Core Analytics
- **Stock Mentions**: Total mentions across all tracked subreddits with detailed breakdowns
- **Market Sentiment**: Average sentiment score (-1 to +1) with distribution analysis
- **Trending Stocks**: Count of stocks gaining momentum (aka “going parabolic”)

### Individual Top Performers
- **Meme Stock #1**: The current king of the apes (e.g., “META - Meta Platforms Inc”)
- **Meme Stock #2**: The silver medal holder (e.g., “TSLA - Tesla Inc”)
- **Meme Stock #3**: Bronze but still going strong (e.g., “GME - GameStop Corp”)

*Each comes with current price, daily change %, volume data, and 5-day price history—so you’ll always know if it’s time to “buy the dip” or “sell the rip.”*

### Intelligent Stage Analysis
- **Meme Stock Stage**: Your personal “don’t catch a falling knife” detector

**Stage Progression:**
- 🌱 **Start** → New mentions appearing, early buzz (quiet... too quiet)
- 📈 **Rising Interest** → Increased chatter and volume spikes (apes start to assemble)
- 🚀 **Stock Rising** → Price momentum building with strong sentiment (rockets warming up)
- 🏔️ **Within Estimated Peak** → High activity, consider your exit strategy (moon or bust)
- 🛑 **DO NOT BUY** → Danger zone detected, paper hands might be wise (CEOs tweeting emojis)
- 📉 **Dropping** → The party’s over, time for loss porn posts (portfolio in shambles)

---

## 🎪 The Meme Stock Lifecycle

Our advanced AI (Arathmatic Ignorance, not Artificial Intelligence) analyzes multiple factors to determine where each stock sits in the classic meme stock journey:

- **Volume Spikes**: When trading volume goes brrrr
- **Reddit Mentions**: Ape activity tracking across subreddits
- **Price Momentum**: Because stonks only go up (except when they don’t)
- **Sentiment Analysis**: Measuring the collective emotional state of retail investors
- **Historical Patterns**: Learning from past rocket ships and crash landings

---

## 🛠️ Installation

### Prerequisites

1. **Home Assistant** (obviously)
2. **HACS** installed and configured
3. **Reddit Account** with API access
4. **Diamond hands** (optional but recommended)

---

### Reddit API Setup

*This is the part where you become a Reddit developer. Don’t worry, it’s easier than timing the market.*

1. Visit [Reddit App Preferences](https://www.reddit.com/prefs/apps)
2. Click **“create another app...”**
3. **CRITICAL:** Select **“script”** as the application type (not “web” or “installed”)
4. Fill in the details:
   - **Name:** `meme_stock_insight` (or whatever makes you happy)
   - **Type:** **script** (seriously, this is important)
   - **Redirect URI:** `http://localhost` (required but ignored)
5. Copy your **Client ID** (14-character string under the app name)
6. Copy your **Client Secret** (the “secret” string)
7. Make sure the Reddit username you’ll use owns this app

*Pro tip: If you get authentication errors, double-check that your app type is “script”. This has caused more headaches than a GameStop squeeze.*

---

### HACS Installation

1. Add this repository to HACS as a custom repository:
   - **URL:** `https://github.com/BestMasterChief/meme_stock_insight`
   - **Category:** Integration
2. Install **“Meme Stock Insight”** from HACS
3. Restart Home Assistant (core restart is sufficient)

---

### Integration Setup

1. Go to **Settings** → **Devices & Services**
2. Click **“+ Add Integration”**
3. Search for **“Meme Stock Insight”**
4. Enter your Reddit credentials:
   - Client ID and Client Secret from your Reddit app
   - Your Reddit username and password
   - Subreddits to monitor (default: `wallstreetbets,stocks,investing`)
   - Update interval (default: 5 minutes)

---

## 📈 Dashboard Examples

### Basic Meme Stock Card

type: entities
title: "🦍 Current Meme Stock Leaders"
entities:

sensor.meme_stock_meme_stock_1

sensor.meme_stock_meme_stock_2

sensor.meme_stock_meme_stock_3

text

### Stage Analysis Display

type: entity
entity: sensor.meme_stock_meme_stock_stage
name: "Market Phase"
icon: mdi:chart-timeline-variant

text

### Sentiment Gauge

type: gauge
entity: sensor.meme_stock_market_sentiment
name: "Ape Sentiment"
min: -1
max: 1
severity:
green: 0.2
yellow: -0.2
red: -0.5

text

---

## 🤖 Automation Ideas

### HODL Alert

automation:

alias: "Diamond Hands Reminder"
trigger:

platform: state
entity_id: sensor.meme_stock_meme_stock_stage
to: "Within Estimated Peak"
action:

service: notify.mobile_app
data:
title: "💎🤲 Decision Time!"
message: "{{ states('sensor.meme_stock_meme_stock_1') }} might be peaking. Time to be greedy when others are fearful?"

text

### Danger Zone Warning

automation:

alias: "Paper Hands Alert"
trigger:

platform: state
entity_id: sensor.meme_stock_meme_stock_stage
to: "DO NOT BUY"
action:

service: notify.mobile_app
data:
title: "🚨 Abort Mission!"
message: "Meme stock danger zone detected. Consider your exit strategy."

text

---

## 🔧 Configuration Options

All settings can be modified through the Home Assistant UI after initial setup:

- **Subreddits:** Comma-separated list (default: `wallstreetbets,stocks,investing`)
- **Update Interval:** 60–3600 seconds (default: 300 seconds/5 minutes)
- **Stock Symbols:** Automatically tracks 60+ popular meme and mainstream stocks

---

## 📊 Technical Details

### Data Sources

- **Reddit API:** Via PRAW (Python Reddit API Wrapper)
- **Stock Prices:** Yahoo Finance API via `yfinance`
- **Real-time Updates:** Every 5 minutes (configurable)

### Tracked Symbols

GME, AMC, TSLA, META, NVDA, AMD, AAPL, PLTR, HOOD, COIN, and 50+ more popular meme stocks and crypto pairs

### Performance

- Processes up to 5 subreddits simultaneously
- Analyzes 30 posts per subreddit with 10 comments each
- 90-second timeout protection prevents Home Assistant blocking
- Intelligent caching reduces API calls

---

## 🚨 Troubleshooting

### "Reddit Authentication Failed"

- Verify your app type is **“script”** (most common issue)
- Check that your Reddit username owns the Reddit app
- Ensure Client ID and Client Secret are correct
- Confirm your username/password are accurate

### "Integration Setup Timeout"

- Restart Home Assistant completely
- Check your internet connection
- Verify Reddit API isn’t down (check redditstatus.com)

### Zero Values in All Sensors

- Wait 5–10 minutes after setup for first data fetch
- Check that your configured subreddits are accessible
- Verify the integration shows as “Connected” in Devices & Services

### HACS Installation Issues

- Ensure `hacs.json` exists in repository root
- Verify you’re using the custom repository URL
- Check that HACS is properly configured

---

## 🎭 The Fine Print

This integration is provided “as-is” with no warranties, express or implied. We make no guarantees about:

- Accuracy of Reddit sentiment analysis
- Reliability of stock price data
- Your ability to time the market
- Whether diamond hands or paper hands is the right strategy
- The moon’s actual distance from any given stock price

**Remember:** The market can remain irrational longer than you can remain solvent. This integration is a tool for information, not a crystal ball for financial success.

---

## 🤝 Contributing

Found a bug? Have a feature request? Want to add more rocket emojis?

- **Issues:** [GitHub Issues](https://github.com/BestMasterChief/meme_stock_insight/issues)
- **Discussions:** Share your diamond hands success stories
- **Pull Requests:** Always welcome (especially if they make the code go brrr faster)

---

## 📜 License

MIT License – Because open source is like diamond hands for code.

*“In the midst of chaos, there is also opportunity.”* — Sun Tzu (probably about meme stocks)

**Version 0.5.0** – Now with enhanced ape intelligence and 42% more rockets 🚀

*This integration was built by apes, for apes, with the understanding that we’re all just trying to make it **to the moon** one stonk at a time.*
