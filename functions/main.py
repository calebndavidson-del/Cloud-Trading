"""
Firebase Functions for Cloud Trading Bot API
Provides essential REST endpoints for the trading bot functionality
"""
import json
import logging
from datetime import datetime
from firebase_functions import https_fn, options
from flask import Request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global state for equity (in production, this would be stored in Firestore)
PORTFOLIO_STATE = {
    'equity': 100000.0,
    'last_updated': datetime.utcnow().isoformat()
}

@https_fn.on_request(
    cors=options.CorsOptions(
        cors_origins=["*"],
        cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
)
def api(req: Request):
    """Main API function handler for all endpoints"""
    
    # Handle CORS preflight
    if req.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    # Get the path after /api
    path = req.path.replace('/api', '').strip('/')
    
    try:
        if path == 'status':
            return handle_status(req)
        elif path == 'market-data':
            return handle_market_data(req)
        elif path == 'market-trends':
            return handle_market_trends(req)
        elif path == 'update-equity':
            return handle_update_equity(req)
        elif path == 'config':
            return handle_config(req)
        elif path == 'health':
            return handle_health(req)
        else:
            return jsonify({'error': 'Endpoint not found'}), 404
            
    except Exception as e:
        logger.error(f"Error handling request to {path}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def handle_health(req):
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'cloud-trading-bot-firebase',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

def handle_status(req):
    """Get trading bot status"""
    return jsonify({
        'status': 'running',
        'environment': 'firebase',
        'trading_enabled': False,
        'paper_trading': True,
        'portfolio_value': PORTFOLIO_STATE['equity'],
        'is_running': True,
        'daily_pnl': 0,
        'active_strategies': 1,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

def handle_market_data(req):
    """Get mock market data for demo purposes"""
    symbols = req.args.get('symbols', 'AAPL,GOOGL,MSFT').split(',')
    
    # Mock market data - in production, this would fetch from real data sources
    mock_data = {}
    for symbol in symbols:
        if symbol.strip():
            mock_data[symbol.strip()] = {
                'price': 150.00 + hash(symbol) % 100,
                'change': (hash(symbol) % 10) - 5,
                'change_percent': ((hash(symbol) % 10) - 5) / 150.0 * 100,
                'volume': 1000000 + hash(symbol) % 500000,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }
    
    return jsonify({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'symbols': symbols,
        'data': mock_data,
        'status': 'success'
    }), 200

def handle_market_trends(req):
    """Get mock market trends"""
    trends = {
        'market_sentiment': 'neutral',
        'volatility_index': 18.5,
        'fear_greed_index': 65,
        'major_indices': {
            'SPY': {'price': 420.50, 'change': 2.1},
            'QQQ': {'price': 350.25, 'change': -1.5},
            'IWM': {'price': 185.75, 'change': 0.8}
        }
    }
    
    return jsonify({
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'trends': trends,
        'status': 'success'
    }), 200

def handle_update_equity(req):
    """Handle equity update requests"""
    if req.method != 'POST':
        return jsonify({'error': 'Method not allowed'}), 405
    
    try:
        data = req.get_json()
        if not data or 'equity' not in data:
            return jsonify({'error': 'Missing equity value in request'}), 400
        
        new_equity = float(data['equity'])
        if new_equity <= 0:
            return jsonify({'error': 'Equity must be positive'}), 400
        
        # Update global state (in production, save to Firestore)
        PORTFOLIO_STATE['equity'] = new_equity
        PORTFOLIO_STATE['last_updated'] = datetime.utcnow().isoformat()
        
        logger.info(f"Equity updated to ${new_equity:,.2f}")
        
        return jsonify({
            'status': 'success',
            'equity': new_equity,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'message': f'Equity updated to ${new_equity:,.2f}'
        }), 200
        
    except (ValueError, TypeError) as e:
        return jsonify({'error': 'Invalid equity value'}), 400

def handle_config(req):
    """Get bot configuration"""
    config = {
        'env': 'firebase',
        'trading': {
            'default_symbols': ['AAPL', 'GOOGL', 'MSFT', 'TSLA'],
            'paper_trading': True,
            'trading_enabled': False
        },
        'portfolio': {
            'equity': PORTFOLIO_STATE['equity'],
            'last_updated': PORTFOLIO_STATE['last_updated']
        }
    }
    
    return jsonify(config), 200