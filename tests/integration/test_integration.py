"""
Integration tests for the Cloud Trading Bot.
"""
import pytest
import asyncio
from unittest.mock import patch, Mock
from market_data_manager import MarketDataManager
from backend.data_collector import fetch_market_data
from backend.optimizer import optimize_strategy
from backend.paper_trader import paper_trade


@pytest.mark.integration
class TestMarketDataIntegration:
    """Integration tests for market data collection."""
    
    @pytest.mark.asyncio
    async def test_market_data_manager_integration(self):
        """Test market data manager with real provider integration."""
        # Use mock data to avoid network calls
        with patch('os.path.exists', return_value=False):
            manager = MarketDataManager()
            
            # Test that manager initializes providers
            assert len(manager.providers) > 0
            
            # Test quote fetching (will use fallback due to network issues)
            try:
                quote = await manager.fetch_quote('AAPL')
                # Either gets real data or handles error gracefully
                assert quote is None or isinstance(quote, dict)
            except Exception as e:
                # Network errors are expected in test environment
                assert 'error' in str(e).lower() or 'failed' in str(e).lower()
    
    def test_data_collector_integration(self):
        """Test data collector integration with different modes."""
        # Test with mock data
        data = fetch_market_data(['AAPL', 'GOOGL'], use_mock=True)
        
        assert isinstance(data, dict)
        assert len(data) == 2
        assert 'AAPL' in data
        assert 'GOOGL' in data
        
        for symbol, quote in data.items():
            assert 'price' in quote
            assert 'volume' in quote
            assert quote['price'] > 0
            assert quote['volume'] > 0


@pytest.mark.integration
class TestTradingWorkflowIntegration:
    """Integration tests for the complete trading workflow."""
    
    def test_optimization_integration(self):
        """Test optimization with real market data structure."""
        # Use mock data for consistent testing
        market_data = {
            'AAPL': {'price': 150.0, 'volume': 1000000},
            'GOOGL': {'price': 2800.0, 'volume': 500000}
        }
        
        result = optimize_strategy(market_data, n_trials=5)
        
        assert isinstance(result, dict)
        assert 'best_value' in result
        assert 'best_params' in result
        assert 'backtest_results' in result
        assert isinstance(result['best_params'], dict)
    
    def test_paper_trading_integration(self):
        """Test paper trading with market data integration."""
        config = {
            'initial_capital': 10000,
            'symbols': ['AAPL', 'GOOGL']
        }
        
        result = paper_trade(config)
        
        assert isinstance(result, dict)
        assert 'portfolio_value' in result
        assert 'initial_capital' in result
        assert 'total_trades' in result
        assert result['initial_capital'] == 10000
    
    def test_end_to_end_workflow_integration(self):
        """Test the complete end-to-end workflow."""
        symbols = ['AAPL']
        
        # Step 1: Fetch market data
        market_data = fetch_market_data(symbols, use_mock=True)
        assert isinstance(market_data, dict)
        assert 'AAPL' in market_data
        
        # Step 2: Optimize strategy
        optimization = optimize_strategy(market_data, n_trials=3)
        assert 'best_params' in optimization
        
        # Step 3: Run paper trading with optimized parameters
        trading_config = {
            'initial_capital': 10000,
            'symbols': symbols,
            'strategy_params': optimization['best_params']
        }
        
        trading_result = paper_trade(trading_config)
        assert 'portfolio_value' in trading_result
        assert trading_result['portfolio_value'] >= 0


@pytest.mark.integration
class TestConfigurationIntegration:
    """Integration tests for configuration management."""
    
    def test_config_loading_integration(self):
        """Test configuration loading and provider initialization."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open') as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = '''
                {
                    "providers": {
                        "yahoo_finance": {"enabled": true, "priority": 1, "timeout": 10},
                        "alpha_vantage": {"enabled": false, "priority": 2},
                        "iex_cloud": {"enabled": false, "priority": 3}
                    },
                    "fallback_settings": {
                        "max_retries": 3,
                        "retry_delay": 1.0,
                        "cache_duration": 60
                    }
                }
                '''
                
                manager = MarketDataManager('test_config.json')
                
                assert 'providers' in manager.config
                assert 'fallback_settings' in manager.config
                assert manager.max_retries == 3
                assert manager.retry_delay == 1.0


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Integration tests for performance."""
    
    def test_multiple_symbol_performance(self):
        """Test performance with multiple symbols."""
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        
        import time
        start_time = time.time()
        
        data = fetch_market_data(symbols, use_mock=True)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        assert execution_time < 5.0  # 5 seconds max
        assert len(data) == len(symbols)
    
    def test_optimization_performance(self):
        """Test optimization performance."""
        market_data = {
            'AAPL': {'price': 150.0, 'volume': 1000000},
            'GOOGL': {'price': 2800.0, 'volume': 500000}
        }
        
        import time
        start_time = time.time()
        
        result = optimize_strategy(market_data, n_trials=10)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete within reasonable time
        assert execution_time < 30.0  # 30 seconds max
        assert 'best_value' in result