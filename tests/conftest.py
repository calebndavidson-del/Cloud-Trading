"""
Test fixtures and utilities for Cloud Trading tests.
"""
import pytest
import os
import json
from typing import Dict, Any
from unittest.mock import Mock


@pytest.fixture(scope="session")
def test_config():
    """Test configuration fixture."""
    return {
        "env": "test",
        "use_mock_data": True,
        "api_keys": {
            "yahoo": "test_key",
            "alpha_vantage": "test_key"
        },
        "trading": {
            "default_symbols": ["AAPL", "GOOGL", "MSFT", "TSLA"],
            "trading_enabled": False,
            "paper_trading": True
        }
    }


@pytest.fixture(scope="session") 
def mock_market_data():
    """Mock market data fixture."""
    return {
        "AAPL": {
            "price": 150.25,
            "volume": 1000000,
            "open": 149.50,
            "high": 151.00,
            "low": 148.75,
            "market_cap": 2500000000000,
            "pe_ratio": 25.5,
            "provider": "mock"
        },
        "GOOGL": {
            "price": 2800.50,
            "volume": 500000,
            "open": 2795.00,
            "high": 2810.00,
            "low": 2785.00,
            "market_cap": 1800000000000,
            "pe_ratio": 22.3,
            "provider": "mock"
        },
        "MSFT": {
            "price": 330.75,
            "volume": 750000,
            "open": 328.50,
            "high": 332.00,
            "low": 327.00,
            "market_cap": 2450000000000,
            "pe_ratio": 28.1,
            "provider": "mock"
        },
        "TSLA": {
            "price": 250.00,
            "volume": 2000000,
            "open": 245.00,
            "high": 255.00,
            "low": 243.50,
            "market_cap": 800000000000,
            "pe_ratio": 45.2,
            "provider": "mock"
        }
    }


@pytest.fixture(scope="session")
def mock_market_trends():
    """Mock market trends fixture."""
    return {
        "sp500": {
            "current_price": 4500.25,
            "change_percent": 1.25,
            "trend": "up"
        }
    }


@pytest.fixture
def test_environment(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("USE_MOCK_DATA", "true")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("TRADING_ENABLED", "false")
    monkeypatch.setenv("PAPER_TRADING", "true")


@pytest.fixture
def api_client():
    """Flask test client fixture."""
    os.environ["USE_MOCK_DATA"] = "true"
    os.environ["ENVIRONMENT"] = "test"
    
    from api import app
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing."""
    return [
        {"symbol": "AAPL", "action": "buy", "shares": 10, "price": 150.0, "pnl": 0},
        {"symbol": "AAPL", "action": "sell", "shares": 10, "price": 155.0, "pnl": 50.0},
        {"symbol": "GOOGL", "action": "buy", "shares": 5, "price": 2800.0, "pnl": 0},
        {"symbol": "GOOGL", "action": "sell", "shares": 5, "price": 2750.0, "pnl": -250.0}
    ]


@pytest.fixture
def sample_optimization_params():
    """Sample optimization parameters."""
    return {
        "initial_capital": 10000,
        "short_ma_period": 5,
        "long_ma_period": 15,
        "symbols": ["AAPL", "GOOGL"]
    }


class MockProvider:
    """Mock market data provider for testing."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.mock_data = {
            'AAPL': {'price': 150.25, 'volume': 1000000},
            'GOOGL': {'price': 2800.50, 'volume': 500000},
            'MSFT': {'price': 330.75, 'volume': 750000}
        }
    
    def fetch_quote(self, symbol: str):
        return self.mock_data.get(symbol)
    
    def fetch_quotes(self, symbols: list):
        return {symbol: self.fetch_quote(symbol) for symbol in symbols}


def create_mock_response(data: Dict[str, Any], status_code: int = 200):
    """Create mock HTTP response."""
    mock_response = Mock()
    mock_response.json.return_value = data
    mock_response.status_code = status_code
    mock_response.text = json.dumps(data)
    return mock_response