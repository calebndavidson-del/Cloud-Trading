"""
Comprehensive Parameter Space for Trading Bot Optimization and Backtesting

This module provides a complete, extensible parameter space that covers:
- RL/ML model hyperparameters
- Trading strategy parameters
- Feature engineering parameters
- Technical indicator parameters
- Risk management parameters

The parameter space is designed to be compatible with multiple optimization frameworks
including Optuna, scikit-optimize, and custom grid/random search implementations.

Author: Trading Bot Development Team
Last Updated: 2025
"""

import numpy as np
from typing import Dict, List, Tuple, Union, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ParameterType(Enum):
    """Enumeration of parameter types for optimization frameworks."""
    FLOAT = "float"
    INTEGER = "int"
    CATEGORICAL = "categorical"
    BOOLEAN = "boolean"


class OptimizationMethod(Enum):
    """Supported optimization methods."""
    GRID_SEARCH = "grid"
    RANDOM_SEARCH = "random"
    BAYESIAN = "bayesian"
    EVOLUTIONARY = "evolutionary"


@dataclass
class ParameterDefinition:
    """
    Definition of a single parameter for optimization.
    
    Attributes:
        name: Parameter name
        param_type: Type of parameter (float, int, categorical, boolean)
        bounds: For numeric types, (min, max). For categorical, list of options
        default: Default value
        description: Human-readable description
        log_scale: Whether to use log scale for numeric parameters
        step: Step size for integer/float parameters (None for continuous)
    """
    name: str
    param_type: ParameterType
    bounds: Union[Tuple[float, float], List[Any]]
    default: Any
    description: str
    log_scale: bool = False
    step: Optional[float] = None


class TradingParameterSpace:
    """
    Comprehensive parameter space for trading bot optimization.
    
    This class provides a structured way to define, validate, and sample
    parameters for trading strategy optimization and backtesting.
    """
    
    def __init__(self):
        """Initialize the parameter space with all trading-related parameters."""
        self.parameters = {}
        self._define_rl_ml_parameters()
        self._define_strategy_parameters()
        self._define_feature_engineering_parameters()
        self._define_technical_indicator_parameters()
        self._define_risk_management_parameters()
        
    def _define_rl_ml_parameters(self):
        """Define reinforcement learning and machine learning hyperparameters."""
        rl_ml_params = {
            # Neural Network Architecture
            'hidden_layers': ParameterDefinition(
                name='hidden_layers',
                param_type=ParameterType.INTEGER,
                bounds=(1, 5),
                default=3,
                description='Number of hidden layers in neural network'
            ),
            'neurons_per_layer': ParameterDefinition(
                name='neurons_per_layer',
                param_type=ParameterType.INTEGER,
                bounds=(32, 512),
                default=128,
                description='Number of neurons per hidden layer',
                step=32
            ),
            'activation_function': ParameterDefinition(
                name='activation_function',
                param_type=ParameterType.CATEGORICAL,
                bounds=['relu', 'tanh', 'sigmoid', 'leaky_relu', 'elu'],
                default='relu',
                description='Activation function for neural network layers'
            ),
            
            # Learning Parameters
            'learning_rate': ParameterDefinition(
                name='learning_rate',
                param_type=ParameterType.FLOAT,
                bounds=(1e-5, 1e-1),
                default=3e-4,
                description='Learning rate for model training',
                log_scale=True
            ),
            'batch_size': ParameterDefinition(
                name='batch_size',
                param_type=ParameterType.INTEGER,
                bounds=(16, 256),
                default=64,
                description='Batch size for training',
                step=16
            ),
            'optimizer': ParameterDefinition(
                name='optimizer',
                param_type=ParameterType.CATEGORICAL,
                bounds=['adam', 'sgd', 'rmsprop', 'adamw'],
                default='adam',
                description='Optimizer algorithm for training'
            ),
            
            # RL-Specific Parameters
            'discount_factor': ParameterDefinition(
                name='discount_factor',
                param_type=ParameterType.FLOAT,
                bounds=(0.9, 0.999),
                default=0.99,
                description='Discount factor (gamma) for future rewards'
            ),
            'epsilon_start': ParameterDefinition(
                name='epsilon_start',
                param_type=ParameterType.FLOAT,
                bounds=(0.5, 1.0),
                default=0.9,
                description='Starting epsilon for epsilon-greedy exploration'
            ),
            'epsilon_end': ParameterDefinition(
                name='epsilon_end',
                param_type=ParameterType.FLOAT,
                bounds=(0.01, 0.1),
                default=0.05,
                description='Final epsilon for epsilon-greedy exploration'
            ),
            'epsilon_decay': ParameterDefinition(
                name='epsilon_decay',
                param_type=ParameterType.FLOAT,
                bounds=(0.995, 0.9999),
                default=0.999,
                description='Epsilon decay rate per episode'
            ),
            'memory_buffer_size': ParameterDefinition(
                name='memory_buffer_size',
                param_type=ParameterType.INTEGER,
                bounds=(10000, 100000),
                default=50000,
                description='Size of experience replay buffer',
                step=10000
            ),
            'target_update_frequency': ParameterDefinition(
                name='target_update_frequency',
                param_type=ParameterType.INTEGER,
                bounds=(100, 2000),
                default=1000,
                description='Frequency of target network updates',
                step=100
            ),
            'training_frequency': ParameterDefinition(
                name='training_frequency',
                param_type=ParameterType.INTEGER,
                bounds=(1, 10),
                default=4,
                description='Training frequency (every N steps)'
            ),
        }
        
        self.parameters['rl_ml'] = rl_ml_params
    
    def _define_strategy_parameters(self):
        """Define trading strategy parameters."""
        strategy_params = {
            # Portfolio Management
            'initial_capital': ParameterDefinition(
                name='initial_capital',
                param_type=ParameterType.FLOAT,
                bounds=(10000, 1000000),
                default=100000,
                description='Initial trading capital in USD'
            ),
            'max_positions': ParameterDefinition(
                name='max_positions',
                param_type=ParameterType.INTEGER,
                bounds=(1, 20),
                default=5,
                description='Maximum number of concurrent positions'
            ),
            'position_sizing_method': ParameterDefinition(
                name='position_sizing_method',
                param_type=ParameterType.CATEGORICAL,
                bounds=['fixed', 'percent_capital', 'volatility_adjusted', 'kelly'],
                default='percent_capital',
                description='Method for determining position sizes'
            ),
            'base_position_size': ParameterDefinition(
                name='base_position_size',
                param_type=ParameterType.FLOAT,
                bounds=(0.01, 0.2),
                default=0.05,
                description='Base position size as fraction of capital'
            ),
            
            # Signal Generation
            'signal_threshold': ParameterDefinition(
                name='signal_threshold',
                param_type=ParameterType.FLOAT,
                bounds=(0.1, 0.9),
                default=0.6,
                description='Threshold for buy/sell signal generation'
            ),
            'signal_confirmation_periods': ParameterDefinition(
                name='signal_confirmation_periods',
                param_type=ParameterType.INTEGER,
                bounds=(1, 5),
                default=2,
                description='Number of periods to confirm signals'
            ),
            'min_hold_periods': ParameterDefinition(
                name='min_hold_periods',
                param_type=ParameterType.INTEGER,
                bounds=(1, 20),
                default=5,
                description='Minimum periods to hold a position'
            ),
            
            # Rebalancing
            'rebalancing_frequency': ParameterDefinition(
                name='rebalancing_frequency',
                param_type=ParameterType.CATEGORICAL,
                bounds=['daily', 'weekly', 'monthly', 'quarterly'],
                default='weekly',
                description='Portfolio rebalancing frequency'
            ),
            'rebalancing_threshold': ParameterDefinition(
                name='rebalancing_threshold',
                param_type=ParameterType.FLOAT,
                bounds=(0.01, 0.1),
                default=0.05,
                description='Portfolio drift threshold for rebalancing'
            ),
        }
        
        self.parameters['strategy'] = strategy_params
    
    def _define_feature_engineering_parameters(self):
        """Define feature engineering parameters."""
        feature_params = {
            # Data Processing
            'lookback_window': ParameterDefinition(
                name='lookback_window',
                param_type=ParameterType.INTEGER,
                bounds=(10, 252),
                default=60,
                description='Lookback window for feature calculation (trading days)'
            ),
            'feature_scaling_method': ParameterDefinition(
                name='feature_scaling_method',
                param_type=ParameterType.CATEGORICAL,
                bounds=['standard', 'minmax', 'robust', 'quantile'],
                default='standard',
                description='Method for scaling features'
            ),
            'outlier_removal_method': ParameterDefinition(
                name='outlier_removal_method',
                param_type=ParameterType.CATEGORICAL,
                bounds=['none', 'iqr', 'zscore', 'modified_zscore'],
                default='iqr',
                description='Method for outlier detection and removal'
            ),
            'outlier_threshold': ParameterDefinition(
                name='outlier_threshold',
                param_type=ParameterType.FLOAT,
                bounds=(2.0, 4.0),
                default=3.0,
                description='Threshold for outlier detection (standard deviations)'
            ),
            
            # Feature Selection
            'feature_selection_method': ParameterDefinition(
                name='feature_selection_method',
                param_type=ParameterType.CATEGORICAL,
                bounds=['none', 'correlation', 'mutual_info', 'lasso', 'recursive'],
                default='correlation',
                description='Method for automatic feature selection'
            ),
            'max_features': ParameterDefinition(
                name='max_features',
                param_type=ParameterType.INTEGER,
                bounds=(5, 50),
                default=20,
                description='Maximum number of features to use'
            ),
            'correlation_threshold': ParameterDefinition(
                name='correlation_threshold',
                param_type=ParameterType.FLOAT,
                bounds=(0.7, 0.95),
                default=0.85,
                description='Correlation threshold for feature removal'
            ),
            
            # Technical Features
            'price_features': ParameterDefinition(
                name='price_features',
                param_type=ParameterType.CATEGORICAL,
                bounds=[['ohlc'], ['ohlc', 'returns'], ['ohlc', 'returns', 'log_returns']],
                default=['ohlc', 'returns'],
                description='Price-based features to include'
            ),
            'volume_features': ParameterDefinition(
                name='volume_features',
                param_type=ParameterType.BOOLEAN,
                bounds=[True, False],
                default=True,
                description='Whether to include volume-based features'
            ),
            'volatility_features': ParameterDefinition(
                name='volatility_features',
                param_type=ParameterType.BOOLEAN,
                bounds=[True, False],
                default=True,
                description='Whether to include volatility features'
            ),
        }
        
        self.parameters['feature_engineering'] = feature_params
    
    def _define_technical_indicator_parameters(self):
        """Define technical indicator parameters."""
        indicator_params = {
            # Moving Averages
            'sma_periods': ParameterDefinition(
                name='sma_periods',
                param_type=ParameterType.CATEGORICAL,
                bounds=[[5, 10, 20], [10, 20, 50], [20, 50, 100], [5, 20, 50, 100]],
                default=[10, 20, 50],
                description='Simple moving average periods'
            ),
            'ema_periods': ParameterDefinition(
                name='ema_periods',
                param_type=ParameterType.CATEGORICAL,
                bounds=[[12, 26], [9, 21], [12, 26, 50], [5, 10, 20, 50]],
                default=[12, 26],
                description='Exponential moving average periods'
            ),
            
            # RSI Parameters
            'rsi_period': ParameterDefinition(
                name='rsi_period',
                param_type=ParameterType.INTEGER,
                bounds=(5, 30),
                default=14,
                description='RSI calculation period'
            ),
            'rsi_overbought': ParameterDefinition(
                name='rsi_overbought',
                param_type=ParameterType.FLOAT,
                bounds=(65, 85),
                default=70,
                description='RSI overbought threshold'
            ),
            'rsi_oversold': ParameterDefinition(
                name='rsi_oversold',
                param_type=ParameterType.FLOAT,
                bounds=(15, 35),
                default=30,
                description='RSI oversold threshold'
            ),
            
            # MACD Parameters
            'macd_fast_period': ParameterDefinition(
                name='macd_fast_period',
                param_type=ParameterType.INTEGER,
                bounds=(8, 15),
                default=12,
                description='MACD fast EMA period'
            ),
            'macd_slow_period': ParameterDefinition(
                name='macd_slow_period',
                param_type=ParameterType.INTEGER,
                bounds=(20, 35),
                default=26,
                description='MACD slow EMA period'
            ),
            'macd_signal_period': ParameterDefinition(
                name='macd_signal_period',
                param_type=ParameterType.INTEGER,
                bounds=(5, 15),
                default=9,
                description='MACD signal line EMA period'
            ),
            
            # Bollinger Bands
            'bb_period': ParameterDefinition(
                name='bb_period',
                param_type=ParameterType.INTEGER,
                bounds=(10, 30),
                default=20,
                description='Bollinger Bands period'
            ),
            'bb_std_dev': ParameterDefinition(
                name='bb_std_dev',
                param_type=ParameterType.FLOAT,
                bounds=(1.5, 2.5),
                default=2.0,
                description='Bollinger Bands standard deviation multiplier'
            ),
            
            # Stochastic Oscillator
            'stoch_k_period': ParameterDefinition(
                name='stoch_k_period',
                param_type=ParameterType.INTEGER,
                bounds=(5, 20),
                default=14,
                description='Stochastic %K period'
            ),
            'stoch_d_period': ParameterDefinition(
                name='stoch_d_period',
                param_type=ParameterType.INTEGER,
                bounds=(1, 5),
                default=3,
                description='Stochastic %D smoothing period'
            ),
            'stoch_overbought': ParameterDefinition(
                name='stoch_overbought',
                param_type=ParameterType.FLOAT,
                bounds=(75, 85),
                default=80,
                description='Stochastic overbought threshold'
            ),
            'stoch_oversold': ParameterDefinition(
                name='stoch_oversold',
                param_type=ParameterType.FLOAT,
                bounds=(15, 25),
                default=20,
                description='Stochastic oversold threshold'
            ),
            
            # Volume Indicators
            'volume_sma_period': ParameterDefinition(
                name='volume_sma_period',
                param_type=ParameterType.INTEGER,
                bounds=(10, 50),
                default=20,
                description='Volume SMA period for volume analysis'
            ),
            'vwap_period': ParameterDefinition(
                name='vwap_period',
                param_type=ParameterType.INTEGER,
                bounds=(10, 50),
                default=20,
                description='Volume Weighted Average Price period'
            ),
        }
        
        self.parameters['technical_indicators'] = indicator_params
    
    def _define_risk_management_parameters(self):
        """Define risk management parameters."""
        risk_params = {
            # Stop Loss and Take Profit
            'stop_loss_pct': ParameterDefinition(
                name='stop_loss_pct',
                param_type=ParameterType.FLOAT,
                bounds=(0.01, 0.1),
                default=0.05,
                description='Stop loss percentage (fraction of entry price)'
            ),
            'take_profit_pct': ParameterDefinition(
                name='take_profit_pct',
                param_type=ParameterType.FLOAT,
                bounds=(0.02, 0.2),
                default=0.1,
                description='Take profit percentage (fraction of entry price)'
            ),
            'trailing_stop': ParameterDefinition(
                name='trailing_stop',
                param_type=ParameterType.BOOLEAN,
                bounds=[True, False],
                default=False,
                description='Whether to use trailing stop loss'
            ),
            'trailing_stop_pct': ParameterDefinition(
                name='trailing_stop_pct',
                param_type=ParameterType.FLOAT,
                bounds=(0.01, 0.05),
                default=0.02,
                description='Trailing stop percentage'
            ),
            
            # Position Sizing Risk
            'max_position_pct': ParameterDefinition(
                name='max_position_pct',
                param_type=ParameterType.FLOAT,
                bounds=(0.05, 0.3),
                default=0.2,
                description='Maximum position size as percentage of capital'
            ),
            'max_sector_allocation': ParameterDefinition(
                name='max_sector_allocation',
                param_type=ParameterType.FLOAT,
                bounds=(0.2, 0.6),
                default=0.4,
                description='Maximum allocation to any single sector'
            ),
            'max_correlation_exposure': ParameterDefinition(
                name='max_correlation_exposure',
                param_type=ParameterType.FLOAT,
                bounds=(0.3, 0.8),
                default=0.6,
                description='Maximum exposure to correlated assets'
            ),
            
            # Portfolio Risk
            'max_portfolio_drawdown': ParameterDefinition(
                name='max_portfolio_drawdown',
                param_type=ParameterType.FLOAT,
                bounds=(0.1, 0.3),
                default=0.2,
                description='Maximum allowed portfolio drawdown'
            ),
            'target_volatility': ParameterDefinition(
                name='target_volatility',
                param_type=ParameterType.FLOAT,
                bounds=(0.1, 0.4),
                default=0.2,
                description='Target portfolio volatility (annualized)'
            ),
            'volatility_lookback': ParameterDefinition(
                name='volatility_lookback',
                param_type=ParameterType.INTEGER,
                bounds=(20, 100),
                default=60,
                description='Lookback period for volatility calculation'
            ),
            
            # Risk Adjustment
            'volatility_scaling': ParameterDefinition(
                name='volatility_scaling',
                param_type=ParameterType.BOOLEAN,
                bounds=[True, False],
                default=True,
                description='Whether to scale positions by volatility'
            ),
            'correlation_adjustment': ParameterDefinition(
                name='correlation_adjustment',
                param_type=ParameterType.BOOLEAN,
                bounds=[True, False],
                default=True,
                description='Whether to adjust positions based on correlations'
            ),
            'var_limit': ParameterDefinition(
                name='var_limit',
                param_type=ParameterType.FLOAT,
                bounds=(0.01, 0.05),
                default=0.025,
                description='Value at Risk limit (95% confidence)'
            ),
        }
        
        self.parameters['risk_management'] = risk_params
    
    def get_parameter_space(self, categories: Optional[List[str]] = None) -> Dict[str, ParameterDefinition]:
        """
        Get parameter space for specified categories.
        
        Args:
            categories: List of parameter categories to include. If None, returns all.
            
        Returns:
            Dictionary of parameter definitions
        """
        if categories is None:
            categories = list(self.parameters.keys())
        
        result = {}
        for category in categories:
            if category in self.parameters:
                for param_name, param_def in self.parameters[category].items():
                    result[f"{category}_{param_name}"] = param_def
        
        return result
    
    def get_default_parameters(self, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get default parameter values for specified categories.
        
        Args:
            categories: List of parameter categories to include. If None, returns all.
            
        Returns:
            Dictionary of default parameter values
        """
        param_space = self.get_parameter_space(categories)
        return {name: param_def.default for name, param_def in param_space.items()}
    
    def validate_parameters(self, params: Dict[str, Any], categories: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
        """
        Validate parameter values against their definitions.
        
        Args:
            params: Dictionary of parameter values to validate
            categories: List of parameter categories to validate. If None, validates all.
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        param_space = self.get_parameter_space(categories)
        errors = []
        
        for param_name, value in params.items():
            if param_name not in param_space:
                errors.append(f"Unknown parameter: {param_name}")
                continue
            
            param_def = param_space[param_name]
            
            # Type validation
            if param_def.param_type == ParameterType.FLOAT and not isinstance(value, (int, float)):
                errors.append(f"{param_name}: Expected float, got {type(value).__name__}")
                continue
            elif param_def.param_type == ParameterType.INTEGER and not isinstance(value, int):
                errors.append(f"{param_name}: Expected int, got {type(value).__name__}")
                continue
            elif param_def.param_type == ParameterType.BOOLEAN and not isinstance(value, bool):
                errors.append(f"{param_name}: Expected bool, got {type(value).__name__}")
                continue
            
            # Bounds validation
            if param_def.param_type in [ParameterType.FLOAT, ParameterType.INTEGER]:
                min_val, max_val = param_def.bounds
                if not (min_val <= value <= max_val):
                    errors.append(f"{param_name}: Value {value} out of bounds [{min_val}, {max_val}]")
            elif param_def.param_type == ParameterType.CATEGORICAL:
                if value not in param_def.bounds:
                    errors.append(f"{param_name}: Value {value} not in allowed options {param_def.bounds}")
        
        return len(errors) == 0, errors
    
    def sample_parameters(self, 
                         categories: Optional[List[str]] = None,
                         method: str = 'random',
                         n_samples: int = 1,
                         seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Sample parameters from the parameter space.
        
        Args:
            categories: List of parameter categories to sample. If None, samples all.
            method: Sampling method ('random', 'latin_hypercube', 'grid')
            n_samples: Number of parameter sets to sample
            seed: Random seed for reproducibility
            
        Returns:
            List of parameter dictionaries
        """
        if seed is not None:
            np.random.seed(seed)
        
        param_space = self.get_parameter_space(categories)
        samples = []
        
        for _ in range(n_samples):
            sample = {}
            for param_name, param_def in param_space.items():
                if param_def.param_type == ParameterType.FLOAT:
                    min_val, max_val = param_def.bounds
                    if param_def.log_scale:
                        sample[param_name] = np.exp(np.random.uniform(np.log(min_val), np.log(max_val)))
                    else:
                        sample[param_name] = np.random.uniform(min_val, max_val)
                elif param_def.param_type == ParameterType.INTEGER:
                    min_val, max_val = param_def.bounds
                    sample[param_name] = np.random.randint(min_val, max_val + 1)
                elif param_def.param_type == ParameterType.CATEGORICAL:
                    # Handle categorical parameters with complex objects (like lists)
                    bounds = param_def.bounds
                    if isinstance(bounds[0], list):
                        # For parameters containing lists, select randomly from the options
                        sample[param_name] = bounds[np.random.randint(len(bounds))]
                    else:
                        sample[param_name] = np.random.choice(bounds)
                elif param_def.param_type == ParameterType.BOOLEAN:
                    sample[param_name] = np.random.choice([True, False])
            
            samples.append(sample)
        
        return samples
    
    def create_optuna_trial_suggest(self, trial, categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create parameter suggestions for Optuna trial.
        
        Args:
            trial: Optuna trial object
            categories: List of parameter categories to include. If None, includes all.
            
        Returns:
            Dictionary of suggested parameters
        """
        param_space = self.get_parameter_space(categories)
        suggestions = {}
        
        for param_name, param_def in param_space.items():
            if param_def.param_type == ParameterType.FLOAT:
                min_val, max_val = param_def.bounds
                suggestions[param_name] = trial.suggest_float(
                    param_name, min_val, max_val, log=param_def.log_scale, step=param_def.step
                )
            elif param_def.param_type == ParameterType.INTEGER:
                min_val, max_val = param_def.bounds
                suggestions[param_name] = trial.suggest_int(
                    param_name, min_val, max_val, step=param_def.step or 1
                )
            elif param_def.param_type == ParameterType.CATEGORICAL:
                suggestions[param_name] = trial.suggest_categorical(param_name, param_def.bounds)
            elif param_def.param_type == ParameterType.BOOLEAN:
                suggestions[param_name] = trial.suggest_categorical(param_name, [True, False])
        
        return suggestions
    
    def get_parameter_info(self, category: Optional[str] = None) -> str:
        """
        Get formatted information about parameters.
        
        Args:
            category: Specific category to get info for. If None, returns info for all.
            
        Returns:
            Formatted string with parameter information
        """
        categories = [category] if category else list(self.parameters.keys())
        info_lines = []
        
        for cat in categories:
            if cat not in self.parameters:
                continue
            
            info_lines.append(f"\n=== {cat.upper().replace('_', ' ')} PARAMETERS ===")
            for param_name, param_def in self.parameters[cat].items():
                bounds_str = str(param_def.bounds)
                if param_def.param_type in [ParameterType.FLOAT, ParameterType.INTEGER]:
                    bounds_str = f"[{param_def.bounds[0]}, {param_def.bounds[1]}]"
                
                info_lines.append(
                    f"  {param_name}:\n"
                    f"    Type: {param_def.param_type.value}\n"
                    f"    Bounds: {bounds_str}\n"
                    f"    Default: {param_def.default}\n"
                    f"    Description: {param_def.description}"
                )
        
        return "\n".join(info_lines)


# Convenience function to get the default parameter space instance
def get_parameter_space() -> TradingParameterSpace:
    """
    Get a default instance of the trading parameter space.
    
    Returns:
        TradingParameterSpace instance with all parameters defined
    """
    return TradingParameterSpace()


# Example usage and testing functions
if __name__ == "__main__":
    # Create parameter space
    param_space = TradingParameterSpace()
    
    # Print parameter information
    print("=== TRADING BOT PARAMETER SPACE ===")
    print(param_space.get_parameter_info())
    
    # Get default parameters
    defaults = param_space.get_default_parameters()
    print(f"\n=== DEFAULT PARAMETERS ===")
    for name, value in defaults.items():
        print(f"{name}: {value}")
    
    # Sample random parameters
    samples = param_space.sample_parameters(n_samples=3, seed=42)
    print(f"\n=== RANDOM PARAMETER SAMPLES ===")
    for i, sample in enumerate(samples):
        print(f"Sample {i+1}:")
        for name, value in list(sample.items())[:5]:  # Show first 5 for brevity
            print(f"  {name}: {value}")
        print("  ...")
    
    # Validate parameters
    test_params = {
        'rl_ml_learning_rate': 0.001,
        'strategy_initial_capital': 50000,
        'risk_management_stop_loss_pct': 0.03
    }
    is_valid, errors = param_space.validate_parameters(test_params)
    print(f"\n=== PARAMETER VALIDATION ===")
    print(f"Valid: {is_valid}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"  - {error}")