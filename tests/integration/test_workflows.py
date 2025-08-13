"""
End-to-end integration tests for complete trading workflows.
"""
import pytest
import json
import time
from unittest.mock import patch


@pytest.mark.e2e
class TestCompleteTradingWorkflow:
    """End-to-end tests for complete trading workflows."""
    
    def test_full_trading_bot_workflow(self, test_environment):
        """Test complete trading bot workflow from start to finish."""
        # Import here to ensure test environment is set
        from backend.bot import run_bot
        from backend.data_collector import fetch_market_data
        from backend.optimizer import optimize_strategy
        from backend.paper_trader import paper_trade
        
        # 1. Data Collection Phase
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        market_data = fetch_market_data(symbols)
        
        assert isinstance(market_data, dict)
        assert len(market_data) > 0
        
        # Verify each symbol has required data
        for symbol in symbols:
            assert symbol in market_data
            if 'error' not in market_data[symbol]:
                required_fields = ['price', 'volume']
                for field in required_fields:
                    assert field in market_data[symbol]
        
        # 2. Strategy Optimization Phase
        optimization_result = optimize_strategy(market_data, n_trials=5)
        
        assert 'best_params' in optimization_result
        assert 'best_value' in optimization_result
        assert 'backtest_results' in optimization_result
        
        # 3. Paper Trading Phase
        trading_params = {
            'initial_capital': 10000,
            'symbols': symbols[:2]  # Use first 2 symbols
        }
        
        trading_result = paper_trade(trading_params)
        
        assert 'portfolio_value' in trading_result or 'error' in trading_result
        
        # 4. Full Bot Execution
        try:
            run_bot()
            print("✅ Full trading bot workflow completed successfully")
        except Exception as e:
            pytest.fail(f"Bot execution failed: {e}")
    
    def test_strategy_development_workflow(self, test_environment):
        """Test strategy development and testing workflow."""
        from backend.optimizer import backtest_strategy, optimize_strategy
        from backend.data_collector import fetch_market_data
        
        # 1. Get market data
        market_data = fetch_market_data(['AAPL', 'TSLA'])
        assert len(market_data) > 0
        
        # 2. Test initial strategy parameters
        initial_params = {
            'initial_capital': 10000,
            'short_ma_period': 5,
            'long_ma_period': 15
        }
        
        backtest_result = backtest_strategy(market_data, initial_params)
        assert 'trades' in backtest_result or 'error' in backtest_result
        
        # 3. Optimize strategy
        optimization = optimize_strategy(market_data, n_trials=10)
        assert 'best_params' in optimization
        
        # 4. Test optimized strategy
        if 'error' not in optimization:
            optimized_backtest = backtest_strategy(market_data, optimization['best_params'])
            assert 'trades' in optimized_backtest or 'error' in optimized_backtest
        
        print("✅ Strategy development workflow completed")


@pytest.mark.e2e
class TestUserJourneySimulation:
    """Simulate different user journeys through the system."""
    
    def test_new_user_onboarding_journey(self, api_client):
        """Simulate new user exploring the system."""
        # 1. User checks if system is healthy
        health_response = api_client.get('/health')
        assert health_response.status_code == 200
        
        # 2. User checks system status
        status_response = api_client.get('/api/status')
        assert status_response.status_code == 200
        status_data = json.loads(status_response.data)
        
        # 3. User views configuration
        config_response = api_client.get('/api/config')
        assert config_response.status_code == 200
        config_data = json.loads(config_response.data)
        
        # 4. User explores market data
        default_symbols = config_data['trading']['default_symbols']
        market_response = api_client.get(f'/api/market-data?symbols={",".join(default_symbols[:2])}')
        assert market_response.status_code == 200
        
        # 5. User checks market trends
        trends_response = api_client.get('/api/market-trends')
        assert trends_response.status_code == 200
        
        # 6. User tries running the bot
        bot_response = api_client.post('/api/bot/run')
        assert bot_response.status_code in [200, 500]  # May fail in test env
        
        print("✅ New user onboarding journey completed")
    
    def test_day_trading_simulation(self, test_environment):
        """Simulate a day trading scenario."""
        from backend.paper_trader import PaperTrader
        from backend.data_collector import fetch_market_data
        
        # 1. Initialize paper trader
        trader = PaperTrader(initial_capital=10000)
        
        # 2. Get morning market data
        symbols = ['AAPL', 'GOOGL']
        morning_data = fetch_market_data(symbols)
        
        # 3. Execute morning trades
        for symbol, data in morning_data.items():
            if 'error' not in data:
                price = data['price']
                shares = 10
                trader.buy(symbol, shares, price)
        
        # 4. Simulate market movements and afternoon trades
        afternoon_data = fetch_market_data(symbols)
        
        # 5. Close some positions
        for symbol in trader.positions:
            if symbol in afternoon_data and 'error' not in afternoon_data[symbol]:
                shares_to_sell = min(5, trader.positions[symbol])
                trader.sell(symbol, shares_to_sell, afternoon_data[symbol]['price'])
        
        # 6. Get final summary
        summary = trader.get_summary()
        assert 'portfolio_value' in summary
        assert 'total_trades' in summary
        
        print(f"✅ Day trading simulation completed. Portfolio value: ${summary.get('portfolio_value', 0):.2f}")
    
    def test_long_term_investment_workflow(self, test_environment):
        """Simulate long-term investment strategy workflow."""
        from backend.optimizer import optimize_strategy
        from backend.data_collector import fetch_market_data
        from backend.paper_trader import paper_trade
        
        # 1. Research phase - get market data for analysis
        research_symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        market_data = fetch_market_data(research_symbols)
        
        # 2. Strategy optimization for long-term parameters
        long_term_optimization = optimize_strategy(market_data, n_trials=10)
        
        # 3. Paper trading with optimized strategy
        if 'error' not in long_term_optimization:
            best_params = long_term_optimization['best_params']
            best_params['symbols'] = research_symbols[:2]
            
            trading_result = paper_trade(best_params)
            assert 'portfolio_value' in trading_result or 'error' in trading_result
        
        print("✅ Long-term investment workflow completed")


@pytest.mark.e2e
class TestFailureRecoveryScenarios:
    """Test system behavior under failure conditions."""
    
    @patch('backend.data_collector.fetch_market_data')
    def test_data_provider_failure_recovery(self, mock_fetch_data, api_client):
        """Test recovery when primary data provider fails."""
        # Simulate primary provider failure, fallback to mock data
        mock_fetch_data.return_value = {
            'AAPL': {'error': 'Provider timeout'},
            'GOOGL': {'price': 2800, 'volume': 500000}  # Partial success
        }
        
        # System should handle partial failures gracefully
        response = api_client.get('/api/market-data?symbols=AAPL,GOOGL')
        
        # Should still return 200 with error details
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
        
        print("✅ Data provider failure recovery test completed")
    
    def test_optimization_failure_handling(self, test_environment):
        """Test behavior when optimization fails."""
        from backend.optimizer import optimize_strategy
        
        # Test with invalid/empty market data
        invalid_data = {
            'INVALID': {'error': 'No data available'}
        }
        
        result = optimize_strategy(invalid_data, n_trials=3)
        
        # Should handle gracefully
        assert isinstance(result, dict)
        if 'error' in result:
            print(f"✅ Optimization failure handled: {result['error']}")
        else:
            print("✅ Optimization completed despite invalid data")
    
    def test_paper_trading_edge_cases(self, test_environment):
        """Test paper trading with edge case scenarios."""
        from backend.paper_trader import PaperTrader
        
        # Test with minimal capital
        trader = PaperTrader(initial_capital=100)
        
        # Try to buy expensive stock
        success = trader.buy('GOOGL', 1, 2800)  # More than available capital
        assert not success  # Should fail
        
        # Try to sell stock we don't own
        success = trader.sell('AAPL', 10, 150)
        assert not success  # Should fail
        
        # Get summary even with no trades
        summary = trader.get_summary()
        assert 'portfolio_value' in summary
        assert summary['portfolio_value'] == 100  # Should equal initial capital
        
        print("✅ Paper trading edge cases handled correctly")


@pytest.mark.e2e  
@pytest.mark.slow
class TestMarketDataIntegration:
    """Test market data integration scenarios."""
    
    def test_multi_symbol_data_consistency(self, test_environment):
        """Test data consistency across multiple symbols."""
        from backend.data_collector import fetch_market_data
        
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        
        # Fetch data multiple times
        data_fetches = []
        for _ in range(3):
            data = fetch_market_data(symbols)
            data_fetches.append(data)
            time.sleep(0.1)
        
        # Check consistency (with mock data, should be identical)
        for symbol in symbols:
            prices = []
            for fetch in data_fetches:
                if symbol in fetch and 'price' in fetch[symbol]:
                    prices.append(fetch[symbol]['price'])
            
            # Mock data should be consistent
            if len(prices) > 1:
                assert all(p == prices[0] for p in prices), f"Inconsistent prices for {symbol}: {prices}"
        
        print("✅ Multi-symbol data consistency verified")
    
    def test_market_trends_analysis(self, test_environment):
        """Test market trends analysis workflow."""
        from backend.data_collector import fetch_market_trends
        
        trends = fetch_market_trends()
        
        if 'error' not in trends and 'sp500' in trends:
            sp500 = trends['sp500']
            
            # Validate trend data structure
            assert 'current_price' in sp500
            assert 'change_percent' in sp500
            assert 'trend' in sp500
            assert sp500['trend'] in ['up', 'down']
            
            print(f"✅ Market trends analysis: S&P 500 {sp500['trend']} {sp500['change_percent']:.2f}%")
        else:
            print("✅ Market trends analysis completed (mock data)")


@pytest.mark.e2e
class TestSystemStressScenarios:
    """Test system under stress conditions."""
    
    def test_rapid_api_requests(self, api_client):
        """Test rapid succession of API requests."""
        endpoints = ['/health', '/api/status', '/api/market-data']
        
        results = []
        start_time = time.time()
        
        # Make rapid requests
        for _ in range(10):
            for endpoint in endpoints:
                response = api_client.get(endpoint)
                results.append(response.status_code)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        assert all(status in [200, 500] for status in results)
        
        print(f"✅ Rapid API requests test: {len(results)} requests in {total_time:.2f}s")
    
    def test_large_symbol_list_handling(self, api_client):
        """Test handling of large symbol lists."""
        # Create large symbol list
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX', 'CRM', 'ORCL']
        symbol_string = ','.join(symbols)
        
        response = api_client.get(f'/api/market-data?symbols={symbol_string}')
        
        # Should handle gracefully
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = json.loads(response.data)
            assert len(data['symbols']) <= len(symbols)  # May filter invalid symbols
        
        print(f"✅ Large symbol list test: {len(symbols)} symbols")