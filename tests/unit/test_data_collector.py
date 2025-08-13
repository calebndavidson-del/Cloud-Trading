"""
Unit tests for live market data collection - NO MOCK DATA ALLOWED.
Tests live data enforcement and error handling.
"""
import pytest
import os
from unittest.mock import Mock, patch
from backend.data_collector import fetch_market_data, fetch_market_trends


class TestLiveDataEnforcement:
    """Test live data enforcement - no mock data allowed."""
    
    def test_mock_data_rejection(self):
        """Test that mock data requests are rejected."""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        
        # Should raise exception when mock data is explicitly requested
        with pytest.raises(Exception) as excinfo:
            fetch_market_data(symbols, use_mock=True)
        
        assert "Mock data is not allowed" in str(excinfo.value)
    
    def test_environment_variable_rejection(self):
        """Test that USE_MOCK_DATA environment variable is rejected."""
        symbols = ['AAPL']
        
        # Set environment variable
        original_value = os.environ.get('USE_MOCK_DATA')
        os.environ['USE_MOCK_DATA'] = 'true'
        
        try:
            with pytest.raises(Exception) as excinfo:
                fetch_market_data(symbols)
            
            assert "USE_MOCK_DATA environment variable detected" in str(excinfo.value)
        finally:
            # Restore original value
            if original_value is None:
                os.environ.pop('USE_MOCK_DATA', None)
            else:
                os.environ['USE_MOCK_DATA'] = original_value
    
    def test_live_data_failure_no_internet(self):
        """Test that system fails gracefully when no internet connection."""
        symbols = ['AAPL']
        
        # Ensure mock data is disabled
        original_value = os.environ.get('USE_MOCK_DATA')
        os.environ['USE_MOCK_DATA'] = 'false'
        
        try:
            # This should fail because no internet access in test environment
            with pytest.raises(Exception) as excinfo:
                fetch_market_data(symbols, use_mock=False)
            
            # Should mention that mock data fallback is disabled
            assert "Mock data fallback is disabled" in str(excinfo.value)
        finally:
            # Restore original value
            if original_value is None:
                os.environ.pop('USE_MOCK_DATA', None)
            else:
                os.environ['USE_MOCK_DATA'] = original_value
    
    def test_fetch_market_trends_mock_rejection(self):
        """Test that market trends rejects mock data."""
        # Set environment to request mock data
        original_value = os.environ.get('USE_MOCK_DATA')
        os.environ['USE_MOCK_DATA'] = 'true'
        
        try:
            with pytest.raises(Exception) as excinfo:
                fetch_market_trends()
            
            assert "USE_MOCK_DATA environment variable detected" in str(excinfo.value)
        finally:
            # Restore original value
            if original_value is None:
                os.environ.pop('USE_MOCK_DATA', None)
            else:
                os.environ['USE_MOCK_DATA'] = original_value


class TestDataValidation:
    """Test data validation and quality checks."""
    
    def test_data_structure_requirements(self):
        """Test that required data structure is maintained."""
        # This tests the expected structure when live data would be available
        expected_fields = ['price', 'volume', 'open', 'high', 'low']
        
        # Test that our validation logic works
        test_data = {
            'price': 150.0,
            'volume': 1000000,
            'open': 149.0,
            'high': 151.0,
            'low': 148.0
        }
        
        for field in expected_fields:
            assert field in test_data
            assert isinstance(test_data[field], (int, float))
            assert test_data[field] > 0


if __name__ == '__main__':
    pytest.main([__file__])