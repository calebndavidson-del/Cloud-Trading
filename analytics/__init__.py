"""
Enhanced Analytics Module for Trading Bot

This module provides advanced analytics capabilities including:
- Live bid-ask spread monitoring
- Market liquidity prediction
- Tail risk analysis (VaR, CVaR, drawdown probabilities)

Replaces simple standard deviation-based risk metrics with comprehensive
tail risk analysis for better extreme event risk management.
"""

from .spread_monitor import SpreadMonitor
from .liquidity_predictor import LiquidityPredictor
from .tail_risk_analyzer import TailRiskAnalyzer

__all__ = [
    'SpreadMonitor',
    'LiquidityPredictor', 
    'TailRiskAnalyzer'
]