"""
API smoke tests - Quick validation that all endpoints are working.
"""
import pytest
import json
from typing import Dict, Any


@pytest.mark.smoke
class TestAPISmoke:
    """Smoke tests for all API endpoints."""
    
    def test_health_endpoint(self, api_client):
        """Test health check endpoint."""
        response = api_client.get('/health')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert data['service'] == 'cloud-trading-bot'
        assert 'version' in data
    
    def test_status_endpoint(self, api_client):
        """Test status endpoint."""
        response = api_client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'environment' in data
        assert 'trading_enabled' in data
        assert 'paper_trading' in data
    
    def test_market_data_endpoint(self, api_client):
        """Test market data endpoint."""
        response = api_client.get('/api/market-data')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'timestamp' in data
        assert 'symbols' in data
        assert 'data' in data
        assert 'status' in data
        assert data['status'] == 'success'
    
    def test_market_data_with_symbols(self, api_client):
        """Test market data endpoint with specific symbols."""
        response = api_client.get('/api/market-data?symbols=AAPL,GOOGL')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'AAPL' in data['symbols']
        assert 'GOOGL' in data['symbols']
        assert 'AAPL' in data['data']
        assert 'GOOGL' in data['data']
    
    def test_market_trends_endpoint(self, api_client):
        """Test market trends endpoint."""
        response = api_client.get('/api/market-trends')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'timestamp' in data
        assert 'trends' in data
        assert 'status' in data
    
    def test_bot_run_endpoint(self, api_client):
        """Test bot execution endpoint."""
        response = api_client.post('/api/bot/run')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'status' in data
        assert 'message' in data
    
    def test_config_endpoint(self, api_client):
        """Test configuration endpoint."""
        response = api_client.get('/api/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'env' in data
        assert 'trading' in data
        assert 'default_symbols' in data['trading']
    
    def test_invalid_endpoint_404(self, api_client):
        """Test that invalid endpoints return 404."""
        response = api_client.get('/api/invalid-endpoint')
        
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data


@pytest.mark.smoke  
class TestAPIErrorHandling:
    """Test API error handling scenarios."""
    
    def test_market_data_invalid_symbols(self, api_client):
        """Test market data with invalid symbols."""
        response = api_client.get('/api/market-data?symbols=INVALID,BADSTOCK')
        
        # Should still return 200 but with error info in data
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'data' in data
    
    def test_empty_symbols_parameter(self, api_client):
        """Test market data with empty symbols parameter."""
        response = api_client.get('/api/market-data?symbols=')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        # Should fall back to default symbols
        assert len(data['symbols']) > 0


@pytest.mark.smoke
class TestAPIResponseStructure:
    """Test API response structure consistency."""
    
    def test_market_data_response_structure(self, api_client):
        """Test market data response has correct structure."""
        response = api_client.get('/api/market-data?symbols=AAPL')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        # Check response structure
        required_fields = ['timestamp', 'symbols', 'data', 'status']
        for field in required_fields:
            assert field in data
        
        # Check data structure for each symbol
        for symbol, symbol_data in data['data'].items():
            if 'error' not in symbol_data:
                expected_fields = ['price', 'volume', 'open', 'high', 'low']
                for field in expected_fields:
                    assert field in symbol_data
    
    def test_status_response_structure(self, api_client):
        """Test status response has correct structure."""
        response = api_client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        required_fields = ['status', 'environment', 'trading_enabled', 'paper_trading']
        for field in required_fields:
            assert field in data
    
    def test_config_response_structure(self, api_client):
        """Test config response has correct structure."""
        response = api_client.get('/api/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert 'env' in data
        assert 'trading' in data
        
        trading_config = data['trading']
        required_trading_fields = ['default_symbols', 'paper_trading', 'trading_enabled']
        for field in required_trading_fields:
            assert field in trading_config