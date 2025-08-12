"""
Models Module

This module provides machine learning and prediction capabilities including:
- ML prediction models for price and return forecasting
- Reinforcement learning agents for automated trading
- Strategy management and coordination
- Model ensemble and combination techniques

Supports both traditional ML and advanced deep learning approaches.
"""

from .predictor import Predictor, EnsemblePredictor
from .rl_agent import RLAgent, ActorCriticAgent, DQNAgent
from .strategy_manager import StrategyManager

__all__ = [
    'Predictor',
    'EnsemblePredictor',
    'RLAgent',
    'ActorCriticAgent', 
    'DQNAgent',
    'StrategyManager'
]