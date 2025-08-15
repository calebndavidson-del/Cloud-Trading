# Cloud Trading Bot

A fully automated trading bot deployed on Google Cloud with real-time dashboard access from any device.

## 🚀 Features

- **Real-time Trading**: Automated trading strategies with live market data
- **Web Dashboard**: Clean, responsive dashboard accessible from phone/laptop
- **Strategy Backtesting**: Test strategies against historical data
- **Strategy Optimization**: AI-powered strategy parameter optimization
- **Paper Trading**: Safe testing mode before live trading
- **Google Cloud Native**: Fully deployed on Google Cloud Run

## 🌐 Live Demo

Once deployed, access your dashboard at: `https://your-service-url.run.app`

## 📁 Project Structure

```
Cloud-Trading/
├── backend/                    # Core trading logic
│   ├── bot.py                 # Main bot orchestrator
│   ├── config.py              # Configuration management
│   ├── data_collector.py      # Market data fetching
│   ├── optimizer.py           # Strategy optimization
│   └── paper_trader.py        # Paper trading simulation
├── dashboard/                  # Static HTML dashboard
│   └── index.html             # Main dashboard interface
├── api.py                     # Flask API server
├── Dockerfile                 # Container configuration
├── cloud-run.yaml            # Cloud Run service config
├── deploy.sh                 # Google Cloud deployment script
├── setup-local.sh            # Local development setup
└── requirements.txt          # Python dependencies
```

## 🛠️ Quick Start

### Prerequisites

1. **Google Cloud Account** with billing enabled
2. **gcloud CLI** installed and configured
3. **Docker** installed (for local testing)
4. **Python 3.11+** for local development

### 1. Clone and Setup

```bash
git clone https://github.com/your-username/Cloud-Trading.git
cd Cloud-Trading

# Setup local development
./setup-local.sh setup
```

### 2. Configure Environment

Edit the `.env` file created during setup:

```env
# API Keys (get from respective providers)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
IEX_CLOUD_API_KEY=your_iex_cloud_key

# Google Cloud Project
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_REGION=us-central1
```

### 3. Deploy to Google Cloud

```bash
# Set your Google Cloud project
export GOOGLE_CLOUD_PROJECT=your-project-id

# Deploy (this will setup everything automatically)
./deploy.sh
```

The deployment script will:
- Enable required Google Cloud APIs
- Build and push Docker image
- Deploy to Cloud Run
- Configure scaling and security
- Return your dashboard URL

### 4. Access Dashboard

Your dashboard will be available at the URL returned by the deployment script:
- **Dashboard**: `https://your-service-url.run.app`
- **API Health**: `https://your-service-url.run.app/health`
- **API Docs**: `https://your-service-url.run.app/api/system/status`

## 🧪 Local Development

```bash
# Setup development environment
./setup-local.sh setup

# Test the setup
./setup-local.sh test

# Run local server
./setup-local.sh run
```

Local development URLs:
- Dashboard: http://localhost:8080
- API: http://localhost:8080/api/

## 📊 Dashboard Features

The dashboard provides a complete trading interface:

### Live Trading Tab
- Real-time system status
- Portfolio value and P&L
- Start/stop trading controls
- Market data refresh

### Market Data Tab
- Live market data for any symbols
- Price and volume information
- Historical trends (coming soon)

### Backtest Tab
- Test strategies against historical data
- Configure symbols and initial capital
- View detailed results and performance metrics

### Optimization Tab
- AI-powered parameter optimization
- Genetic algorithm-based tuning
- Multi-strategy performance comparison

## 🔧 Configuration

### API Keys

Get free API keys from:
- **Alpha Vantage**: https://www.alphavantage.co/support/#api-key
- **IEX Cloud**: https://iexcloud.io/cloud-login/

### Environment Variables

Set these in Google Cloud Run console or local `.env` file:

```env
# Required
GOOGLE_CLOUD_PROJECT=your-project-id
ALPHA_VANTAGE_API_KEY=your_key
IEX_CLOUD_API_KEY=your_key

# Optional
GOOGLE_CLOUD_REGION=us-central1
ENVIRONMENT=production
TRADING_ENABLED=false  # Set to true for live trading
PAPER_TRADING=true     # Start with paper trading
```

## 🚀 Deployment Commands

```bash
# Full deployment
./deploy.sh

# Setup project only
./deploy.sh setup

# Build and push image only
./deploy.sh build

# Test existing deployment
./deploy.sh test

# Get service URL
./deploy.sh url
```

## 📈 Monitoring

Google Cloud provides built-in monitoring:

1. **Cloud Run Metrics**: CPU, memory, request latency
2. **Logs**: View application logs in Cloud Console
3. **Error Reporting**: Automatic error tracking
4. **Uptime Monitoring**: Setup alerts for downtime

Access monitoring at: https://console.cloud.google.com/run

## 🔒 Security

- **Authentication**: Cloud Run handles HTTPS automatically
- **Environment Variables**: Securely stored in Cloud Run
- **API Keys**: Never exposed in code or logs
- **Paper Trading**: Default safe mode

## 💰 Costs

Google Cloud Run pricing (pay-per-use):
- **Free Tier**: 2 million requests/month
- **Typical Usage**: $5-20/month for most trading bots
- **Scaling**: Automatic scaling from 0 to high traffic

## 🆘 Troubleshooting

### Deployment Issues

```bash
# Check deployment status
gcloud run services describe cloud-trading-bot --region=us-central1

# View logs
gcloud logging read "resource.type=cloud_run_revision" --limit=50

# Test locally
./setup-local.sh test
```

### Common Issues

1. **API Keys**: Ensure all required API keys are set
2. **Permissions**: Check Google Cloud project permissions
3. **Quotas**: Verify API quotas aren't exceeded
4. **Regions**: Ensure consistent region configuration

### Support

- **Issues**: Open GitHub issue with logs
- **Documentation**: Check Google Cloud Run docs
- **Logs**: Use `gcloud logging read` for troubleshooting

## 🔄 Updates

To update your deployment:

```bash
# Pull latest changes
git pull origin main

# Redeploy
./deploy.sh
```

The bot will automatically scale down and up with zero downtime.

## 📚 API Reference

### System Endpoints
- `GET /health` - Health check
- `GET /api/system/status` - System status
- `POST /api/system/start` - Start trading
- `POST /api/system/stop` - Stop trading

### Market Data Endpoints
- `GET /api/market-data?symbols=AAPL,GOOGL` - Get market data
- `GET /api/market-trends` - Get market trends

### Trading Endpoints
- `POST /api/bot/run` - Manual bot execution
- `GET /api/config` - Get configuration

### Backtest Endpoints
- `POST /api/backtest/start` - Start backtest
- `GET /api/backtest/status/{jobId}` - Check status
- `GET /api/backtest/results/{jobId}` - Get results

### Optimization Endpoints
- `POST /api/optimization/start` - Start optimization
- `GET /api/optimization/status/{jobId}` - Check status
- `GET /api/optimization/results/{jobId}` - Get results

## 🎯 Next Steps

1. **Configure API Keys**: Add real market data API keys
2. **Enable Live Trading**: Set `TRADING_ENABLED=true` when ready
3. **Add Monitoring**: Setup Cloud Monitoring alerts
4. **Custom Strategies**: Implement your own trading strategies
5. **Database**: Add Cloud SQL for persistent data storage

## 📄 License

MIT License - see LICENSE file for details.

---

**⚠️ Disclaimer**: This is for educational purposes. Always test thoroughly in paper trading mode before risking real money. Past performance doesn't guarantee future results.