"""
Test utilities and helper functions for Cloud Trading tests.
"""
import time
import json
import functools
from typing import Dict, Any, Callable
from unittest.mock import Mock, patch
import pandas as pd


def timing_test(func: Callable) -> Callable:
    """Decorator to measure test execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"⏱️  {func.__name__} executed in {execution_time:.3f}s")
        
        return result
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 0.1):
    """Decorator to retry flaky tests."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        print(f"🔄 {func.__name__} failed (attempt {attempt + 1}/{max_retries}), retrying...")
                        time.sleep(delay)
                    else:
                        print(f"❌ {func.__name__} failed after {max_retries} attempts")
            
            raise last_exception
        return wrapper
    return decorator


class MockMarketDataProvider:
    """Enhanced mock market data provider for testing."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.call_count = 0
        self.failure_rate = 0.0
        self.latency = 0.0
        
    def set_failure_rate(self, rate: float):
        """Set the failure rate (0.0 to 1.0)."""
        self.failure_rate = rate
    
    def set_latency(self, seconds: float):
        """Set artificial latency for testing."""
        self.latency = seconds
    
    def fetch_quote(self, symbol: str) -> Dict[str, Any]:
        """Mock fetch single quote with configurable behavior."""
        self.call_count += 1
        
        # Add latency if configured
        if self.latency > 0:
            time.sleep(self.latency)
        
        # Simulate failures if configured
        if random.random() < self.failure_rate:
            raise Exception(f"Mock failure for {symbol}")
        
        # Return mock data
        base_prices = {
            'AAPL': 150.0, 'GOOGL': 2800.0, 'MSFT': 330.0,
            'TSLA': 250.0, 'AMZN': 180.0, 'META': 300.0
        }
        
        base_price = base_prices.get(symbol, 100.0)
        variation = random.uniform(-0.02, 0.02)  # ±2% variation
        
        return {
            'symbol': symbol,
            'price': round(base_price * (1 + variation), 2),
            'volume': random.randint(100000, 5000000),
            'open': round(base_price * random.uniform(0.98, 1.02), 2),
            'high': round(base_price * random.uniform(1.01, 1.05), 2),
            'low': round(base_price * random.uniform(0.95, 0.99), 2),
            'market_cap': random.randint(50000000000, 3000000000000),
            'pe_ratio': round(random.uniform(15, 35), 2),
            'provider': 'MockProvider'
        }


class APITestHelper:
    """Helper class for API testing."""
    
    def __init__(self, client):
        self.client = client
        self.response_times = []
    
    def get_with_timing(self, endpoint: str) -> tuple:
        """Make GET request and return response with timing."""
        start_time = time.time()
        response = self.client.get(endpoint)
        end_time = time.time()
        
        response_time = end_time - start_time
        self.response_times.append(response_time)
        
        return response, response_time
    
    def post_with_timing(self, endpoint: str, data: Dict = None) -> tuple:
        """Make POST request and return response with timing."""
        start_time = time.time()
        response = self.client.post(endpoint, json=data)
        end_time = time.time()
        
        response_time = end_time - start_time
        self.response_times.append(response_time)
        
        return response, response_time
    
    def get_average_response_time(self) -> float:
        """Get average response time for all requests."""
        return sum(self.response_times) / len(self.response_times) if self.response_times else 0.0
    
    def reset_timing(self):
        """Reset timing statistics."""
        self.response_times = []


def create_mock_yfinance_ticker(symbol_data: Dict[str, Dict[str, Any]]):
    """Create a mock yfinance Ticker with specified data."""
    def mock_ticker_factory(symbol):
        mock_instance = Mock()
        
        if symbol in symbol_data:
            data = symbol_data[symbol]
            
            # Create mock historical data
            if 'price' in data:
                mock_hist = pd.DataFrame({
                    'Close': [data['price']],
                    'Volume': [data.get('volume', 1000000)],
                    'Open': [data.get('open', data['price'] * 0.99)],
                    'High': [data.get('high', data['price'] * 1.01)],
                    'Low': [data.get('low', data['price'] * 0.98)]
                })
                mock_instance.history.return_value = mock_hist
            else:
                # Return empty dataframe for missing data
                mock_instance.history.return_value = pd.DataFrame()
            
            # Create mock info data
            mock_instance.info = {
                'marketCap': data.get('market_cap', 1000000000),
                'trailingPE': data.get('pe_ratio', 25.0)
            }
        else:
            # Symbol not found
            mock_instance.history.return_value = pd.DataFrame()
            mock_instance.info = {}
        
        return mock_instance
    
    return mock_ticker_factory


def assert_market_data_structure(data: Dict[str, Any], symbols: list = None):
    """Assert that market data has the expected structure."""
    assert isinstance(data, dict), "Market data should be a dictionary"
    
    if symbols:
        for symbol in symbols:
            assert symbol in data, f"Symbol {symbol} should be in market data"
    
    for symbol, symbol_data in data.items():
        if 'error' not in symbol_data:
            # Check required fields for valid data
            required_fields = ['price', 'volume']
            for field in required_fields:
                assert field in symbol_data, f"Field {field} missing for {symbol}"
                assert isinstance(symbol_data[field], (int, float)), f"Field {field} should be numeric for {symbol}"
                assert symbol_data[field] >= 0, f"Field {field} should be non-negative for {symbol}"


def assert_api_response_structure(response_data: Dict[str, Any], expected_fields: list):
    """Assert that API response has the expected structure."""
    assert isinstance(response_data, dict), "Response should be a dictionary"
    
    for field in expected_fields:
        assert field in response_data, f"Field {field} missing from response"


def generate_test_symbols(count: int) -> list:
    """Generate a list of test symbols."""
    return [f'TEST{i:03d}' for i in range(count)]


def simulate_network_conditions(delay: float = 0.0, failure_rate: float = 0.0):
    """Context manager to simulate network conditions."""
    class NetworkSimulator:
        def __init__(self, delay, failure_rate):
            self.delay = delay
            self.failure_rate = failure_rate
            self.original_fetch = None
        
        def __enter__(self):
            # Store original function
            from backend.data_collector import fetch_market_data
            self.original_fetch = fetch_market_data
            
            # Create wrapped function with network simulation
            def wrapped_fetch(*args, **kwargs):
                import random
                
                # Simulate delay
                if self.delay > 0:
                    time.sleep(self.delay)
                
                # Simulate failure
                if random.random() < self.failure_rate:
                    raise ConnectionError("Simulated network failure")
                
                return self.original_fetch(*args, **kwargs)
            
            # Patch the function
            self.patcher = patch('backend.data_collector.fetch_market_data', wrapped_fetch)
            self.patcher.start()
            
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            self.patcher.stop()
    
    return NetworkSimulator(delay, failure_rate)


class TestDataGenerator:
    """Generate test data for various scenarios."""
    
    @staticmethod
    def create_price_series(base_price: float, length: int, volatility: float = 0.02) -> list:
        """Create a realistic price series for testing."""
        import random
        import math
        
        
        prices = [base_price]
        
        for _ in range(length):
            # Use geometric Brownian motion for realistic price movement
            dt = 1.0  # Daily time step
            drift = 0.0001  # Small positive drift
            random_shock = random.gauss(0, 1)
            
            price_change = drift * dt + volatility * math.sqrt(dt) * random_shock
            new_price = prices[-1] * math.exp(price_change)
            
            # Ensure positive prices
            prices.append(max(new_price, 0.01))
        
        return prices
    
    @staticmethod
    def create_trade_history(num_trades: int) -> list:
        """Create test trade history."""
        import random
        from datetime import datetime, timedelta
        
        trades = []
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        base_date = datetime.now() - timedelta(days=30)
        
        for i in range(num_trades):
            symbol = random.choice(symbols)
            action = random.choice(['buy', 'sell'])
            shares = random.randint(1, 100)
            price = random.uniform(100, 500)
            
            trade = {
                'id': i + 1,
                'timestamp': base_date + timedelta(days=random.randint(0, 30)),
                'symbol': symbol,
                'action': action,
                'shares': shares,
                'price': round(price, 2),
                'pnl': random.uniform(-100, 100) if action == 'sell' else 0
            }
            
            trades.append(trade)
        
        return sorted(trades, key=lambda x: x['timestamp'])
    
    @staticmethod
    def create_optimization_scenarios() -> list:
        """Create test scenarios for optimization."""
        return [
            {
                'name': 'conservative',
                'parameters': {
                    'short_ma_period': 10,
                    'long_ma_period': 30,
                    'initial_capital': 10000
                }
            },
            {
                'name': 'aggressive',
                'parameters': {
                    'short_ma_period': 3,
                    'long_ma_period': 10,
                    'initial_capital': 10000
                }
            },
            {
                'name': 'balanced',
                'parameters': {
                    'short_ma_period': 5,
                    'long_ma_period': 20,
                    'initial_capital': 10000
                }
            }
        ]


class PerformanceMonitor:
    """Monitor performance metrics during tests."""
    
    def __init__(self):
        self.metrics = {
            'response_times': [],
            'memory_usage': [],
            'error_counts': {},
            'throughput': 0
        }
        self.start_time = None
        self.request_count = 0
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.request_count = 0
    
    def record_request(self, response_time: float, error: str = None):
        """Record a request for monitoring."""
        self.metrics['response_times'].append(response_time)
        self.request_count += 1
        
        if error:
            self.metrics['error_counts'][error] = self.metrics['error_counts'].get(error, 0) + 1
    
    def record_memory_usage(self):
        """Record current memory usage."""
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.metrics['memory_usage'].append(memory_mb)
        except ImportError:
            pass  # psutil not available
    
    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        response_times = self.metrics['response_times']
        
        if not response_times:
            return {'error': 'No requests recorded'}
        
        total_time = time.time() - self.start_time if self.start_time else 0
        
        summary = {
            'total_requests': len(response_times),
            'avg_response_time': sum(response_times) / len(response_times),
            'min_response_time': min(response_times),
            'max_response_time': max(response_times),
            'throughput': len(response_times) / total_time if total_time > 0 else 0,
            'error_rate': sum(self.metrics['error_counts'].values()) / len(response_times),
            'error_counts': self.metrics['error_counts']
        }
        
        if self.metrics['memory_usage']:
            summary['avg_memory_mb'] = sum(self.metrics['memory_usage']) / len(self.metrics['memory_usage'])
            summary['max_memory_mb'] = max(self.metrics['memory_usage'])
        
        return summary


def validate_test_environment():
    """Validate that the test environment is properly configured."""
    import os
    
    required_env_vars = ['USE_MOCK_DATA', 'ENVIRONMENT']
    missing_vars = [var for var in required_env_vars if var not in os.environ]
    
    if missing_vars:
        raise EnvironmentError(f"Missing required environment variables: {missing_vars}")
    
    # Verify mock data is enabled for tests
    if os.environ.get('USE_MOCK_DATA', '').lower() != 'true':
        print("⚠️  Warning: USE_MOCK_DATA is not set to 'true' - tests may use real data")
    
    return True


def log_test_results(test_name: str, results: Dict[str, Any]):
    """Log test results in a standardized format."""
    print(f"\n📊 Test Results: {test_name}")
    print("=" * 50)
    
    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.3f}")
        elif isinstance(value, dict):
            print(f"{key}:")
            for subkey, subvalue in value.items():
                print(f"  {subkey}: {subvalue}")
        else:
            print(f"{key}: {value}")
    
    print("=" * 50)