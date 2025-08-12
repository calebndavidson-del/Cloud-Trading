# Trading Bot Parameter Space

This directory contains a comprehensive parameter space for optimization and backtesting of trading strategies. The parameter space covers all aspects of algorithmic trading including RL/ML hyperparameters, trading strategies, feature engineering, technical indicators, and risk management.

## Overview

The parameter space is designed to be:
- **Comprehensive**: Covers all major aspects of trading bot optimization
- **Extensible**: Easy to add new parameters and categories
- **Compatible**: Works with multiple optimization frameworks (Optuna, scikit-optimize, etc.)
- **Validated**: Built-in parameter validation and constraint checking
- **Well-documented**: Thorough comments and documentation for each parameter

## Files

### Core Module
- `parameter_space.py` - Main parameter space implementation with 61+ parameters across 5 categories
- `enhanced_optimizer.py` - Enhanced optimizer that integrates with the parameter space
- `usage_examples.py` - Comprehensive examples showing how to use the parameter space

### Test Files
- `../test_parameter_integration.py` - Integration tests with existing optimizer

## Parameter Categories

### 1. RL/ML Model Hyperparameters (13 parameters)
- **Network Architecture**: Hidden layers, neurons per layer, activation functions
- **Learning Parameters**: Learning rate, batch size, optimizer selection
- **RL-Specific**: Discount factor, exploration parameters, memory buffer settings

### 2. Strategy Parameters (9 parameters)
- **Portfolio Management**: Capital allocation, position limits, sizing methods
- **Signal Generation**: Thresholds, confirmation periods, hold times
- **Rebalancing**: Frequency and thresholds for portfolio rebalancing

### 3. Feature Engineering Parameters (10 parameters)
- **Data Processing**: Lookback windows, scaling methods, outlier handling
- **Feature Selection**: Selection methods, correlation thresholds, max features
- **Technical Features**: Price, volume, and volatility feature inclusion

### 4. Technical Indicator Parameters (16 parameters)
- **Moving Averages**: SMA and EMA periods
- **Momentum Indicators**: RSI, MACD, Stochastic oscillator settings
- **Volatility Indicators**: Bollinger Bands parameters
- **Volume Indicators**: Volume SMA, VWAP settings

### 5. Risk Management Parameters (13 parameters)
- **Stop Loss/Take Profit**: Percentage levels, trailing stops
- **Position Sizing**: Maximum position limits, sector allocation
- **Portfolio Risk**: Drawdown limits, volatility targets, VaR limits
- **Risk Adjustments**: Volatility scaling, correlation adjustments

## Quick Start

```python
from backend.optimization.parameter_space import get_parameter_space

# Create parameter space
param_space = get_parameter_space()

# Get all parameters
all_params = param_space.get_parameter_space()
print(f"Total parameters: {len(all_params)}")

# Get default values
defaults = param_space.get_default_parameters(['strategy'])

# Sample random parameters
samples = param_space.sample_parameters(['strategy'], n_samples=5)

# Validate parameters
is_valid, errors = param_space.validate_parameters(your_params)
```

## Integration with Optuna

```python
import optuna
from backend.optimization.parameter_space import get_parameter_space

param_space = get_parameter_space()

def objective(trial):
    # Get parameter suggestions
    params = param_space.create_optuna_trial_suggest(trial, ['strategy'])
    
    # Run your optimization logic here
    return your_objective_function(params)

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
```

## Enhanced Optimizer Usage

```python
from backend.optimization.enhanced_optimizer import EnhancedOptimizer

# Initialize optimizer
optimizer = EnhancedOptimizer()

# Run optimization with specific categories
result = optimizer.optimize_strategy(
    market_data=your_data,
    n_trials=100,
    categories=['strategy', 'risk_management'],
    objective_metric='sharpe'
)

# Get parameter importance
importance = optimizer.get_parameter_importance()
```

## Parameter Types

The parameter space supports four parameter types:

1. **FLOAT**: Continuous numeric parameters with optional log scaling
2. **INTEGER**: Discrete numeric parameters with optional step sizes
3. **CATEGORICAL**: Categorical choices including complex objects (lists)
4. **BOOLEAN**: Binary True/False parameters

Each parameter includes:
- Type and bounds definition
- Default value
- Human-readable description
- Optional constraints (log scale, step size)

## Validation and Constraints

All parameters have built-in validation:

```python
# Example validation
test_params = {
    'strategy_initial_capital': 50000,
    'risk_management_stop_loss_pct': 0.03
}

is_valid, errors = param_space.validate_parameters(test_params)
if not is_valid:
    print("Validation errors:", errors)
```

## Extensibility

To add new parameters:

1. Add the parameter to the appropriate `_define_*_parameters()` method
2. Define the parameter using `ParameterDefinition`
3. Add validation logic if needed
4. Update documentation

Example:
```python
'new_parameter': ParameterDefinition(
    name='new_parameter',
    param_type=ParameterType.FLOAT,
    bounds=(0.1, 1.0),
    default=0.5,
    description='Description of the new parameter'
)
```

## Best Practices

1. **Start Small**: Begin with strategy and risk management parameters
2. **Iterative Optimization**: Add parameter categories gradually
3. **Validation**: Always validate parameters before optimization
4. **Documentation**: Document custom parameters and constraints
5. **Testing**: Test parameter changes with small trial counts first

## Performance Considerations

- **Parameter Count**: Higher parameter counts require more optimization trials
- **Categorical Parameters**: Complex categorical parameters may need custom handling
- **Validation**: Parameter validation adds minimal overhead but improves reliability
- **Memory**: Parameter sampling uses minimal memory for reasonable sample sizes

## Examples

See `usage_examples.py` for comprehensive examples including:
- Basic parameter exploration
- Strategy-focused optimization
- Technical indicator tuning
- ML hyperparameter optimization
- Comprehensive multi-category optimization
- Parameter validation examples

## Integration with Existing Code

The parameter space is designed to work with the existing optimizer infrastructure:

- Compatible with `backend.optimizer.optimize_strategy()`
- Integrates with existing backtest functions
- Supports current market data formats
- Maintains backward compatibility

## Future Enhancements

Planned improvements:
- Multi-objective optimization support
- Parameter importance analysis
- Automated constraint generation
- Parameter correlation analysis
- Custom optimization algorithms
- Integration with external optimization libraries