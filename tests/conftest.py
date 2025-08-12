"""
Shared pytest fixtures and configuration for all tests.
"""
import pytest
import os
import asyncio
from unittest.mock import Mock, patch
from typing import Dict, Any


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_environment():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        'USE_MOCK_DATA': 'true',
        'ALPHA_VANTAGE_API_KEY': 'test_key',
        'IEX_CLOUD_API_KEY': 'test_key',
        'AWS_ACCESS_KEY_ID': 'test_key',
        'AWS_SECRET_ACCESS_KEY': 'test_secret',
        'AWS_DEFAULT_REGION': 'us-west-2'
    }):
        yield


@pytest.fixture
def sample_market_data():
    """Sample market data for testing."""
    return {
        'AAPL': {
            'price': 150.25,
            'volume': 1000000,
            'open': 149.50,
            'high': 151.00,
            'low': 148.75,
            'market_cap': 2500000000000,
            'pe_ratio': 25.5
        },
        'GOOGL': {
            'price': 2800.50,
            'volume': 500000,
            'open': 2795.00,
            'high': 2805.25,
            'low': 2790.00,
            'market_cap': 1800000000000,
            'pe_ratio': 22.8
        }
    }


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        'providers': {
            'yahoo_finance': {'enabled': True, 'timeout': 10},
            'alpha_vantage': {'enabled': True, 'timeout': 15},
            'iex_cloud': {'enabled': True, 'timeout': 10}
        },
        'fallback_settings': {
            'max_retries': 3,
            'retry_delay': 1.0,
            'enable_fallback_data': True
        }
    }


@pytest.fixture
def mock_yfinance():
    """Mock yfinance responses."""
    with patch('yfinance.Ticker') as mock_ticker:
        mock_instance = Mock()
        mock_ticker.return_value = mock_instance
        
        # Mock history data
        mock_history = Mock()
        mock_history.empty = False
        mock_history.__getitem__ = Mock(side_effect=lambda key: Mock(iloc=[-1]))
        mock_history['Close'].iloc = [150.25]
        mock_history['Volume'].iloc = [1000000]
        mock_history['Open'].iloc = [149.50]
        mock_history['High'].iloc = [151.00]
        mock_history['Low'].iloc = [148.75]
        
        mock_instance.history.return_value = mock_history
        mock_instance.info = {
            'marketCap': 2500000000000,
            'trailingPE': 25.5
        }
        
        yield mock_ticker


@pytest.fixture
def mock_requests():
    """Mock requests for API calls."""
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'Global Quote': {
                '05. price': '150.25',
                '06. volume': '1000000',
                '09. change': '2.50',
                '10. change percent': '1.69%'
            }
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_aiohttp():
    """Mock aiohttp for async API calls."""
    import aiohttp
    with patch('aiohttp.ClientSession') as mock_session:
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = asyncio.coroutine(lambda: {
            'AAPL': {
                'latestPrice': 150.25,
                'latestVolume': 1000000,
                'change': 2.50,
                'changePercent': 0.0169
            }
        })
        
        mock_get = asyncio.coroutine(lambda *args, **kwargs: mock_response)
        mock_session.return_value.__aenter__.return_value.get = mock_get
        
        yield mock_session