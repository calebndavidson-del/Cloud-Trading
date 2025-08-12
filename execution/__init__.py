"""
Execution Module

This module provides order execution and portfolio management capabilities including:
- Order management and execution
- Portfolio tracking and risk management
- Real-time position monitoring
- Trade settlement and reconciliation

Supports various order types and execution algorithms for optimal trade execution.
"""

from .order_executor import OrderExecutor, ExecutionAlgorithm
from .portfolio_tracker import PortfolioTracker, RiskManager

__all__ = [
    'OrderExecutor',
    'ExecutionAlgorithm',
    'PortfolioTracker',
    'RiskManager'
]