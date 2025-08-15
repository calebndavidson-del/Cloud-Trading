"""
Flask API wrapper for the Cloud Trading Bot
Provides REST endpoints for the trading bot functionality
"""
import os
import logging
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory, redirect
from flask_cors import CORS
from backend.bot import run_bot
from backend.data_collector import fetch_market_data, fetch_market_trends
from backend.config import get_config
from backend.optimizer import backtest_strategy, optimize_strategy

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Serve dashboard
@app.route('/')
def serve_dashboard():
    """Serve the main dashboard"""
    return send_from_directory('dashboard', 'index.html')

@app.route('/dashboard')
def redirect_to_dashboard():
    """Redirect /dashboard to root"""
    return redirect('/')

@app.route('/dashboard/<path:filename>')
def serve_dashboard_assets(filename):
    """Serve dashboard static assets"""
    return send_from_directory('dashboard', filename)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for container orchestration"""
    return jsonify({
        'status': 'healthy',
        'service': 'cloud-trading-bot',
        'version': '1.0.0'
    }), 200

@app.route('/api/health', methods=['GET'])
def api_health_check():
    """Health check endpoint for API"""
    return jsonify({
        'status': 'healthy',
        'service': 'cloud-trading-bot',
        'version': '1.0.0'
    }), 200

@app.route('/api/system/status', methods=['GET'])
def get_system_status():
    """Get comprehensive system status"""
    try:
        config = get_config()
        return jsonify({
            'status': 'running',
            'environment': config['env'],
            'is_running': True,
            'trading_enabled': config['trading'].get('trading_enabled', False),
            'paper_trading': config['trading'].get('paper_trading', True),
            'portfolio_value': 100000.0,  # Mock value for now
            'daily_pnl': 1250.75,  # Mock value for now
            'active_strategies': 3,  # Mock value for now
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/start', methods=['POST'])
def start_system():
    """Start the trading system"""
    try:
        # In a real implementation, this would start the trading engine
        return jsonify({
            'status': 'started',
            'message': 'Trading system started successfully',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    except Exception as e:
        logger.error(f"Error starting system: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/system/stop', methods=['POST'])
def stop_system():
    """Stop the trading system"""
    try:
        # In a real implementation, this would stop the trading engine
        return jsonify({
            'status': 'stopped',
            'message': 'Trading system stopped successfully',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
    except Exception as e:
        logger.error(f"Error stopping system: {e}")
        return jsonify({'error': str(e)}), 500

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

# Job status tracking (in production, use Redis or database)
active_jobs = {}

@app.route('/api/strategies', methods=['GET'])
def get_available_strategies_endpoint():
    """Get list of available trading strategies"""
    try:
        from backend.optimization.parameter_space import get_available_strategies
        strategies = get_available_strategies()
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

@app.route('/api/backtest/start', methods=['POST'])
def start_backtest():
    """Start a backtesting job"""
    try:
        config = request.get_json()
        if not config:
            return jsonify({'error': 'No configuration provided'}), 400
        
        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Get market data
        symbols = config.get('symbols', ['AAPL', 'GOOGL', 'MSFT'])
        market_data = fetch_market_data(symbols)
        
        # Start backtest (in production, run asynchronously)
        backtest_result = backtest_strategy(market_data, config)
        
        # Store job result
        active_jobs[job_id] = {
            'status': 'completed',
            'progress': 100,
            'results': backtest_result,
            'type': 'backtest',
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        return jsonify({
            'jobId': job_id,
            'status': 'started',
            'message': 'Backtesting job started successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting backtest: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest/status/<job_id>', methods=['GET'])
def get_backtest_status(job_id):
    """Get status of a backtesting job"""
    try:
        if job_id not in active_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = active_jobs[job_id]
        return jsonify({
            'jobId': job_id,
            'status': job['status'],
            'progress': job['progress'],
            'completed': job['status'] == 'completed',
            'type': job['type'],
            'created_at': job['created_at']
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting backtest status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/backtest/results/<job_id>', methods=['GET'])
def get_backtest_results(job_id):
    """Get results of a backtesting job"""
    try:
        if job_id not in active_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = active_jobs[job_id]
        if job['status'] != 'completed':
            return jsonify({'error': 'Job not completed yet'}), 400
        
        return jsonify({
            'jobId': job_id,
            'results': job['results'],
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimization/start', methods=['POST'])
def start_optimization():
    """Start an optimization job"""
    try:
        config = request.get_json()
        if not config:
            return jsonify({'error': 'No configuration provided'}), 400
        
        # Generate job ID
        import uuid
        job_id = str(uuid.uuid4())
        
        # Get market data
        symbols = config.get('symbols', ['AAPL', 'GOOGL', 'MSFT'])
        market_data = fetch_market_data(symbols)
        
        # Start optimization (in production, run asynchronously)
        n_trials = config.get('generations', 10)  # Use generations as trials
        optimization_result = optimize_strategy(market_data, n_trials=n_trials)
        
        # Store job result
        active_jobs[job_id] = {
            'status': 'completed',
            'progress': 100,
            'results': optimization_result,
            'type': 'optimization',
            'created_at': datetime.utcnow().isoformat() + 'Z'
        }
        
        return jsonify({
            'jobId': job_id,
            'status': 'started',
            'message': 'Optimization job started successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error starting optimization: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimization/status/<job_id>', methods=['GET'])
def get_optimization_status(job_id):
    """Get status of an optimization job"""
    try:
        if job_id not in active_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = active_jobs[job_id]
        return jsonify({
            'jobId': job_id,
            'status': job['status'],
            'progress': job['progress'],
            'completed': job['status'] == 'completed',
            'type': job['type'],
            'created_at': job['created_at'],
            'results': job.get('results') if job['status'] == 'completed' else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting optimization status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/optimization/results/<job_id>', methods=['GET'])
def get_optimization_results(job_id):
    """Get results of an optimization job"""
    try:
        if job_id not in active_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = active_jobs[job_id]
        if job['status'] != 'completed':
            return jsonify({'error': 'Job not completed yet'}), 400
        
        return jsonify({
            'jobId': job_id,
            'results': job['results'],
            'status': 'success',
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting optimization results: {e}")
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