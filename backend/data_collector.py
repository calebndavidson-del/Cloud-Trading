"""
Data collection functions for Yahoo Finance and other APIs.
"""
import yfinance as yf
import requests
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def fetch_market_data(symbols: list = None, use_mock: bool = None) -> Dict[str, Any]:
    """
    Fetch market data from Yahoo Finance.
    
    Args:
        symbols: List of stock symbols to fetch. Defaults to ['AAPL', 'GOOGL', 'MSFT']
        use_mock: If True, use mock data. If None, auto-detect based on environment
    
    Returns:
        Dictionary containing market data for each symbol
    """
    if symbols is None:
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    
    # Auto-detect if we should use mock data
    if use_mock is None:
        import os
        use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
    
    if use_mock:
        return _get_mock_market_data(symbols)
    
    market_data = {}
    
    try:
        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="1d")
            
            if not hist.empty:
                market_data[symbol] = {
                    "price": float(hist['Close'].iloc[-1]),
                    "volume": int(hist['Volume'].iloc[-1]),
                    "open": float(hist['Open'].iloc[-1]),
                    "high": float(hist['High'].iloc[-1]),
                    "low": float(hist['Low'].iloc[-1]),
                    "market_cap": info.get('marketCap', 0),
                    "pe_ratio": info.get('trailingPE', 0)
                }
            else:
                logger.warning(f"No data available for {symbol}")
                market_data[symbol] = {"error": "No data available"}
                
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        # Fallback to mock data on error
        logger.info("Falling back to mock data")
        return _get_mock_market_data(symbols)
    
    return market_data

def _get_mock_market_data(symbols: list) -> Dict[str, Any]:
    """Generate mock market data for testing."""
    import random
    random.seed(42)  # For reproducible results
    
    base_prices = {
        'AAPL': 190.0, 'GOOGL': 130.0, 'MSFT': 350.0, 
        'TSLA': 250.0, 'AMZN': 150.0, 'META': 300.0,
        'NVDA': 500.0, 'NFLX': 450.0
    }
    
    market_data = {}
    for symbol in symbols:
        base_price = base_prices.get(symbol, 100.0)
        variation = random.uniform(-0.05, 0.05)  # ±5% variation
        current_price = base_price * (1 + variation)
        
        market_data[symbol] = {
            "price": round(current_price, 2),
            "volume": random.randint(1000000, 50000000),
            "open": round(current_price * random.uniform(0.98, 1.02), 2),
            "high": round(current_price * random.uniform(1.01, 1.05), 2),
            "low": round(current_price * random.uniform(0.95, 0.99), 2),
            "market_cap": random.randint(50000000000, 3000000000000),
            "pe_ratio": round(random.uniform(15, 35), 2)
        }
    
    return market_data

def fetch_market_trends() -> Dict[str, Any]:
    """
    Fetch market trends and top gainers/losers.
    
    Returns:
        Dictionary containing market trend data
    """
    try:
        # Check if we should use mock data
        import os
        use_mock = os.getenv("USE_MOCK_DATA", "false").lower() == "true"
        
        if use_mock:
            return _get_mock_trends()
        
        # Get S&P 500 data as market trend indicator
        sp500 = yf.Ticker("^GSPC")
        sp500_hist = sp500.history(period="5d")
        
        if not sp500_hist.empty:
            current_price = float(sp500_hist['Close'].iloc[-1])
            prev_price = float(sp500_hist['Close'].iloc[-2])
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            return {
                "sp500": {
                    "current_price": current_price,
                    "change_percent": change_pct,
                    "trend": "up" if change_pct > 0 else "down"
                }
            }
    except Exception as e:
        logger.error(f"Error fetching market trends: {e}")
        logger.info("Falling back to mock trend data")
        return _get_mock_trends()
    
    return {"error": "No trend data available"}

def _get_mock_trends() -> Dict[str, Any]:
    """Generate mock market trend data."""
    import random
    random.seed(42)
    
    change_pct = random.uniform(-2.0, 2.0)
    
    return {
        "sp500": {
            "current_price": 4500.0 + random.uniform(-50, 50),
            "change_percent": round(change_pct, 2),
            "trend": "up" if change_pct > 0 else "down"
        }
    }