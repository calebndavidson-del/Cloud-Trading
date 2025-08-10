"""
AWS ECS Strategy Engine - Always-on trading strategy orchestrator.
This runs as a containerized service in ECS and manages the trading strategy.
"""
import time
import json
import logging
import signal
import sys
from datetime import datetime, timedelta
from typing import Dict, Any
import asyncio

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class TradingStrategyEngine:
    """
    Main trading strategy engine that runs continuously in ECS.
    """
    
    def __init__(self):
        self.running = True
        self.aws_manager = None
        self.config = None
        self.last_data_fetch = None
        self.trading_enabled = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        self.running = False
    
    async def initialize(self):
        """Initialize the strategy engine."""
        try:
            # Import AWS services
            import sys
            import os
            sys.path.append('/app')
            
            from aws.services import create_aws_manager
            from backend.config import get_config
            
            # Initialize AWS services
            self.aws_manager = create_aws_manager()
            self.config = get_config()
            
            logger.info("Strategy engine initialized successfully")
            
            # Load configuration from DynamoDB if available
            await self._load_remote_config()
            
            # Log startup information
            self.aws_manager.store_logs_s3(
                self.config['aws']['s3']['logs_bucket'],
                f"Strategy engine started at {datetime.utcnow().isoformat()}",
                "startup"
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize strategy engine: {e}")
            raise
    
    async def _load_remote_config(self):
        """Load configuration from DynamoDB."""
        try:
            remote_config = self.aws_manager.get_config(
                self.config['aws']['dynamodb']['config_table']
            )
            
            if remote_config:
                # Merge remote config with local config
                self.config.update(remote_config)
                logger.info("Loaded remote configuration from DynamoDB")
            else:
                # Store current config in DynamoDB
                self.aws_manager.store_config(
                    self.config['aws']['dynamodb']['config_table'],
                    self.config
                )
                logger.info("Stored initial configuration in DynamoDB")
                
        except Exception as e:
            logger.error(f"Error loading remote config: {e}")
    
    async def run_strategy_loop(self):
        """Main strategy execution loop."""
        logger.info("Starting strategy execution loop...")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Fetch latest market data via Lambda
                market_data = await self._fetch_market_data()
                
                if market_data and 'error' not in market_data:
                    # Analyze market data and make trading decisions
                    await self._analyze_and_trade(market_data)
                    
                    # Update strategy state
                    await self._update_strategy_state(market_data)
                
                # Calculate sleep time to maintain consistent intervals
                execution_time = time.time() - start_time
                sleep_time = max(0, 60 - execution_time)  # Run every minute
                
                if self.running:
                    await asyncio.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"Error in strategy loop: {e}")
                await asyncio.sleep(30)  # Wait before retrying
    
    async def _fetch_market_data(self) -> Dict[str, Any]:
        """Fetch market data via Lambda function."""
        try:
            payload = {
                'symbols': self.config['trading']['default_symbols']
            }
            
            result = self.aws_manager.invoke_lambda(
                self.config['aws']['lambda']['function_name'],
                payload
            )
            
            if 'body' in result:
                return json.loads(result['body'])
            else:
                logger.error(f"Unexpected Lambda response: {result}")
                return {'error': 'Invalid Lambda response'}
                
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            return {'error': str(e)}
    
    async def _analyze_and_trade(self, market_data: Dict[str, Any]):
        """Analyze market data and execute trading strategy."""
        try:
            from backend.optimizer import backtest_strategy
            from backend.paper_trader import PaperTrader
            from backend.metrics import compute_rsi, compute_moving_average
            
            # Simple momentum strategy example
            for symbol, data in market_data.get('market_data', {}).items():
                if 'error' in data:
                    continue
                
                current_price = data['price']
                
                # Get historical prices (simplified - in real implementation, 
                # you'd maintain price history in DynamoDB)
                historical_prices = self._get_price_history(symbol, current_price)
                
                # Calculate technical indicators
                rsi = compute_rsi(historical_prices)
                ma_5 = compute_moving_average(historical_prices, 5)
                ma_20 = compute_moving_average(historical_prices, 20)
                
                # Trading signal logic
                should_buy = (rsi < 30 and current_price > ma_5 and ma_5 > ma_20)
                should_sell = (rsi > 70 or current_price < ma_5)
                
                # Execute trades (paper trading for safety)
                if should_buy and self.config['trading'].get('paper_trading', True):
                    await self._execute_paper_trade(symbol, 'buy', current_price, data)
                elif should_sell:
                    await self._execute_paper_trade(symbol, 'sell', current_price, data)
                
                logger.debug(f"{symbol}: Price=${current_price:.2f}, RSI={rsi:.1f}, MA5=${ma_5:.2f}, MA20=${ma_20:.2f}")
                
        except Exception as e:
            logger.error(f"Error in analyze_and_trade: {e}")
    
    def _get_price_history(self, symbol: str, current_price: float) -> list:
        """Get or simulate price history for a symbol."""
        # In a real implementation, this would fetch from DynamoDB or other storage
        # For now, simulate some price history
        import random
        random.seed(hash(symbol) % 1000)
        
        prices = []
        base_price = current_price * random.uniform(0.95, 1.05)
        
        for i in range(30):  # 30 data points
            variation = random.uniform(-0.02, 0.02)
            new_price = base_price * (1 + variation)
            prices.append(new_price)
            base_price = new_price
        
        prices.append(current_price)  # Add current price
        return prices
    
    async def _execute_paper_trade(self, symbol: str, action: str, price: float, market_data: Dict[str, Any]):
        """Execute a paper trade and store in DynamoDB."""
        try:
            trade = {
                'symbol': symbol,
                'action': action,
                'price': price,
                'timestamp': datetime.utcnow().isoformat(),
                'market_data': market_data,
                'strategy': 'momentum_rsi',
                'paper_trade': True
            }
            
            # Calculate position size (simplified)
            if action == 'buy':
                portfolio_value = 10000  # Simplified
                position_size = portfolio_value * 0.1  # 10% per position
                shares = int(position_size / price)
                trade['shares'] = shares
                trade['cost'] = shares * price
            
            # Store trade in DynamoDB
            success = self.aws_manager.store_trade(
                self.config['aws']['dynamodb']['trades_table'],
                trade
            )
            
            if success:
                logger.info(f"Executed paper trade: {action} {trade.get('shares', 0)} shares of {symbol} at ${price:.2f}")
            
        except Exception as e:
            logger.error(f"Error executing paper trade: {e}")
    
    async def _update_strategy_state(self, market_data: Dict[str, Any]):
        """Update strategy state in DynamoDB."""
        try:
            state = {
                'id': 'strategy_state',
                'timestamp': datetime.utcnow().isoformat(),
                'last_execution': datetime.utcnow().isoformat(),
                'market_data_timestamp': market_data.get('timestamp'),
                'symbols_processed': len(market_data.get('market_data', {})),
                'strategy_status': 'running',
                'ttl': int((datetime.utcnow() + timedelta(days=1)).timestamp())
            }
            
            # Store in DynamoDB
            dynamodb = self.aws_manager.dynamodb
            table = dynamodb.Table(self.config['aws']['dynamodb']['state_table'])
            table.put_item(Item=state)
            
        except Exception as e:
            logger.error(f"Error updating strategy state: {e}")
    
    async def shutdown(self):
        """Graceful shutdown of the strategy engine."""
        logger.info("Shutting down strategy engine...")
        
        try:
            # Log shutdown
            self.aws_manager.store_logs_s3(
                self.config['aws']['s3']['logs_bucket'],
                f"Strategy engine stopped at {datetime.utcnow().isoformat()}",
                "shutdown"
            )
            
            # Update final state
            state = {
                'id': 'strategy_state',
                'timestamp': datetime.utcnow().isoformat(),
                'strategy_status': 'stopped',
                'shutdown_reason': 'graceful_shutdown'
            }
            
            dynamodb = self.aws_manager.dynamodb
            table = dynamodb.Table(self.config['aws']['dynamodb']['state_table'])
            table.put_item(Item=state)
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
        
        logger.info("Strategy engine shutdown complete")

async def main():
    """Main entry point for the strategy engine."""
    strategy_engine = TradingStrategyEngine()
    
    try:
        await strategy_engine.initialize()
        await strategy_engine.run_strategy_loop()
    except Exception as e:
        logger.error(f"Fatal error in strategy engine: {e}")
        sys.exit(1)
    finally:
        await strategy_engine.shutdown()

if __name__ == "__main__":
    asyncio.run(main())