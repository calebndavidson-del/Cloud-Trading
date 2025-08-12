"""
Features Module

This module provides advanced feature engineering and data processing capabilities
for the trading bot, including technical analysis, natural language processing,
and state representation for reinforcement learning agents.
"""

from .feature_engineering import FeatureEngineer
from .nlp_processor import NLPProcessor
from .state_builder import StateBuilder

__all__ = [
    'FeatureEngineer',
    'NLPProcessor',
    'StateBuilder'
]