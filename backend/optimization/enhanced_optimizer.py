"""
Enhanced optimizer that integrates with the comprehensive parameter space.

This module extends the existing optimizer to work with the new parameter space,
providing more sophisticated optimization capabilities for the trading bot.
"""

import optuna
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
import logging
from backend.optimizer import backtest_strategy, simulate_price_series
from backend.optimization.parameter_space import get_parameter_space, TradingParameterSpace

logger = logging.getLogger(__name__)


class EnhancedOptimizer:
    """
    Enhanced optimizer that uses the comprehensive parameter space for 
    more sophisticated trading strategy optimization.
    """
    
    def __init__(self, parameter_categories: Optional[List[str]] = None):
        """
        Initialize the enhanced optimizer.
        
        Args:
            parameter_categories: List of parameter categories to optimize.
                                If None, uses all categories.
        """
        self.param_space = get_parameter_space()
        self.parameter_categories = parameter_categories
        self.optimization_history = []
    
    def optimize_strategy(self, 
                         market_data: Dict[str, Any], 
                         n_trials: int = 100,
                         categories: Optional[List[str]] = None,
                         objective_metric: str = 'sharpe',
                         **optuna_kwargs) -> Dict[str, Any]:
        """
        Optimize strategy parameters using the comprehensive parameter space.
        
        Args:
            market_data: Market data for optimization
            n_trials: Number of optimization trials
            categories: Parameter categories to optimize (overrides instance setting)
            objective_metric: Metric to optimize ('sharpe', 'return', 'calmar')
            **optuna_kwargs: Additional arguments for optuna study
            
        Returns:
            Optimization results with best parameters and performance metrics
        """
        try:
            # Use provided categories or instance default
            opt_categories = categories or self.parameter_categories
            
            def objective(trial):
                # Get parameter suggestions from the parameter space
                parameters = self.param_space.create_optuna_trial_suggest(trial, opt_categories)
                
                # Validate parameters
                is_valid, errors = self.param_space.validate_parameters(parameters, opt_categories)
                if not is_valid:
                    logger.warning(f"Invalid parameters generated: {errors}")
                    return -1000  # Heavy penalty for invalid parameters
                
                # Run backtest with the suggested parameters
                backtest_result = self._enhanced_backtest(market_data, parameters)
                
                if 'error' in backtest_result:
                    logger.warning(f"Backtest failed: {backtest_result['error']}")
                    return -1000
                
                # Calculate objective value based on specified metric
                return self._calculate_objective(backtest_result, objective_metric)
            
            # Create and run Optuna study
            study_kwargs = {
                'direction': 'maximize',
                'sampler': optuna.samplers.TPESampler(seed=42),
                **optuna_kwargs
            }
            
            study = optuna.create_study(**study_kwargs)
            study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
            
            # Get best parameters and run final detailed backtest
            best_params = study.best_params
            best_backtest = self._enhanced_backtest(market_data, best_params)
            
            # Store optimization history
            optimization_result = {
                'best_params': best_params,
                'best_value': study.best_value,
                'backtest_results': best_backtest,
                'optimization_trials': n_trials,
                'objective_metric': objective_metric,
                'parameter_categories': opt_categories,
                'study': study
            }
            
            self.optimization_history.append(optimization_result)
            
            return optimization_result
        
        except Exception as e:
            logger.error(f"Error in enhanced optimization: {e}")
            return {'error': str(e)}
    
    def _enhanced_backtest(self, market_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced backtest that processes parameters from the parameter space.
        
        Args:
            market_data: Market data for backtesting
            parameters: Parameters from the parameter space
            
        Returns:
            Enhanced backtest results
        """
        try:
            # Extract strategy-specific parameters for the existing backtest function
            strategy_params = {}
            
            # Map parameter space parameters to strategy parameters
            param_mapping = {
                'strategy_initial_capital': 'initial_capital',
                'technical_indicators_sma_periods': 'sma_periods',
                'technical_indicators_ema_periods': 'ema_periods',
                'technical_indicators_rsi_period': 'rsi_period',
                'risk_management_stop_loss_pct': 'stop_loss_pct',
                'risk_management_take_profit_pct': 'take_profit_pct'
            }
            
            # Apply parameter mapping
            for param_space_name, strategy_name in param_mapping.items():
                if param_space_name in parameters:
                    strategy_params[strategy_name] = parameters[param_space_name]
            
            # Set defaults for required parameters if not provided
            if 'initial_capital' not in strategy_params:
                strategy_params['initial_capital'] = parameters.get('strategy_initial_capital', 100000)
            
            # Extract moving average periods for compatibility with existing backtest
            sma_periods = strategy_params.get('sma_periods', [10, 20, 50])
            if isinstance(sma_periods, list) and len(sma_periods) >= 2:
                strategy_params['short_ma_period'] = min(sma_periods)
                strategy_params['long_ma_period'] = max(sma_periods)
            else:
                strategy_params['short_ma_period'] = 10
                strategy_params['long_ma_period'] = 20
            
            # Run the existing backtest function
            backtest_result = backtest_strategy(market_data, strategy_params)
            
            # Add enhanced metrics
            if 'error' not in backtest_result:
                backtest_result['enhanced_metrics'] = self._calculate_enhanced_metrics(
                    backtest_result, parameters
                )
                backtest_result['parameter_space_params'] = parameters
            
            return backtest_result
        
        except Exception as e:
            logger.error(f"Error in enhanced backtest: {e}")
            return {'error': str(e)}
    
    def _calculate_enhanced_metrics(self, backtest_result: Dict[str, Any], 
                                  parameters: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate additional performance metrics based on parameter space settings.
        
        Args:
            backtest_result: Basic backtest results
            parameters: Parameter space parameters
            
        Returns:
            Dictionary of enhanced metrics
        """
        enhanced_metrics = {}
        
        try:
            trades = backtest_result.get('trades', [])
            metrics = backtest_result.get('metrics', {})
            
            # Risk-adjusted returns
            sharpe = metrics.get('sharpe', 0)
            max_drawdown = metrics.get('max_drawdown', 0)
            
            # Calmar ratio (annual return / max drawdown)
            net_profit = metrics.get('net_profit', 0)
            initial_capital = parameters.get('strategy_initial_capital', 100000)
            annual_return = net_profit / initial_capital if initial_capital > 0 else 0
            
            calmar_ratio = annual_return / max_drawdown if max_drawdown > 0 else 0
            enhanced_metrics['calmar_ratio'] = calmar_ratio
            
            # Risk-adjusted position sizing score
            max_position_pct = parameters.get('risk_management_max_position_pct', 0.2)
            position_sizing_score = 1.0 / max_position_pct  # Lower max position = higher score
            enhanced_metrics['position_sizing_score'] = position_sizing_score
            
            # Parameter efficiency score (simpler strategies score higher)
            complexity_penalty = 0
            if parameters.get('rl_ml_hidden_layers', 1) > 3:
                complexity_penalty += 0.1
            if len(parameters.get('technical_indicators_sma_periods', [])) > 3:
                complexity_penalty += 0.1
            
            efficiency_score = max(0, 1.0 - complexity_penalty)
            enhanced_metrics['efficiency_score'] = efficiency_score
            
            # Overall composite score
            composite_score = (sharpe * 0.4 + 
                             calmar_ratio * 0.3 + 
                             position_sizing_score * 0.2 + 
                             efficiency_score * 0.1)
            enhanced_metrics['composite_score'] = composite_score
            
        except Exception as e:
            logger.error(f"Error calculating enhanced metrics: {e}")
        
        return enhanced_metrics
    
    def _calculate_objective(self, backtest_result: Dict[str, Any], metric: str) -> float:
        """
        Calculate the objective value for optimization.
        
        Args:
            backtest_result: Backtest results
            metric: Metric to optimize
            
        Returns:
            Objective value (higher is better)
        """
        try:
            base_metrics = backtest_result.get('metrics', {})
            enhanced_metrics = backtest_result.get('enhanced_metrics', {})
            
            if metric == 'sharpe':
                return base_metrics.get('sharpe', 0)
            elif metric == 'return':
                return base_metrics.get('net_profit', 0)
            elif metric == 'calmar':
                return enhanced_metrics.get('calmar_ratio', 0)
            elif metric == 'composite':
                return enhanced_metrics.get('composite_score', 0)
            else:
                logger.warning(f"Unknown metric: {metric}, defaulting to Sharpe")
                return base_metrics.get('sharpe', 0)
        
        except Exception as e:
            logger.error(f"Error calculating objective for metric {metric}: {e}")
            return -1000
    
    def get_optimization_history(self) -> List[Dict[str, Any]]:
        """
        Get the history of optimization runs.
        
        Returns:
            List of optimization results
        """
        return self.optimization_history
    
    def get_parameter_importance(self, study_index: int = -1) -> Dict[str, float]:
        """
        Get parameter importance from the most recent optimization study.
        
        Args:
            study_index: Index of the optimization study to analyze
            
        Returns:
            Dictionary of parameter importance scores
        """
        try:
            if not self.optimization_history:
                return {}
            
            study = self.optimization_history[study_index]['study']
            importance = optuna.importance.get_param_importances(study)
            return importance
        
        except Exception as e:
            logger.error(f"Error calculating parameter importance: {e}")
            return {}


def demonstrate_enhanced_optimizer():
    """
    Demonstrate the enhanced optimizer with sample market data.
    """
    # Create sample market data
    sample_data = {
        'AAPL': {'price': 150.0, 'volume': 1000000},
        'GOOGL': {'price': 2500.0, 'volume': 500000}
    }
    
    # Initialize enhanced optimizer
    optimizer = EnhancedOptimizer()
    
    # Run optimization with different categories
    print("=== ENHANCED OPTIMIZER DEMONSTRATION ===")
    
    # Optimize only strategy and risk management parameters
    result = optimizer.optimize_strategy(
        market_data=sample_data,
        n_trials=20,  # Small number for demo
        categories=['strategy', 'risk_management'],
        objective_metric='sharpe'
    )
    
    if 'error' not in result:
        print(f"Best Sharpe ratio: {result['best_value']:.4f}")
        print(f"Best parameters: {list(result['best_params'].keys())[:5]}...")  # Show first 5
        
        # Show parameter importance
        importance = optimizer.get_parameter_importance()
        if importance:
            print("Top 3 most important parameters:")
            sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            for param, score in sorted_importance[:3]:
                print(f"  {param}: {score:.4f}")
    else:
        print(f"Optimization failed: {result['error']}")


if __name__ == "__main__":
    demonstrate_enhanced_optimizer()