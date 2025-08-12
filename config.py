"""
Configuration Management Module

Provides centralized configuration management for the trading bot system.
Supports multiple configuration sources, environment-specific settings,
dynamic configuration updates, and validation.

Features:
- YAML/JSON configuration file support
- Environment variable overrides
- Configuration validation
- Dynamic configuration updates
- Cloud deployment configurations
- Security and credentials management
"""

import os
import json
import yaml
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
from pathlib import Path


class ConfigurationManager:
    """
    Centralized configuration management for the trading bot system.
    
    Features:
    - Multi-source configuration loading
    - Environment-specific configurations
    - Configuration validation
    - Dynamic updates
    - Secure credential handling
    """
    
    def __init__(self, config_path: Optional[str] = None, environment: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_path: Path to configuration file
            environment: Environment name (dev, staging, prod)
        """
        self.config_path = config_path or self._get_default_config_path()
        self.environment = environment or os.getenv('TRADING_ENV', 'development')
        self.config = {}
        self.schema = self._load_config_schema()
        self.logger = logging.getLogger(__name__)
        
        # Load configuration
        self.load_configuration()
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path."""
        return os.path.join(os.path.dirname(__file__), 'config', f'{self.environment}.yaml')
    
    def _load_config_schema(self) -> Dict[str, Any]:
        """Load configuration schema for validation."""
        schema_path = os.path.join(os.path.dirname(__file__), 'config', 'schema.yaml')
        try:
            with open(schema_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning("Configuration schema not found, skipping validation")
            return {}
    
    def load_configuration(self) -> None:
        """Load configuration from file and environment variables."""
        # Load base configuration
        base_config = self._load_base_config()
        
        # Load environment-specific configuration
        env_config = self._load_environment_config()
        
        # Merge configurations
        self.config = self._merge_configs(base_config, env_config)
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Validate configuration
        self._validate_configuration()
        
        self.logger.info(f"Configuration loaded for environment: {self.environment}")
    
    def _load_base_config(self) -> Dict[str, Any]:
        """Load base configuration file."""
        base_path = os.path.join(os.path.dirname(__file__), 'config', 'base.yaml')
        return self._load_config_file(base_path)
    
    def _load_environment_config(self) -> Dict[str, Any]:
        """Load environment-specific configuration."""
        return self._load_config_file(self.config_path)
    
    def _load_config_file(self, file_path: str) -> Dict[str, Any]:
        """Load configuration from file."""
        if not os.path.exists(file_path):
            self.logger.warning(f"Configuration file not found: {file_path}")
            return {}
        
        try:
            with open(file_path, 'r') as f:
                if file_path.endswith('.yaml') or file_path.endswith('.yml'):
                    return yaml.safe_load(f) or {}
                elif file_path.endswith('.json'):
                    return json.load(f)
                else:
                    raise ValueError(f"Unsupported configuration file format: {file_path}")
        except Exception as e:
            self.logger.error(f"Error loading configuration file {file_path}: {e}")
            return {}
    
    def _merge_configs(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Merge configuration dictionaries."""
        merged = base.copy()
        
        for key, value in override.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides."""
        env_prefix = 'TRADING_'
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower().replace('_', '.')
                self._set_nested_value(self.config, config_key, self._parse_env_value(value))
    
    def _set_nested_value(self, config: Dict[str, Any], key_path: str, value: Any) -> None:
        """Set nested configuration value using dot notation."""
        keys = key_path.split('.')
        current = config
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _parse_env_value(self, value: str) -> Any:
        """Parse environment variable value to appropriate type."""
        # Try to parse as JSON first
        try:
            return json.loads(value)
        except (json.JSONDecodeError, ValueError):
            pass
        
        # Parse boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Parse numeric values
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def _validate_configuration(self) -> None:
        """Validate configuration against schema."""
        if not self.schema:
            return
        
        # Implement configuration validation logic
        # This would check required fields, data types, value ranges, etc.
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._get_nested_value(self.config, key, default)
    
    def _get_nested_value(self, config: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get nested configuration value using dot notation."""
        keys = key.split('.')
        current = config
        
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default
        
        return current
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        self._set_nested_value(self.config, key, value)
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update configuration with multiple values.
        
        Args:
            updates: Dictionary of configuration updates
        """
        self.config = self._merge_configs(self.config, updates)
    
    def get_all(self) -> Dict[str, Any]:
        """Get complete configuration."""
        return self.config.copy()
    
    def save_configuration(self, file_path: Optional[str] = None) -> None:
        """
        Save current configuration to file.
        
        Args:
            file_path: File path to save to (optional)
        """
        save_path = file_path or self.config_path
        
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w') as f:
                if save_path.endswith('.yaml') or save_path.endswith('.yml'):
                    yaml.dump(self.config, f, default_flow_style=False, indent=2)
                elif save_path.endswith('.json'):
                    json.dump(self.config, f, indent=2)
                
            self.logger.info(f"Configuration saved to: {save_path}")
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
    
    def reload_configuration(self) -> None:
        """Reload configuration from file."""
        self.load_configuration()
        self.logger.info("Configuration reloaded")


# Default configuration structure
DEFAULT_CONFIG = {
    'system': {
        'name': 'Adaptive Trading Bot',
        'version': '1.0.0',
        'environment': 'development',
        'debug': True,
        'log_level': 'INFO'
    },
    
    'trading': {
        'universe': ['AAPL', 'GOOGL', 'MSFT', 'TSLA'],
        'cycle_interval': 60,
        'learning_mode': True,
        'paper_trading': True,
        'initial_capital': 1000000,
        'base_currency': 'USD'
    },
    
    'data_sources': {
        'market_data': {
            'enabled': True,
            'providers': ['yahoo_finance', 'alpha_vantage'],
            'update_frequency': 60,
            'cache_duration': 300
        },
        'news_data': {
            'enabled': True,
            'providers': ['financial_news_api'],
            'sentiment_analysis': True,
            'update_frequency': 300
        },
        'earnings_data': {
            'enabled': False,
            'providers': ['earnings_api'],
            'update_frequency': 3600
        },
        'filings_data': {
            'enabled': False,
            'providers': ['sec_edgar'],
            'update_frequency': 3600
        },
        'order_book_data': {
            'enabled': False,
            'providers': ['level2_provider'],
            'depth_levels': 10
        },
        'social_data': {
            'enabled': False,
            'providers': ['twitter_api', 'reddit_api'],
            'sentiment_analysis': True
        },
        'options_data': {
            'enabled': False,
            'providers': ['options_api'],
            'update_frequency': 300
        },
        'macro_data': {
            'enabled': False,
            'providers': ['fred_api'],
            'update_frequency': 3600
        },
        'short_interest_data': {
            'enabled': False,
            'providers': ['short_interest_api'],
            'update_frequency': 3600
        },
        'etf_flows_data': {
            'enabled': False,
            'providers': ['etf_flows_api'],
            'update_frequency': 3600
        }
    },
    
    'feature_processing': {
        'engineering': {
            'technical_indicators': True,
            'statistical_features': True,
            'pattern_recognition': True,
            'lookback_periods': [5, 10, 20, 50, 100]
        },
        'nlp': {
            'sentiment_analysis': True,
            'entity_extraction': True,
            'topic_modeling': False,
            'language': 'en'
        },
        'state_building': {
            'sequence_length': 50,
            'normalization': 'standard',
            'feature_selection': True
        }
    },
    
    'models': {
        'predictors': {
            'linear_predictor': {
                'enabled': True,
                'model_type': 'ridge',
                'alpha': 1.0
            },
            'tree_predictor': {
                'enabled': True,
                'model_type': 'xgboost',
                'n_estimators': 100,
                'max_depth': 6
            },
            'neural_predictor': {
                'enabled': False,
                'architecture': 'lstm',
                'layers': [64, 32],
                'dropout': 0.2
            }
        },
        'rl_agents': {
            'dqn_agent': {
                'enabled': False,
                'state_size': 100,
                'action_size': 3,
                'learning_rate': 0.001
            },
            'actor_critic_agent': {
                'enabled': False,
                'state_size': 100,
                'action_size': 1,
                'actor_lr': 0.001,
                'critic_lr': 0.002
            }
        }
    },
    
    'strategy_management': {
        'allocation_method': 'equal_weight',
        'rebalance_frequency': 'daily',
        'strategies': {
            'momentum_strategy': {
                'enabled': True,
                'weight': 0.3,
                'lookback_period': 20
            },
            'mean_reversion_strategy': {
                'enabled': True,
                'weight': 0.3,
                'lookback_window': 50
            },
            'ml_prediction_strategy': {
                'enabled': True,
                'weight': 0.4,
                'confidence_threshold': 0.6
            }
        }
    },
    
    'execution': {
        'order_execution': {
            'default_algorithm': 'market',
            'max_order_value': 100000,
            'execution_delay': 0.1
        },
        'portfolio_tracking': {
            'initial_capital': 1000000,
            'benchmark': 'SPY',
            'rebalance_threshold': 0.05
        }
    },
    
    'risk_management': {
        'max_position_size': 0.1,
        'max_sector_concentration': 0.3,
        'max_drawdown': 0.15,
        'var_confidence': 0.95,
        'stop_loss': 0.05,
        'take_profit': 0.15
    },
    
    'learning': {
        'reward_calculation': {
            'reward_type': 'risk_adjusted',
            'risk_penalty': 0.1,
            'transaction_cost_penalty': 0.001
        },
        'model_training': {
            'training_frequency': 'weekly',
            'validation_split': 0.2,
            'hyperparameter_optimization': True
        },
        'performance_logging': {
            'logging_frequency': 'daily',
            'metrics_to_track': ['return', 'sharpe', 'drawdown'],
            'benchmark_symbol': 'SPY'
        }
    },
    
    'cloud': {
        'deployment': {
            'provider': 'aws',
            'region': 'us-east-1',
            'auto_scaling': True,
            'monitoring': True
        },
        'storage': {
            'data_bucket': 'trading-bot-data',
            'model_bucket': 'trading-bot-models',
            'log_bucket': 'trading-bot-logs'
        },
        'compute': {
            'instance_type': 't3.medium',
            'min_instances': 1,
            'max_instances': 5
        }
    },
    
    'security': {
        'encryption': {
            'data_at_rest': True,
            'data_in_transit': True,
            'key_rotation': True
        },
        'authentication': {
            'method': 'api_key',
            'token_expiry': 3600
        },
        'access_control': {
            'role_based': True,
            'audit_logging': True
        }
    },
    
    'monitoring': {
        'metrics': {
            'system_metrics': True,
            'business_metrics': True,
            'alert_thresholds': {
                'cpu_usage': 80,
                'memory_usage': 85,
                'error_rate': 5
            }
        },
        'logging': {
            'level': 'INFO',
            'format': 'json',
            'rotation': 'daily'
        }
    }
}


def create_default_config_files():
    """Create default configuration files."""
    config_dir = Path(__file__).parent / 'config'
    config_dir.mkdir(exist_ok=True)
    
    # Base configuration
    base_config_path = config_dir / 'base.yaml'
    with open(base_config_path, 'w') as f:
        yaml.dump(DEFAULT_CONFIG, f, default_flow_style=False, indent=2)
    
    # Environment-specific configurations
    environments = ['development', 'staging', 'production']
    
    for env in environments:
        env_config = DEFAULT_CONFIG.copy()
        
        if env == 'production':
            env_config['system']['debug'] = False
            env_config['system']['log_level'] = 'WARNING'
            env_config['trading']['paper_trading'] = False
        elif env == 'staging':
            env_config['system']['debug'] = False
            env_config['trading']['paper_trading'] = True
        
        env_config_path = config_dir / f'{env}.yaml'
        with open(env_config_path, 'w') as f:
            yaml.dump(env_config, f, default_flow_style=False, indent=2)


# Global configuration instance
config_manager = ConfigurationManager()


def get_config(key: str = None, default: Any = None) -> Any:
    """
    Get configuration value.
    
    Args:
        key: Configuration key (optional, returns full config if None)
        default: Default value if key not found
        
    Returns:
        Configuration value
    """
    if key is None:
        return config_manager.get_all()
    return config_manager.get(key, default)


def update_config(updates: Dict[str, Any]) -> None:
    """
    Update configuration.
    
    Args:
        updates: Configuration updates
    """
    config_manager.update(updates)


def reload_config() -> None:
    """Reload configuration from file."""
    config_manager.reload_configuration()


if __name__ == "__main__":
    # Create default configuration files if they don't exist
    create_default_config_files()
    print("Default configuration files created successfully")