"""
IEX Cloud market data provider implementation.
"""
import asyncio
import aiohttp
import os
from typing import Dict, List, Optional, Any
import time
import logging

from market_data_provider import MarketDataProvider, ProviderError


class IEXCloudProvider(MarketDataProvider):
    """IEX Cloud data provider using their REST API."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = os.getenv('IEX_CLOUD_API_KEY', config.get('api_key', ''))
        self.base_url = config.get('base_url', 'https://cloud.iexapis.com/stable/stock/')
        self.rate_limit_delay = 0.1  # IEX Cloud has generous rate limits
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        
        if not self.api_key or self.api_key == 'IEX_CLOUD_API_KEY':
            self.logger.warning("IEX Cloud API key not configured. Provider will be disabled.")
            self.enabled = False
    
    async def fetch_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single stock quote from IEX Cloud.
        
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
            
            # IEX Cloud quote endpoint
            url = f"{self.base_url}{normalized_symbol}/quote"
            params = {'token': self.api_key}
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status == 404:
                        self.logger.warning(f"Symbol {normalized_symbol} not found")
                        return None
                    
                    if response.status != 200:
                        raise ProviderError(self.name, f"HTTP {response.status}: {await response.text()}")
                    
                    data = await response.json()
                    
                    # Check if data is available
                    if not data or data.get('latestPrice') is None:
                        self.logger.warning(f"No quote data found for symbol {normalized_symbol}")
                        return None
                    
                    # Parse IEX Cloud response format
                    raw_data = {
                        'price': float(data.get('latestPrice', 0.0)),
                        'volume': int(data.get('latestVolume', 0)),
                        'change': float(data.get('change', 0.0)),
                        'change_percent': float(data.get('changePercent', 0.0)) * 100,  # IEX returns as decimal
                        'high': float(data.get('high', 0.0)),
                        'low': float(data.get('low', 0.0)),
                        'open': float(data.get('open', 0.0)),
                        'previous_close': float(data.get('previousClose', 0.0))
                    }
                    
                    return self._normalize_quote_data(raw_data, normalized_symbol)
                    
        except Exception as e:
            self.logger.error(f"Error fetching quote for {symbol}: {str(e)}")
            raise ProviderError(self.name, f"Failed to fetch quote for {symbol}", e)
    
    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch multiple stock quotes from IEX Cloud.
        IEX Cloud supports batch requests which is more efficient.
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        if not self.enabled:
            return {symbol: None for symbol in symbols}
        
        if not symbols:
            return {}
        
        try:
            self._rate_limit()
            normalized_symbols = [self.normalize_symbol(s) for s in symbols]
            
            # Use IEX Cloud batch endpoint for efficiency
            symbols_str = ','.join(normalized_symbols)
            url = f"{self.base_url}market/batch"
            params = {
                'symbols': symbols_str,
                'types': 'quote',
                'token': self.api_key
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        raise ProviderError(self.name, f"HTTP {response.status}: {await response.text()}")
                    
                    data = await response.json()
                    results = {}
                    
                    for i, symbol in enumerate(symbols):
                        normalized_symbol = normalized_symbols[i]
                        
                        try:
                            symbol_data = data.get(normalized_symbol, {})
                            quote_data = symbol_data.get('quote', {})
                            
                            if quote_data and quote_data.get('latestPrice') is not None:
                                raw_data = {
                                    'price': float(quote_data.get('latestPrice', 0.0)),
                                    'volume': int(quote_data.get('latestVolume', 0)),
                                    'change': float(quote_data.get('change', 0.0)),
                                    'change_percent': float(quote_data.get('changePercent', 0.0)) * 100,
                                    'high': float(quote_data.get('high', 0.0)),
                                    'low': float(quote_data.get('low', 0.0)),
                                    'open': float(quote_data.get('open', 0.0)),
                                    'previous_close': float(quote_data.get('previousClose', 0.0))
                                }
                                results[symbol] = self._normalize_quote_data(raw_data, normalized_symbol)
                            else:
                                self.logger.warning(f"No quote data found for symbol {normalized_symbol}")
                                results[symbol] = None
                                
                        except Exception as e:
                            self.logger.error(f"Error processing quote for {symbol}: {str(e)}")
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