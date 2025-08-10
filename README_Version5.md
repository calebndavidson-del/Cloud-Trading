# Cloud Trading Bot

A fully cloud-based, always-on trading bot with **modular market data fetching** that:
- Supports multiple data providers (Yahoo Finance, Alpha Vantage, IEX Cloud) with automatic fallback
- Scans market APIs for top stocks and trends with real-time data access
- Provides a real-time dashboard (Streamlit)
- Supports backtesting and parameter optimization
- Enables paper trading with best parameters

## 🚀 New Features: Modular Market Data Fetcher

### Multi-Provider Support
The trading bot now includes a robust market data fetching system that supports:

- **Yahoo Finance** (Primary, no API key required)
- **Alpha Vantage** (Secondary, requires API key)
- **IEX Cloud** (Tertiary, requires API key)

### Automatic Fallback System
- Attempts to fetch data from all providers simultaneously
- Automatically falls back to secondary sources if primary providers fail
- Intelligent caching to reduce API calls and improve performance
- Graceful error handling with detailed logging

### Key Benefits
- **Always Fresh Data**: System ensures strategies always have access to the freshest available data
- **High Availability**: Multiple provider fallback prevents data outages
- **Cost Optimization**: Intelligent caching reduces unnecessary API calls
- **Easy Extension**: Simple interface for adding new data providers

## 📁 Project Structure

```
Cloud-Trading/
├── market_data_config.json          # Configuration for data providers
├── market_data_provider.py          # Base abstract provider class
├── yahoo_finance_provider.py        # Yahoo Finance implementation
├── alpha_vantage_provider.py        # Alpha Vantage implementation
├── iex_cloud_provider.py           # IEX Cloud implementation
├── market_data_manager.py          # Main orchestration manager
├── market_data_examples.py         # Integration examples
├── backend_data_collector_Version2.py  # Enhanced data collector
├── backend_bot_Version2.py         # Main bot logic
├── backend_config_Version2.py      # Configuration management
├── dashboard_app_Version2.py       # Streamlit dashboard
└── requirements_Version9.txt       # Python dependencies
```

## 🛠️ Setup & Installation

### 1. Basic Setup

```bash
# Clone the repository
git clone <repository-url>
cd Cloud-Trading

# Install dependencies
pip install -r requirements_Version9.txt
```

### 2. API Key Configuration

#### Option A: Environment Variables (Recommended)
```bash
export ALPHA_VANTAGE_API_KEY="your-alpha-vantage-key"
export IEX_CLOUD_API_KEY="your-iex-cloud-key"
```

#### Option B: Configuration File
Edit `market_data_config.json`:
```json
{
  "providers": {
    "alpha_vantage": {
      "enabled": true,
      "api_key": "your-alpha-vantage-key"
    },
    "iex_cloud": {
      "enabled": true,
      "api_key": "your-iex-cloud-key"
    }
  }
}
```

### 3. Get API Keys

#### Alpha Vantage (Free Tier: 5 calls/minute)
1. Visit: https://www.alphavantage.co/support/#api-key
2. Sign up for a free account
3. Copy your API key

#### IEX Cloud (Free Tier: 50,000 calls/month)
1. Visit: https://iexcloud.io/pricing/
2. Sign up for a free account
3. Copy your publishable token

**Note**: Yahoo Finance works without an API key and serves as the primary fallback.

## 🚀 Quick Start

### Basic Usage

```python
from backend_data_collector_Version2 import fetch_market_data

# Fetch data for default symbols
data = fetch_market_data()
print(data)

# Fetch data for specific symbols
custom_symbols = ["AAPL", "GOOGL", "TSLA"]
data = fetch_market_data(custom_symbols)
```

### Advanced Usage

```python
from market_data_manager import MarketDataManager

# Initialize manager
manager = MarketDataManager()

# Fetch single quote
quote = manager.fetch_quote_sync("AAPL")
print(f"AAPL: ${quote['price']:.2f} from {quote['provider']}")

# Fetch multiple quotes
quotes = manager.fetch_quotes_sync(["AAPL", "GOOGL", "MSFT"])
for symbol, data in quotes.items():
    if data:
        print(f"{symbol}: ${data['price']:.2f}")
```

### Run Example Integration

```bash
python market_data_examples.py
```

### Run the Trading Bot

```bash
python backend_bot_Version2.py
```

## 📊 Data Provider Configuration

### Configuration File: `market_data_config.json`

```json
{
  "providers": {
    "yahoo_finance": {
      "enabled": true,
      "priority": 1,
      "timeout": 10,
      "base_url": "https://query1.finance.yahoo.com/v8/finance/chart/",
      "api_key": null
    },
    "alpha_vantage": {
      "enabled": true,
      "priority": 2,
      "timeout": 15,
      "base_url": "https://www.alphavantage.co/query",
      "api_key": "ALPHA_VANTAGE_API_KEY"
    },
    "iex_cloud": {
      "enabled": true,
      "priority": 3,
      "timeout": 12,
      "base_url": "https://cloud.iexapis.com/stable/stock/",
      "api_key": "IEX_CLOUD_API_KEY"
    }
  },
  "fallback_settings": {
    "max_retries": 3,
    "retry_delay": 1.0,
    "cache_duration": 60
  },
  "data_settings": {
    "default_symbols": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
    "fields": ["price", "volume", "change", "change_percent", "high", "low", "open", "previous_close"],
    "update_interval": 30
  }
}
```

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| `enabled` | Enable/disable provider | `true` |
| `priority` | Provider priority (1=highest) | `1` |
| `timeout` | Request timeout in seconds | `10` |
| `max_retries` | Maximum retry attempts | `3` |
| `retry_delay` | Delay between retries | `1.0` |
| `cache_duration` | Cache data for N seconds | `60` |

## 🔧 Adding New Data Sources

### Step 1: Create Provider Class

Create a new file `your_provider.py`:

```python
from market_data_provider import MarketDataProvider, ProviderError
import aiohttp

class YourProvider(MarketDataProvider):
    def __init__(self, config):
        super().__init__(config)
        self.api_key = config.get('api_key')
    
    async def fetch_quote(self, symbol):
        # Implement your provider logic
        async with aiohttp.ClientSession() as session:
            # Make API call
            # Process response
            # Return normalized data
            pass
    
    async def fetch_quotes(self, symbols):
        # Implement batch fetching
        pass
```

### Step 2: Register Provider

Update `market_data_manager.py`:

```python
from your_provider import YourProvider

# Add to provider_classes dictionary
provider_classes = {
    'yahoo_finance': YahooFinanceProvider,
    'alpha_vantage': AlphaVantageProvider,
    'iex_cloud': IEXCloudProvider,
    'your_provider': YourProvider  # Add here
}
```

### Step 3: Update Configuration

Add to `market_data_config.json`:

```json
{
  "providers": {
    "your_provider": {
      "enabled": true,
      "priority": 4,
      "timeout": 10,
      "api_key": "YOUR_API_KEY"
    }
  }
}
```

## 🔍 Monitoring & Debugging

### Check Provider Status

```python
from backend_data_collector_Version2 import get_provider_status

status = get_provider_status()
for provider, info in status.items():
    print(f"{provider}: {'✓' if info['available'] else '✗'}")
```

### Monitor Cache Performance

```python
from backend_data_collector_Version2 import get_cache_info

cache_info = get_cache_info()
print(f"Cache efficiency: {cache_info['fresh_entries']}/{cache_info['total_entries']}")
```

### Clear Cache

```python
from backend_data_collector_Version2 import clear_cache

clear_cache()
print("Cache cleared")
```

## 📈 Integration with Trading Strategies

### Example Strategy Implementation

```python
from market_data_manager import MarketDataManager

class MomentumStrategy:
    def __init__(self):
        self.data_manager = MarketDataManager()
    
    def get_signals(self, symbols):
        # Get fresh data with automatic fallback
        quotes = self.data_manager.fetch_quotes_sync(symbols)
        
        signals = {}
        for symbol, data in quotes.items():
            if data and data['change_percent'] > 2.0:
                signals[symbol] = 'BUY'
            elif data and data['change_percent'] < -2.0:
                signals[symbol] = 'SELL'
            else:
                signals[symbol] = 'HOLD'
        
        return signals
```

### Ensure Fresh Data Access

The system guarantees fresh data through:

1. **Multi-provider fetching**: Tries all providers simultaneously
2. **Intelligent caching**: Reduces redundant API calls
3. **Automatic fallback**: Falls back to secondary providers
4. **Error handling**: Graceful degradation on failures

## 🐳 Docker Deployment

### Build and Run

```bash
# Build container
docker build -t cloud-trading-bot .

# Run with environment variables
docker run -p 8501:8501 \
  -e ALPHA_VANTAGE_API_KEY=your_key \
  -e IEX_CLOUD_API_KEY=your_key \
  cloud-trading-bot
```

### Access Dashboard

Visit `http://<your-cloud-ip>:8501` in your browser.

## 🌐 Cloud Deployment

Deploy on any cloud platform that supports Docker:

- **AWS**: ECS, EC2, or Fargate
- **Google Cloud**: Cloud Run or GKE
- **DigitalOcean**: App Platform or Droplets
- **Render**: Web Services
- **Fly.io**: Apps

### Environment Variables for Cloud

Set these in your cloud provider:

```
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
IEX_CLOUD_API_KEY=your_iex_cloud_key
YAHOO_API_KEY=not_required
```

## 🔍 Troubleshooting

### Common Issues

1. **"Provider not available"**
   - Check API keys are set correctly
   - Verify network connectivity
   - Check provider service status

2. **"All providers failed"**
   - Check internet connection
   - Verify API quotas haven't been exceeded
   - Check if symbols are valid

3. **Slow performance**
   - Increase cache duration
   - Reduce number of symbols
   - Check provider rate limits

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 API Reference

### MarketDataManager

| Method | Description | Returns |
|--------|-------------|---------|
| `fetch_quote_sync(symbol)` | Fetch single quote | `Dict` or `None` |
| `fetch_quotes_sync(symbols)` | Fetch multiple quotes | `Dict[str, Dict]` |
| `get_provider_status()` | Get provider status | `Dict` |
| `clear_cache()` | Clear data cache | `None` |
| `get_cache_info()` | Get cache statistics | `Dict` |

### Data Format

```python
{
  "symbol": "AAPL",
  "price": 150.25,
  "volume": 1000000,
  "change": 2.50,
  "change_percent": 1.69,
  "high": 152.00,
  "low": 148.50,
  "open": 149.00,
  "previous_close": 147.75,
  "timestamp": 1634567890.123,
  "provider": "YahooFinanceProvider"
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add your data provider or enhancement
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

**Need help?** Check the examples in `market_data_examples.py` or open an issue!
