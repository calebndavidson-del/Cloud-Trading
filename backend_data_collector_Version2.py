"""
Data collection functions for Yahoo Finance and other APIs.
Enhanced with modular market data fetcher supporting multiple providers.
"""
from typing import Dict, List, Optional, Any
from market_data_manager import MarketDataManager

# Initialize the market data manager
_data_manager = None

def get_data_manager() -> MarketDataManager:
    """Get or create the global market data manager instance."""
    global _data_manager
    if _data_manager is None:
        _data_manager = MarketDataManager()
    return _data_manager

def fetch_market_data(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fetch market data for specified symbols using the modular data fetcher.
    
    Args:
        symbols: List of stock symbols to fetch. If None, uses default symbols.
        
    Returns:
        Dictionary mapping symbols to quote data
    """
    if symbols is None:
        symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
    
    data_manager = get_data_manager()
    
    try:
        # Use the sync version for backward compatibility
        results = data_manager.fetch_quotes_sync(symbols)
        
        # Filter out None results and format for backward compatibility
        market_data = {}
        for symbol, quote_data in results.items():
            if quote_data is not None:
                market_data[symbol] = {
                    "price": quote_data.get("price", 0.0),
                    "volume": quote_data.get("volume", 0),
                    "change": quote_data.get("change", 0.0),
                    "change_percent": quote_data.get("change_percent", 0.0),
                    "high": quote_data.get("high", 0.0),
                    "low": quote_data.get("low", 0.0),
                    "open": quote_data.get("open", 0.0),
                    "previous_close": quote_data.get("previous_close", 0.0),
                    "provider": quote_data.get("provider", "unknown")
                }
            else:
                # Fallback data if all providers fail
                market_data[symbol] = {
                    "price": 0.0,
                    "volume": 0,
                    "change": 0.0,
                    "change_percent": 0.0,
                    "high": 0.0,
                    "low": 0.0,
                    "open": 0.0,
                    "previous_close": 0.0,
                    "provider": "none"
                }
        
        return market_data
        
    except Exception as e:
        print(f"Error fetching market data: {e}")
        # Return fallback data
        return {symbol: {"price": 0.0} for symbol in symbols}

def fetch_single_quote(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch a single stock quote.
    
    Args:
        symbol: Stock symbol to fetch
        
    Returns:
        Dictionary with quote data or None if failed
    """
    data_manager = get_data_manager()
    return data_manager.fetch_quote_sync(symbol)

def get_provider_status() -> Dict[str, Any]:
    """
    Get status of all market data providers.
    
    Returns:
        Dictionary with provider status information
    """
    data_manager = get_data_manager()
    return data_manager.get_provider_status()

def clear_cache():
    """Clear the market data cache."""
    data_manager = get_data_manager()
    data_manager.clear_cache()

def get_cache_info() -> Dict[str, Any]:
    """
    Get information about the current cache state.
    
    Returns:
        Dictionary with cache information
    """
    data_manager = get_data_manager()
    return data_manager.get_cache_info()