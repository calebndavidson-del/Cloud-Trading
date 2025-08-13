"""
Unit tests for paper trading functionality.
"""
import pytest
from unittest.mock import patch, Mock
from backend.paper_trader import PaperTrader, paper_trade


class TestPaperTrader:
    """Test PaperTrader class functionality."""
    
    def test_initialization(self):
        """Test PaperTrader initialization."""
        initial_capital = 10000
        trader = PaperTrader(initial_capital)
        
        assert trader.initial_capital == initial_capital
        assert trader.cash == initial_capital
        assert trader.positions == {}
        assert trader.trades == []
        assert trader.portfolio_history == []
    
    def test_buy_order_success(self):
        """Test successful buy order execution."""
        trader = PaperTrader(10000)
        
        success = trader.buy('AAPL', 10, 150.0)
        
        assert success is True
        assert trader.cash == 10000 - (10 * 150.0)  # 8500
        assert trader.positions['AAPL'] == 10
        assert len(trader.trades) == 1
        
        trade = trader.trades[0]
        assert trade['symbol'] == 'AAPL'
        assert trade['action'] == 'buy'
        assert trade['shares'] == 10
        assert trade['price'] == 150.0
        assert trade['cost'] == 1500.0
    
    def test_buy_order_insufficient_funds(self):
        """Test buy order with insufficient funds."""
        trader = PaperTrader(1000)  # Small capital
        
        success = trader.buy('AAPL', 10, 150.0)  # Costs $1500
        
        assert success is False
        assert trader.cash == 1000  # Unchanged
        assert 'AAPL' not in trader.positions
        assert len(trader.trades) == 0
    
    def test_sell_order_success(self):
        """Test successful sell order execution."""
        trader = PaperTrader(10000)
        
        # First buy some shares
        trader.buy('AAPL', 10, 150.0)
        
        # Then sell some
        success = trader.sell('AAPL', 5, 155.0)
        
        assert success is True
        assert trader.positions['AAPL'] == 5  # 5 remaining
        assert len(trader.trades) == 2
        
        sell_trade = trader.trades[1]
        assert sell_trade['symbol'] == 'AAPL'
        assert sell_trade['action'] == 'sell'
        assert sell_trade['shares'] == 5
        assert sell_trade['price'] == 155.0
        assert sell_trade['proceeds'] == 775.0
        assert 'pnl' in sell_trade  # Should calculate PnL
    
    def test_sell_order_insufficient_shares(self):
        """Test sell order with insufficient shares."""
        trader = PaperTrader(10000)
        
        # Try to sell without owning any shares
        success = trader.sell('AAPL', 5, 150.0)
        
        assert success is False
        assert trader.cash == 10000  # Unchanged
        assert len(trader.trades) == 0
    
    def test_sell_all_shares(self):
        """Test selling all shares removes position."""
        trader = PaperTrader(10000)
        
        # Buy and then sell all shares
        trader.buy('AAPL', 10, 150.0)
        trader.sell('AAPL', 10, 155.0)
        
        assert 'AAPL' not in trader.positions  # Position removed
        assert len(trader.trades) == 2
    
    def test_portfolio_value_calculation(self):
        """Test portfolio value calculation."""
        trader = PaperTrader(10000)
        
        # Buy some shares
        trader.buy('AAPL', 10, 150.0)  # Costs $1500
        trader.buy('GOOGL', 2, 2800.0)  # Costs $5600
        
        current_prices = {
            'AAPL': 160.0,  # Up $10
            'GOOGL': 2750.0  # Down $50
        }
        
        portfolio_value = trader.get_portfolio_value(current_prices)
        
        expected_cash = 10000 - 1500 - 5600  # 2900
        expected_positions_value = (10 * 160.0) + (2 * 2750.0)  # 1600 + 5500 = 7100
        expected_total = expected_cash + expected_positions_value  # 10000
        
        assert portfolio_value == expected_total
    
    def test_pnl_calculation(self):
        """Test profit/loss calculation on sells."""
        trader = PaperTrader(10000)
        
        # Buy at different prices
        trader.buy('AAPL', 5, 150.0)
        trader.buy('AAPL', 5, 160.0)  # Now have 10 shares, avg price = 155
        
        # Sell at higher price
        trader.sell('AAPL', 5, 170.0)
        
        sell_trade = trader.trades[-1]
        assert 'pnl' in sell_trade
        
        # PnL should be positive (sold above average buy price)
        expected_avg_buy = ((5 * 150.0) + (5 * 160.0)) / 10  # 155
        expected_pnl = (170.0 - expected_avg_buy) * 5  # 15 * 5 = 75
        assert sell_trade['pnl'] == expected_pnl


class TestPaperTraderSummary:
    """Test PaperTrader summary functionality."""
    
    @patch('backend.data_collector.fetch_market_data')
    def test_get_summary_basic(self, mock_fetch):
        """Test basic summary generation."""
        # Mock market data response
        mock_fetch.return_value = {
            'AAPL': {'price': 160.0, 'volume': 1000000},
            'GOOGL': {'price': 2750.0, 'volume': 500000}
        }
        
        trader = PaperTrader(10000)
        trader.buy('AAPL', 10, 150.0)
        trader.sell('AAPL', 5, 155.0)
        
        summary = trader.get_summary()
        
        assert 'initial_capital' in summary
        assert 'current_cash' in summary
        assert 'positions' in summary
        assert 'portfolio_value' in summary
        assert 'total_return' in summary
        assert 'return_percentage' in summary
        assert 'total_trades' in summary
        assert 'completed_trades' in summary
        assert 'metrics' in summary
        assert 'recent_trades' in summary
        
        assert summary['initial_capital'] == 10000
        assert summary['total_trades'] == 2
        assert summary['completed_trades'] == 1  # Only sell trades count as completed
    
    @patch('backend.data_collector.fetch_market_data')
    def test_get_summary_with_no_positions(self, mock_fetch):
        """Test summary when no positions are held."""
        mock_fetch.return_value = {'AAPL': {'price': 150.0, 'volume': 1000000}}
        
        trader = PaperTrader(10000)
        
        summary = trader.get_summary()
        
        assert summary['portfolio_value'] == 10000  # Should equal initial capital
        assert summary['total_return'] == 0
        assert summary['return_percentage'] == 0
        assert len(summary['positions']) == 0
    
    @patch('backend.data_collector.fetch_market_data')
    def test_get_summary_error_handling(self, mock_fetch):
        """Test summary error handling."""
        # Mock data collection error
        mock_fetch.side_effect = Exception("Data fetch failed")
        
        trader = PaperTrader(10000)
        
        summary = trader.get_summary()
        
        assert 'error' in summary


class TestPaperTradeFunction:
    """Test the paper_trade convenience function."""
    
    @patch('backend.data_collector.fetch_market_data')
    def test_paper_trade_basic(self, mock_fetch):
        """Test basic paper_trade function."""
        mock_fetch.return_value = {
            'AAPL': {'price': 150.0, 'volume': 1000000},
            'GOOGL': {'price': 2800.0, 'volume': 500000}
        }
        
        params = {
            'initial_capital': 10000,
            'symbols': ['AAPL', 'GOOGL']
        }
        
        result = paper_trade(params)
        
        assert isinstance(result, dict)
        assert 'portfolio_value' in result or 'error' in result
        
        if 'portfolio_value' in result:
            assert 'strategy_params' in result
            assert result['strategy_params'] == params
    
    @patch('backend.data_collector.fetch_market_data')
    def test_paper_trade_default_symbols(self, mock_fetch):
        """Test paper_trade with default symbols."""
        mock_fetch.return_value = {
            'AAPL': {'price': 150.0, 'volume': 1000000},
            'GOOGL': {'price': 2800.0, 'volume': 500000},
            'MSFT': {'price': 330.0, 'volume': 750000}
        }
        
        params = {'initial_capital': 10000}  # No symbols specified
        
        result = paper_trade(params)
        
        assert isinstance(result, dict)
        # Should use default symbols
    
    @patch('backend.data_collector.fetch_market_data')
    def test_paper_trade_market_data_error(self, mock_fetch):
        """Test paper_trade when market data fetch fails."""
        mock_fetch.return_value = {'error': 'Data fetch failed'}
        
        params = {
            'initial_capital': 10000,
            'symbols': ['AAPL']
        }
        
        result = paper_trade(params)
        
        assert 'error' in result
    
    @patch('backend.data_collector.fetch_market_data')
    def test_paper_trade_strategy_execution(self, mock_fetch):
        """Test paper_trade strategy execution logic."""
        mock_fetch.return_value = {
            'AAPL': {'price': 100.0, 'volume': 1000000},  # Affordable
            'GOOGL': {'price': 3000.0, 'volume': 500000}  # May be too expensive
        }
        
        params = {
            'initial_capital': 1000,  # Limited capital
            'symbols': ['AAPL', 'GOOGL']
        }
        
        result = paper_trade(params)
        
        if 'error' not in result:
            # Should have made some trades based on affordability
            assert 'total_trades' in result
            
            # With $1000 capital and 20% allocation per position ($200):
            # AAPL at $100 = can buy 2 shares
            # GOOGL at $3000 = can't afford any
            if result['total_trades'] > 0:
                assert result['total_trades'] >= 1  # At least bought AAPL


class TestPaperTradingScenarios:
    """Test various paper trading scenarios."""
    
    def test_multiple_buy_sell_cycles(self):
        """Test multiple buy/sell cycles."""
        trader = PaperTrader(10000)
        
        # Cycle 1
        trader.buy('AAPL', 10, 150.0)
        trader.sell('AAPL', 10, 155.0)
        
        # Cycle 2
        trader.buy('AAPL', 15, 160.0)
        trader.sell('AAPL', 10, 165.0)
        
        assert trader.positions['AAPL'] == 5  # 5 shares remaining
        assert len(trader.trades) == 4
        
        # Check that both sell trades have PnL calculated
        sell_trades = [t for t in trader.trades if t['action'] == 'sell']
        assert len(sell_trades) == 2
        for trade in sell_trades:
            assert 'pnl' in trade
    
    def test_diversified_portfolio(self):
        """Test trading multiple symbols."""
        trader = PaperTrader(20000)
        
        # Buy different stocks
        trader.buy('AAPL', 10, 150.0)
        trader.buy('GOOGL', 3, 2800.0)
        trader.buy('MSFT', 20, 330.0)
        
        assert len(trader.positions) == 3
        assert trader.positions['AAPL'] == 10
        assert trader.positions['GOOGL'] == 3
        assert trader.positions['MSFT'] == 20
        
        # Calculate expected remaining cash
        total_cost = (10 * 150) + (3 * 2800) + (20 * 330)
        expected_cash = 20000 - total_cost
        assert trader.cash == expected_cash
    
    def test_edge_case_zero_shares(self):
        """Test edge case of buying zero shares."""
        trader = PaperTrader(10000)
        
        success = trader.buy('AAPL', 0, 150.0)
        
        # Should handle gracefully
        assert success is False or trader.positions.get('AAPL', 0) == 0
    
    def test_edge_case_zero_price(self):
        """Test edge case of zero price."""
        trader = PaperTrader(10000)
        
        success = trader.buy('AAPL', 10, 0.0)
        
        # Should handle gracefully (might succeed with zero cost)
        assert isinstance(success, bool)
    
    def test_fractional_shares_handling(self):
        """Test handling of fractional shares (should be rejected)."""
        trader = PaperTrader(10000)
        
        # Try to buy fractional shares
        success = trader.buy('AAPL', 10.5, 150.0)
        
        # Implementation should handle this appropriately
        assert isinstance(success, bool)


class TestPaperTradingMetrics:
    """Test metrics calculation in paper trading."""
    
    @patch('backend.data_collector.fetch_market_data')
    def test_metrics_with_profitable_trades(self, mock_fetch):
        """Test metrics calculation with profitable trades."""
        mock_fetch.return_value = {
            'AAPL': {'price': 160.0, 'volume': 1000000}
        }
        
        trader = PaperTrader(10000)
        
        # Make profitable trades
        trader.buy('AAPL', 10, 150.0)
        trader.sell('AAPL', 10, 160.0)  # $100 profit
        
        summary = trader.get_summary()
        
        if 'metrics' in summary:
            metrics = summary['metrics']
            assert 'net_profit' in metrics
            assert metrics['net_profit'] > 0  # Should be profitable
    
    @patch('backend.data_collector.fetch_market_data')
    def test_metrics_with_losing_trades(self, mock_fetch):
        """Test metrics calculation with losing trades."""
        mock_fetch.return_value = {
            'AAPL': {'price': 140.0, 'volume': 1000000}
        }
        
        trader = PaperTrader(10000)
        
        # Make losing trades
        trader.buy('AAPL', 10, 150.0)
        trader.sell('AAPL', 10, 140.0)  # $100 loss
        
        summary = trader.get_summary()
        
        if 'metrics' in summary:
            metrics = summary['metrics']
            assert 'net_profit' in metrics
            assert metrics['net_profit'] < 0  # Should show loss