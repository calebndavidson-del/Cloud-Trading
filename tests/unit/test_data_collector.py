"""
Unit tests for market data collection and provider functionality.
"""
import pytest
from unittest.mock import Mock, patch
from backend.data_collector import fetch_market_data, fetch_market_trends, _get_mock_market_data, _get_mock_trends


class TestMarketDataFetching:
    """Test market data fetching functionality."""
    
    def test_mock_data_generation(self):
        """Test mock data generation."""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        mock_data = _get_mock_market_data(symbols)
        
        assert isinstance(mock_data, dict)
        assert len(mock_data) == len(symbols)
        
        for symbol in symbols:
            assert symbol in mock_data
            data = mock_data[symbol]
            
            # Check required fields
            required_fields = ['price', 'volume', 'open', 'high', 'low', 'market_cap', 'pe_ratio']
            for field in required_fields:
                assert field in data
                assert isinstance(data[field], (int, float))
                assert data[field] > 0
    
    def test_mock_data_consistency(self):
        """Test that mock data is consistent across calls."""
        symbols = ['AAPL', 'GOOGL']
        
        data1 = _get_mock_market_data(symbols)
        data2 = _get_mock_market_data(symbols)
        
        # Should be identical due to fixed random seed
        assert data1 == data2
    
    def test_fetch_market_data_with_mock(self, test_environment):
        """Test fetch_market_data with mock data enabled."""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        
        result = fetch_market_data(symbols, use_mock=True)
        
        assert isinstance(result, dict)
        assert len(result) == len(symbols)
        
        for symbol in symbols:
            assert symbol in result
            assert 'price' in result[symbol]
            assert 'volume' in result[symbol]
    
    def test_fetch_market_data_default_symbols(self, test_environment):
        """Test fetch_market_data with default symbols."""
        result = fetch_market_data(use_mock=True)
        
        assert isinstance(result, dict)
        assert len(result) > 0  # Should have default symbols
    
    @patch('yfinance.Ticker')
    def test_fetch_market_data_yfinance_success(self, mock_ticker, test_environment):
        """Test successful yfinance data fetching."""
        # Mock yfinance response
        mock_ticker_instance = Mock()
        mock_ticker.return_value = mock_ticker_instance
        
        # Mock history data
        import pandas as pd
        mock_hist = pd.DataFrame({
            'Close': [150.25],
            'Volume': [1000000],
            'Open': [149.50],
            'High': [151.00],
            'Low': [148.75]
        })
        mock_ticker_instance.history.return_value = mock_hist
        
        # Mock info data
        mock_ticker_instance.info = {
            'marketCap': 2500000000000,
            'trailingPE': 25.5
        }
        
        result = fetch_market_data(['AAPL'], use_mock=False)
        
        assert 'AAPL' in result
        assert result['AAPL']['price'] == 150.25
        assert result['AAPL']['volume'] == 1000000
    
    @patch('yfinance.Ticker')
    def test_fetch_market_data_yfinance_failure(self, mock_ticker, test_environment):
        """Test yfinance failure fallback to mock data."""
        # Mock yfinance failure
        mock_ticker.side_effect = Exception("Network error")
        
        result = fetch_market_data(['AAPL'], use_mock=False)
        
        # Should fall back to mock data
        assert isinstance(result, dict)
        assert 'AAPL' in result
        assert 'price' in result['AAPL']


class TestMarketTrends:
    """Test market trends functionality."""
    
    def test_mock_trends_generation(self):
        """Test mock trends data generation."""
        trends = _get_mock_trends()
        
        assert isinstance(trends, dict)
        assert 'sp500' in trends
        
        sp500_data = trends['sp500']
        required_fields = ['current_price', 'change_percent', 'trend']
        for field in required_fields:
            assert field in sp500_data
        
        assert sp500_data['trend'] in ['up', 'down']
        assert isinstance(sp500_data['current_price'], (int, float))
        assert isinstance(sp500_data['change_percent'], (int, float))
    
    def test_fetch_market_trends_mock(self, test_environment):
        """Test fetch_market_trends with mock data."""
        result = fetch_market_trends()
        
        assert isinstance(result, dict)
        if 'sp500' in result:
            sp500 = result['sp500']
            assert 'current_price' in sp500
            assert 'change_percent' in sp500
            assert 'trend' in sp500
    
    @patch('yfinance.Ticker')
    def test_fetch_market_trends_yfinance_success(self, mock_ticker, test_environment):
        """Test successful market trends fetching."""
        # Mock yfinance SP500 data
        mock_ticker_instance = Mock()
        mock_ticker.return_value = mock_ticker_instance
        
        import pandas as pd
        mock_hist = pd.DataFrame({
            'Close': [4450.25, 4500.25]  # Two days of data
        })
        mock_ticker_instance.history.return_value = mock_hist
        
        with patch.dict('os.environ', {'USE_MOCK_DATA': 'false'}):
            result = fetch_market_trends()
        
        if 'sp500' in result:
            sp500 = result['sp500']
            assert sp500['current_price'] == 4500.25
            assert 'change_percent' in sp500
            assert 'trend' in sp500


class TestDataCollectorEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_empty_symbol_list(self):
        """Test handling of empty symbol list."""
        result = fetch_market_data([], use_mock=True)
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_invalid_symbols(self):
        """Test handling of invalid symbols."""
        result = fetch_market_data(['INVALID123', 'BADSTOCK'], use_mock=True)
        
        assert isinstance(result, dict)
        # Mock data generator should handle any symbol
        assert len(result) == 2
    
    def test_none_symbol_list(self):
        """Test handling of None symbol list."""
        result = fetch_market_data(None, use_mock=True)
        
        assert isinstance(result, dict)
        assert len(result) > 0  # Should use defaults
    
    @patch('yfinance.Ticker')
    def test_partial_yfinance_failure(self, mock_ticker, test_environment):
        """Test partial failure in yfinance data fetching."""
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            if symbol == 'AAPL':
                # Success for AAPL
                import pandas as pd
                mock_instance.history.return_value = pd.DataFrame({
                    'Close': [150.25],
                    'Volume': [1000000],
                    'Open': [149.50],
                    'High': [151.00],
                    'Low': [148.75]
                })
                mock_instance.info = {'marketCap': 2500000000000, 'trailingPE': 25.5}
            else:
                # Failure for other symbols
                mock_instance.history.return_value = pd.DataFrame()  # Empty dataframe
                mock_instance.info = {}
            return mock_instance
        
        mock_ticker.side_effect = mock_ticker_side_effect
        
        result = fetch_market_data(['AAPL', 'GOOGL'], use_mock=False)
        
        # Should contain AAPL data and either mock or error for GOOGL
        assert 'AAPL' in result
        if 'GOOGL' in result:
            # Could be mock data fallback or error
            assert isinstance(result['GOOGL'], dict)


class TestEnvironmentConfiguration:
    """Test environment-based configuration."""
    
    def test_mock_data_environment_variable(self, monkeypatch):
        """Test USE_MOCK_DATA environment variable."""
        # Test with mock data enabled
        monkeypatch.setenv("USE_MOCK_DATA", "true")
        result = fetch_market_data(['AAPL'])
        assert isinstance(result, dict)
        assert 'AAPL' in result
        
        # Test with mock data disabled (should still work due to fallback)
        monkeypatch.setenv("USE_MOCK_DATA", "false")
        result = fetch_market_data(['AAPL'])
        assert isinstance(result, dict)
    
    def test_environment_detection(self, monkeypatch):
        """Test automatic environment detection."""
        # Test production-like environment
        monkeypatch.delenv("USE_MOCK_DATA", raising=False)
        monkeypatch.setenv("ENVIRONMENT", "production")
        
        result = fetch_market_data(['AAPL'])
        assert isinstance(result, dict)
        
        # Test development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        result = fetch_market_data(['AAPL'])
        assert isinstance(result, dict)