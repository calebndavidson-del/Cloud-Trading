"""
Simulated paper trading engine.
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import logging
from backend.data_collector import fetch_market_data
from backend.metrics import compute_metrics

logger = logging.getLogger(__name__)

class PaperTrader:
    """
    Paper trading simulation engine.
    """
    
    def __init__(self, initial_capital: float = 10000):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # symbol -> shares
        self.trades = []
        self.portfolio_history = []
        
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate current portfolio value."""
        portfolio_value = self.cash
        
        for symbol, shares in self.positions.items():
            if symbol in current_prices:
                portfolio_value += shares * current_prices[symbol]
        
        return portfolio_value
    
    def buy(self, symbol: str, shares: int, price: float) -> bool:
        """
        Execute a buy order.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares to buy
            price: Price per share
        
        Returns:
            True if order executed successfully
        """
        cost = shares * price
        
        if cost > self.cash:
            logger.warning(f"Insufficient funds to buy {shares} shares of {symbol}")
            return False
        
        self.cash -= cost
        self.positions[symbol] = self.positions.get(symbol, 0) + shares
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'buy',
            'shares': shares,
            'price': price,
            'cost': cost
        }
        
        self.trades.append(trade)
        logger.info(f"Bought {shares} shares of {symbol} at ${price:.2f}")
        
        return True
    
    def sell(self, symbol: str, shares: int, price: float) -> bool:
        """
        Execute a sell order.
        
        Args:
            symbol: Stock symbol
            shares: Number of shares to sell
            price: Price per share
        
        Returns:
            True if order executed successfully
        """
        current_shares = self.positions.get(symbol, 0)
        
        if shares > current_shares:
            logger.warning(f"Insufficient shares to sell {shares} of {symbol} (have {current_shares})")
            return False
        
        proceeds = shares * price
        self.cash += proceeds
        self.positions[symbol] -= shares
        
        if self.positions[symbol] == 0:
            del self.positions[symbol]
        
        # Calculate PnL if we have previous buy trades
        buy_trades = [t for t in self.trades if t['symbol'] == symbol and t['action'] == 'buy']
        if buy_trades:
            avg_buy_price = sum(t['price'] * t['shares'] for t in buy_trades) / sum(t['shares'] for t in buy_trades)
            pnl = (price - avg_buy_price) * shares
        else:
            pnl = 0
        
        trade = {
            'timestamp': datetime.now().isoformat(),
            'symbol': symbol,
            'action': 'sell',
            'shares': shares,
            'price': price,
            'proceeds': proceeds,
            'pnl': pnl
        }
        
        self.trades.append(trade)
        logger.info(f"Sold {shares} shares of {symbol} at ${price:.2f} (PnL: ${pnl:.2f})")
        
        return True
    
    def get_summary(self) -> Dict[str, Any]:
        """Get trading summary and metrics."""
        try:
            # Get current market data for portfolio valuation
            symbols = list(self.positions.keys()) if self.positions else ['AAPL']
            market_data = fetch_market_data(symbols)
            
            current_prices = {}
            for symbol, data in market_data.items():
                if 'price' in data:
                    current_prices[symbol] = data['price']
            
            portfolio_value = self.get_portfolio_value(current_prices)
            total_return = portfolio_value - self.initial_capital
            return_pct = (total_return / self.initial_capital) * 100
            
            # Calculate trade metrics
            sell_trades = [t for t in self.trades if t['action'] == 'sell' and 'pnl' in t]
            metrics = compute_metrics(sell_trades)
            
            return {
                'initial_capital': self.initial_capital,
                'current_cash': self.cash,
                'positions': self.positions,
                'portfolio_value': portfolio_value,
                'total_return': total_return,
                'return_percentage': return_pct,
                'total_trades': len(self.trades),
                'completed_trades': len(sell_trades),
                'metrics': metrics,
                'recent_trades': self.trades[-10:] if self.trades else []
            }
        
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {'error': str(e)}

def paper_trade(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run paper trading with given parameters.
    
    Args:
        params: Trading parameters including strategy config
    
    Returns:
        Paper trading results and summary
    """
    try:
        trader = PaperTrader(params.get('initial_capital', 10000))
        
        # Get symbols to trade
        symbols = params.get('symbols', ['AAPL', 'GOOGL', 'MSFT'])
        
        # Fetch current market data
        market_data = fetch_market_data(symbols)
        
        if 'error' in market_data:
            return {'error': f"Failed to fetch market data: {market_data['error']}"}
        
        # Simple example strategy: buy stocks below their moving average
        for symbol, data in market_data.items():
            if 'error' in data:
                continue
            
            current_price = data['price']
            
            # Simple buy condition: if we have cash and the stock looks good
            available_cash = trader.cash * 0.2  # Use 20% of cash per position
            if available_cash > current_price:
                shares_to_buy = int(available_cash // current_price)
                if shares_to_buy > 0:
                    trader.buy(symbol, shares_to_buy, current_price)
        
        # Return summary
        summary = trader.get_summary()
        summary['strategy_params'] = params
        
        return summary
    
    except Exception as e:
        logger.error(f"Error in paper trading: {e}")
        return {'error': str(e)}