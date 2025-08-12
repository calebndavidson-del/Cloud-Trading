"""
Unit tests for backend data collector module.
"""
import pytest
import os
from unittest.mock import Mock, patch
from backend.data_collector import fetch_market_data, fetch_market_trends, _get_mock_market_data, _get_mock_trends


class TestDataCollector:
    """Test the data collector functions."""
    
    def test_fetch_market_data_default_symbols(self, mock_yfinance):
        """Test fetching market data with default symbols."""
        data = fetch_market_data()
        
        assert isinstance(data, dict)
        assert len(data) == 5  # Default symbols: AAPL, GOOGL, MSFT, TSLA, AMZN
        assert 'AAPL' in data
        assert 'GOOGL' in data
        assert 'MSFT' in data
        assert 'TSLA' in data
        assert 'AMZN' in data
    
    def test_fetch_market_data_custom_symbols(self, mock_yfinance):
        """Test fetching market data with custom symbols."""
        symbols = ['AAPL', 'MSFT']
        data = fetch_market_data(symbols)
        
        assert isinstance(data, dict)
        assert len(data) == 2
        assert 'AAPL' in data
        assert 'MSFT' in data
    
    def test_fetch_market_data_mock_mode(self):
        """Test fetching market data in mock mode."""
        symbols = ['AAPL', 'GOOGL']
        data = fetch_market_data(symbols, use_mock=True)
        
        assert isinstance(data, dict)
        assert len(data) == 2
        assert 'AAPL' in data
        assert 'GOOGL' in data
        
        # Verify mock data structure
        for symbol in symbols:
            quote = data[symbol]
            assert 'price' in quote
            assert 'volume' in quote
            assert 'open' in quote
            assert 'high' in quote
            assert 'low' in quote
            assert 'market_cap' in quote
            assert 'pe_ratio' in quote
    
    def test_fetch_market_data_environment_detection(self):
        """Test environment-based mock detection."""
        with patch.dict(os.environ, {'USE_MOCK_DATA': 'true'}):
            data = fetch_market_data(['AAPL'])
            assert isinstance(data, dict)
            assert 'AAPL' in data
    
    def test_fetch_market_data_error_fallback(self):
        """Test fallback to mock data on error."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.side_effect = Exception("Network error")
            
            data = fetch_market_data(['AAPL'])
            
            assert isinstance(data, dict)
            assert 'AAPL' in data
            # Should return mock data on error
    
    def test_get_mock_market_data(self):
        """Test mock market data generation."""
        symbols = ['AAPL', 'GOOGL', 'UNKNOWN']
        mock_data = _get_mock_market_data(symbols)
        
        assert isinstance(mock_data, dict)
        assert len(mock_data) == 3
        
        for symbol in symbols:
            assert symbol in mock_data
            quote = mock_data[symbol]
            assert isinstance(quote['price'], float)
            assert isinstance(quote['volume'], int)
            assert quote['price'] > 0
            assert quote['volume'] > 0
    
    def test_fetch_market_trends_success(self, mock_yfinance):
        """Test successful market trends fetching."""
        trends = fetch_market_trends()
        
        assert isinstance(trends, dict)
        assert 'sp500' in trends
        sp500_data = trends['sp500']
        assert 'current_price' in sp500_data
        assert 'change_percent' in sp500_data
        assert 'trend' in sp500_data
        assert sp500_data['trend'] in ['up', 'down']
    
    def test_fetch_market_trends_mock_mode(self):
        """Test market trends in mock mode."""
        with patch.dict(os.environ, {'USE_MOCK_DATA': 'true'}):
            trends = fetch_market_trends()
            
            assert isinstance(trends, dict)
            assert 'sp500' in trends
    
    def test_fetch_market_trends_error_fallback(self):
        """Test fallback to mock trends on error."""
        with patch('yfinance.Ticker') as mock_ticker:
            mock_ticker.side_effect = Exception("Network error")
            
            trends = fetch_market_trends()
            
            assert isinstance(trends, dict)
            assert 'sp500' in trends
    
    def test_get_mock_trends(self):
        """Test mock trends generation."""
        mock_trends = _get_mock_trends()
        
        assert isinstance(mock_trends, dict)
        assert 'sp500' in mock_trends
        
        sp500_data = mock_trends['sp500']
        assert 'current_price' in sp500_data
        assert 'change_percent' in sp500_data
        assert 'trend' in sp500_data
        assert sp500_data['trend'] in ['up', 'down']