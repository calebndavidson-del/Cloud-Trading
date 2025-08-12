"""
Unit tests for backend paper trader module.
"""
import pytest
from unittest.mock import Mock, patch
from backend.paper_trader import paper_trade


class TestPaperTrader:
    """Test the paper trading functionality."""
    
    def test_paper_trade_success(self):
        """Test successful paper trading."""
        config = {
            'initial_capital': 10000,
            'symbols': ['AAPL', 'GOOGL']
        }
        
        result = paper_trade(config)
        
        assert isinstance(result, dict)
        assert 'portfolio_value' in result
        assert 'total_trades' in result or 'completed_trades' in result
        assert isinstance(result['portfolio_value'], (int, float))
        assert result['portfolio_value'] >= 0
    
    def test_paper_trade_default_config(self):
        """Test paper trading with default configuration."""
        result = paper_trade({})
        
        assert isinstance(result, dict)
        assert 'portfolio_value' in result
    
    def test_paper_trade_custom_capital(self):
        """Test paper trading with custom initial capital."""
        config = {'initial_capital': 50000}
        
        result = paper_trade(config)
        
        assert isinstance(result, dict)
        assert 'portfolio_value' in result
    
    def test_paper_trade_multiple_symbols(self):
        """Test paper trading with multiple symbols."""
        config = {
            'initial_capital': 20000,
            'symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        }
        
        result = paper_trade(config)
        
        assert isinstance(result, dict)
        assert 'portfolio_value' in result
    
    def test_paper_trade_error_handling(self):
        """Test error handling in paper trading."""
        # Test with invalid configuration
        config = {'initial_capital': -1000}  # Negative capital
        
        result = paper_trade(config)
        
        # Should handle gracefully
        assert isinstance(result, dict)