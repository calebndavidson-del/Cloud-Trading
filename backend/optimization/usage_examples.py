"""
Comprehensive usage examples for the trading bot parameter space.

This module demonstrates how to use the parameter space for various optimization
scenarios and integration with the existing trading bot infrastructure.
"""

import sys
import os
sys.path.append('/home/runner/work/Cloud-Trading/Cloud-Trading')

from backend.optimization.parameter_space import get_parameter_space, TradingParameterSpace
from backend.optimization.enhanced_optimizer import EnhancedOptimizer
import optuna
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def example_1_basic_parameter_exploration():
    """
    Example 1: Basic parameter space exploration.
    
    This example shows how to explore the parameter space, get defaults,
    and understand the available parameters.
    """
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic Parameter Space Exploration")
    print("="*60)
    
    # Create parameter space
    param_space = get_parameter_space()
    
    # Get information about all parameters
    print("📊 Parameter Space Overview:")
    print(f"  Total parameters: {len(param_space.get_parameter_space())}")
    
    # Show parameters by category
    categories = ['rl_ml', 'strategy', 'feature_engineering', 'technical_indicators', 'risk_management']
    for category in categories:
        cat_params = param_space.get_parameter_space([category])
        print(f"  {category.replace('_', ' ').title()}: {len(cat_params)} parameters")
    
    # Get default values for strategy parameters
    print("\n🎯 Default Strategy Parameters:")
    strategy_defaults = param_space.get_default_parameters(['strategy'])
    for param, value in strategy_defaults.items():
        param_name = param.replace('strategy_', '')
        print(f"  {param_name}: {value}")
    
    # Sample random parameters
    print("\n🎲 Random Parameter Sampling:")
    samples = param_space.sample_parameters(['risk_management'], n_samples=2, seed=42)
    for i, sample in enumerate(samples, 1):
        print(f"  Sample {i}:")
        for param, value in list(sample.items())[:3]:  # Show first 3
            param_name = param.replace('risk_management_', '')
            print(f"    {param_name}: {value}")
        print("    ...")


def example_2_strategy_optimization():
    """
    Example 2: Strategy-focused optimization.
    
    This example demonstrates optimizing only strategy and risk management
    parameters for a specific trading approach.
    """
    print("\n" + "="*60)
    print("EXAMPLE 2: Strategy-Focused Optimization")
    print("="*60)
    
    # Create sample market data
    market_data = {
        'AAPL': {'price': 150.0, 'volume': 1000000},
        'GOOGL': {'price': 2500.0, 'volume': 500000},
        'MSFT': {'price': 300.0, 'volume': 800000}
    }
    
    # Initialize enhanced optimizer for strategy parameters only
    optimizer = EnhancedOptimizer()
    
    print("🚀 Running strategy optimization...")
    print("   Optimizing: Strategy + Risk Management parameters")
    print("   Trials: 15 (for demo purposes)")
    
    # Run optimization
    result = optimizer.optimize_strategy(
        market_data=market_data,
        n_trials=15,
        categories=['strategy', 'risk_management'],
        objective_metric='sharpe'
    )
    
    if 'error' not in result:
        print(f"\n📈 Optimization Results:")
        print(f"   Best Sharpe Ratio: {result['best_value']:.4f}")
        print(f"   Parameters optimized: {len(result['best_params'])}")
        
        # Show top parameters
        print(f"\n🎯 Best Parameters (top 5):")
        best_params = list(result['best_params'].items())[:5]
        for param, value in best_params:
            param_name = param.replace('strategy_', '').replace('risk_management_', '')
            if isinstance(value, float):
                print(f"   {param_name}: {value:.4f}")
            else:
                print(f"   {param_name}: {value}")
        print("   ...")
        
        # Show parameter importance if available
        importance = optimizer.get_parameter_importance()
        if importance:
            print(f"\n📊 Most Important Parameters:")
            sorted_importance = sorted(importance.items(), key=lambda x: x[1], reverse=True)
            for param, score in sorted_importance[:3]:
                param_name = param.replace('strategy_', '').replace('risk_management_', '')
                print(f"   {param_name}: {score:.4f}")
    else:
        print(f"❌ Optimization failed: {result['error']}")


def example_3_technical_indicator_tuning():
    """
    Example 3: Technical indicator parameter tuning.
    
    This example shows how to optimize technical indicator parameters
    for better signal generation.
    """
    print("\n" + "="*60)
    print("EXAMPLE 3: Technical Indicator Parameter Tuning")
    print("="*60)
    
    param_space = get_parameter_space()
    
    # Get technical indicator parameters
    ti_params = param_space.get_parameter_space(['technical_indicators'])
    
    print("🔧 Available Technical Indicator Parameters:")
    indicator_groups = {}
    
    for param_name, param_def in ti_params.items():
        indicator = param_name.split('_')[2]  # Extract indicator name
        if indicator not in indicator_groups:
            indicator_groups[indicator] = []
        indicator_groups[indicator].append((param_name.split('_', 2)[2], param_def.default))
    
    for indicator, params in indicator_groups.items():
        print(f"  {indicator.upper()}:")
        for param_name, default in params:
            print(f"    {param_name}: {default}")
    
    # Example of creating a custom parameter set for RSI optimization
    print(f"\n🎯 Custom RSI Optimization Example:")
    
    # Sample RSI-specific parameters
    rsi_samples = param_space.sample_parameters(['technical_indicators'], n_samples=3, seed=123)
    
    for i, sample in enumerate(rsi_samples, 1):
        rsi_params = {k: v for k, v in sample.items() if 'rsi' in k}
        if rsi_params:
            print(f"  RSI Configuration {i}:")
            for param, value in rsi_params.items():
                param_name = param.replace('technical_indicators_rsi_', '')
                print(f"    {param_name}: {value}")


def example_4_ml_hyperparameter_optimization():
    """
    Example 4: Machine Learning hyperparameter optimization.
    
    This example demonstrates optimizing RL/ML model hyperparameters
    for reinforcement learning agents.
    """
    print("\n" + "="*60)
    print("EXAMPLE 4: ML Hyperparameter Optimization")
    print("="*60)
    
    param_space = get_parameter_space()
    
    # Get ML parameters
    ml_params = param_space.get_parameter_space(['rl_ml'])
    
    print("🧠 ML/RL Hyperparameter Categories:")
    
    # Group parameters by type
    network_params = {}
    learning_params = {}
    rl_params = {}
    
    for param_name, param_def in ml_params.items():
        param_key = param_name.replace('rl_ml_', '')
        
        if any(x in param_key for x in ['layer', 'neuron', 'activation']):
            network_params[param_key] = param_def.default
        elif any(x in param_key for x in ['learning', 'batch', 'optimizer']):
            learning_params[param_key] = param_def.default
        else:
            rl_params[param_key] = param_def.default
    
    print("  Network Architecture:")
    for param, value in network_params.items():
        print(f"    {param}: {value}")
    
    print("  Learning Parameters:")
    for param, value in learning_params.items():
        print(f"    {param}: {value}")
    
    print("  RL-Specific Parameters:")
    for param, value in rl_params.items():
        print(f"    {param}: {value}")
    
    # Simulate ML model configuration
    print(f"\n🎯 Example ML Configuration:")
    ml_sample = param_space.sample_parameters(['rl_ml'], n_samples=1, seed=456)[0]
    
    print("  Suggested RL Agent Configuration:")
    print(f"    Network: {ml_sample['rl_ml_hidden_layers']} layers x {ml_sample['rl_ml_neurons_per_layer']} neurons")
    print(f"    Activation: {ml_sample['rl_ml_activation_function']}")
    print(f"    Learning rate: {ml_sample['rl_ml_learning_rate']:.6f}")
    print(f"    Batch size: {ml_sample['rl_ml_batch_size']}")
    print(f"    Exploration: ε={ml_sample['rl_ml_epsilon_start']:.2f} → {ml_sample['rl_ml_epsilon_end']:.2f}")


def example_5_comprehensive_optimization():
    """
    Example 5: Comprehensive optimization across all parameter categories.
    
    This example shows how to run a full optimization across all
    parameter categories for maximum performance.
    """
    print("\n" + "="*60)
    print("EXAMPLE 5: Comprehensive Multi-Category Optimization")
    print("="*60)
    
    param_space = get_parameter_space()
    
    # Show what a comprehensive optimization would include
    all_categories = ['rl_ml', 'strategy', 'feature_engineering', 'technical_indicators', 'risk_management']
    
    print("🌐 Comprehensive Optimization Scope:")
    total_params = 0
    
    for category in all_categories:
        cat_params = param_space.get_parameter_space([category])
        total_params += len(cat_params)
        print(f"  {category.replace('_', ' ').title()}: {len(cat_params)} parameters")
    
    print(f"  Total optimization space: {total_params} parameters")
    
    # Calculate approximate search space size
    continuous_params = 0
    discrete_params = 0
    categorical_params = 0
    
    all_params = param_space.get_parameter_space()
    for param_def in all_params.values():
        if param_def.param_type.value in ['float', 'int']:
            if param_def.param_type.value == 'float':
                continuous_params += 1
            else:
                discrete_params += 1
        else:
            categorical_params += 1
    
    print(f"\n📊 Parameter Space Composition:")
    print(f"  Continuous parameters: {continuous_params}")
    print(f"  Discrete parameters: {discrete_params}")
    print(f"  Categorical parameters: {categorical_params}")
    
    print(f"\n💡 Recommended Optimization Strategy:")
    print("  1. Start with strategy + risk management (15-30 trials)")
    print("  2. Add technical indicators (50-100 trials)")
    print("  3. Include feature engineering (100-200 trials)")
    print("  4. Add ML hyperparameters (200-500 trials)")
    print("  5. Multi-objective optimization for final tuning")
    
    # Show example configuration for Bayesian optimization
    print(f"\n🎯 Bayesian Optimization Configuration:")
    print("  Sampler: TPE (Tree-structured Parzen Estimator)")
    print("  Objective: Multi-objective (Sharpe + Calmar ratio)")
    print("  Pruning: Median pruner for early stopping")
    print("  Trials: 500-1000 for production optimization")


def example_6_parameter_validation():
    """
    Example 6: Parameter validation and constraint checking.
    
    This example demonstrates how to validate parameters and
    handle constraint violations.
    """
    print("\n" + "="*60)
    print("EXAMPLE 6: Parameter Validation and Constraints")
    print("="*60)
    
    param_space = get_parameter_space()
    
    # Test valid parameters
    print("✅ Testing Valid Parameters:")
    valid_params = {
        'strategy_initial_capital': 50000,
        'strategy_max_positions': 5,
        'risk_management_stop_loss_pct': 0.03,
        'technical_indicators_rsi_period': 14
    }
    
    is_valid, errors = param_space.validate_parameters(valid_params)
    print(f"  Parameters: {valid_params}")
    print(f"  Valid: {is_valid}")
    print(f"  Errors: {errors}")
    
    # Test invalid parameters
    print(f"\n❌ Testing Invalid Parameters:")
    invalid_params = {
        'strategy_initial_capital': -1000,  # Invalid: negative
        'strategy_max_positions': 25,       # Invalid: too high
        'risk_management_stop_loss_pct': 0.5,  # Invalid: too high
        'technical_indicators_rsi_period': 5,   # Invalid: too low
        'unknown_parameter': 'test'         # Invalid: doesn't exist
    }
    
    is_valid, errors = param_space.validate_parameters(invalid_params)
    print(f"  Parameters: {invalid_params}")
    print(f"  Valid: {is_valid}")
    print(f"  Errors:")
    for error in errors:
        print(f"    - {error}")
    
    # Show parameter constraints
    print(f"\n📋 Parameter Constraint Examples:")
    sample_params = ['strategy_initial_capital', 'risk_management_stop_loss_pct', 'rl_ml_learning_rate']
    
    all_params = param_space.get_parameter_space()
    for param_name in sample_params:
        if param_name in all_params:
            param_def = all_params[param_name]
            print(f"  {param_name}:")
            print(f"    Type: {param_def.param_type.value}")
            print(f"    Range: {param_def.bounds}")
            print(f"    Default: {param_def.default}")
            if param_def.log_scale:
                print(f"    Log scale: Yes")


def main():
    """Run all parameter space usage examples."""
    print("TRADING BOT PARAMETER SPACE - USAGE EXAMPLES")
    print("="*80)
    print("This demonstration shows how to use the comprehensive parameter space")
    print("for optimization and backtesting of trading strategies.")
    
    try:
        example_1_basic_parameter_exploration()
        example_2_strategy_optimization()
        example_3_technical_indicator_tuning()
        example_4_ml_hyperparameter_optimization()
        example_5_comprehensive_optimization()
        example_6_parameter_validation()
        
        print("\n" + "="*80)
        print("🎉 ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nNext steps:")
        print("1. Integrate with your trading bot's main optimization loop")
        print("2. Set up automated parameter sweeps for strategy development")
        print("3. Use the parameter space for A/B testing different configurations")
        print("4. Implement multi-objective optimization for robust strategies")
        
    except Exception as e:
        print(f"\n❌ Example execution failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()