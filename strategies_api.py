#!/usr/bin/env python3
"""
Production-ready minimal API server for strategy optimization UI
Includes only the essential endpoints needed for the dropdown functionality
"""
import sys
import os
import logging
from datetime import datetime

# Add the project root to Python path
sys.path.append('/home/runner/work/Cloud-Trading/Cloud-Trading')

from flask import Flask, jsonify
from flask_cors import CORS

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'cloud-trading-strategies-api',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

@app.route('/api/strategies', methods=['GET'])
def get_available_strategies_endpoint():
    """Get list of available trading strategies"""
    try:
        from backend.optimization.parameter_space import get_available_strategies
        strategies = get_available_strategies()
        
        logger.info(f"Successfully loaded {len(strategies)} strategies")
        return jsonify({
            'strategies': strategies,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

@app.route('/api/strategies/<strategy_name>/parameters', methods=['GET'])
def get_strategy_parameter_space_endpoint(strategy_name):
    """Get parameter space for a specific strategy"""
    try:
        from backend.optimization.parameter_space import get_strategy_parameter_space
        parameter_space = get_strategy_parameter_space(strategy_name)
        
        param_count = len(parameter_space) if parameter_space else 0
        logger.info(f"Successfully loaded {param_count} parameters for {strategy_name}")
        
        return jsonify({
            'strategy': strategy_name,
            'parameter_space': parameter_space,
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    except Exception as e:
        logger.error(f"Error getting parameter space for {strategy_name}: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'error': 'Endpoint not found',
        'status': 'error',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'error': 'Internal server error',
        'status': 'error',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Cloud Trading Strategies API")
    logger.info(f"Port: {port}")
    logger.info(f"Debug: {debug}")
    logger.info("Available endpoints:")
    logger.info("  GET /health - Health check")
    logger.info("  GET /api/strategies - List available strategies")
    logger.info("  GET /api/strategies/<name>/parameters - Get strategy parameters")
    
    try:
        # Test that we can import the backend modules
        from backend.optimization.parameter_space import get_available_strategies
        strategies = get_available_strategies()
        logger.info(f"✓ Successfully initialized with {len(strategies)} strategies")
        for strategy in strategies:
            logger.info(f"  - {strategy['name']}: {strategy['displayName']}")
    except Exception as e:
        logger.error(f"✗ Failed to initialize backend: {e}")
        sys.exit(1)
    
    app.run(host='0.0.0.0', port=port, debug=debug)