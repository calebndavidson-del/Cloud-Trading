"""
Yahoo Finance market data provider implementation.
"""
import asyncio
import aiohttp
import yfinance as yf
from typing import Dict, List, Optional, Any
import time
import logging

from market_data_provider import MarketDataProvider, ProviderError


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance data provider using yfinance library."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rate_limit_delay = 0.5  # Yahoo Finance rate limiting
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    async def fetch_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single stock quote from Yahoo Finance.
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            Dictionary with quote data or None if failed
        """
        try:
            self._rate_limit()
            normalized_symbol = self.normalize_symbol(symbol)
            
            # Use yfinance to get current data
            ticker = yf.Ticker(normalized_symbol)
            info = ticker.info
            
            if not info or 'regularMarketPrice' not in info:
                self.logger.warning(f"No data available for symbol {normalized_symbol}")
                return None
            
            # Extract relevant data
            raw_data = {
                'price': info.get('regularMarketPrice', 0.0),
                'volume': info.get('regularMarketVolume', 0),
                'change': info.get('regularMarketChange', 0.0),
                'change_percent': info.get('regularMarketChangePercent', 0.0),
                'high': info.get('regularMarketDayHigh', 0.0),
                'low': info.get('regularMarketDayLow', 0.0),
                'open': info.get('regularMarketOpen', 0.0),
                'previous_close': info.get('regularMarketPreviousClose', 0.0)
            }
            
            return self._normalize_quote_data(raw_data, normalized_symbol)
            
        except Exception as e:
            self.logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            raise ProviderError(self.name, f"Failed to fetch quote for {symbol}", e)
    
    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch multiple stock quotes from Yahoo Finance.
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        results = {}
        
        try:
            # Normalize symbols
            normalized_symbols = [self.normalize_symbol(s) for s in symbols]
            
            # Use yfinance to download data for multiple symbols
            self._rate_limit()
            tickers = yf.Tickers(' '.join(normalized_symbols))
            
            for i, symbol in enumerate(symbols):
                normalized_symbol = normalized_symbols[i]
                try:
                    ticker = tickers.tickers[normalized_symbol]
                    info = ticker.info
                    
                    if info and 'regularMarketPrice' in info:
                        raw_data = {
                            'price': info.get('regularMarketPrice', 0.0),
                            'volume': info.get('regularMarketVolume', 0),
                            'change': info.get('regularMarketChange', 0.0),
                            'change_percent': info.get('regularMarketChangePercent', 0.0),
                            'high': info.get('regularMarketDayHigh', 0.0),
                            'low': info.get('regularMarketDayLow', 0.0),
                            'open': info.get('regularMarketOpen', 0.0),
                            'previous_close': info.get('regularMarketPreviousClose', 0.0)
                        }
                        results[symbol] = self._normalize_quote_data(raw_data, normalized_symbol)
                    else:
                        self.logger.warning(f"No data available for symbol {normalized_symbol}")
                        results[symbol] = None
                        
                except Exception as e:
                    self.logger.error(f"Error fetching quote for {symbol}: {str(e)}")
                    results[symbol] = None
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error fetching quotes for symbols {symbols}: {str(e)}")
            # Return None for all symbols on general failure
            return {symbol: None for symbol in symbols}
    
    def fetch_quote_sync(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Synchronous version of fetch_quote for backward compatibility.
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            Dictionary with quote data or None if failed
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.fetch_quote(symbol))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self.fetch_quote(symbol))
    
    def fetch_quotes_sync(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Synchronous version of fetch_quotes for backward compatibility.
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.fetch_quotes(symbols))
        except RuntimeError:
            # If no event loop is running, create a new one
            return asyncio.run(self.fetch_quotes(symbols))