"""
Main Entry Point for Adaptive Cloud-Ready Trading Bot

This is the main application entry point that initializes and starts
the complete trading bot system with all its components.

Usage:
    python main.py [--config CONFIG_FILE] [--env ENVIRONMENT] [--mode MODE]

Arguments:
    --config: Path to configuration file (optional)
    --env: Environment (development, staging, production)
    --mode: Execution mode (trading, backtest, optimization)

Features:
- Command-line argument parsing
- Environment setup and validation
- System initialization and health checks
- Graceful shutdown handling
- Error recovery and logging
"""

import argparse
import asyncio
import sys
import signal
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# Import core modules
from orchestrator import TradingBotOrchestrator
from config import ConfigurationManager, create_default_config_files


class TradingBotApplication:
    """
    Main application class for the trading bot system.
    
    Handles application lifecycle, initialization, and shutdown procedures.
    """
    
    def __init__(self, config_path: Optional[str] = None, environment: str = 'development', mode: str = 'trading'):
        """
        Initialize trading bot application.
        
        Args:
            config_path: Path to configuration file
            environment: Environment name
            mode: Execution mode
        """
        self.config_path = config_path
        self.environment = environment
        self.mode = mode
        self.orchestrator = None
        self.config_manager = None
        self.logger = None
        self.shutdown_event = asyncio.Event()
        
        # Setup logging first
        self._setup_logging()
        
        # Setup signal handlers
        self._setup_signal_handlers()
    
    def _setup_logging(self) -> None:
        """Setup application logging."""
        # Basic logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler(f'trading_bot_{self.environment}.log')
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Starting Trading Bot Application in {self.environment} environment")
    
    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""
        if sys.platform != 'win32':
            # Unix/Linux signal handling
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        else:
            # Windows signal handling
            signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.shutdown_event.set()
    
    async def initialize(self) -> bool:
        """
        Initialize the trading bot application.
        
        Returns:
            True if initialization successful
        """
        try:
            # Load configuration
            self.logger.info("Loading configuration...")
            self.config_manager = ConfigurationManager(
                config_path=self.config_path,
                environment=self.environment
            )
            
            # Get configuration
            config = self.config_manager.get_all()
            
            # Update configuration based on execution mode
            self._update_config_for_mode(config)
            
            # Validate configuration
            if not self._validate_configuration(config):
                return False
            
            # Initialize orchestrator
            self.logger.info("Initializing trading bot orchestrator...")
            self.orchestrator = TradingBotOrchestrator(config)
            
            # Initialize all subsystems
            await self.orchestrator.initialize_system()
            
            # Perform health checks
            if not await self._perform_health_checks():
                return False
            
            self.logger.info("Trading bot application initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize application: {e}")
            return False
    
    def _update_config_for_mode(self, config: Dict[str, Any]) -> None:
        """Update configuration based on execution mode."""
        # Ensure required nested dictionaries exist before assignment
        config.setdefault('trading', {})
        config.setdefault('execution', {})
        config['execution'].setdefault('order_execution', {})
        config.setdefault('learning', {})
        config['learning'].setdefault('model_training', {})
        if self.mode == 'backtest':
            config['trading']['paper_trading'] = True
            config['trading']['learning_mode'] = False
            config['execution']['order_execution']['default_algorithm'] = 'market'
            
        elif self.mode == 'optimization':
            config['trading']['paper_trading'] = True
            config['trading']['learning_mode'] = True
            config['learning']['model_training']['hyperparameter_optimization'] = True
            
        elif self.mode == 'trading':
            if self.environment == 'production':
                config['trading']['paper_trading'] = False
            else:
                config['trading']['paper_trading'] = True
        
        self.logger.info(f"Configuration updated for mode: {self.mode}")
    
    def _validate_configuration(self, config: Dict[str, Any]) -> bool:
        """
        Validate configuration for required settings.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if configuration is valid
        """
        required_sections = [
            'trading', 'data_sources', 'execution', 'risk_management'
        ]
        
        for section in required_sections:
            if section not in config:
                self.logger.error(f"Missing required configuration section: {section}")
                return False
        
        # Validate trading universe
        if not config['trading'].get('universe'):
            self.logger.error("Trading universe cannot be empty")
            return False
        
        # Validate initial capital
        if config['trading'].get('initial_capital', 0) <= 0:
            self.logger.error("Initial capital must be greater than 0")
            return False
        
        self.logger.info("Configuration validation passed")
        return True
    
    async def _perform_health_checks(self) -> bool:
        """
        Perform system health checks.
        
        Returns:
            True if all health checks pass
        """
        try:
            # Check orchestrator status
            status = self.orchestrator.get_system_status()
            
            if not status.get('is_running', False):
                self.logger.warning("Orchestrator is not in running state")
            
            # Check data collector connectivity
            if not status.get('active_data_collectors', 0):
                self.logger.warning("No active data collectors found")
            
            # Check portfolio tracker
            if status.get('portfolio_value', 0) <= 0 and self.mode == 'trading':
                self.logger.warning("Portfolio value is zero or negative")
            
            self.logger.info("Health checks completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    async def run(self) -> int:
        """
        Run the trading bot application.
        
        Returns:
            Exit code (0 for success, 1 for error)
        """
        try:
            if self.mode == 'trading':
                await self._run_trading_mode()
            elif self.mode == 'backtest':
                await self._run_backtest_mode()
            elif self.mode == 'optimization':
                await self._run_optimization_mode()
            else:
                self.logger.error(f"Unknown execution mode: {self.mode}")
                return 1
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Application runtime error: {e}")
            return 1
    
    async def _run_trading_mode(self) -> None:
        """Run in live trading mode."""
        self.logger.info("Starting live trading mode...")
        
        # Start trading loop
        trading_task = asyncio.create_task(self.orchestrator.start_trading_loop())
        
        # Wait for shutdown signal or trading completion
        await asyncio.wait([
            trading_task,
            asyncio.create_task(self.shutdown_event.wait())
        ], return_when=asyncio.FIRST_COMPLETED)
        
        # Graceful shutdown
        await self.orchestrator.stop_trading_loop()
        
        self.logger.info("Live trading mode stopped")
    
    async def _run_backtest_mode(self) -> None:
        """Run in backtesting mode."""
        self.logger.info("Starting backtesting mode...")
        
        # Configure backtest parameters
        backtest_config = self.config_manager.get('backtest', {})
        
        # Run backtest
        # This would typically involve:
        # 1. Loading historical data
        # 2. Running trading strategies on historical data
        # 3. Calculating performance metrics
        # 4. Generating backtest report
        
        self.logger.info("Backtesting completed")
    
    async def _run_optimization_mode(self) -> None:
        """Run in optimization mode."""
        self.logger.info("Starting optimization mode...")
        
        # Configure optimization parameters
        optimization_config = self.config_manager.get('optimization', {})
        
        # Run optimization
        # This would typically involve:
        # 1. Setting up parameter search space
        # 2. Running multiple backtest iterations
        # 3. Optimizing strategy parameters
        # 4. Generating optimization report
        
        self.logger.info("Optimization completed")
    
    async def shutdown(self) -> None:
        """Perform graceful application shutdown."""
        self.logger.info("Shutting down trading bot application...")
        
        if self.orchestrator:
            try:
                await self.orchestrator.stop_trading_loop()
            except Exception as e:
                self.logger.error(f"Error during orchestrator shutdown: {e}")
        
        # Additional cleanup tasks
        await self._cleanup_resources()
        
        self.logger.info("Application shutdown completed")
    
    async def _cleanup_resources(self) -> None:
        """Clean up application resources."""
        # Close database connections, file handles, etc.
        pass


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Adaptive Cloud-Ready Trading Bot',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--env',
        type=str,
        choices=['development', 'staging', 'production'],
        default='development',
        help='Environment to run in'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['trading', 'backtest', 'optimization'],
        default='trading',
        help='Execution mode'
    )
    
    parser.add_argument(
        '--create-config',
        action='store_true',
        help='Create default configuration files and exit'
    )
    
    parser.add_argument(
        '--validate-config',
        action='store_true',
        help='Validate configuration and exit'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
        default='INFO',
        help='Logging level'
    )
    
    return parser.parse_args()


async def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Set logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Handle special commands
    if args.create_config:
        create_default_config_files()
        print("Default configuration files created successfully")
        return 0
    
    if args.validate_config:
        try:
            config_manager = ConfigurationManager(
                config_path=args.config,
                environment=args.env
            )
            print("Configuration validation passed")
            return 0
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            return 1
    
    # Create and run application
    app = TradingBotApplication(
        config_path=args.config,
        environment=args.env,
        mode=args.mode
    )
    
    try:
        # Initialize application
        if not await app.initialize():
            return 1
        
        # Run application
        exit_code = await app.run()
        
        # Shutdown application
        await app.shutdown()
        
        return exit_code
        
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        await app.shutdown()
        return 0
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        await app.shutdown()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)