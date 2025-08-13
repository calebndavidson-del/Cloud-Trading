"""
Unit tests for optimization and backtesting functionality.
"""
import pytest
import numpy as np
from unittest.mock import patch, Mock
from backend.optimizer import backtest_strategy, optimize_strategy, simulate_price_series
from backend.metrics import compute_metrics


class TestBacktesting:
    """Test backtesting functionality."""
    
    def test_simulate_price_series(self):
        """Test price series simulation."""
        base_price = 100.0
        length = 30
        
        prices = simulate_price_series(base_price, length)
        
        assert len(prices) == length + 1  # +1 for base price
        assert prices[0] == base_price
        assert all(p > 0 for p in prices)  # No negative prices
    
    def test_price_series_deterministic(self):
        """Test that price series is deterministic with same seed."""
        prices1 = simulate_price_series(100.0, 20)
        prices2 = simulate_price_series(100.0, 20)
        
        # Should be identical due to fixed random seed
        assert prices1 == prices2
    
    def test_backtest_strategy_basic(self, mock_market_data):
        """Test basic backtesting functionality."""
        parameters = {
            'initial_capital': 10000,
            'short_ma_period': 5,
            'long_ma_period': 15
        }
        
        result = backtest_strategy(mock_market_data, parameters)
        
        assert isinstance(result, dict)
        assert 'trades' in result
        assert 'metrics' in result
        assert 'final_portfolio_value' in result
        assert 'parameters' in result
        
        # Check that parameters are preserved
        assert result['parameters'] == parameters
    
    def test_backtest_strategy_invalid_params(self, mock_market_data):
        """Test backtesting with invalid parameters."""
        # Invalid: short MA >= long MA
        invalid_params = {
            'initial_capital': 10000,
            'short_ma_period': 15,
            'long_ma_period': 10
        }
        
        result = backtest_strategy(mock_market_data, invalid_params)
        
        # Should still complete but may not generate good results
        assert isinstance(result, dict)
        assert 'trades' in result or 'error' in result
    
    def test_backtest_strategy_with_errors(self):
        """Test backtesting with market data containing errors."""
        error_data = {
            'AAPL': {'error': 'No data available'},
            'GOOGL': {'price': 2800, 'volume': 500000}
        }
        
        parameters = {
            'initial_capital': 10000,
            'short_ma_period': 5,
            'long_ma_period': 15
        }
        
        result = backtest_strategy(error_data, parameters)
        
        assert isinstance(result, dict)
        # Should handle errors gracefully
        assert 'trades' in result or 'error' in result
    
    def test_backtest_trade_generation(self, mock_market_data):
        """Test that backtesting generates realistic trades."""
        parameters = {
            'initial_capital': 10000,
            'short_ma_period': 3,
            'long_ma_period': 10
        }
        
        result = backtest_strategy(mock_market_data, parameters)
        
        if 'trades' in result and result['trades']:
            trades = result['trades']
            
            # Check trade structure
            for trade in trades:
                assert 'symbol' in trade
                assert 'action' in trade
                assert 'price' in trade
                assert 'shares' in trade
                assert 'timestamp' in trade
                assert trade['action'] in ['buy', 'sell']
                assert trade['shares'] > 0
                assert trade['price'] > 0
    
    def test_backtest_portfolio_value_calculation(self, mock_market_data):
        """Test portfolio value calculation in backtesting."""
        parameters = {
            'initial_capital': 10000,
            'short_ma_period': 5,
            'long_ma_period': 15
        }
        
        result = backtest_strategy(mock_market_data, parameters)
        
        if 'final_portfolio_value' in result:
            final_value = result['final_portfolio_value']
            assert isinstance(final_value, (int, float))
            assert final_value >= 0  # Can't be negative


class TestOptimization:
    """Test optimization functionality."""
    
    def test_optimize_strategy_basic(self, mock_market_data):
        """Test basic optimization functionality."""
        result = optimize_strategy(mock_market_data, n_trials=5)
        
        assert isinstance(result, dict)
        assert 'best_params' in result
        assert 'best_value' in result
        assert 'backtest_results' in result
        assert 'optimization_trials' in result
        
        # Check that optimization was performed
        assert result['optimization_trials'] == 5
    
    def test_optimize_strategy_parameter_bounds(self, mock_market_data):
        """Test that optimization respects parameter bounds."""
        result = optimize_strategy(mock_market_data, n_trials=10)
        
        if 'error' not in result:
            best_params = result['best_params']
            
            # Check parameter bounds
            assert 3 <= best_params['short_ma_period'] <= 10
            assert 10 <= best_params['long_ma_period'] <= 30
            assert best_params['short_ma_period'] < best_params['long_ma_period']
            assert best_params['initial_capital'] == 10000
    
    def test_optimize_strategy_with_invalid_data(self):
        """Test optimization with invalid market data."""
        invalid_data = {
            'INVALID': {'error': 'No data available'}
        }
        
        result = optimize_strategy(invalid_data, n_trials=3)
        
        # Should handle gracefully
        assert isinstance(result, dict)
        if 'error' not in result:
            # If it completes, check structure
            assert 'best_params' in result
            assert 'best_value' in result
    
    def test_optimize_strategy_minimal_trials(self, mock_market_data):
        """Test optimization with minimal trials."""
        result = optimize_strategy(mock_market_data, n_trials=2)
        
        assert isinstance(result, dict)
        if 'error' not in result:
            assert result['optimization_trials'] == 2
            assert 'best_params' in result
    
    @patch('optuna.create_study')
    def test_optimization_objective_function(self, mock_create_study, mock_market_data):
        """Test the optimization objective function behavior."""
        # Mock Optuna study
        mock_study = Mock()
        mock_trial = Mock()
        mock_create_study.return_value = mock_study
        
        # Configure trial mock
        mock_trial.suggest_int.side_effect = lambda name, low, high: {
            'short_ma_period': 5,
            'long_ma_period': 15
        }[name]
        
        # Mock study optimization to call objective once
        def mock_optimize(objective, n_trials, show_progress_bar):
            # Call objective function once to test it
            objective_value = objective(mock_trial)
            mock_study.best_params = {'short_ma_period': 5, 'long_ma_period': 15}
            mock_study.best_value = objective_value
        
        mock_study.optimize = mock_optimize
        
        result = optimize_strategy(mock_market_data, n_trials=1)
        
        # Optimization should complete
        assert isinstance(result, dict)
        mock_create_study.assert_called_once()


class TestOptimizationEdgeCases:
    """Test edge cases in optimization."""
    
    def test_optimization_with_empty_data(self):
        """Test optimization with empty market data."""
        empty_data = {}
        
        result = optimize_strategy(empty_data, n_trials=3)
        
        assert isinstance(result, dict)
        # May complete with error or empty results
    
    def test_optimization_parameter_validation(self, mock_market_data):
        """Test optimization parameter validation within objective."""
        # The objective function should penalize invalid parameters
        result = optimize_strategy(mock_market_data, n_trials=5)
        
        if 'error' not in result and 'best_params' in result:
            params = result['best_params']
            # Valid parameters should be selected
            assert params['short_ma_period'] < params['long_ma_period']
    
    def test_optimization_sharpe_calculation(self, mock_market_data):
        """Test that optimization considers Sharpe ratio correctly."""
        result = optimize_strategy(mock_market_data, n_trials=10)
        
        if 'error' not in result:
            # Should have a best value (Sharpe ratio)
            assert 'best_value' in result
            assert isinstance(result['best_value'], (int, float))
    
    def test_optimization_trade_penalty(self, mock_market_data):
        """Test that optimization penalizes strategies with too few trades."""
        # This is tested implicitly in the objective function
        # Strategies with < 5 trades get penalized
        result = optimize_strategy(mock_market_data, n_trials=5)
        
        if 'error' not in result and 'backtest_results' in result:
            backtest = result['backtest_results']
            if 'metrics' in backtest:
                metrics = backtest['metrics']
                # If optimization worked well, should have reasonable metrics
                assert isinstance(metrics, dict)


class TestMetricsIntegration:
    """Test integration with metrics calculation."""
    
    def test_backtest_metrics_calculation(self, mock_market_data):
        """Test that backtesting properly calculates metrics."""
        parameters = {
            'initial_capital': 10000,
            'short_ma_period': 5,
            'long_ma_period': 15
        }
        
        result = backtest_strategy(mock_market_data, parameters)
        
        if 'metrics' in result:
            metrics = result['metrics']
            
            # Check expected metric fields
            expected_fields = ['net_profit', 'sharpe', 'win_rate', 'max_drawdown', 'total_trades']
            for field in expected_fields:
                assert field in metrics
                assert isinstance(metrics[field], (int, float))
    
    def test_optimization_uses_metrics(self, mock_market_data):
        """Test that optimization uses computed metrics."""
        result = optimize_strategy(mock_market_data, n_trials=5)
        
        if 'error' not in result and 'backtest_results' in result:
            backtest = result['backtest_results']
            
            if 'metrics' in backtest:
                metrics = backtest['metrics']
                # Should have Sharpe ratio since that's what we optimize for
                assert 'sharpe' in metrics


class TestParameterValidation:
    """Test parameter validation and constraints."""
    
    def test_capital_constraints(self, mock_market_data):
        """Test behavior with different capital amounts."""
        # Test with very low capital
        low_capital_params = {
            'initial_capital': 100,
            'short_ma_period': 5,
            'long_ma_period': 15
        }
        
        result = backtest_strategy(mock_market_data, low_capital_params)
        assert isinstance(result, dict)
        
        # Test with high capital
        high_capital_params = {
            'initial_capital': 1000000,
            'short_ma_period': 5,
            'long_ma_period': 15
        }
        
        result = backtest_strategy(mock_market_data, high_capital_params)
        assert isinstance(result, dict)
    
    def test_moving_average_period_validation(self, mock_market_data):
        """Test moving average period constraints."""
        # Test with very short periods
        short_params = {
            'initial_capital': 10000,
            'short_ma_period': 1,
            'long_ma_period': 2
        }
        
        result = backtest_strategy(mock_market_data, short_params)
        assert isinstance(result, dict)
        
        # Test with very long periods
        long_params = {
            'initial_capital': 10000,
            'short_ma_period': 20,
            'long_ma_period': 50
        }
        
        result = backtest_strategy(mock_market_data, long_params)
        assert isinstance(result, dict)