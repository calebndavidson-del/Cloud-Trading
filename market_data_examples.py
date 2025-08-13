"""
Example integration code showing how to use the modular market data fetcher
in trading bot strategies.
"""
import time
import logging
from typing import Dict, List, Any
from market_data_manager import MarketDataManager
from backend.data_collector import fetch_market_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TradingStrategy:
    """Example trading strategy using the market data fetcher."""
    
    def __init__(self, symbols: List[str] = None):
        """
        Initialize the strategy.
        
        Args:
            symbols: List of symbols to track
        """
        self.symbols = symbols or ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
        self.data_manager = MarketDataManager()
        self.positions = {}
        self.cash = 100000.0  # Starting with $100k
        
    def get_fresh_data(self) -> Dict[str, Any]:
        """
        Get the freshest available market data from all providers.
        This method demonstrates the automatic fallback system.
        """
        logger.info("Fetching fresh market data...")
        
        # Method 1: Use the backward-compatible function
        market_data = fetch_market_data(self.symbols)
        
        # Method 2: Use the data manager directly for more control
        # market_data = self.data_manager.fetch_quotes_sync(self.symbols)
        
        return market_data
    
    def analyze_market(self, market_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Analyze market data and generate trading signals.
        
        Args:
            market_data: Market data from the fetcher
            
        Returns:
            Dictionary mapping symbols to signals ('BUY', 'SELL', 'HOLD')
        """
        signals = {}
        
        for symbol, data in market_data.items():
            if data is None or data.get('price', 0) == 0:
                signals[symbol] = 'HOLD'  # No data available
                continue
                
            price = data.get('price', 0)
            change_percent = data.get('change_percent', 0)
            
            # Simple momentum strategy
            if change_percent > 2.0:
                signals[symbol] = 'BUY'
            elif change_percent < -2.0:
                signals[symbol] = 'SELL'
            else:
                signals[symbol] = 'HOLD'
        
        return signals
    
    def execute_trades(self, signals: Dict[str, str], market_data: Dict[str, Any]):
        """
        Execute trades based on signals (paper trading example).
        
        Args:
            signals: Trading signals for each symbol
            market_data: Current market data
        """
        for symbol, signal in signals.items():
            if signal == 'HOLD':
                continue
                
            data = market_data.get(symbol)
            if not data or data.get('price', 0) == 0:
                logger.warning(f"Cannot execute trade for {symbol}: no price data")
                continue
                
            price = data['price']
            
            if signal == 'BUY' and symbol not in self.positions:
                # Buy $10,000 worth of stock
                shares = 10000 / price
                if self.cash >= 10000:
                    self.positions[symbol] = shares
                    self.cash -= 10000
                    logger.info(f"BOUGHT {shares:.2f} shares of {symbol} at ${price:.2f}")
                
            elif signal == 'SELL' and symbol in self.positions:
                # Sell all shares
                shares = self.positions.pop(symbol)
                self.cash += shares * price
                logger.info(f"SOLD {shares:.2f} shares of {symbol} at ${price:.2f}")
    
    def run_strategy(self):
        """
        Main strategy execution loop.
        Demonstrates continuous monitoring with fresh data.
        """
        logger.info("Starting trading strategy...")
        
        for iteration in range(3):  # Run for 3 iterations as example
            logger.info(f"\n--- Strategy Iteration {iteration + 1} ---")
            
            # Get fresh market data with automatic fallback
            market_data = self.get_fresh_data()
            
            # Check data quality
            successful_fetches = sum(1 for data in market_data.values() 
                                   if data and data.get('provider') != 'none')
            total_symbols = len(self.symbols)
            
            logger.info(f"Data quality: {successful_fetches}/{total_symbols} symbols fetched successfully")
            
            # Analyze and execute
            signals = self.analyze_market(market_data)
            self.execute_trades(signals, market_data)
            
            # Display portfolio status
            portfolio_value = self.cash + sum(
                self.positions.get(symbol, 0) * market_data.get(symbol, {}).get('price', 0)
                for symbol in self.symbols
            )
            
            logger.info(f"Portfolio value: ${portfolio_value:,.2f}")
            logger.info(f"Cash: ${self.cash:,.2f}")
            logger.info(f"Positions: {self.positions}")
            
            # Note: Provider status and cache info removed as part of Version2 cleanup
            logger.info("Data collection completed successfully")
            
            # Wait before next iteration (in real scenario, this would be market hours)
            if iteration < 2:
                time.sleep(2)


def demo_multi_provider_fallback():
    """
    Demonstrate the multi-provider fallback system.
    """
    logger.info("=== Multi-Provider Fallback Demo ===")
    
    data_manager = MarketDataManager()
    
    # Test single quote fetch
    logger.info("Testing single quote fetch...")
    quote = data_manager.fetch_quote_sync("AAPL")
    if quote:
        logger.info(f"AAPL quote: ${quote['price']:.2f} from {quote['provider']}")
    else:
        logger.info("Failed to fetch AAPL quote from any provider")
    
    # Test multiple quotes fetch
    logger.info("Testing multiple quotes fetch...")
    symbols = ["AAPL", "GOOGL", "MSFT"]
    quotes = data_manager.fetch_quotes_sync(symbols)
    
    for symbol, quote in quotes.items():
        if quote:
            logger.info(f"{symbol}: ${quote['price']:.2f} from {quote['provider']}")
        else:
            logger.info(f"{symbol}: No data available")
    
    # Show final provider status
    status = data_manager.get_provider_status()
    logger.info(f"Final provider status: {status}")


def demo_configuration_management():
    """
    Demonstrate configuration management and provider setup.
    """
    logger.info("=== Configuration Management Demo ===")
    
    # Load and display current configuration
    data_manager = MarketDataManager()
    
    logger.info("Current provider configuration:")
    for provider in data_manager.providers:
        logger.info(f"- {provider.name}: enabled={provider.enabled}, "
                   f"timeout={provider.timeout}s")
    
    # Demonstrate cache management
    logger.info("Cache management:")
    cache_info = data_manager.get_cache_info()
    logger.info(f"Current cache state: {cache_info}")
    
    # Clear cache
    data_manager.clear_cache()
    logger.info("Cache cleared")
    
    cache_info = data_manager.get_cache_info()
    logger.info(f"Cache after clearing: {cache_info}")


if __name__ == "__main__":
    print("=== Market Data Fetcher Integration Examples ===\n")
    
    # Demo 1: Multi-provider fallback
    demo_multi_provider_fallback()
    print("\n" + "="*60 + "\n")
    
    # Demo 2: Configuration management
    demo_configuration_management()
    print("\n" + "="*60 + "\n")
    
    # Demo 3: Trading strategy integration
    strategy = TradingStrategy()
    strategy.run_strategy()