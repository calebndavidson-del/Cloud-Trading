"""
Flask API wrapper for the Cloud Trading Bot
Provides REST endpoints for the trading bot functionality
"""
import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request
from flask_cors import CORS
from backend.bot import run_bot
from backend.data_collector import fetch_market_data, fetch_market_trends
from backend.config import get_config

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container orchestration"""
    return jsonify({
        'status': 'healthy',
        'service': 'cloud-trading-bot',
        'version': '1.0.0'
    }), 200

@app.route('/api/status', methods=['GET'])
def get_status():
    """Get trading bot status"""
    try:
        config = get_config()
        return jsonify({
            'status': 'running',
            'environment': config['env'],
            'trading_enabled': config['trading'].get('trading_enabled', False),
            'paper_trading': config['trading'].get('paper_trading', True)
        }), 200
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/market-data', methods=['GET'])
def get_market_data():
    """Get current market data"""
    try:
        symbols = request.args.get('symbols', '').split(',') if request.args.get('symbols') else None
        if not symbols:
            config = get_config()
            symbols = config['trading']['default_symbols']
        
        # Remove empty strings from symbols
        symbols = [s.strip() for s in symbols if s.strip()]
        
        market_data = fetch_market_data(symbols)
        
        # Add timestamp to response
        from datetime import datetime
        response = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'symbols': symbols,
            'data': market_data,
            'status': 'success'
        }
        
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error fetching market data: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

@app.route('/api/market-trends', methods=['GET'])
def get_market_trends():
    """Get market trends and indicators"""
    try:
        trends = fetch_market_trends()
        return jsonify({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'trends': trends,
            'status': 'success'
        }), 200
    except Exception as e:
        logger.error(f"Error fetching market trends: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

@app.route('/api/bot/run', methods=['POST'])
def run_trading_bot():
    """Run the trading bot (for testing/manual execution)"""
    try:
        # Run bot in test mode
        result = run_bot()
        return jsonify({
            'status': 'completed',
            'message': 'Trading bot executed successfully'
        }), 200
    except Exception as e:
        logger.error(f"Error running bot: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/config', methods=['GET'])
def get_configuration():
    """Get bot configuration (non-sensitive data only)"""
    try:
        config = get_config()
        # Return only non-sensitive configuration
        safe_config = {
            'env': config['env'],
            'trading': {
                'default_symbols': config['trading']['default_symbols'],
                'paper_trading': config['trading'].get('paper_trading', True),
                'trading_enabled': config['trading'].get('trading_enabled', False)
            }
        }
        return jsonify(safe_config), 200
    except Exception as e:
        logger.error(f"Error getting configuration: {e}")
        return jsonify({'error': str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('ENVIRONMENT', 'development') == 'development'
    
    logger.info(f"Starting Cloud Trading Bot API on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)