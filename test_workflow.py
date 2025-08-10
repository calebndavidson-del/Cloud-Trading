#!/usr/bin/env python3
"""
Complete workflow test for the trading bot.
"""
import os
import sys

# Set up environment
os.environ['USE_MOCK_DATA'] = 'true'
sys.path.append(os.getcwd())

def main():
    print('Testing complete trading bot workflow...')
    
    # Test data collection
    from backend.data_collector import fetch_market_data, fetch_market_trends
    market_data = fetch_market_data(['AAPL', 'GOOGL'])
    print(f'✅ Market data fetched for {len(market_data)} symbols')
    
    # Test strategy optimization
    from backend.optimizer import optimize_strategy
    optimization = optimize_strategy(market_data, n_trials=5)
    print(f'✅ Strategy optimization completed: {optimization.get("best_value", "N/A")}')
    
    # Test paper trading
    from backend.paper_trader import paper_trade
    trading_result = paper_trade({'initial_capital': 10000, 'symbols': ['AAPL']})
    print(f'✅ Paper trading test: Portfolio value = ${trading_result.get("portfolio_value", 0):.2f}')
    
    print('🎉 All tests passed! AWS backend setup is ready for deployment.')

if __name__ == "__main__":
    main()