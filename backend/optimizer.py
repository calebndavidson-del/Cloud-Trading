"""
Backtesting and parameter optimization engine.
"""
import optuna
import numpy as np
from typing import Dict, List, Any, Tuple
import logging
from backend.metrics import compute_metrics, compute_rsi, compute_moving_average

logger = logging.getLogger(__name__)

def backtest_strategy(market_data: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Backtest a trading strategy with given parameters.
    
    Args:
        market_data: Historical market data
        parameters: Strategy parameters to test
    
    Returns:
        Backtest results including trades and metrics
    """
    try:
        trades = []
        position = 0
        cash = parameters.get('initial_capital', 10000)
        
        # Simple moving average crossover strategy example
        for symbol, data in market_data.items():
            if 'error' in data:
                continue
                
            # Simulate historical prices (in real implementation, use actual historical data)
            prices = simulate_price_series(data['price'], 30)
            
            short_ma_period = parameters.get('short_ma_period', 5)
            long_ma_period = parameters.get('long_ma_period', 15)
            
            for i in range(long_ma_period, len(prices)):
                short_ma = compute_moving_average(prices[i-short_ma_period:i], short_ma_period)
                long_ma = compute_moving_average(prices[i-long_ma_period:i], long_ma_period)
                current_price = prices[i]
                
                # Buy signal: short MA crosses above long MA
                if short_ma > long_ma and position == 0:
                    shares = cash // current_price
                    if shares > 0:
                        position = shares
                        cash -= shares * current_price
                        trades.append({
                            'symbol': symbol,
                            'action': 'buy',
                            'price': current_price,
                            'shares': shares,
                            'timestamp': i
                        })
                
                # Sell signal: short MA crosses below long MA
                elif short_ma < long_ma and position > 0:
                    cash += position * current_price
                    pnl = (current_price - trades[-1]['price']) * position
                    trades.append({
                        'symbol': symbol,
                        'action': 'sell',
                        'price': current_price,
                        'shares': position,
                        'pnl': pnl,
                        'timestamp': i
                    })
                    position = 0
        
        # Calculate trade PnLs for metrics
        trade_pnls = [trade for trade in trades if 'pnl' in trade]
        metrics = compute_metrics(trade_pnls)
        
        return {
            'trades': trades,
            'metrics': metrics,
            'final_portfolio_value': cash + (position * prices[-1] if prices else 0),
            'parameters': parameters
        }
    
    except Exception as e:
        logger.error(f"Error in backtesting: {e}")
        return {'error': str(e)}

def simulate_price_series(base_price: float, length: int) -> List[float]:
    """
    Simulate a price series for backtesting purposes.
    
    Args:
        base_price: Starting price
        length: Number of price points to generate
    
    Returns:
        List of simulated prices
    """
    np.random.seed(42)  # For reproducible results
    returns = np.random.normal(0.001, 0.02, length)  # Daily returns with drift
    prices = [base_price]
    
    for ret in returns:
        new_price = prices[-1] * (1 + ret)
        prices.append(max(new_price, 0.01))  # Prevent negative prices
    
    return prices

def optimize_strategy(market_data: Dict[str, Any], n_trials: int = 100) -> Dict[str, Any]:
    """
    Optimize strategy parameters using Optuna.
    
    Args:
        market_data: Market data for optimization
        n_trials: Number of optimization trials
    
    Returns:
        Optimization results with best parameters
    """
    try:
        def objective(trial):
            parameters = {
                'initial_capital': 10000,
                'short_ma_period': trial.suggest_int('short_ma_period', 3, 10),
                'long_ma_period': trial.suggest_int('long_ma_period', 10, 30)
            }
            
            # Ensure short MA period is less than long MA period
            if parameters['short_ma_period'] >= parameters['long_ma_period']:
                return -1000  # Penalty for invalid parameters
            
            backtest_result = backtest_strategy(market_data, parameters)
            
            if 'error' in backtest_result:
                return -1000
            
            # Optimize for Sharpe ratio with penalty for low number of trades
            metrics = backtest_result['metrics']
            sharpe = metrics.get('sharpe', 0)
            num_trades = metrics.get('total_trades', 0)
            
            # Penalty if too few trades
            if num_trades < 5:
                sharpe -= 1
            
            return sharpe
        
        study = optuna.create_study(direction='maximize')
        study.optimize(objective, n_trials=n_trials, show_progress_bar=False)
        
        best_params = study.best_params
        best_params['initial_capital'] = 10000
        
        # Run final backtest with best parameters
        best_backtest = backtest_strategy(market_data, best_params)
        
        return {
            'best_params': best_params,
            'best_value': study.best_value,
            'backtest_results': best_backtest,
            'optimization_trials': n_trials
        }
    
    except Exception as e:
        logger.error(f"Error in optimization: {e}")
        return {'error': str(e)}