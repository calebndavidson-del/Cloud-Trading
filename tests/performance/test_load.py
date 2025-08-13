"""
Performance and load tests for the Cloud Trading backend.
"""
import pytest
import time
import threading
import concurrent.futures
from unittest.mock import patch


@pytest.mark.performance
class TestAPIPerformance:
    """Performance tests for API endpoints."""
    
    def test_health_endpoint_response_time(self, api_client):
        """Test health endpoint response time."""
        times = []
        
        for _ in range(10):
            start_time = time.time()
            response = api_client.get('/health')
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"Health endpoint - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
        
        # Health endpoint should be very fast
        assert avg_time < 0.05  # 50ms average
        assert max_time < 0.1   # 100ms max
    
    def test_market_data_endpoint_performance(self, api_client):
        """Test market data endpoint performance."""
        times = []
        
        for _ in range(5):
            start_time = time.time()
            response = api_client.get('/api/market-data?symbols=AAPL,GOOGL,MSFT')
            end_time = time.time()
            
            assert response.status_code == 200
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"Market data endpoint - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
        
        # With mock data, should be fast
        assert avg_time < 1.0   # 1 second average
        assert max_time < 2.0   # 2 seconds max
    
    def test_bot_execution_performance(self, api_client):
        """Test bot execution performance."""
        start_time = time.time()
        response = api_client.post('/api/bot/run')
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        print(f"Bot execution time: {execution_time:.3f}s")
        
        # Bot execution should complete reasonably quickly with mock data
        assert execution_time < 30.0  # 30 seconds max
        assert response.status_code in [200, 500]  # Allow expected errors


@pytest.mark.performance
class TestConcurrentRequests:
    """Test handling of concurrent requests."""
    
    def test_concurrent_health_checks(self, api_client):
        """Test concurrent health check requests."""
        def make_request():
            response = api_client.get('/health')
            return response.status_code, time.time()
        
        num_threads = 10
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(make_request) for _ in range(num_threads)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        status_codes = [result[0] for result in results]
        assert all(code == 200 for code in status_codes)
        
        print(f"Concurrent health checks: {num_threads} requests in {total_time:.3f}s")
        
        # Should handle concurrent requests efficiently
        assert total_time < 2.0  # All requests within 2 seconds
    
    def test_concurrent_market_data_requests(self, api_client):
        """Test concurrent market data requests."""
        def make_request(symbol):
            start = time.time()
            response = api_client.get(f'/api/market-data?symbols={symbol}')
            end = time.time()
            return response.status_code, end - start
        
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request, symbol) for symbol in symbols]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # All requests should succeed
        status_codes = [result[0] for result in results]
        response_times = [result[1] for result in results]
        
        success_count = sum(1 for code in status_codes if code == 200)
        avg_response_time = sum(response_times) / len(response_times)
        
        print(f"Concurrent market data: {success_count}/{len(symbols)} successful, avg time: {avg_response_time:.3f}s")
        
        # Most requests should succeed
        assert success_count >= len(symbols) * 0.8  # At least 80% success rate
    
    def test_mixed_endpoint_load(self, api_client):
        """Test load with mixed endpoint requests."""
        def make_mixed_requests():
            endpoints = [
                '/health',
                '/api/status', 
                '/api/market-data?symbols=AAPL',
                '/api/market-trends',
                '/api/config'
            ]
            
            results = []
            for endpoint in endpoints:
                start = time.time()
                response = api_client.get(endpoint)
                end = time.time()
                results.append((endpoint, response.status_code, end - start))
            
            return results
        
        num_workers = 3
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = [executor.submit(make_mixed_requests) for _ in range(num_workers)]
            all_results = []
            for future in concurrent.futures.as_completed(futures):
                all_results.extend(future.result())
        
        # Analyze results
        success_count = sum(1 for _, status, _ in all_results if status == 200)
        total_requests = len(all_results)
        avg_time = sum(time for _, _, time in all_results) / total_requests
        
        print(f"Mixed load test: {success_count}/{total_requests} successful, avg time: {avg_time:.3f}s")
        
        # Should handle mixed load well
        assert success_count >= total_requests * 0.8  # 80% success rate


@pytest.mark.performance
class TestDataProcessingPerformance:
    """Test performance of data processing components."""
    
    def test_market_data_fetch_performance(self, test_environment):
        """Test market data fetching performance."""
        from backend.data_collector import fetch_market_data
        
        symbol_counts = [1, 5, 10, 20]
        
        for count in symbol_counts:
            symbols = [f'SYMBOL{i}' for i in range(count)]
            
            start_time = time.time()
            result = fetch_market_data(symbols, use_mock=True)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            print(f"Market data fetch ({count} symbols): {processing_time:.3f}s")
            
            # Performance should scale reasonably
            assert processing_time < count * 0.1  # Max 100ms per symbol
            assert isinstance(result, dict)
            assert len(result) == count
    
    def test_optimization_performance(self, test_environment, mock_market_data):
        """Test optimization performance with different trial counts."""
        from backend.optimizer import optimize_strategy
        
        trial_counts = [5, 10, 20]
        
        for trials in trial_counts:
            start_time = time.time()
            result = optimize_strategy(mock_market_data, n_trials=trials)
            end_time = time.time()
            
            optimization_time = end_time - start_time
            
            print(f"Optimization ({trials} trials): {optimization_time:.3f}s")
            
            # Performance should be reasonable
            assert optimization_time < trials * 2.0  # Max 2s per trial
            
            if 'error' not in result:
                assert 'best_params' in result
                assert result['optimization_trials'] == trials
    
    def test_backtesting_performance(self, test_environment, mock_market_data):
        """Test backtesting performance."""
        from backend.optimizer import backtest_strategy
        
        parameters = {
            'initial_capital': 10000,
            'short_ma_period': 5,
            'long_ma_period': 15
        }
        
        # Test multiple runs
        times = []
        for _ in range(5):
            start_time = time.time()
            result = backtest_strategy(mock_market_data, parameters)
            end_time = time.time()
            
            times.append(end_time - start_time)
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"Backtesting - Avg: {avg_time:.3f}s, Max: {max_time:.3f}s")
        
        # Backtesting should be fast with mock data
        assert avg_time < 1.0  # 1 second average
        assert max_time < 2.0  # 2 seconds max
    
    def test_paper_trading_performance(self, test_environment):
        """Test paper trading performance."""
        from backend.paper_trader import paper_trade
        
        params = {
            'initial_capital': 10000,
            'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        }
        
        start_time = time.time()
        result = paper_trade(params)
        end_time = time.time()
        
        trading_time = end_time - start_time
        
        print(f"Paper trading execution: {trading_time:.3f}s")
        
        # Paper trading should be fast with mock data
        assert trading_time < 5.0  # 5 seconds max
        assert 'portfolio_value' in result or 'error' in result


@pytest.mark.performance
@pytest.mark.slow
class TestMemoryUsage:
    """Test memory usage patterns."""
    
    def test_large_data_handling(self, test_environment):
        """Test handling of large datasets."""
        from backend.data_collector import fetch_market_data
        
        # Test with many symbols
        large_symbol_list = [f'STOCK{i:04d}' for i in range(100)]
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        result = fetch_market_data(large_symbol_list, use_mock=True)
        
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = memory_after - memory_before
        
        print(f"Memory usage - Before: {memory_before:.1f}MB, After: {memory_after:.1f}MB, Increase: {memory_increase:.1f}MB")
        
        # Memory increase should be reasonable
        assert memory_increase < 100  # Less than 100MB increase
        assert len(result) == 100
    
    def test_repeated_operations_memory(self, test_environment):
        """Test memory usage over repeated operations."""
        from backend.data_collector import fetch_market_data
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        
        # Record initial memory
        initial_memory = process.memory_info().rss / 1024 / 1024
        
        # Perform repeated operations
        for _ in range(10):
            result = fetch_market_data(['AAPL', 'GOOGL', 'MSFT'], use_mock=True)
            assert len(result) == 3
        
        # Record final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_increase = final_memory - initial_memory
        
        print(f"Memory after repeated operations - Initial: {initial_memory:.1f}MB, Final: {final_memory:.1f}MB, Increase: {memory_increase:.1f}MB")
        
        # Memory should not grow significantly
        assert memory_increase < 50  # Less than 50MB increase


@pytest.mark.performance
class TestScalabilityLimits:
    """Test system behavior at scale limits."""
    
    def test_maximum_concurrent_requests(self, api_client):
        """Test maximum number of concurrent requests."""
        def make_request(request_id):
            start = time.time()
            response = api_client.get('/health')
            end = time.time()
            return request_id, response.status_code, end - start
        
        max_workers = 20
        num_requests = 50
        
        start_time = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(make_request, i) for i in range(num_requests)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        success_count = sum(1 for _, status, _ in results if status == 200)
        avg_response_time = sum(time for _, _, time in results) / len(results)
        
        print(f"Scale test: {success_count}/{num_requests} successful in {total_time:.3f}s, avg response: {avg_response_time:.3f}s")
        
        # Should handle high load reasonably
        assert success_count >= num_requests * 0.7  # 70% success rate at high load
        assert total_time < 10.0  # Complete within 10 seconds
    
    def test_large_symbol_list_limits(self, api_client):
        """Test API behavior with very large symbol lists."""
        # Create very large symbol list
        large_symbols = [f'SYM{i:05d}' for i in range(500)]
        symbol_string = ','.join(large_symbols)
        
        start_time = time.time()
        response = api_client.get(f'/api/market-data?symbols={symbol_string}')
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"Large symbol list ({len(large_symbols)} symbols): {processing_time:.3f}s, status: {response.status_code}")
        
        # Should handle gracefully (may return error or partial data)
        assert response.status_code in [200, 400, 500]
        assert processing_time < 30.0  # Should not hang indefinitely
    
    def test_optimization_trial_limits(self, test_environment, mock_market_data):
        """Test optimization with high trial counts."""
        from backend.optimizer import optimize_strategy
        
        high_trial_count = 100
        
        start_time = time.time()
        result = optimize_strategy(mock_market_data, n_trials=high_trial_count)
        end_time = time.time()
        
        optimization_time = end_time - start_time
        
        print(f"High trial optimization ({high_trial_count} trials): {optimization_time:.3f}s")
        
        # Should complete but may take longer
        assert optimization_time < 300.0  # 5 minutes max
        
        if 'error' not in result:
            assert result['optimization_trials'] == high_trial_count