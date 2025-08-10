"""
Alpha Vantage market data provider implementation.
"""
import asyncio
import aiohttp
import os
from typing import Dict, List, Optional, Any
import time
import logging

from market_data_provider import MarketDataProvider, ProviderError


class AlphaVantageProvider(MarketDataProvider):
    """Alpha Vantage data provider using their REST API."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv('ALPHA_VANTAGE_API_KEY', config.get('api_key', ''))
        self.base_url = config.get('base_url', 'https://www.alphavantage.co/query')
        self.rate_limit_delay = 12.0  # Alpha Vantage free tier: 5 calls per minute
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if not self.api_key or self.api_key == 'ALPHA_VANTAGE_API_KEY':
            self.logger.warning("Alpha Vantage API key not configured. Provider will be disabled.")
            self.enabled = False
    
    async def fetch_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single stock quote from Alpha Vantage.
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            Dictionary with quote data or None if failed
        """
        if not self.enabled:
            return None
            
        try:
            self._rate_limit()
            normalized_symbol = self.normalize_symbol(symbol)
            
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': normalized_symbol,
                'apikey': self.api_key
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status != 200:
                        raise ProviderError(self.name, f"HTTP {response.status}: {await response.text()}")
                    
                    data = await response.json()
                    
                    # Check for API errors
                    if 'Error Message' in data:
                        raise ProviderError(self.name, data['Error Message'])
                    
                    if 'Note' in data:
                        raise ProviderError(self.name, "API call frequency limit reached")
                    
                    # Extract quote data
                    quote_data = data.get('Global Quote', {})
                    if not quote_data:
                        self.logger.warning(f"No quote data found for symbol {normalized_symbol}")
                        return None
                    
                    # Parse Alpha Vantage response format
                    raw_data = {
                        'price': float(quote_data.get('05. price', 0.0)),
                        'volume': int(quote_data.get('06. volume', 0)),
                        'change': float(quote_data.get('09. change', 0.0)),
                        'change_percent': float(quote_data.get('10. change percent', '0%').rstrip('%')),
                        'high': float(quote_data.get('03. high', 0.0)),
                        'low': float(quote_data.get('04. low', 0.0)),
                        'open': float(quote_data.get('02. open', 0.0)),
                        'previous_close': float(quote_data.get('08. previous close', 0.0))
                    }
                    
                    return self._normalize_quote_data(raw_data, normalized_symbol)
                    
        except Exception as e:
            self.logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            raise ProviderError(self.name, f"Failed to fetch quote for {symbol}", e)
    
    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch multiple stock quotes from Alpha Vantage.
        Note: Alpha Vantage doesn't support batch requests, so we make individual calls.
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        if not self.enabled:
            return {symbol: None for symbol in symbols}
        
        results = {}
        
        # Alpha Vantage doesn't support batch requests, so we need to make individual calls
        # This is rate-limited, so it may be slow for many symbols
        for symbol in symbols:
            try:
                quote_data = await self.fetch_quote(symbol)
                results[symbol] = quote_data
            except Exception as e:
                self.logger.error(f"Error fetching quote for {symbol}: {str(e)}")
                results[symbol] = None
        
        return results
    
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