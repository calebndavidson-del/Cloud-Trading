"""
Unit tests for backend optimizer module.
"""
import pytest
from unittest.mock import Mock, patch
from backend.optimizer import optimize_strategy


class TestOptimizer:
    """Test the strategy optimizer."""
    
    def test_optimize_strategy_success(self, sample_market_data):
        """Test successful strategy optimization."""
        result = optimize_strategy(sample_market_data, n_trials=5)
        
        assert isinstance(result, dict)
        assert 'best_value' in result
        assert 'best_params' in result
        assert 'backtest_results' in result
        assert 'optimization_trials' in result
        assert isinstance(result['best_value'], (int, float))
        assert isinstance(result['best_params'], dict)
    
    def test_optimize_strategy_with_parameters(self, sample_market_data):
        """Test optimization with custom parameters."""
        result = optimize_strategy(sample_market_data, n_trials=10)
        
        assert isinstance(result, dict)
        assert 'best_value' in result
        assert 'best_params' in result
        assert 'backtest_results' in result
    
    def test_optimize_strategy_empty_data(self):
        """Test optimization with empty market data."""
        empty_data = {}
        
        result = optimize_strategy(empty_data, n_trials=5)
        
        # Should handle empty data gracefully
        assert isinstance(result, dict)
    
    def test_optimize_strategy_error_handling(self, sample_market_data):
        """Test error handling in optimization."""
        with patch('optuna.create_study') as mock_study:
            mock_study.side_effect = Exception("Optimization error")
            
            result = optimize_strategy(sample_market_data, n_trials=5)
            
            # Should return error information
            assert isinstance(result, dict)
            assert 'error' in result or 'best_value' in result
    
    @pytest.mark.slow
    def test_optimize_strategy_longer_run(self, sample_market_data):
        """Test optimization with more trials (marked as slow)."""
        result = optimize_strategy(sample_market_data, n_trials=20)
        
        assert isinstance(result, dict)
        assert 'best_value' in result
        assert 'best_params' in result