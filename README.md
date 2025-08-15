# Cloud Trading Bot - Google Cloud Deployment

A sophisticated trading bot with modern cloud-native deployment using Google Cloud Run. This version provides automatic scaling, serverless architecture, and zero infrastructure maintenance.

## 🏗️ Google Cloud Architecture

### Cloud Stack
- **Backend**: Python Flask API → Google Cloud Run (serverless containers)
- **Frontend**: React Dashboard (can be deployed to any static hosting)
- **Database**: In-memory/file-based configuration
- **CI/CD**: GitHub Actions (automated deployment on push)

### Benefits
- ✅ **Serverless scaling** (automatic scale to zero)
- ✅ **Container-based** (Docker deployment)
- ✅ **Pay-per-use** pricing model
- ✅ **Git push = deploy** workflow
- ✅ **No infrastructure management**

## 🚀 Quick Start (Google Cloud Deployment)

### 1. Prerequisites
- GitHub account
- Google Cloud account (free tier available)
- Google Cloud CLI installed
- Docker installed (for local testing)

### 2. Google Cloud Setup
```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/Cloud-Trading.git
cd Cloud-Trading

# Install Google Cloud CLI if not already installed
# https://cloud.google.com/sdk/docs/install

# Login and create a new project
gcloud auth login
gcloud projects create YOUR_PROJECT_ID --name="Cloud Trading Bot"
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
```

### 3. Local Development Setup
```bash
# Install Python dependencies
pip install -r requirements.txt
pip install flask flask-cors gunicorn

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your settings

# Start local development server
export PYTHONPATH=$(pwd)
python api.py
```

### 4. Deploy to Google Cloud Run
```bash
# Build and deploy using GitHub Actions (recommended)
git push origin main

# Or deploy manually:
# Build Docker image
docker build -t gcr.io/YOUR_PROJECT_ID/cloud-trading-bot .

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/cloud-trading-bot

# Deploy to Cloud Run
gcloud run deploy cloud-trading-bot \
    --image gcr.io/YOUR_PROJECT_ID/cloud-trading-bot \
    --platform managed \
    --region us-west1 \
    --allow-unauthenticated \
    --port 8080
```

### 5. Test Locally
```bash
# Start the API server
python api.py

# The API will be available at:
# Backend API: http://localhost:8080
# Health check: http://localhost:8080/health
# API status: http://localhost:8080/api/status
```

## 🔧 Configuration

### Environment Variables
- Local environment: `.env.example` (copy to `.env.local`)
- Production environment: Set via Cloud Run console or CLI

### API Endpoints
- Health Check: `/health`  
- System Status: `/api/status`
- Market Data: `/api/market-data`
- Bot Execution: `/api/bot/run` (POST)
- Configuration: `/api/config`

## 🛠️ Local Development

### Backend Development
```bash
# Run the API server
python api.py

# Run the dashboard app
python dashboard_app.py
```

Visit:
- Backend API: http://localhost:8080
- Dashboard App: Run `streamlit run dashboard_app.py` then visit http://localhost:8501

## 📚 API Endpoints

The trading bot includes a REST API with these endpoints:

- `GET /health` - Health check
- `GET /api/status` - Bot status and configuration
- `GET /api/market-data` - Real-time market data
- `GET /api/market-trends` - Market trends and indicators
- `POST /api/bot/run` - Execute trading bot
- `GET /api/config` - Bot configuration (non-sensitive)

## 🛠️ Development Workflow

### Local Development
```bash
# Backend development
python api.py

# Run trading bot
python -m backend.bot
```

### Cloud Deployment
Simply push to main branch for automatic deployment:
```bash
git push origin main
```

## 📁 Project Structure

```
Cloud-Trading/
├── backend/                    # Core trading logic
│   ├── __init__.py
│   ├── bot.py                 # Main bot orchestrator
│   ├── config.py              # Configuration management
│   ├── data_collector.py      # Market data fetching
│   ├── decision_engine.py     # Trading decision engine
│   ├── live_data_manager.py   # Live data management
│   ├── market_scanner.py      # Market scanning
│   ├── metrics.py             # Financial calculations
│   ├── optimizer.py           # Strategy optimization
│   ├── paper_trader.py        # Paper trading simulation
│   └── optimization/          # Advanced optimization
│       ├── README.md          # Optimization documentation
│       ├── enhanced_optimizer.py
│       ├── parameter_space.py
│       └── usage_examples.py
├── frontend/                  # React dashboard (optional)
├── .github/workflows/         # CI/CD configuration
│   └── deploy.yml            # Google Cloud deployment
├── api.py                    # Flask API server
├── dashboard_app.py          # Streamlit dashboard
├── Dockerfile               # Google Cloud Run container
├── requirements.txt         # Python dependencies
├── market_data_config.json  # Market data configuration
├── .env.example            # Environment variables template
├── README.md               # This file
└── DEPLOYMENT.md           # Detailed deployment guide
```

## 🛠️ Local Development

### Setup Local Environment

```bash
# Install Python dependencies
pip install -r requirements.txt

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your settings

# Test the bot locally
export PYTHONPATH=$(pwd)
python backend/bot.py
```

### Test Individual Components

```bash
# Test market data collection
python -c "from backend.data_collector import fetch_market_data; print(fetch_market_data())"

# Test paper trading
python -c "from backend.paper_trader import paper_trade; print(paper_trade({}))"

# Test strategy optimization
python -c "from backend.optimizer import optimize_strategy; from backend.data_collector import fetch_market_data; print(optimize_strategy(fetch_market_data(), 5))"
```

## 🎯 Trading Features

### Core Capabilities
- **Real-time market data** fetching from multiple providers
- **Technical analysis** with 20+ indicators
- **Paper trading** simulation for strategy testing  
- **Live trading** execution (when enabled)
- **Strategy optimization** using advanced algorithms
- **Risk management** with configurable parameters
- **Decision transparency** with detailed logging

### Supported Assets
- US stocks and ETFs
- Major indices (S&P 500, NASDAQ, etc.)
- Crypto currencies (via API integration)
- Options (with extended data sources)

## 🔧 Configuration Options

The bot supports extensive configuration through environment variables and config files:

- **Trading mode**: Paper trading, live trading, or analysis only
- **Market data sources**: Multiple provider fallback
- **Risk parameters**: Position sizing, stop losses, max positions
- **Strategy parameters**: Technical indicator settings, signals
- **Optimization settings**: Backtesting periods, parameter ranges

See `.env.example` for all available configuration options.

## 🚀 Deployment Options

### Google Cloud Run (Recommended)
- Automatic scaling and zero-maintenance serverless deployment
- Pay-per-use pricing model
- Integrated CI/CD with GitHub Actions

### Local Development
- Flask API server for development and testing
- Streamlit dashboard for interactive analysis
- Docker containers for consistent environments

### Frontend Options
- React dashboard (included in `frontend/` directory)
- Streamlit app (`dashboard_app.py`)
- REST API for custom integrations

## 📚 Documentation

- **Core Trading Logic**: See `backend/` directory
- **Optimization Guide**: See `backend/optimization/README.md`
- **Deployment Guide**: See `DEPLOYMENT.md`
- **API Reference**: Built-in at `/api/status` endpoint

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This trading bot is for educational and research purposes only. Trading involves significant risk of loss. Always use paper trading mode for testing. Never risk more than you can afford to lose. The authors are not responsible for any financial losses.

## 📞 Support

- 🐛 Issues: [GitHub Issues](https://github.com/calebndavidson-del/Cloud-Trading/issues)
- 📖 Documentation: Available in repository docs
- 💡 Feature Requests: Submit via GitHub Issues