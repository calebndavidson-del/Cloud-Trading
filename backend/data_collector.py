"""
Live-only data collection functions - NO MOCK DATA ALLOWED.
Enhanced with comprehensive decision support data.
"""
import asyncio
import yfinance as yf
import pandas as pd
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

# Import the new live data manager
from backend.live_data_manager import get_live_market_data_manager, LiveMarketDataManager
from backend.decision_engine import DecisionEngine

logger = logging.getLogger(__name__)

def fetch_market_data(symbols: list = None, use_mock: bool = None) -> Dict[str, Any]:
    """
    Fetch LIVE market data - NO MOCK DATA ALLOWED.
    
    Args:
        symbols: List of stock symbols to fetch. Defaults to ['AAPL', 'GOOGL', 'MSFT']
        use_mock: DEPRECATED - Mock data is not allowed in production
    
    Returns:
        Dictionary containing LIVE market data for each symbol
        
    Raises:
        Exception: If live data cannot be fetched or if mock data is requested
    """
    if symbols is None:
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    
    # ENFORCE LIVE-ONLY MODE - No mock data allowed
    if use_mock is True:
        raise Exception("Mock data is not allowed - live data only mode enforced")
    
    # Check environment variable and reject if mock is requested
    import os
    if os.getenv("USE_MOCK_DATA", "false").lower() == "true":
        raise Exception("USE_MOCK_DATA environment variable detected - live data only mode enforced")
    
    logger.info(f"Fetching LIVE market data for symbols: {symbols}")
    
    try:
        # Use the direct live data function for sync context
        return _fetch_direct_live_data(symbols)
            
    except Exception as e:
        logger.error(f"Error fetching live market data: {e}")
        # DO NOT fall back to mock data - fail instead
        raise Exception(f"Failed to fetch live market data: {e}. Mock data fallback is disabled.")

def _fetch_direct_live_data(symbols: List[str]) -> Dict[str, Any]:
    """
    Direct live data fetch using yfinance for sync contexts
    """
    market_data = {}
    
    for symbol in symbols:
        try:
            ticker = yf.Ticker(symbol)
            
            # Get 1-minute data for freshness
            hist = ticker.history(period="1d", interval="1m")
            info = ticker.info
            
            if not hist.empty:
                latest = hist.iloc[-1]
                
                # Validate data freshness
                latest_timestamp = hist.index[-1].to_pydatetime()
                # Ensure timezone-naive comparison
                if latest_timestamp.tzinfo is not None:
                    latest_timestamp = latest_timestamp.replace(tzinfo=None)
                
                current_time = datetime.now()
                age_seconds = (current_time - latest_timestamp).total_seconds()
                
                if age_seconds > 300:  # 5 minutes max age
                    logger.warning(f"Data for {symbol} is {age_seconds/60:.1f} minutes old")
                
                market_data[symbol] = {
                    "price": float(latest['Close']),
                    "volume": int(latest['Volume']),
                    "open": float(latest['Open']),
                    "high": float(latest['High']),
                    "low": float(latest['Low']),
                    "market_cap": info.get('marketCap', 0),
                    "pe_ratio": info.get('trailingPE', 0),
                    "timestamp": latest_timestamp.isoformat(),
                    "data_age_seconds": age_seconds,
                    "data_quality": {
                        'freshness': 'fresh' if age_seconds < 300 else 'stale',
                        'source': 'yahoo_finance_direct',
                        'timestamp': datetime.now().isoformat()
                    }
                }
            else:
                logger.error(f"No live data available for {symbol}")
                raise Exception(f"No live data available for {symbol}")
                
        except Exception as e:
            logger.error(f"Error fetching live data for {symbol}: {e}")
            raise Exception(f"Failed to fetch live data for {symbol}: {e}")
    
    return market_data

# MOCK DATA FUNCTIONS REMOVED - Live data only mode enforced

def fetch_market_trends() -> Dict[str, Any]:
    """
    Fetch LIVE market trends - NO MOCK DATA ALLOWED.
    
    Returns:
        Dictionary containing LIVE market trend data
        
    Raises:
        Exception: If live data cannot be fetched
    """
    logger.info("Fetching LIVE market trends")
    
    try:
        # Check if mock data is being requested and reject
        import os
        if os.getenv("USE_MOCK_DATA", "false").lower() == "true":
            raise Exception("USE_MOCK_DATA environment variable detected - live data only mode enforced")
        
        # Get live S&P 500 data as market trend indicator
        sp500 = yf.Ticker("^GSPC")
        sp500_hist = sp500.history(period="5d", interval="1m")  # Use minute data for freshness
        
        if not sp500_hist.empty:
            current_price = float(sp500_hist['Close'].iloc[-1])
            prev_price = float(sp500_hist['Close'].iloc[-2])
            change_pct = ((current_price - prev_price) / prev_price) * 100
            
            # Validate data freshness
            latest_timestamp = sp500_hist.index[-1].to_pydatetime()
            age_seconds = (datetime.now() - latest_timestamp).total_seconds()
            
            if age_seconds > 300:  # 5 minutes max age
                logger.warning(f"Market trend data is {age_seconds/60:.1f} minutes old")
            
            return {
                "sp500": {
                    "current_price": current_price,
                    "change_percent": change_pct,
                    "trend": "up" if change_pct > 0 else "down",
                    "timestamp": latest_timestamp.isoformat(),
                    "data_age_seconds": age_seconds,
                    "data_quality": {
                        'freshness': 'fresh' if age_seconds < 300 else 'stale',
                        'source': 'yahoo_finance_live',
                        'timestamp': datetime.now().isoformat()
                    }
                }
            }
        else:
            raise Exception("No live S&P 500 data available")
            
    except Exception as e:
        logger.error(f"Error fetching live market trends: {e}")
        # DO NOT fall back to mock data - fail instead
        raise Exception(f"Failed to fetch live market trends: {e}. Mock data fallback is disabled.")

async def fetch_comprehensive_market_data(symbols: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Fetch comprehensive market data including technical, fundamental, and sentiment data
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        Dictionary with comprehensive data for each symbol
    """
    logger.info(f"Fetching comprehensive market data for {len(symbols)} symbols")
    
    try:
        data_manager = get_live_market_data_manager()
        
        # Fetch all data types concurrently
        tasks = []
        
        # Live market data
        tasks.append(data_manager.fetch_live_market_data(symbols))
        
        # Historical data for technical analysis (for each symbol)
        for symbol in symbols:
            tasks.append(data_manager.fetch_historical_data(symbol, period="3mo", interval="1d"))
            tasks.append(data_manager.fetch_fundamental_data(symbol))
            tasks.append(data_manager.fetch_news_sentiment(symbol))
            tasks.append(data_manager.fetch_social_sentiment(symbol))
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Parse results
        live_data = results[0] if not isinstance(results[0], Exception) else {}
        
        comprehensive_data = {}
        
        for i, symbol in enumerate(symbols):
            symbol_data = {
                'live_data': live_data.get(symbol, {}).data if symbol in live_data else {},
                'historical_data': results[1 + i * 4] if not isinstance(results[1 + i * 4], Exception) else pd.DataFrame(),
                'fundamental_data': results[2 + i * 4] if not isinstance(results[2 + i * 4], Exception) else {},
                'news_sentiment': results[3 + i * 4] if not isinstance(results[3 + i * 4], Exception) else {},
                'social_sentiment': results[4 + i * 4] if not isinstance(results[4 + i * 4], Exception) else {},
                'timestamp': datetime.now().isoformat()
            }
            
            comprehensive_data[symbol] = symbol_data
        
        logger.info(f"Successfully fetched comprehensive data for {len(comprehensive_data)} symbols")
        return comprehensive_data
        
    except Exception as e:
        logger.error(f"Error fetching comprehensive market data: {e}")
        raise

async def make_trading_decisions(symbols: List[str]) -> Dict[str, Any]:
    """
    Make trading decisions for given symbols using comprehensive analysis
    
    Args:
        symbols: List of stock symbols
        
    Returns:
        Dictionary with trading decisions for each symbol
    """
    logger.info(f"Making trading decisions for {len(symbols)} symbols")
    
    try:
        # Get comprehensive market data
        comprehensive_data = await fetch_comprehensive_market_data(symbols)
        
        # Initialize decision engine
        decision_engine = DecisionEngine()
        
        decisions = {}
        
        for symbol in symbols:
            symbol_data = comprehensive_data.get(symbol, {})
            
            if not symbol_data.get('live_data'):
                logger.warning(f"No live data available for {symbol}, skipping decision")
                continue
            
            try:
                # Make decision using all available data
                decision = decision_engine.make_decision(
                    symbol=symbol,
                    market_data=symbol_data['live_data'],
                    historical_data=symbol_data['historical_data'],
                    fundamental_data=symbol_data['fundamental_data'],
                    news_sentiment=symbol_data['news_sentiment'],
                    social_sentiment=symbol_data['social_sentiment']
                )
                
                # Convert decision to serializable format
                decisions[symbol] = {
                    'signal': decision.overall_signal.value,
                    'confidence': decision.confidence,
                    'risk_score': decision.risk_score,
                    'position_size': decision.position_size,
                    'reasoning': decision.reasoning,
                    'factors': [
                        {
                            'name': factor.name,
                            'signal': factor.signal.value,
                            'confidence': factor.confidence,
                            'weight': factor.weight,
                            'reasoning': factor.reasoning,
                            'data_source': factor.data_source
                        }
                        for factor in decision.factors
                    ],
                    'timestamp': decision.timestamp.isoformat()
                }
                
                logger.info(f"Decision for {symbol}: {decision.overall_signal.value} (confidence: {decision.confidence:.2f})")
                
            except Exception as e:
                logger.error(f"Error making decision for {symbol}: {e}")
                decisions[symbol] = {
                    'signal': 'HOLD',
                    'confidence': 0.0,
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return decisions
        
    except Exception as e:
        logger.error(f"Error making trading decisions: {e}")
        raise

# MOCK TREND DATA FUNCTION REMOVED - Live data only mode enforced