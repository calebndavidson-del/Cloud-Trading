"""
Main scanning and trading bot logic.
- Scans Yahoo Finance and other APIs for top stocks and trends.
- Orchestrates data collection, optimization, and paper trading.
"""
import logging
from backend.data_collector import fetch_market_data, fetch_market_trends
from backend.config import get_config

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def run_bot():
    """
    Main bot execution function.
    """
    try:
        config = get_config()
        logger.info(f"Starting trading bot in {config['env']} environment")
        
        # Fetch market data
        logger.info("Fetching market data...")
        symbols = config['trading']['default_symbols']
        market_data = fetch_market_data(symbols)
        
        if 'error' in market_data:
            logger.error(f"Error fetching market data: {market_data['error']}")
            return
        
        logger.info(f"Successfully fetched data for {len(market_data)} symbols")
        
        # Fetch market trends
        logger.info("Fetching market trends...")
        trends = fetch_market_trends()
        
        # Display results
        print("\n=== Market Data ===")
        for symbol, data in market_data.items():
            if 'error' not in data:
                print(f"{symbol}: ${data['price']:.2f} (Volume: {data['volume']:,})")
            else:
                print(f"{symbol}: {data['error']}")
        
        print("\n=== Market Trends ===")
        if 'error' not in trends and 'sp500' in trends:
            sp500_data = trends['sp500']
            print(f"S&P 500: ${sp500_data['current_price']:.2f} ({sp500_data['change_percent']:+.2f}%) - Trend: {sp500_data['trend']}")
        else:
            print("Market trend data unavailable")
        
        logger.info("Bot execution completed successfully")
        
    except Exception as e:
        logger.error(f"Error in bot execution: {e}")
        raise

if __name__ == "__main__":
    run_bot()