"""
Base abstract class for market data providers.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import time


class MarketDataProvider(ABC):
    """Abstract base class for all market data providers."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the provider with configuration.
        
        Args:
            config: Provider configuration dictionary
        """
        self.config = config
        self.name = self.__class__.__name__
        self.enabled = config.get('enabled', True)
        self.timeout = config.get('timeout', 10)
        self.last_request_time = 0
        self.rate_limit_delay = 0.1  # Default rate limiting
    
    @abstractmethod
    async def fetch_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single stock quote.
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            Dictionary with quote data or None if failed
        """
        pass
    
    @abstractmethod
    async def fetch_quotes(self, symbols: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Fetch multiple stock quotes.
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary mapping symbols to quote data
        """
        pass
    
    def is_available(self) -> bool:
        """Check if the provider is available and enabled."""
        return self.enabled
    
    def normalize_symbol(self, symbol: str) -> str:
        """Normalize symbol format for this provider."""
        return symbol.upper().strip()
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _normalize_quote_data(self, raw_data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
        """
        Normalize quote data to a standard format.
        
        Args:
            raw_data: Raw data from the provider
            symbol: Symbol for the quote
            
        Returns:
            Normalized quote data
        """
        return {
            'symbol': symbol,
            'price': raw_data.get('price', 0.0),
            'volume': raw_data.get('volume', 0),
            'change': raw_data.get('change', 0.0),
            'change_percent': raw_data.get('change_percent', 0.0),
            'high': raw_data.get('high', 0.0),
            'low': raw_data.get('low', 0.0),
            'open': raw_data.get('open', 0.0),
            'previous_close': raw_data.get('previous_close', 0.0),
            'timestamp': time.time(),
            'provider': self.name
        }


class ProviderError(Exception):
    """Custom exception for provider-specific errors."""
    
    def __init__(self, provider_name: str, message: str, original_error: Optional[Exception] = None):
        self.provider_name = provider_name
        self.original_error = original_error
        super().__init__(f"{provider_name}: {message}")