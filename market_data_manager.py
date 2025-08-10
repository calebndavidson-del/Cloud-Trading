"""
Market Data Manager with multi-provider support and fallback logic.
"""
import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, Any, Type
from concurrent.futures import ThreadPoolExecutor, as_completed

from market_data_provider import MarketDataProvider, ProviderError
from yahoo_finance_provider import YahooFinanceProvider
from alpha_vantage_provider import AlphaVantageProvider
from iex_cloud_provider import IEXCloudProvider


class MarketDataManager:
    """
    Manages multiple market data providers with automatic fallback.
    Ensures fresh data by trying all providers and falling back as needed.
    """
    
    def __init__(self, config_path: str = "market_data_config.json"):
        """
        Initialize the market data manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.providers: List[MarketDataProvider] = []
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.cache_duration = self.config.get('fallback_settings', {}).get('cache_duration', 60)
        self.max_retries = self.config.get('fallback_settings', {}).get('max_retries', 3)
        self.retry_delay = self.config.get('fallback_settings', {}).get('retry_delay', 1.0)
        
        # Set up logging
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
        # Initialize providers
        self._initialize_providers()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Configuration file {self.config_path} not found")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing configuration file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if config file is missing."""
        return {
            "providers": {
                "yahoo_finance": {"enabled": True, "priority": 1, "timeout": 10},
                "alpha_vantage": {"enabled": False, "priority": 2, "timeout": 15},
                "iex_cloud": {"enabled": False, "priority": 3, "timeout": 12}
            },
            "fallback_settings": {
                "max_retries": 3,
                "retry_delay": 1.0,
                "cache_duration": 60
            }
        }
    
    def _initialize_providers(self):
        """Initialize all configured providers and sort by priority."""
        provider_classes: Dict[str, Type[MarketDataProvider]] = {
            'yahoo_finance': YahooFinanceProvider,
            'alpha_vantage': AlphaVantageProvider,
            'iex_cloud': IEXCloudProvider
        }
        
        provider_configs = []
        
        for provider_name, provider_config in self.config.get('providers', {}).items():
            if provider_config.get('enabled', False) and provider_name in provider_classes:
                provider_class = provider_classes[provider_name]
                provider = provider_class(provider_config)
                
                if provider.is_available():
                    provider_configs.append({
                        'provider': provider,
                        'priority': provider_config.get('priority', 999)
                    })
                    self.logger.info(f"Initialized provider: {provider_name}")
                else:
                    self.logger.warning(f"Provider {provider_name} is not available")
        
        # Sort providers by priority (lower number = higher priority)
        provider_configs.sort(key=lambda x: x['priority'])
        self.providers = [pc['provider'] for pc in provider_configs]
        
        if not self.providers:
            self.logger.warning("No providers available! Only Yahoo Finance will be used as fallback.")
            # Add Yahoo Finance as a default fallback
            yahoo_config = self.config.get('providers', {}).get('yahoo_finance', {
                'enabled': True, 'priority': 1, 'timeout': 10
            })
            self.providers = [YahooFinanceProvider(yahoo_config)]
    
    def _is_cached_data_fresh(self, symbol: str) -> bool:
        """Check if cached data for a symbol is still fresh."""
        if symbol not in self.cache:
            return False
        
        cache_time = self.cache[symbol].get('timestamp', 0)
        return (time.time() - cache_time) < self.cache_duration
    
    def _get_cached_data(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Get cached data for a symbol if it's fresh."""
        if self._is_cached_data_fresh(symbol):
            return self.cache[symbol]
        return None
    
    def _cache_data(self, symbol: str, data: Dict[str, Any]):
        """Cache data for a symbol."""
        if data:
            self.cache[symbol] = data
    
    async def fetch_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single stock quote with automatic provider fallback.
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            Dictionary with quote data or None if all providers fail
        """
        # Check cache first
        cached_data = self._get_cached_data(symbol)
        if cached_data:
            self.logger.debug(f"Returning cached data for {symbol}")
            return cached_data
        
        # Try each provider in priority order
        for provider in self.providers:
            for attempt in range(self.max_retries):
                try:
                    self.logger.debug(f"Attempting to fetch {symbol} from {provider.name} (attempt {attempt + 1})")
                    quote_data = await provider.fetch_quote(symbol)
                    
                    if quote_data:
                        self.logger.info(f"Successfully fetched {symbol} from {provider.name}")
                        self._cache_data(symbol, quote_data)
                        return quote_data
                    else:
                        self.logger.warning(f"No data returned for {symbol} from {provider.name}")
                        
                except ProviderError as e:
                    self.logger.warning(f"Provider error for {symbol} from {provider.name}: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                except Exception as e:
                    self.logger.error(f"Unexpected error for {symbol} from {provider.name}: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
        
        self.logger.error(f"All providers failed for symbol {symbol}")
        return None
    
    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch multiple stock quotes with automatic provider fallback.
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        results = {}
        remaining_symbols = []
        
        # Check cache first
        for symbol in symbols:
            cached_data = self._get_cached_data(symbol)
            if cached_data:
                results[symbol] = cached_data
            else:
                remaining_symbols.append(symbol)
        
        if not remaining_symbols:
            return results
        
        # Try each provider in priority order for remaining symbols
        for provider in self.providers:
            if not remaining_symbols:
                break
                
            for attempt in range(self.max_retries):
                try:
                    self.logger.debug(f"Attempting to fetch {len(remaining_symbols)} symbols from {provider.name} (attempt {attempt + 1})")
                    provider_results = await provider.fetch_quotes(remaining_symbols)
                    
                    # Process results and cache successful ones
                    symbols_to_remove = []
                    for symbol in remaining_symbols:
                        if symbol in provider_results and provider_results[symbol] is not None:
                            quote_data = provider_results[symbol]
                            results[symbol] = quote_data
                            self._cache_data(symbol, quote_data)
                            symbols_to_remove.append(symbol)
                            self.logger.debug(f"Successfully fetched {symbol} from {provider.name}")
                    
                    # Remove successfully fetched symbols
                    for symbol in symbols_to_remove:
                        remaining_symbols.remove(symbol)
                    
                    # If we got some results, don't retry this provider
                    if symbols_to_remove:
                        break
                        
                except ProviderError as e:
                    self.logger.warning(f"Provider error from {provider.name}: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
                except Exception as e:
                    self.logger.error(f"Unexpected error from {provider.name}: {e}")
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self.retry_delay)
        
        # Add None for any symbols that couldn't be fetched
        for symbol in remaining_symbols:
            results[symbol] = None
            self.logger.error(f"All providers failed for symbol {symbol}")
        
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
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status information for all providers.
        
        Returns:
            Dictionary with provider status information
        """
        status = {}
        for provider in self.providers:
            status[provider.name] = {
                'enabled': provider.enabled,
                'available': provider.is_available(),
                'last_request_time': provider.last_request_time,
                'timeout': provider.timeout
            }
        return status
    
    def clear_cache(self):
        """Clear the data cache."""
        self.cache.clear()
        self.logger.info("Data cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about the current cache state.
        
        Returns:
            Dictionary with cache information
        """
        current_time = time.time()
        fresh_entries = 0
        stale_entries = 0
        
        for symbol, data in self.cache.items():
            cache_time = data.get('timestamp', 0)
            if (current_time - cache_time) < self.cache_duration:
                fresh_entries += 1
            else:
                stale_entries += 1
        
        return {
            'total_entries': len(self.cache),
            'fresh_entries': fresh_entries,
            'stale_entries': stale_entries,
            'cache_duration': self.cache_duration
        }