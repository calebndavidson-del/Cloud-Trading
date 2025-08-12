"""
Learning Module

This module provides machine learning training and performance monitoring including:
- Reward calculation for RL agents
- Model training orchestration
- Performance logging and analysis
- Learning curve visualization
- Model evaluation and validation

Supports continuous learning and model improvement in production environments.
"""

from .reward_calculator import RewardCalculator, CustomRewardFunction
from .model_trainer import ModelTrainer, TrainingPipeline
from .performance_logger import PerformanceLogger, MetricsTracker

__all__ = [
    'RewardCalculator',
    'CustomRewardFunction',
    'ModelTrainer',
    'TrainingPipeline',
    'PerformanceLogger',
    'MetricsTracker'
]