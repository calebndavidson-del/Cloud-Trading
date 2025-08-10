"""
Financial metrics computation (net profit, Sharpe, RSI, etc.).
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)

def compute_metrics(trade_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Compute trading performance metrics.
    
    Args:
        trade_results: List of trade dictionaries with 'pnl' key
    
    Returns:
        Dictionary containing computed metrics
    """
    if not trade_results:
        return {"net_profit": 0, "sharpe": 0, "win_rate": 0, "max_drawdown": 0}
    
    try:
        pnls = [trade.get('pnl', 0) for trade in trade_results]
        returns = np.array(pnls)
        
        # Basic metrics
        net_profit = sum(returns)
        win_rate = len([r for r in returns if r > 0]) / len(returns) if returns.size > 0 else 0
        
        # Sharpe ratio (assuming daily returns)
        if returns.std() > 0:
            sharpe = (returns.mean() / returns.std()) * np.sqrt(252)  # Annualized
        else:
            sharpe = 0
        
        # Maximum drawdown
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = cumulative_returns - running_max
        max_drawdown = abs(min(drawdowns)) if len(drawdowns) > 0 else 0
        
        return {
            "net_profit": float(net_profit),
            "sharpe": float(sharpe),
            "win_rate": float(win_rate),
            "max_drawdown": float(max_drawdown),
            "total_trades": len(trade_results),
            "avg_trade": float(net_profit / len(trade_results)) if trade_results else 0
        }
    
    except Exception as e:
        logger.error(f"Error computing metrics: {e}")
        return {"error": str(e)}

def compute_rsi(prices: List[float], period: int = 14) -> float:
    """
    Compute Relative Strength Index (RSI).
    
    Args:
        prices: List of price values
        period: RSI calculation period
    
    Returns:
        RSI value (0-100)
    """
    if len(prices) < period + 1:
        return 50.0  # Neutral RSI
    
    try:
        prices_array = np.array(prices)
        deltas = np.diff(prices_array)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return float(rsi)
    
    except Exception as e:
        logger.error(f"Error computing RSI: {e}")
        return 50.0

def compute_moving_average(prices: List[float], period: int) -> float:
    """
    Compute simple moving average.
    
    Args:
        prices: List of price values
        period: Moving average period
    
    Returns:
        Moving average value
    """
    if len(prices) < period:
        return np.mean(prices) if prices else 0.0
    
    return float(np.mean(prices[-period:]))