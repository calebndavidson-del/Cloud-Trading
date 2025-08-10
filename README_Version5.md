# Cloud Trading Bot

A fully cloud-based, always-on trading bot that:
- Scans Yahoo Finance and market APIs for top stocks and trends
- Provides a real-time dashboard (Streamlit)
- Supports backtesting and parameter optimization
- Enables paper trading with best parameters

## Structure

- `backend/`: Bot logic, data collection, optimization, metrics, and paper trading
- `dashboard/`: Streamlit dashboard UI
- `Dockerfile`: For cloud container deployment
- `requirements.txt`: Python dependencies

## Quick Start (Cloud)

1. **Build and run with Docker**  
   ```bash
   docker build -t cloud-trading-bot .
   docker run -p 8501:8501 -e YAHOO_API_KEY=your_key cloud-trading-bot
   ```

2. **Access Dashboard**  
   Visit `http://<your-cloud-ip>:8501` in your browser.

## Deployment

- Deploy on any cloud platform that supports Docker (AWS, DigitalOcean, Fly.io, Render, etc.)
- Set environment variables (e.g., `YAHOO_API_KEY`) in your cloud provider

## Next Steps

- Implement actual data collection, optimization, metrics, and trading logic in `backend/`
- Expand dashboard with real data, plots, and controls
