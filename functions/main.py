"""
Firebase Functions for Cloud Trading Bot API
Provides essential REST endpoints for the trading bot functionality
"""
import json
import logging
import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Try to import Firebase Functions, fall back to Flask for testing
try:
    from firebase_functions import https_fn, options
    from flask import Request, jsonify
    FIREBASE_MODE = True
except ImportError:
    from flask import Flask, request as Request, jsonify
    FIREBASE_MODE = False

# Import backend modules for live data
try:
    from backend.live_data_manager import get_live_market_data_manager
    from backend.data_collector import fetch_market_data, fetch_market_trends
    LIVE_DATA_AVAILABLE = True
    logger = logging.getLogger(__name__)
    logger.info("Live data modules imported successfully")
except ImportError as e:
    LIVE_DATA_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning(f"Could not import live data modules: {e}")

# Configure logging
logging.basicConfig(level=logging.INFO)

# Global state for equity (in production, this would be stored in Firestore)
PORTFOLIO_STATE = {
    'equity': 100000.0,
    'last_updated': datetime.utcnow().isoformat()
}

if FIREBASE_MODE:
    @https_fn.on_request(
        cors=options.CorsOptions(
            cors_origins=["*"],
            cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )
    )
    def api(req: Request):
        """Main API function handler for all endpoints"""
        return handle_request(req)
else:
    # Flask app for testing
    app = Flask(__name__)
    
    @app.route('/api/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    def api_flask(endpoint):
        """Flask endpoint handler for testing"""
        return handle_request(Request)

def handle_request(req):
    """Handle API requests (works for both Firebase and Flask)"""
    
    # Handle CORS preflight
    if req.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    # Get the path - Firebase Functions handle the routing differently
    if FIREBASE_MODE:
        # Firebase Functions receive the full path including /api
        path = req.path.strip('/')
        # Remove 'api/' prefix if present
        if path.startswith('api/'):
            path = path[4:]
    else:
        path = req.endpoint or 'health'  # Default for testing
    
    logger.info(f"Handling request to path: {path}")
    
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
        elif path == 'data/autonomous-selection' or path == 'autonomous-selection':
            return handle_autonomous_selection(req)
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
    """Get live market data from real data sources"""
    if FIREBASE_MODE:
        symbols = req.args.get('symbols', 'AAPL,GOOGL,MSFT').split(',')
    else:
        symbols = getattr(req, 'args', {}).get('symbols', 'AAPL,GOOGL,MSFT').split(',')
    
    # Clean up symbols list
    symbols = [s.strip() for s in symbols if s.strip()]
    
    if not LIVE_DATA_AVAILABLE:
        logger.error("Live data modules not available, cannot fetch real market data")
        return jsonify({
            'error': 'Live data service unavailable',
            'message': 'Backend live data modules not accessible',
            'symbols': symbols,
            'status': 'error'
        }), 503
    
    try:
        # Use live data fetcher - this is synchronous but may need async wrapper
        live_data = asyncio.run(fetch_market_data(symbols))
        
        if not live_data or not live_data.get('data'):
            raise Exception("No live data returned")
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'symbols': symbols,
            'data': live_data['data'],
            'source': 'live_data',
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching live market data: {e}")
        # In production, we fail rather than return mock data
        return jsonify({
            'error': 'Failed to fetch live market data',
            'message': str(e),
            'symbols': symbols,
            'status': 'error'
        }), 500

def handle_market_trends(req):
    """Get live market trends from real data sources"""
    if not LIVE_DATA_AVAILABLE:
        logger.error("Live data modules not available, cannot fetch real market trends")
        return jsonify({
            'error': 'Live data service unavailable',
            'message': 'Backend live data modules not accessible',
            'status': 'error'
        }), 503
    
    try:
        # Use live data fetcher for market trends
        live_trends = asyncio.run(fetch_market_trends())
        
        if not live_trends:
            raise Exception("No live trends data returned")
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'trends': live_trends,
            'source': 'live_data',
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching live market trends: {e}")
        # In production, we fail rather than return mock data
        return jsonify({
            'error': 'Failed to fetch live market trends',
            'message': str(e),
            'status': 'error'
        }), 500

def handle_update_equity(req):
    """Handle equity update requests"""
    if req.method != 'POST':
        return jsonify({'error': 'Method not allowed'}), 405
    
    try:
        if FIREBASE_MODE:
            data = req.get_json()
        else:
            data = getattr(req, 'json_data', None)
            
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

def handle_autonomous_selection(req):
    """Handle autonomous stock selection requests"""
    if not LIVE_DATA_AVAILABLE:
        logger.error("Live data modules not available, cannot perform autonomous selection")
        return jsonify({
            'error': 'Autonomous selection service unavailable',
            'message': 'Backend autonomous selection modules not accessible',
            'status': 'error'
        }), 503
    
    try:
        # Get max_symbols parameter
        if FIREBASE_MODE:
            max_symbols = int(req.args.get('max_symbols', 15))
        else:
            max_symbols = int(getattr(req, 'args', {}).get('max_symbols', 15))
        
        # Import and use autonomous selection
        from backend.market_scanner import get_autonomous_stock_selection
        
        logger.info(f"Performing autonomous stock selection for {max_symbols} symbols")
        symbols = get_autonomous_stock_selection(max_stocks=max_symbols)
        
        if not symbols:
            raise Exception("No symbols returned from autonomous selection")
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'symbols': symbols,
            'count': len(symbols),
            'max_requested': max_symbols,
            'source': 'autonomous_selection',
            'status': 'success'
        }), 200
        
    except Exception as e:
        logger.error(f"Error performing autonomous selection: {e}")
        return jsonify({
            'error': 'Failed to perform autonomous selection',
            'message': str(e),
            'fallback_symbols': ['AAPL', 'MSFT', 'GOOGL'],
            'status': 'error'
        }), 500

# For testing without Firebase
if not FIREBASE_MODE and __name__ == "__main__":
    app.run(debug=True, port=5001)