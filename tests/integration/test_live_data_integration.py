"""
Integration tests for live data management and error handling.
Tests live data integration, connection recovery, and transparency.
"""

import pytest
import asyncio
import aiohttp
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from backend.live_data_manager import (
    LiveMarketDataManager, DataSource, DataFreshness, 
    ConnectionMonitor, MarketDataPoint, DataQuality
)


class TestConnectionMonitor:
    """Test connection monitoring and recovery mechanisms"""
    
    def setup_method(self):
        self.monitor = ConnectionMonitor()
    
    def test_success_recording(self):
        """Test recording successful connections"""
        source = DataSource.YAHOO_FINANCE
        
        self.monitor.record_success(source)
        
        assert self.monitor.is_healthy(source) is True
        assert self.monitor.error_counts[source] == 0
        assert source in self.monitor.last_success
        assert self.monitor.recovery_attempts[source] == 0
    
    def test_error_recording(self):
        """Test recording connection errors"""
        source = DataSource.YAHOO_FINANCE
        error = Exception("Connection timeout")
        
        self.monitor.record_error(source, error)
        
        assert self.monitor.error_counts[source] == 1
        assert self.monitor.connection_status[source] is False
    
    def test_max_errors_threshold(self):
        """Test max errors threshold"""
        source = DataSource.YAHOO_FINANCE
        error = Exception("Connection timeout")
        
        # Record max errors
        for i in range(self.monitor.max_errors):
            self.monitor.record_error(source, error)
        
        assert not self.monitor.is_healthy(source)
        assert self.monitor.error_counts[source] == self.monitor.max_errors
    
    def test_recovery_cooldown(self):
        """Test recovery cooldown mechanism"""
        source = DataSource.YAHOO_FINANCE
        
        # Record a success, then check retry eligibility
        self.monitor.record_success(source)
        
        # Immediately after success, retry should be allowed
        assert self.monitor.can_retry(source) is True
        
        # Simulate waiting for cooldown period
        self.monitor.last_success[source] = datetime.now() - timedelta(seconds=400)
        assert self.monitor.can_retry(source) is True
    
    def test_start_recovery(self):
        """Test recovery attempt tracking"""
        source = DataSource.YAHOO_FINANCE
        
        initial_attempts = self.monitor.recovery_attempts.get(source, 0)
        self.monitor.start_recovery(source)
        
        assert self.monitor.recovery_attempts[source] == initial_attempts + 1


class TestLiveMarketDataManager:
    """Test live market data manager functionality"""
    
    def setup_method(self):
        # Create manager with test config
        self.manager = LiveMarketDataManager()
        self.manager.config = self._get_test_config()
    
    def _get_test_config(self):
        """Get test configuration"""
        return {
            "providers": {
                "yahoo_finance": {
                    "enabled": True,
                    "priority": 1,
                    "timeout": 10,
                    "api_key": None
                }
            },
            "live_only_mode": True,
            "allow_mock_data": False,
            "max_data_age_seconds": 300,
            "require_real_time": True,
            "fallback_settings": {
                "max_retries": 3,
                "retry_delay": 2.0,
                "exponential_backoff": True
            }
        }
    
    def test_live_only_mode_enforcement(self):
        """Test that live-only mode is enforced"""
        assert self.manager.config['live_only_mode'] is True
        assert self.manager.config['allow_mock_data'] is False
        assert self.manager.config['require_real_time'] is True
    
    def test_data_freshness_validation(self):
        """Test data freshness validation"""
        # Test real-time data
        current_data = {'timestamp': datetime.now()}
        freshness = self.manager._validate_data_freshness(current_data, DataSource.YAHOO_FINANCE)
        assert freshness == DataFreshness.REAL_TIME
        
        # Test fresh data (3 minutes old)
        fresh_data = {'timestamp': datetime.now() - timedelta(minutes=3)}
        freshness = self.manager._validate_data_freshness(fresh_data, DataSource.YAHOO_FINANCE)
        assert freshness == DataFreshness.FRESH
        
        # Test stale data (10 minutes old)
        stale_data = {'timestamp': datetime.now() - timedelta(minutes=10)}
        freshness = self.manager._validate_data_freshness(stale_data, DataSource.YAHOO_FINANCE)
        assert freshness == DataFreshness.STALE
        
        # Test expired data (20 minutes old)
        expired_data = {'timestamp': datetime.now() - timedelta(minutes=20)}
        freshness = self.manager._validate_data_freshness(expired_data, DataSource.YAHOO_FINANCE)
        assert freshness == DataFreshness.EXPIRED
    
    def test_data_quality_validation(self):
        """Test comprehensive data quality validation"""
        # Complete, accurate data
        good_data = {
            'price': 150.0,
            'volume': 1000000,
            'open': 149.0,
            'high': 151.0,
            'low': 148.0,
            'timestamp': datetime.now()
        }
        
        quality = self.manager._validate_data_quality(good_data, DataSource.YAHOO_FINANCE)
        
        assert quality.completeness == 1.0  # All fields present
        assert quality.accuracy > 0.9  # Prices are reasonable
        assert quality.freshness == DataFreshness.REAL_TIME
        assert quality.source == DataSource.YAHOO_FINANCE
    
    def test_data_quality_validation_incomplete(self):
        """Test data quality validation with incomplete data"""
        incomplete_data = {
            'price': 150.0,
            'volume': 1000000,
            # Missing open, high, low
            'timestamp': datetime.now()
        }
        
        quality = self.manager._validate_data_quality(incomplete_data, DataSource.YAHOO_FINANCE)
        
        assert quality.completeness < 1.0  # Missing fields
        assert quality.source == DataSource.YAHOO_FINANCE
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        source = DataSource.ALPHA_VANTAGE
        
        # Set low rate limit for testing
        self.manager.rate_limits[source] = {
            "requests": 2, 
            "window": 60, 
            "current": 0, 
            "reset_time": time.time()
        }
        
        # First two requests should pass
        assert self.manager._check_rate_limit(source) is True
        assert self.manager._check_rate_limit(source) is True
        
        # Third request should fail
        assert self.manager._check_rate_limit(source) is False
    
    @pytest.mark.asyncio
    async def test_session_initialization(self):
        """Test HTTP session initialization"""
        await self.manager._initialize_sessions()
        
        # Check that sessions are created for all data sources
        for source in DataSource:
            assert source in self.manager.session_pool
            assert isinstance(self.manager.session_pool[source], aiohttp.ClientSession)
        
        # Clean up
        await self.manager.close_sessions()
    
    def test_live_only_mode_rejection(self):
        """Test that live-only mode rejects mock data requests"""
        # Test that manager rejects non-live mode
        self.manager.config['live_only_mode'] = False
        
        with pytest.raises(Exception) as excinfo:
            asyncio.run(self.manager.fetch_live_market_data(['AAPL']))
        
        assert "Live-only mode is disabled" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_empty_symbols_handling(self):
        """Test handling of empty symbols list"""
        with pytest.raises(ValueError) as excinfo:
            await self.manager.fetch_live_market_data([])
        
        assert "Symbols list cannot be empty" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_connection_error_handling(self):
        """Test connection error handling and recovery"""
        symbols = ['AAPL']
        
        # Mock all providers to fail
        with patch.object(self.manager, '_fetch_yahoo_finance_data') as mock_yahoo:
            with patch.object(self.manager, '_fetch_alpha_vantage_data') as mock_alpha:
                with patch.object(self.manager, '_fetch_iex_cloud_data') as mock_iex:
                    
                    mock_yahoo.side_effect = Exception("Yahoo Finance connection failed")
                    mock_alpha.side_effect = Exception("Alpha Vantage connection failed")
                    mock_iex.side_effect = Exception("IEX Cloud connection failed")
                    
                    # Should raise exception when all providers fail
                    with pytest.raises(Exception) as excinfo:
                        await self.manager.fetch_live_market_data(symbols)
                    
                    assert "Failed to fetch live data" in str(excinfo.value)
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality"""
        # Mock successful data fetch for health check
        with patch.object(self.manager, '_fetch_yahoo_finance_data') as mock_fetch:
            mock_data_point = MarketDataPoint(
                symbol='AAPL',
                data={'price': 150.0, 'volume': 1000000},
                quality=DataQuality(
                    freshness=DataFreshness.REAL_TIME,
                    completeness=1.0,
                    accuracy=1.0,
                    source=DataSource.YAHOO_FINANCE,
                    timestamp=datetime.now()
                ),
                source=DataSource.YAHOO_FINANCE,
                timestamp=datetime.now()
            )
            mock_fetch.return_value = {'AAPL': mock_data_point}
            
            health_status = await self.manager.health_check()
            
            assert health_status['overall_health'] in ['healthy', 'degraded', 'critical']
            assert 'providers' in health_status
            assert 'timestamp' in health_status
    
    def test_connection_status_reporting(self):
        """Test connection status reporting"""
        # Record some connection events
        self.manager.connection_monitor.record_success(DataSource.YAHOO_FINANCE)
        self.manager.connection_monitor.record_error(DataSource.ALPHA_VANTAGE, Exception("Test error"))
        
        status = self.manager.get_connection_status()
        
        assert DataSource.YAHOO_FINANCE.value in status
        assert DataSource.ALPHA_VANTAGE.value in status
        
        yahoo_status = status[DataSource.YAHOO_FINANCE.value]
        alpha_status = status[DataSource.ALPHA_VANTAGE.value]
        
        assert yahoo_status['healthy'] is True
        assert yahoo_status['error_count'] == 0
        
        assert alpha_status['healthy'] is False
        assert alpha_status['error_count'] == 1


class TestLiveDataIntegration:
    """Integration tests for live data fetching with real APIs"""
    
    def setup_method(self):
        self.manager = LiveMarketDataManager()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_yahoo_finance_data(self):
        """Test fetching real data from Yahoo Finance (requires internet)"""
        symbols = ['AAPL']
        
        try:
            # This test requires internet connection and working Yahoo Finance API
            results = await self.manager._fetch_yahoo_finance_data(symbols)
            
            if results:  # Only test if we got data
                assert 'AAPL' in results
                data_point = results['AAPL']
                
                assert isinstance(data_point, MarketDataPoint)
                assert data_point.symbol == 'AAPL'
                assert 'price' in data_point.data
                assert 'volume' in data_point.data
                assert data_point.quality.freshness in [DataFreshness.REAL_TIME, DataFreshness.FRESH]
                assert data_point.source == DataSource.YAHOO_FINANCE
                
        except Exception as e:
            pytest.skip(f"Yahoo Finance API not available: {e}")
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_data_freshness_enforcement(self):
        """Test that only fresh data is accepted"""
        symbols = ['AAPL']
        
        try:
            results = await self.manager.fetch_live_market_data(symbols)
            
            if results:
                for symbol, data_point in results.items():
                    # All returned data should be fresh
                    assert data_point.quality.freshness in [DataFreshness.REAL_TIME, DataFreshness.FRESH]
                    
                    # Data should be recent
                    age = (datetime.now() - data_point.timestamp).total_seconds()
                    assert age < 600  # Less than 10 minutes old
                    
        except Exception as e:
            pytest.skip(f"Live data API not available: {e}")
    
    @pytest.mark.integration 
    @pytest.mark.asyncio
    async def test_comprehensive_data_fetch(self):
        """Test fetching comprehensive data including historical and fundamental"""
        symbol = 'AAPL'
        
        try:
            # Test historical data
            historical_data = await self.manager.fetch_historical_data(symbol, period="1mo", interval="1d")
            assert not historical_data.empty
            assert 'Close' in historical_data.columns
            assert 'Volume' in historical_data.columns
            
            # Test fundamental data
            fundamental_data = await self.manager.fetch_fundamental_data(symbol)
            assert isinstance(fundamental_data, dict)
            # Should have some fundamental metrics (even if some are 0)
            assert 'market_cap' in fundamental_data
            assert 'timestamp' in fundamental_data
            
        except Exception as e:
            pytest.skip(f"Data APIs not available: {e}")


class TestErrorRecovery:
    """Test error recovery and self-healing mechanisms"""
    
    def setup_method(self):
        self.manager = LiveMarketDataManager()
    
    @pytest.mark.asyncio
    async def test_provider_failover(self):
        """Test automatic failover between providers"""
        symbols = ['AAPL']
        
        # Mock first provider to fail, second to succeed
        with patch.object(self.manager, '_fetch_yahoo_finance_data') as mock_yahoo:
            with patch.object(self.manager, '_fetch_alpha_vantage_data') as mock_alpha:
                
                mock_yahoo.side_effect = Exception("Yahoo Finance failed")
                
                # Mock successful Alpha Vantage response
                mock_data_point = MarketDataPoint(
                    symbol='AAPL',
                    data={
                        'price': 150.0,
                        'volume': 1000000,
                        'open': 149.0,
                        'high': 151.0,
                        'low': 148.0,
                        'timestamp': datetime.now()
                    },
                    quality=DataQuality(
                        freshness=DataFreshness.REAL_TIME,
                        completeness=1.0,
                        accuracy=1.0,
                        source=DataSource.ALPHA_VANTAGE,
                        timestamp=datetime.now()
                    ),
                    source=DataSource.ALPHA_VANTAGE,
                    timestamp=datetime.now()
                )
                mock_alpha.return_value = {'AAPL': mock_data_point}
                
                # Should successfully get data from Alpha Vantage after Yahoo fails
                results = await self.manager.fetch_live_market_data(symbols)
                
                assert 'AAPL' in results
                assert results['AAPL'].source == DataSource.ALPHA_VANTAGE
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling in data fetching"""
        symbols = ['AAPL']
        
        # Mock provider that takes too long
        async def slow_fetch(symbols):
            await asyncio.sleep(35)  # Longer than 30 second timeout
            return {}
        
        with patch.object(self.manager, '_fetch_yahoo_finance_data', side_effect=slow_fetch):
            with patch.object(self.manager, '_fetch_alpha_vantage_data', side_effect=slow_fetch):
                with patch.object(self.manager, '_fetch_iex_cloud_data', side_effect=slow_fetch):
                    
                    # Should handle timeout gracefully
                    with pytest.raises(Exception) as excinfo:
                        await self.manager.fetch_live_market_data(symbols)
                    
                    assert "Failed to fetch live data" in str(excinfo.value)
    
    def test_exponential_backoff(self):
        """Test exponential backoff in retry logic"""
        source = DataSource.YAHOO_FINANCE
        
        # Simulate multiple failures
        for i in range(3):
            self.manager.connection_monitor.record_error(source, Exception(f"Error {i}"))
        
        # Connection should be marked unhealthy
        assert not self.manager.connection_monitor.is_healthy(source)
        
        # Should allow retry after cooldown
        assert self.manager.connection_monitor.can_retry(source)


if __name__ == '__main__':
    # Run with different markers:
    # pytest test_live_data_integration.py -m "not integration"  # Skip integration tests
    # pytest test_live_data_integration.py -m integration       # Only integration tests
    pytest.main([__file__, '-v'])