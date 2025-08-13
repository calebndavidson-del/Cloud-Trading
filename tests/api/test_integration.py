"""
API integration tests - More comprehensive testing of API functionality.
"""
import pytest
import json
import time
from unittest.mock import patch, Mock


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API endpoints."""
    
    def test_market_data_multiple_requests(self, api_client):
        """Test multiple consecutive market data requests."""
        symbols = ['AAPL', 'GOOGL', 'MSFT']
        
        for _ in range(3):
            response = api_client.get(f'/api/market-data?symbols={",".join(symbols)}')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert set(data['symbols']) == set(symbols)
            
            # Small delay between requests
            time.sleep(0.1)
    
    def test_bot_workflow_integration(self, api_client):
        """Test complete bot workflow through API."""
        # 1. Check status
        status_response = api_client.get('/api/status')
        assert status_response.status_code == 200
        
        # 2. Get market data
        market_response = api_client.get('/api/market-data?symbols=AAPL,GOOGL')
        assert market_response.status_code == 200
        
        # 3. Run bot
        bot_response = api_client.post('/api/bot/run')
        assert bot_response.status_code == 200
        
        # 4. Check status again
        final_status = api_client.get('/api/status')
        assert final_status.status_code == 200
    
    def test_market_data_caching_behavior(self, api_client):
        """Test market data response consistency."""
        response1 = api_client.get('/api/market-data?symbols=AAPL')
        response2 = api_client.get('/api/market-data?symbols=AAPL')
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)
        
        # Both should be successful
        assert data1['status'] == 'success'
        assert data2['status'] == 'success'
        
        # Mock data should be consistent
        if 'AAPL' in data1['data'] and 'AAPL' in data2['data']:
            # Prices should be the same since we're using mock data
            assert data1['data']['AAPL']['price'] == data2['data']['AAPL']['price']


@pytest.mark.integration
class TestAPIDataFlow:
    """Test data flow through API endpoints."""
    
    def test_config_to_market_data_flow(self, api_client):
        """Test that config default symbols are used in market data."""
        # Get config
        config_response = api_client.get('/api/config')
        assert config_response.status_code == 200
        
        config_data = json.loads(config_response.data)
        default_symbols = config_data['trading']['default_symbols']
        
        # Get market data without specifying symbols
        market_response = api_client.get('/api/market-data')
        assert market_response.status_code == 200
        
        market_data = json.loads(market_response.data)
        
        # Should use default symbols from config
        assert set(market_data['symbols']) == set(default_symbols)
    
    def test_market_trends_data_structure(self, api_client):
        """Test market trends data structure and content."""
        response = api_client.get('/api/market-trends')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert 'trends' in data
        
        if 'sp500' in data['trends']:
            sp500_data = data['trends']['sp500']
            required_fields = ['current_price', 'change_percent', 'trend']
            for field in required_fields:
                assert field in sp500_data
            
            # Validate data types
            assert isinstance(sp500_data['current_price'], (int, float))
            assert isinstance(sp500_data['change_percent'], (int, float))
            assert sp500_data['trend'] in ['up', 'down']


@pytest.mark.integration
class TestAPIErrorScenarios:
    """Test API error handling in integration scenarios."""
    
    @patch('backend.data_collector.fetch_market_data')
    def test_market_data_backend_error(self, mock_fetch, api_client):
        """Test API behavior when backend data collection fails."""
        # Mock backend error
        mock_fetch.return_value = {'error': 'Network timeout'}
        
        response = api_client.get('/api/market-data?symbols=AAPL')
        
        # API should handle backend errors gracefully
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert data['status'] == 'error'
    
    @patch('backend.bot.run_bot')
    def test_bot_execution_error(self, mock_run_bot, api_client):
        """Test API behavior when bot execution fails."""
        # Mock bot execution error
        mock_run_bot.side_effect = Exception("Bot execution failed")
        
        response = api_client.post('/api/bot/run')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
    
    @patch('backend.config.get_config')
    def test_config_error_handling(self, mock_config, api_client):
        """Test API behavior when config loading fails."""
        # Mock config error
        mock_config.side_effect = Exception("Config load failed")
        
        response = api_client.get('/api/status')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data


@pytest.mark.integration
class TestAPIPerformance:
    """Basic API performance tests."""
    
    def test_health_check_performance(self, api_client):
        """Test health check response time."""
        start_time = time.time()
        response = api_client.get('/health')
        end_time = time.time()
        
        assert response.status_code == 200
        # Health check should be very fast (< 100ms)
        assert (end_time - start_time) < 0.1
    
    def test_concurrent_requests_handling(self, api_client):
        """Test handling of multiple concurrent-ish requests."""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            response = api_client.get('/health')
            results.put(response.status_code)
        
        # Create multiple threads to simulate concurrent requests
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check all requests succeeded
        while not results.empty():
            status_code = results.get()
            assert status_code == 200


@pytest.mark.integration
class TestAPIResponseTiming:
    """Test API response timing and consistency."""
    
    def test_market_data_response_time(self, api_client):
        """Test market data endpoint response time."""
        start_time = time.time()
        response = api_client.get('/api/market-data?symbols=AAPL,GOOGL')
        end_time = time.time()
        
        assert response.status_code == 200
        
        # With mock data, should be fast (< 1 second)
        response_time = end_time - start_time
        assert response_time < 1.0
        
        # Log response time for monitoring
        print(f"Market data response time: {response_time:.3f}s")
    
    def test_all_endpoints_response_time(self, api_client):
        """Test response time for all endpoints."""
        endpoints = [
            ('/health', 'GET'),
            ('/api/status', 'GET'),
            ('/api/market-data', 'GET'),
            ('/api/market-trends', 'GET'),
            ('/api/config', 'GET'),
            ('/api/bot/run', 'POST')
        ]
        
        for endpoint, method in endpoints:
            start_time = time.time()
            
            if method == 'GET':
                response = api_client.get(endpoint)
            else:
                response = api_client.post(endpoint)
            
            end_time = time.time()
            response_time = end_time - start_time
            
            assert response.status_code in [200, 500]  # Allow expected errors
            assert response_time < 5.0  # All endpoints should respond within 5s
            
            print(f"{method} {endpoint}: {response_time:.3f}s")