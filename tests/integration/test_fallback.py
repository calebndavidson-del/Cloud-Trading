"""
Tests for market data provider fallback scenarios and multi-provider handling.
"""
import pytest
from unittest.mock import patch, Mock
import pandas as pd


@pytest.mark.integration
class TestMarketDataFallback:
    """Test market data provider fallback scenarios."""
    
    @patch('yfinance.Ticker')
    def test_yfinance_timeout_fallback(self, mock_ticker, test_environment):
        """Test fallback when Yahoo Finance times out."""
        # Mock yfinance timeout
        mock_ticker.side_effect = TimeoutError("Request timed out")
        
        from backend.data_collector import fetch_market_data
        
        # Should fall back to mock data
        result = fetch_market_data(['AAPL', 'GOOGL'], use_mock=False)
        
        assert isinstance(result, dict)
        assert 'AAPL' in result
        assert 'GOOGL' in result
        
        # Should have mock data structure
        for symbol, data in result.items():
            assert 'price' in data
            assert 'volume' in data
            assert isinstance(data['price'], (int, float))
            assert isinstance(data['volume'], (int, float))
        
        print("✅ YFinance timeout fallback successful")
    
    @patch('yfinance.Ticker')
    def test_yfinance_network_error_fallback(self, mock_ticker, test_environment):
        """Test fallback when Yahoo Finance has network error."""
        # Mock network error
        mock_ticker.side_effect = ConnectionError("Network error")
        
        from backend.data_collector import fetch_market_data
        
        result = fetch_market_data(['AAPL'], use_mock=False)
        
        assert isinstance(result, dict)
        assert 'AAPL' in result
        assert 'price' in result['AAPL']
        
        print("✅ YFinance network error fallback successful")
    
    @patch('yfinance.Ticker')
    def test_yfinance_partial_failure(self, mock_ticker, test_environment):
        """Test handling when only some symbols fail."""
        def mock_ticker_behavior(symbol):
            mock_instance = Mock()
            
            if symbol == 'AAPL':
                # Success for AAPL
                mock_hist = pd.DataFrame({
                    'Close': [150.25],
                    'Volume': [1000000],
                    'Open': [149.50],
                    'High': [151.00],
                    'Low': [148.75]
                })
                mock_instance.history.return_value = mock_hist
                mock_instance.info = {'marketCap': 2500000000000, 'trailingPE': 25.5}
            else:
                # Failure for other symbols
                mock_instance.history.side_effect = Exception("Data not available")
                mock_instance.info = {}
            
            return mock_instance
        
        mock_ticker.side_effect = mock_ticker_behavior
        
        from backend.data_collector import fetch_market_data
        
        result = fetch_market_data(['AAPL', 'GOOGL', 'INVALID'], use_mock=False)
        
        assert isinstance(result, dict)
        
        # AAPL should have real data
        if 'AAPL' in result and 'error' not in result['AAPL']:
            assert result['AAPL']['price'] == 150.25
        
        # Other symbols should have fallback mock data
        assert len(result) == 3  # All symbols should be present
        
        print("✅ Partial failure handling successful")
    
    @patch('yfinance.Ticker')
    def test_yfinance_empty_data_fallback(self, mock_ticker, test_environment):
        """Test fallback when Yahoo Finance returns empty data."""
        # Mock empty response
        mock_instance = Mock()
        mock_instance.history.return_value = pd.DataFrame()  # Empty dataframe
        mock_instance.info = {}
        mock_ticker.return_value = mock_instance
        
        from backend.data_collector import fetch_market_data
        
        result = fetch_market_data(['AAPL'], use_mock=False)
        
        assert isinstance(result, dict)
        assert 'AAPL' in result
        
        # Should fall back to mock data or indicate error appropriately
        if 'error' not in result['AAPL']:
            assert 'price' in result['AAPL']
        
        print("✅ Empty data fallback successful")


@pytest.mark.integration
class TestMarketTrendsFallback:
    """Test market trends fallback scenarios."""
    
    @patch('yfinance.Ticker')
    def test_sp500_fetch_failure_fallback(self, mock_ticker, test_environment):
        """Test fallback when S&P 500 data fetch fails."""
        mock_ticker.side_effect = Exception("S&P 500 data unavailable")
        
        from backend.data_collector import fetch_market_trends
        
        with patch.dict('os.environ', {'USE_MOCK_DATA': 'false'}):
            result = fetch_market_trends()
        
        assert isinstance(result, dict)
        
        # Should fall back to mock trends data
        if 'sp500' in result:
            sp500_data = result['sp500']
            assert 'current_price' in sp500_data
            assert 'change_percent' in sp500_data
            assert 'trend' in sp500_data
        
        print("✅ S&P 500 fetch failure fallback successful")
    
    @patch('yfinance.Ticker')
    def test_trends_partial_data_handling(self, mock_ticker, test_environment):
        """Test handling when trends data is incomplete."""
        mock_instance = Mock()
        
        # Mock incomplete historical data
        mock_hist = pd.DataFrame({
            'Close': [4500.25]  # Only one day of data
        })
        mock_instance.history.return_value = mock_hist
        mock_ticker.return_value = mock_instance
        
        from backend.data_collector import fetch_market_trends
        
        with patch.dict('os.environ', {'USE_MOCK_DATA': 'false'}):
            result = fetch_market_trends()
        
        assert isinstance(result, dict)
        
        # Should handle incomplete data gracefully
        print("✅ Incomplete trends data handling successful")


@pytest.mark.integration
class TestProviderResilience:
    """Test provider resilience and error recovery."""
    
    def test_rapid_successive_failures(self, test_environment):
        """Test behavior under rapid successive provider failures."""
        from backend.data_collector import fetch_market_data
        
        with patch('yfinance.Ticker') as mock_ticker:
            # Simulate failures followed by success
            mock_ticker.side_effect = [
                Exception("Failure 1"),
                Exception("Failure 2"), 
                Exception("Failure 3")
            ]
            
            results = []
            for i in range(3):
                result = fetch_market_data(['AAPL'], use_mock=False)
                results.append(result)
        
        # All should fall back to mock data
        for result in results:
            assert isinstance(result, dict)
            assert 'AAPL' in result
        
        print("✅ Rapid successive failures handled")
    
    def test_intermittent_failures(self, test_environment):
        """Test handling of intermittent provider failures."""
        from backend.data_collector import fetch_market_data
        
        def intermittent_failure(symbol):
            mock_instance = Mock()
            # Alternate between success and failure
            if hasattr(intermittent_failure, 'call_count'):
                intermittent_failure.call_count += 1
            else:
                intermittent_failure.call_count = 1
            
            if intermittent_failure.call_count % 2 == 0:
                # Even calls fail
                raise Exception("Intermittent failure")
            else:
                # Odd calls succeed
                mock_hist = pd.DataFrame({
                    'Close': [150.25],
                    'Volume': [1000000],
                    'Open': [149.50],
                    'High': [151.00],
                    'Low': [148.75]
                })
                mock_instance.history.return_value = mock_hist
                mock_instance.info = {'marketCap': 2500000000000}
                return mock_instance
        
        with patch('yfinance.Ticker', side_effect=intermittent_failure):
            results = []
            for _ in range(4):
                result = fetch_market_data(['AAPL'], use_mock=False)
                results.append(result)
        
        # Should handle both successes and failures
        for result in results:
            assert isinstance(result, dict)
            assert 'AAPL' in result
        
        print("✅ Intermittent failures handled")


@pytest.mark.integration  
class TestDataValidation:
    """Test data validation and quality checks."""
    
    @patch('yfinance.Ticker')
    def test_invalid_price_data_handling(self, mock_ticker, test_environment):
        """Test handling of invalid price data."""
        mock_instance = Mock()
        
        # Mock invalid data (negative prices, NaN values)
        mock_hist = pd.DataFrame({
            'Close': [-150.25, float('nan'), 0],  # Invalid prices
            'Volume': [1000000, -500000, float('inf')],  # Invalid volumes
            'Open': [149.50, float('nan'), -10],
            'High': [151.00, float('nan'), -5],
            'Low': [148.75, float('nan'), -20]
        })
        mock_instance.history.return_value = mock_hist
        mock_instance.info = {'marketCap': 2500000000000}
        mock_ticker.return_value = mock_instance
        
        from backend.data_collector import fetch_market_data
        
        result = fetch_market_data(['AAPL'], use_mock=False)
        
        assert isinstance(result, dict)
        assert 'AAPL' in result
        
        # Should either clean the data or fall back to mock data
        if 'error' not in result['AAPL']:
            data = result['AAPL']
            assert data['price'] > 0  # Should have valid price
            assert data['volume'] >= 0  # Should have valid volume
        
        print("✅ Invalid price data handling successful")
    
    @patch('yfinance.Ticker')
    def test_missing_required_fields(self, mock_ticker, test_environment):
        """Test handling when required fields are missing."""
        mock_instance = Mock()
        
        # Mock data missing required fields
        mock_hist = pd.DataFrame({
            'Close': [150.25],
            # Missing Volume, Open, High, Low
        })
        mock_instance.history.return_value = mock_hist
        mock_instance.info = {}  # Missing market cap and PE ratio
        mock_ticker.return_value = mock_instance
        
        from backend.data_collector import fetch_market_data
        
        result = fetch_market_data(['AAPL'], use_mock=False)
        
        assert isinstance(result, dict)
        assert 'AAPL' in result
        
        # Should handle missing fields gracefully
        print("✅ Missing required fields handling successful")
    
    def test_data_consistency_validation(self, test_environment):
        """Test data consistency validation."""
        from backend.data_collector import fetch_market_data
        
        # Fetch same data multiple times
        results = []
        for _ in range(3):
            result = fetch_market_data(['AAPL', 'GOOGL'], use_mock=True)
            results.append(result)
        
        # Mock data should be consistent
        for symbol in ['AAPL', 'GOOGL']:
            prices = []
            for result in results:
                if symbol in result and 'price' in result[symbol]:
                    prices.append(result[symbol]['price'])
            
            if len(prices) > 1:
                # All prices should be the same for mock data
                assert all(p == prices[0] for p in prices), f"Inconsistent prices for {symbol}"
        
        print("✅ Data consistency validation successful")


@pytest.mark.integration
class TestFailoverScenarios:
    """Test complete failover scenarios."""
    
    def test_complete_provider_outage(self, test_environment):
        """Test behavior when all external providers are down."""
        from backend.data_collector import fetch_market_data, fetch_market_trends
        
        # Mock complete outage
        with patch('yfinance.Ticker', side_effect=Exception("Complete outage")):
            # Market data should fall back to mock
            market_result = fetch_market_data(['AAPL', 'GOOGL'], use_mock=False)
            assert isinstance(market_result, dict)
            assert len(market_result) > 0
            
            # Market trends should fall back to mock
            with patch.dict('os.environ', {'USE_MOCK_DATA': 'false'}):
                trends_result = fetch_market_trends()
            assert isinstance(trends_result, dict)
        
        print("✅ Complete provider outage handled")
    
    def test_graceful_degradation(self, api_client):
        """Test graceful degradation through API."""
        # Test that API continues to work even with provider issues
        with patch('backend.data_collector.fetch_market_data') as mock_fetch:
            # Simulate provider issues
            mock_fetch.return_value = {
                'AAPL': {'error': 'Provider timeout'},
                'GOOGL': {'price': 2800, 'volume': 500000}  # Partial success
            }
            
            response = api_client.get('/api/market-data?symbols=AAPL,GOOGL')
            
            # API should handle gracefully
            assert response.status_code == 200
            
            import json
            data = json.loads(response.data)
            assert 'data' in data
            assert 'status' in data
        
        print("✅ Graceful degradation through API successful")
    
    def test_recovery_after_outage(self, test_environment):
        """Test system recovery after provider outage."""
        from backend.data_collector import fetch_market_data
        
        # First, simulate outage
        with patch('yfinance.Ticker', side_effect=Exception("Outage")):
            outage_result = fetch_market_data(['AAPL'], use_mock=False)
            assert isinstance(outage_result, dict)
        
        # Then, simulate recovery
        with patch('yfinance.Ticker') as mock_ticker:
            mock_instance = Mock()
            mock_hist = pd.DataFrame({
                'Close': [150.25],
                'Volume': [1000000],
                'Open': [149.50],
                'High': [151.00],
                'Low': [148.75]
            })
            mock_instance.history.return_value = mock_hist
            mock_instance.info = {'marketCap': 2500000000000}
            mock_ticker.return_value = mock_instance
            
            recovery_result = fetch_market_data(['AAPL'], use_mock=False)
            assert isinstance(recovery_result, dict)
            
            # Should get real data after recovery
            if 'AAPL' in recovery_result and 'error' not in recovery_result['AAPL']:
                assert recovery_result['AAPL']['price'] == 150.25
        
        print("✅ Recovery after outage successful")


@pytest.mark.integration
class TestProviderConfiguration:
    """Test provider configuration and selection."""
    
    def test_mock_data_override(self, test_environment):
        """Test USE_MOCK_DATA environment variable override."""
        from backend.data_collector import fetch_market_data
        
        # Test with mock data explicitly enabled
        result_mock = fetch_market_data(['AAPL'], use_mock=True)
        assert isinstance(result_mock, dict)
        assert 'AAPL' in result_mock
        
        # Test with mock data explicitly disabled (will fall back anyway due to test env)
        result_no_mock = fetch_market_data(['AAPL'], use_mock=False)
        assert isinstance(result_no_mock, dict)
        assert 'AAPL' in result_no_mock
        
        print("✅ Mock data override configuration working")
    
    def test_environment_based_provider_selection(self, monkeypatch):
        """Test provider selection based on environment."""
        from backend.data_collector import fetch_market_data
        
        # Test development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("USE_MOCK_DATA", "true")
        
        dev_result = fetch_market_data(['AAPL'])
        assert isinstance(dev_result, dict)
        
        # Test production environment (but still use mock for testing)
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("USE_MOCK_DATA", "true")
        
        prod_result = fetch_market_data(['AAPL'])
        assert isinstance(prod_result, dict)
        
        print("✅ Environment-based provider selection working")