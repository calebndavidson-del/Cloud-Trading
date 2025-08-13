"""
Unit tests for the enhanced analytics modules.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
import asyncio

from analytics.spread_monitor import SpreadMonitor
from analytics.liquidity_predictor import LiquidityPredictor
from analytics.tail_risk_analyzer import TailRiskAnalyzer


class TestSpreadMonitor:
    """Test cases for SpreadMonitor class."""
    
    @pytest.fixture
    def spread_config(self):
        """Configuration for spread monitor tests."""
        return {
            'symbols': ['AAPL', 'GOOGL', 'MSFT'],
            'window_size': 50,
            'alert_thresholds': {
                'default': {
                    'max_spread_pct': 0.5,
                    'min_liquidity_score': 40
                }
            },
            'update_interval': 1.0
        }
    
    @pytest.fixture
    def spread_monitor(self, spread_config):
        """Create SpreadMonitor instance for testing."""
        return SpreadMonitor(spread_config)
    
    def test_initialization(self, spread_monitor, spread_config):
        """Test SpreadMonitor initialization."""
        assert spread_monitor.symbols == spread_config['symbols']
        assert spread_monitor.window_size == spread_config['window_size']
        assert spread_monitor.update_interval == spread_config['update_interval']
        assert not spread_monitor.is_monitoring
        assert len(spread_monitor.spread_history) == 0
    
    def test_enhance_quote_with_spread_data(self, spread_monitor):
        """Test quote enhancement with bid/ask data."""
        # Test quote without bid/ask
        quote = {
            'price': 150.0,
            'regularMarketPrice': 150.0,
            'regularMarketVolume': 1000000,
            'regularMarketDayHigh': 152.0,
            'regularMarketDayLow': 148.0
        }
        
        enhanced_quote = asyncio.run(
            spread_monitor._enhance_quote_with_spread_data('AAPL', quote)
        )
        
        assert 'bid' in enhanced_quote
        assert 'ask' in enhanced_quote
        assert 'spread' in enhanced_quote
        assert 'spread_pct' in enhanced_quote
        assert enhanced_quote['ask'] > enhanced_quote['bid']
        assert enhanced_quote['spread'] == enhanced_quote['ask'] - enhanced_quote['bid']
    
    def test_spread_percentage_estimation(self, spread_monitor):
        """Test spread percentage estimation logic."""
        # High price stock (should have lower spread)
        high_price_quote = {'regularMarketVolume': 1000000, 'regularMarketDayHigh': 505, 'regularMarketDayLow': 495}
        high_price_spread = spread_monitor._estimate_spread_percentage('AAPL', 500.0, high_price_quote)
        
        # Low price stock (should have higher spread)
        low_price_quote = {'regularMarketVolume': 100000, 'regularMarketDayHigh': 5.2, 'regularMarketDayLow': 4.8}
        low_price_spread = spread_monitor._estimate_spread_percentage('PENNY', 5.0, low_price_quote)
        
        assert low_price_spread > high_price_spread
        assert high_price_spread > 0
        assert low_price_spread <= 0.5  # Should not exceed cap
    
    def test_process_quote(self, spread_monitor):
        """Test quote processing and spread calculation."""
        quote = {
            'bid': 149.50,
            'ask': 150.50,
            'price': 150.00,
            'timestamp': datetime.now().timestamp()
        }
        
        spread_monitor._process_quote('AAPL', quote)
        
        assert len(spread_monitor.spread_history['AAPL']) == 1
        spread_data = spread_monitor.spread_history['AAPL'][0]
        
        assert spread_data['spread'] == 1.0
        assert abs(spread_data['spread_pct'] - (1.0/150.0*100)) < 0.001
        assert spread_data['mid_price'] == 150.0
    
    def test_liquidity_score_calculation(self, spread_monitor):
        """Test liquidity score calculation."""
        # Add some spread data
        for i in range(10):
            quote = {
                'bid': 149.90 + i * 0.01,
                'ask': 150.10 + i * 0.01,
                'price': 150.00 + i * 0.01,
                'timestamp': datetime.now().timestamp()
            }
            spread_monitor._process_quote('AAPL', quote)
        
        spread_monitor._update_spread_metrics('AAPL')
        liquidity_score = spread_monitor._calculate_liquidity_score('AAPL')
        
        assert 0 <= liquidity_score <= 100
        assert isinstance(liquidity_score, float)
    
    def test_market_impact_cost_estimation(self, spread_monitor):
        """Test market impact cost estimation."""
        # Add spread data
        quote = {
            'bid': 149.95,
            'ask': 150.05,
            'price': 150.00,
            'timestamp': datetime.now().timestamp()
        }
        spread_monitor._process_quote('AAPL', quote)
        spread_monitor._update_spread_metrics('AAPL')
        
        impact_cost = spread_monitor._estimate_market_impact_cost('AAPL')
        
        assert impact_cost >= 0
        assert impact_cost <= 50  # Should not exceed cap
    
    def test_trading_cost_estimate(self, spread_monitor):
        """Test trading cost estimation."""
        # Add spread data
        quote = {
            'bid': 149.90,
            'ask': 150.10,
            'price': 150.00,
            'timestamp': datetime.now().timestamp()
        }
        spread_monitor._process_quote('AAPL', quote)
        spread_monitor._update_spread_metrics('AAPL')
        
        cost_estimate = spread_monitor.calculate_trading_cost_estimate('AAPL', 10000)
        
        assert 'trade_size' in cost_estimate
        assert 'total_cost_bp' in cost_estimate
        assert 'total_cost_dollar' in cost_estimate
        assert cost_estimate['trade_size'] == 10000
        assert cost_estimate['total_cost_dollar'] >= 0
    
    def test_spread_trend_calculation(self, spread_monitor):
        """Test spread trend detection."""
        # Widening spreads
        widening_spreads = [0.1, 0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.28, 0.30, 0.35]
        trend = spread_monitor._calculate_spread_trend(widening_spreads)
        assert trend == 'widening'
        
        # Tightening spreads
        tightening_spreads = [0.30, 0.28, 0.25, 0.22, 0.20, 0.18, 0.15, 0.12, 0.10, 0.08]
        trend = spread_monitor._calculate_spread_trend(tightening_spreads)
        assert trend == 'tightening'
        
        # Stable spreads
        stable_spreads = [0.20] * 10
        trend = spread_monitor._calculate_spread_trend(stable_spreads)
        assert trend == 'stable'


class TestLiquidityPredictor:
    """Test cases for LiquidityPredictor class."""
    
    @pytest.fixture
    def liquidity_config(self):
        """Configuration for liquidity predictor tests."""
        return {
            'symbols': ['AAPL', 'GOOGL'],
            'prediction_horizon': 5,
            'feature_window': 30,
            'model_type': 'rf',
            'retrain_interval': 60
        }
    
    @pytest.fixture
    def liquidity_predictor(self, liquidity_config):
        """Create LiquidityPredictor instance for testing."""
        return LiquidityPredictor(liquidity_config)
    
    def test_initialization(self, liquidity_predictor, liquidity_config):
        """Test LiquidityPredictor initialization."""
        assert liquidity_predictor.symbols == liquidity_config['symbols']
        assert liquidity_predictor.prediction_horizon == liquidity_config['prediction_horizon']
        assert liquidity_predictor.model_type == liquidity_config['model_type']
        assert len(liquidity_predictor.models) == 0
    
    def test_model_creation(self, liquidity_predictor):
        """Test ML model creation."""
        # Test Random Forest model
        liquidity_predictor.model_type = 'rf'
        model = liquidity_predictor._create_model()
        assert hasattr(model, 'fit')
        assert hasattr(model, 'predict')
        
        # Test Gradient Boosting model
        liquidity_predictor.model_type = 'gb'
        model = liquidity_predictor._create_model()
        assert hasattr(model, 'fit')
        assert hasattr(model, 'predict')
        
        # Test ensemble model
        liquidity_predictor.model_type = 'ensemble'
        model = liquidity_predictor._create_model()
        assert isinstance(model, dict)
        assert 'rf' in model
        assert 'gb' in model
    
    def test_feature_extraction(self, liquidity_predictor):
        """Test feature extraction from market data."""
        # Create mock data
        spread_data = [
            {'spread_pct': 0.1, 'timestamp': datetime.now()},
            {'spread_pct': 0.12, 'timestamp': datetime.now()},
            {'spread_pct': 0.08, 'timestamp': datetime.now()}
        ]
        
        order_flow_data = [
            {'total_volume': 1000000, 'order_imbalance': 0.1, 'price_impact': 0.001},
            {'total_volume': 1200000, 'order_imbalance': -0.05, 'price_impact': -0.0005},
            {'total_volume': 900000, 'order_imbalance': 0.2, 'price_impact': 0.002}
        ]
        
        market_data = [
            {'price': 150.0, 'volume': 1000000},
            {'price': 151.0, 'volume': 1100000},
            {'price': 149.5, 'volume': 950000}
        ]
        
        features = liquidity_predictor._extract_features(spread_data, order_flow_data, market_data)
        
        assert len(features) > 0
        assert isinstance(features, list)
        assert all(isinstance(f, (int, float, bool)) for f in features)
    
    def test_liquidity_target_calculation(self, liquidity_predictor):
        """Test liquidity target calculation."""
        spread_data = {'spread_pct': 0.1}
        target = liquidity_predictor._calculate_liquidity_target(spread_data)
        
        assert 0 <= target <= 100
        assert isinstance(target, float)
        
        # Lower spreads should give higher liquidity scores
        low_spread_data = {'spread_pct': 0.05}
        high_spread_data = {'spread_pct': 0.20}
        
        low_target = liquidity_predictor._calculate_liquidity_target(low_spread_data)
        high_target = liquidity_predictor._calculate_liquidity_target(high_spread_data)
        
        assert low_target > high_target
    
    def test_order_flow_simulation(self, liquidity_predictor):
        """Test order flow data simulation."""
        order_flow = liquidity_predictor._simulate_order_flow_data('AAPL')
        
        required_fields = ['timestamp', 'total_volume', 'buy_volume', 'sell_volume', 
                          'trade_count', 'avg_trade_size', 'price_impact', 'order_imbalance']
        
        for field in required_fields:
            assert field in order_flow
        
        assert order_flow['buy_volume'] + order_flow['sell_volume'] == order_flow['total_volume']
        assert -1 <= order_flow['order_imbalance'] <= 1
        assert order_flow['trade_count'] >= 1
    
    def test_prediction_confidence_calculation(self, liquidity_predictor):
        """Test prediction confidence calculation."""
        # Add some mock prediction history
        for i in range(10):
            prediction = {
                'predicted_liquidity_score': 70 + np.random.normal(0, 5),
                'timestamp': datetime.now()
            }
            liquidity_predictor.prediction_history['AAPL'].append(prediction)
        
        confidence = liquidity_predictor._calculate_prediction_confidence('AAPL')
        
        assert 0 <= confidence <= 1
        assert isinstance(confidence, float)
    
    def test_optimal_trade_timing(self, liquidity_predictor):
        """Test optimal trade timing prediction."""
        # Add mock current prediction
        liquidity_predictor.current_predictions['AAPL'] = {
            'predicted_liquidity_score': 75,
            'confidence': 0.8,
            'liquidity_trend': 'improving'
        }
        
        timing_rec = liquidity_predictor.predict_optimal_trade_timing('AAPL', 10000)
        
        assert 'timing_recommendation' in timing_rec
        assert 'reason' in timing_rec
        assert 'estimated_cost_bp' in timing_rec
        assert 'estimated_cost_dollar' in timing_rec
        assert timing_rec['trade_size'] == 10000


class TestTailRiskAnalyzer:
    """Test cases for TailRiskAnalyzer class."""
    
    @pytest.fixture
    def risk_config(self):
        """Configuration for tail risk analyzer tests."""
        return {
            'confidence_levels': [0.95, 0.99],
            'lookback_periods': [30, 90],
            'portfolio_value': 1000000,
            'stress_scenarios': {},
            'update_frequency': 15
        }
    
    @pytest.fixture
    def risk_analyzer(self, risk_config):
        """Create TailRiskAnalyzer instance for testing."""
        return TailRiskAnalyzer(risk_config)
    
    @pytest.fixture
    def sample_returns(self):
        """Generate sample return data for testing."""
        np.random.seed(42)
        returns = np.random.normal(0.001, 0.02, 100)  # 100 days of returns
        # Add some extreme events
        returns[10] = -0.08  # -8% return
        returns[50] = -0.12  # -12% return
        returns[80] = 0.06   # +6% return
        return returns
    
    def test_initialization(self, risk_analyzer, risk_config):
        """Test TailRiskAnalyzer initialization."""
        assert risk_analyzer.confidence_levels == risk_config['confidence_levels']
        assert risk_analyzer.portfolio_value == risk_config['portfolio_value']
        assert len(risk_analyzer.var_estimates) == 0
        assert len(risk_analyzer.price_history) == 0
    
    def test_market_data_update(self, risk_analyzer):
        """Test market data updating."""
        price_data = {
            'price': 150.0,
            'timestamp': datetime.now()
        }
        
        risk_analyzer.update_market_data('AAPL', price_data)
        
        assert len(risk_analyzer.price_history['AAPL']) == 1
        assert risk_analyzer.price_history['AAPL'][0]['price'] == 150.0
        
        # Add second price to generate return
        price_data2 = {
            'price': 153.0,
            'timestamp': datetime.now()
        }
        
        risk_analyzer.update_market_data('AAPL', price_data2)
        
        assert len(risk_analyzer.return_history['AAPL']) == 1
        return_val = risk_analyzer.return_history['AAPL'][0]['return']
        expected_return = (153.0 - 150.0) / 150.0
        assert abs(return_val - expected_return) < 0.0001
    
    def test_portfolio_value_update(self, risk_analyzer):
        """Test portfolio value updating."""
        positions = {'AAPL': 500000, 'GOOGL': 300000, 'MSFT': 200000}
        
        risk_analyzer.update_portfolio_value(1000000, positions)
        
        assert len(risk_analyzer.portfolio_history) == 1
        assert risk_analyzer.portfolio_history[0]['value'] == 1000000
        assert risk_analyzer.portfolio_history[0]['positions'] == positions
    
    def test_basic_statistics_calculation(self, risk_analyzer, sample_returns):
        """Test basic statistics calculation."""
        stats = risk_analyzer._calculate_basic_statistics(sample_returns)
        
        required_stats = ['mean', 'std', 'skewness', 'kurtosis', 'min', 'max', 'median', 'iqr']
        for stat in required_stats:
            assert stat in stats
            assert isinstance(stats[stat], float)
        
        assert stats['min'] <= stats['median'] <= stats['max']
        assert stats['std'] > 0
    
    def test_historical_var_calculation(self, risk_analyzer, sample_returns):
        """Test historical VaR calculation."""
        var_95 = risk_analyzer._calculate_historical_var(sample_returns, 0.95)
        var_99 = risk_analyzer._calculate_historical_var(sample_returns, 0.99)
        
        assert var_95 > 0  # VaR should be positive (loss amount)
        assert var_99 > var_95  # 99% VaR should be higher than 95% VaR
        assert isinstance(var_95, float)
        assert isinstance(var_99, float)
    
    def test_parametric_var_calculation(self, risk_analyzer, sample_returns):
        """Test parametric VaR calculation."""
        var_normal = risk_analyzer._calculate_parametric_var(sample_returns, 0.95, 'normal')
        var_t = risk_analyzer._calculate_parametric_var(sample_returns, 0.95, 't')
        
        assert var_normal > 0
        assert var_t > 0
        assert isinstance(var_normal, float)
        assert isinstance(var_t, float)
    
    def test_monte_carlo_var_calculation(self, risk_analyzer, sample_returns):
        """Test Monte Carlo VaR calculation."""
        var_mc = risk_analyzer._calculate_monte_carlo_var(sample_returns, 0.95, n_simulations=1000)
        
        assert var_mc > 0
        assert isinstance(var_mc, float)
    
    def test_cvar_calculation(self, risk_analyzer, sample_returns):
        """Test CVaR (Expected Shortfall) calculation."""
        cvar_estimates = risk_analyzer._calculate_cvar_multiple_methods(sample_returns, 0.95)
        
        assert 'historical' in cvar_estimates
        assert 'parametric_normal' in cvar_estimates
        
        # CVaR should be >= VaR
        var_95 = risk_analyzer._calculate_historical_var(sample_returns, 0.95)
        assert cvar_estimates['historical'] >= var_95
    
    def test_drawdown_calculation(self, risk_analyzer):
        """Test drawdown calculation."""
        # Create price series with drawdown
        prices = [100, 105, 110, 95, 90, 88, 92, 98, 102, 108]
        
        for i, price in enumerate(prices):
            risk_analyzer.price_history['TEST'].append({
                'price': price,
                'timestamp': datetime.now() + timedelta(days=i)
            })
        
        drawdown_metrics = risk_analyzer._calculate_drawdown_metrics('TEST')
        
        assert 'max_drawdown' in drawdown_metrics
        assert 'current_drawdown' in drawdown_metrics
        assert drawdown_metrics['max_drawdown'] < 0  # Should be negative
        assert isinstance(drawdown_metrics['max_drawdown'], float)
    
    def test_extreme_value_theory_metrics(self, risk_analyzer, sample_returns):
        """Test Extreme Value Theory metrics calculation."""
        evt_metrics = risk_analyzer._calculate_evt_metrics(sample_returns)
        
        if evt_metrics.get('status') != 'insufficient_data':
            assert 'shape_parameter' in evt_metrics
            assert 'scale_parameter' in evt_metrics
            assert 'threshold' in evt_metrics
    
    def test_tail_metrics_calculation(self, risk_analyzer, sample_returns):
        """Test tail metrics calculation."""
        tail_metrics = risk_analyzer._calculate_tail_metrics(sample_returns)
        
        required_metrics = ['left_tail_mean_5pct', 'left_tail_mean_1pct', 
                           'tail_ratio_5pct', 'beyond_var_95_count']
        
        for metric in required_metrics:
            assert metric in tail_metrics
    
    def test_stress_testing(self, risk_analyzer):
        """Test stress testing functionality."""
        # Add some portfolio data
        risk_analyzer.update_portfolio_value(1000000)
        
        # Test market shock scenario
        shock_result = risk_analyzer._scenario_test(-0.20)
        
        assert 'scenario' in shock_result
        assert 'shocked_value' in shock_result
        assert 'loss_amount' in shock_result
        assert shock_result['shocked_value'] < risk_analyzer.portfolio_value
    
    def test_risk_level_assessment(self, risk_analyzer):
        """Test overall risk level assessment."""
        # Mock some risk metrics
        risk_analyzer.tail_risk_summary = {
            'portfolio': {
                'var_estimates': {'95.0%': {'historical': 0.03}},
                'drawdown_analysis': {'current_drawdown': -0.02}
            }
        }
        
        risk_level = risk_analyzer._assess_overall_risk_level()
        
        assert risk_level in ['very_low', 'low', 'medium', 'high']
    
    def test_comprehensive_risk_calculation(self, risk_analyzer, sample_returns):
        """Test comprehensive risk metrics calculation."""
        # Add some market data
        for i, ret in enumerate(sample_returns[:50]):  # Use first 50 returns
            price = 100 * (1 + ret)  # Convert return to price
            risk_analyzer.update_market_data('AAPL', {
                'price': price,
                'timestamp': datetime.now() + timedelta(days=i)
            })
        
        # Add portfolio data
        for i in range(30):
            portfolio_value = 1000000 * (1 + sample_returns[i])
            risk_analyzer.update_portfolio_value(portfolio_value)
        
        # Calculate comprehensive metrics
        results = risk_analyzer.calculate_comprehensive_risk_metrics()
        
        assert 'timestamp' in results
        assert 'individual_assets' in results
        assert 'portfolio' in results
        assert 'stress_tests' in results
        assert 'risk_alerts' in results
        
        if 'AAPL' in results['individual_assets']:
            asset_metrics = results['individual_assets']['AAPL']
            assert 'var_estimates' in asset_metrics
            assert 'cvar_estimates' in asset_metrics
            assert 'drawdown_analysis' in asset_metrics


@pytest.mark.integration
class TestAnalyticsIntegration:
    """Integration tests for analytics modules working together."""
    
    @pytest.fixture
    def mock_market_data_manager(self):
        """Mock market data manager for integration tests."""
        manager = Mock()
        manager.fetch_quotes = AsyncMock(return_value={
            'AAPL': {
                'price': 150.0,
                'regularMarketPrice': 150.0,
                'regularMarketVolume': 1000000,
                'regularMarketDayHigh': 152.0,
                'regularMarketDayLow': 148.0,
                'timestamp': datetime.now().timestamp()
            }
        })
        return manager
    
    @pytest.fixture
    def integrated_analytics_system(self, mock_market_data_manager):
        """Create integrated analytics system for testing."""
        spread_config = {
            'symbols': ['AAPL'],
            'window_size': 20,
            'alert_thresholds': {'default': {'max_spread_pct': 0.5}},
            'update_interval': 1.0
        }
        
        liquidity_config = {
            'symbols': ['AAPL'],
            'prediction_horizon': 5,
            'model_type': 'rf'
        }
        
        risk_config = {
            'confidence_levels': [0.95],
            'portfolio_value': 1000000
        }
        
        spread_monitor = SpreadMonitor(spread_config)
        liquidity_predictor = LiquidityPredictor(liquidity_config)
        risk_analyzer = TailRiskAnalyzer(risk_config)
        
        return {
            'spread_monitor': spread_monitor,
            'liquidity_predictor': liquidity_predictor,
            'risk_analyzer': risk_analyzer,
            'market_data_manager': mock_market_data_manager
        }
    
    @pytest.mark.asyncio
    async def test_spread_to_liquidity_integration(self, integrated_analytics_system):
        """Test integration between spread monitoring and liquidity prediction."""
        spread_monitor = integrated_analytics_system['spread_monitor']
        liquidity_predictor = integrated_analytics_system['liquidity_predictor']
        
        # Simulate spread monitoring updates
        for i in range(15):
            quote = {
                'bid': 149.90 + i * 0.002,
                'ask': 150.10 + i * 0.002,
                'price': 150.00 + i * 0.002,
                'timestamp': datetime.now().timestamp()
            }
            spread_monitor._process_quote('AAPL', quote)
        
        spread_monitor._update_spread_metrics('AAPL')
        
        # Test that liquidity predictor can access spread data
        liquidity_predictor.spread_monitor = spread_monitor
        
        # Simulate data collection
        await liquidity_predictor._collect_microstructure_data('AAPL')
        
        assert len(liquidity_predictor.spread_data_history['AAPL']) > 0
        assert len(liquidity_predictor.order_flow_history['AAPL']) > 0
    
    def test_risk_analyzer_with_market_data(self, integrated_analytics_system):
        """Test risk analyzer with market data from spread monitor."""
        risk_analyzer = integrated_analytics_system['risk_analyzer']
        
        # Simulate price updates
        prices = [100, 102, 99, 95, 98, 103, 101, 97, 105, 108]
        
        for price in prices:
            risk_analyzer.update_market_data('AAPL', {
                'price': price,
                'timestamp': datetime.now()
            })
        
        # Calculate risk metrics
        results = risk_analyzer.calculate_comprehensive_risk_metrics()
        
        assert 'individual_assets' in results
        if 'AAPL' in results['individual_assets']:
            assert 'var_estimates' in results['individual_assets']['AAPL']
    
    def test_analytics_data_flow(self, integrated_analytics_system):
        """Test complete data flow through all analytics modules."""
        spread_monitor = integrated_analytics_system['spread_monitor']
        risk_analyzer = integrated_analytics_system['risk_analyzer']
        
        # Simulate market data flow
        market_data = {
            'AAPL': {
                'price': 150.0,
                'bid': 149.95,
                'ask': 150.05,
                'volume': 1000000
            }
        }
        
        # Update spread monitor
        spread_monitor._process_quote('AAPL', market_data['AAPL'])
        
        # Update risk analyzer
        risk_analyzer.update_market_data('AAPL', market_data['AAPL'])
        
        # Verify data is flowing correctly
        assert len(spread_monitor.spread_history['AAPL']) == 1
        assert len(risk_analyzer.price_history['AAPL']) == 1
        
        # Check that both modules can generate insights
        spread_monitor._update_spread_metrics('AAPL')
        spread_summary = spread_monitor.get_liquidity_summary()
        
        risk_dashboard = risk_analyzer.get_risk_dashboard_summary()
        
        assert 'symbols_monitored' in spread_summary
        assert 'portfolio_value' in risk_dashboard


if __name__ == '__main__':
    pytest.main([__file__])