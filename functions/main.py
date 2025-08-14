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
    from flask import Request, jsonify as flask_jsonify
    FIREBASE_MODE = True
    
    # Use Flask jsonify in Firebase mode
    def jsonify(data):
        import json
        return json.dumps(data), {'Content-Type': 'application/json'}
        
except ImportError:
    from flask import Flask, request as Request, jsonify as flask_jsonify
    FIREBASE_MODE = False
    
    # Create a custom jsonify that works outside app context
    def jsonify(data):
        import json
        class Response:
            def __init__(self, data_str):
                self.data = json.loads(data_str)
        return Response(json.dumps(data))

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
    from flask_cors import CORS
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes
    
    @app.route('/api/<path:endpoint>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    def api_flask(endpoint):
        """Flask endpoint handler for testing"""
        from flask import request
        return handle_request_flask(request, endpoint)

def handle_request_flask(req, endpoint):
    """Handle Flask API requests"""
    
    # Handle CORS preflight
    if req.method == 'OPTIONS':
        return jsonify({'status': 'ok'}), 200
    
    path = endpoint
    logger.info(f"Handling Flask request to path: {path}")
    
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
        elif path.startswith('backtest/'):
            return handle_backtest_endpoints(req, path)
        elif path.startswith('optimization/'):
            return handle_optimization_endpoints(req, path)
        elif path.startswith('trading/'):
            return handle_trading_endpoints(req, path)
        elif path.startswith('system/'):
            return handle_system_endpoints(req, path)
        elif path.startswith('strategies/') or path == 'strategies':
            return handle_strategy_endpoints(req, path)
        elif path.startswith('data/') and path != 'data/autonomous-selection':
            return handle_data_endpoints(req, path)
        else:
            return jsonify({'error': 'Endpoint not found'}), 404
            
    except Exception as e:
        logger.error(f"Error handling request to {path}: {e}")
        return jsonify({'error': 'Internal server error'}), 500

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
        elif path.startswith('backtest/'):
            return handle_backtest_endpoints(req, path)
        elif path.startswith('optimization/'):
            return handle_optimization_endpoints(req, path)
        elif path.startswith('trading/'):
            return handle_trading_endpoints(req, path)
        elif path.startswith('system/'):
            return handle_system_endpoints(req, path)
        elif path.startswith('strategies/') or path == 'strategies':
            return handle_strategy_endpoints(req, path)
        elif path.startswith('data/') and path != 'data/autonomous-selection':
            return handle_data_endpoints(req, path)
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
        # Use live data fetcher - handle both sync and async results
        if asyncio.iscoroutinefunction(fetch_market_data):
            live_data = asyncio.run(fetch_market_data(symbols))
        else:
            live_data = fetch_market_data(symbols)
        
        if not live_data or (isinstance(live_data, dict) and not live_data.get('data') and not any(key in live_data for key in ['AAPL', 'GOOGL', 'MSFT'])):
            raise Exception("No live data returned")
        
        # Handle both formats: {data: {...}} or direct symbol data
        if 'data' in live_data:
            data_section = live_data['data']
        else:
            data_section = live_data
        
        return jsonify({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'symbols': symbols,
            'data': data_section,
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
        # Use live data fetcher - handle both sync and async results
        if asyncio.iscoroutinefunction(fetch_market_trends):
            live_trends = asyncio.run(fetch_market_trends())
        else:
            live_trends = fetch_market_trends()
        
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
        },
        'benchmarks': [
            {'symbol': 'SPY', 'name': 'S&P 500 ETF', 'description': 'Large-cap US stocks'},
            {'symbol': 'QQQ', 'name': 'NASDAQ 100 ETF', 'description': 'Technology-heavy index'},
            {'symbol': 'DIA', 'name': 'Dow Jones Industrial Average ETF', 'description': '30 large US companies'},
            {'symbol': 'IWM', 'name': 'Russell 2000 ETF', 'description': 'Small-cap US stocks'},
            {'symbol': 'VTI', 'name': 'Total Stock Market ETF', 'description': 'Entire US stock market'},
            {'symbol': 'EFA', 'name': 'MSCI EAFE ETF', 'description': 'Developed international markets'},
            {'symbol': 'EEM', 'name': 'Emerging Markets ETF', 'description': 'Emerging market stocks'},
            {'symbol': 'TLT', 'name': '20+ Year Treasury Bond ETF', 'description': 'Long-term government bonds'}
        ]
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

# Global storage for jobs (in production, this would be in a database)
JOBS = {
    'test123': {
        'type': 'backtest',
        'status': 'completed',
        'progress': 100,
        'start_time': '2025-08-14T12:00:00Z',
        'end_time': '2025-08-14T12:30:00Z',
        'message': 'Backtest completed successfully',
        'results': {
            'total_return': 0.15,
            'sharpe_ratio': 1.8,
            'max_drawdown': -0.08,
            'trades': 25
        },
        'summary': {
            'initial_capital': 100000,
            'final_value': 115000,
            'total_trades': 25,
            'win_rate': 0.68
        },
        'trades': [],
        'metrics': {
            'volatility': 0.12,
            'beta': 1.05
        }
    },
    'optimization_1': {
        'type': 'optimization',
        'status': 'completed',
        'progress': 100,
        'start_time': '2025-08-14T13:00:00Z',
        'end_time': '2025-08-14T13:45:00Z',
        'message': 'Optimization completed successfully',
        'results': {
            'best_sharpe': 2.1,
            'best_return': 0.22,
            'trials_completed': 100
        },
        'best_parameters': {
            'sma_short': 10,
            'sma_long': 30,
            'risk_threshold': 0.02
        },
        'performance': {
            'sharpe_ratio': 2.1,
            'total_return': 0.22,
            'max_drawdown': -0.06
        }
    }
}
job_counter = 2

def handle_backtest_endpoints(req, path):
    """Handle backtest-related endpoints"""
    global job_counter
    
    # Remove 'backtest/' prefix
    endpoint = path[9:]  # Remove 'backtest/'
    
    if endpoint == 'start':
        if req.method != 'POST':
            return jsonify({'error': 'Method not allowed'}), 405
            
        try:
            # Get backtest configuration
            if FIREBASE_MODE:
                config = req.get_json() or {}
            else:
                config = getattr(req, 'json', {}) or {}
            
            # Generate job ID
            job_counter += 1
            job_id = f"backtest_{job_counter}"
            
            # Store job info
            JOBS[job_id] = {
                'type': 'backtest',
                'status': 'running',
                'config': config,
                'start_time': datetime.utcnow().isoformat(),
                'progress': 0
            }
            
            # Start backtest in background (simulate)
            # In a real implementation, this would be handled by a task queue
            import threading
            thread = threading.Thread(target=run_backtest_job, args=(job_id, config))
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'job_id': job_id,
                'status': 'started',
                'message': 'Backtest started successfully'
            }), 200
            
        except Exception as e:
            logger.error(f"Error starting backtest: {e}")
            return jsonify({'error': 'Failed to start backtest', 'message': str(e)}), 500
    
    elif endpoint.startswith('status/'):
        job_id = endpoint[7:]  # Remove 'status/'
        
        if job_id not in JOBS:
            return jsonify({'error': 'Job not found'}), 404
        
        job = JOBS[job_id]
        return jsonify({
            'job_id': job_id,
            'status': job['status'],
            'progress': job['progress'],
            'start_time': job['start_time'],
            'end_time': job.get('end_time'),
            'message': job.get('message', '')
        }), 200
    
    elif endpoint.startswith('results/'):
        job_id = endpoint[8:]  # Remove 'results/'
        
        if job_id not in JOBS:
            return jsonify({'error': 'Job not found'}), 404
            
        job = JOBS[job_id]
        if job['status'] != 'completed':
            return jsonify({'error': 'Backtest not completed yet'}), 400
            
        return jsonify({
            'job_id': job_id,
            'results': job.get('results', {}),
            'summary': job.get('summary', {}),
            'trades': job.get('trades', []),
            'metrics': job.get('metrics', {})
        }), 200
    
    else:
        return jsonify({'error': 'Backtest endpoint not found'}), 404

def handle_optimization_endpoints(req, path):
    """Handle optimization-related endpoints"""
    global job_counter
    
    # Remove 'optimization/' prefix  
    endpoint = path[13:]  # Remove 'optimization/'
    
    if endpoint == 'start':
        if req.method != 'POST':
            return jsonify({'error': 'Method not allowed'}), 405
            
        try:
            # Get optimization configuration
            if FIREBASE_MODE:
                config = req.get_json() or {}
            else:
                config = getattr(req, 'json', {}) or {}
            
            # Generate job ID
            job_counter += 1
            job_id = f"optimization_{job_counter}"
            
            # Store job info
            JOBS[job_id] = {
                'type': 'optimization',
                'status': 'running',
                'config': config,
                'start_time': datetime.utcnow().isoformat(),
                'progress': 0
            }
            
            # Start optimization in background (simulate)
            import threading
            thread = threading.Thread(target=run_optimization_job, args=(job_id, config))
            thread.daemon = True
            thread.start()
            
            return jsonify({
                'job_id': job_id,
                'status': 'started',
                'message': 'Optimization started successfully'
            }), 200
            
        except Exception as e:
            logger.error(f"Error starting optimization: {e}")
            return jsonify({'error': 'Failed to start optimization', 'message': str(e)}), 500
    
    elif endpoint.startswith('status/'):
        job_id = endpoint[7:]  # Remove 'status/'
        
        if job_id not in JOBS:
            return jsonify({'error': 'Job not found'}), 404
        
        job = JOBS[job_id]
        return jsonify({
            'job_id': job_id,
            'status': job['status'],
            'progress': job['progress'],
            'start_time': job['start_time'],
            'end_time': job.get('end_time'),
            'message': job.get('message', '')
        }), 200
    
    elif endpoint.startswith('results/'):
        job_id = endpoint[8:]  # Remove 'results/'
        
        if job_id not in JOBS:
            return jsonify({'error': 'Job not found'}), 404
            
        job = JOBS[job_id]
        if job['status'] != 'completed':
            return jsonify({'error': 'Optimization not completed yet'}), 400
            
        return jsonify({
            'job_id': job_id,
            'results': job.get('results', {}),
            'best_parameters': job.get('best_parameters', {}),
            'performance': job.get('performance', {})
        }), 200
    
    else:
        return jsonify({'error': 'Optimization endpoint not found'}), 404

def handle_trading_endpoints(req, path):
    """Handle trading-related endpoints"""
    # Remove 'trading/' prefix
    endpoint = path[8:]  # Remove 'trading/'
    
    if endpoint == 'positions':
        return jsonify({
            'positions': [
                {'symbol': 'AAPL', 'shares': 100, 'current_price': 150.0, 'market_value': 15000.0, 'pnl': 500.0},
                {'symbol': 'GOOGL', 'shares': 50, 'current_price': 2800.0, 'market_value': 140000.0, 'pnl': -2000.0}
            ],
            'total_value': 155000.0,
            'cash': 10000.0
        }), 200
    
    elif endpoint == 'orders/active' or endpoint == 'orders':
        return jsonify({
            'orders': [
                {'id': '001', 'symbol': 'MSFT', 'side': 'buy', 'quantity': 75, 'price': 420.0, 'status': 'pending'},
                {'id': '002', 'symbol': 'TSLA', 'side': 'sell', 'quantity': 25, 'price': 220.0, 'status': 'pending'}
            ]
        }), 200
    
    elif endpoint == 'performance':
        timeframe = req.args.get('timeframe', '1D') if FIREBASE_MODE else getattr(req, 'args', {}).get('timeframe', '1D')
        return jsonify({
            'timeframe': timeframe,
            'total_return': 0.085,  # 8.5%
            'daily_pnl': 1250.0,
            'sharpe_ratio': 1.45,
            'max_drawdown': -0.12,
            'win_rate': 0.67
        }), 200
    
    elif endpoint == 'risk-metrics':
        return jsonify({
            'var_95': -2500.0,  # Value at Risk
            'expected_shortfall': -3200.0,
            'beta': 1.15,
            'volatility': 0.18,
            'correlation_spy': 0.85
        }), 200
    
    else:
        return jsonify({'error': 'Trading endpoint not found'}), 404

def run_backtest_job(job_id, config):
    """Run backtest job in background"""
    try:
        import time
        from backend.paper_trader import PaperTrader
        
        # Update job status
        JOBS[job_id]['status'] = 'running'
        JOBS[job_id]['message'] = 'Initializing backtest...'
        
        # Get configuration
        start_date = config.get('startDate', '2023-01-01')
        end_date = config.get('endDate', '2023-12-31')
        initial_capital = config.get('initialCapital', 100000)
        symbols = config.get('symbols', ['AAPL', 'GOOGL', 'MSFT'])
        benchmark = config.get('benchmarkSymbol', 'SPY')
        
        # Use autonomous selection if enabled
        if config.get('useAutonomousSelection', False):
            try:
                from backend.market_scanner import get_autonomous_stock_selection
                max_symbols = config.get('maxSymbols', 15)
                autonomous_symbols = get_autonomous_stock_selection(max_stocks=max_symbols)
                if autonomous_symbols:
                    symbols = autonomous_symbols
                    logger.info(f"Using autonomous selection: {symbols}")
            except Exception as e:
                logger.warning(f"Autonomous selection failed, using default symbols: {e}")
        
        # Simulate backtest progress
        JOBS[job_id]['progress'] = 10
        JOBS[job_id]['message'] = 'Fetching historical data...'
        time.sleep(1)  # Simulate work
        
        JOBS[job_id]['progress'] = 30
        JOBS[job_id]['message'] = 'Running trading simulation...'
        
        # Initialize paper trader
        trader = PaperTrader(initial_capital)
        
        # Simulate some trades
        for i, symbol in enumerate(symbols[:5]):  # Limit to 5 symbols for demo
            try:
                # Simulate buying
                shares = max(1, int(initial_capital * 0.1 / 100))  # 10% allocation, assuming $100 price
                trader.buy(symbol, shares, 100.0 + i * 10)  # Simulate different prices
                
                # Simulate selling later
                trader.sell(symbol, shares // 2, 110.0 + i * 10)  # Partial sell at higher price
                
                JOBS[job_id]['progress'] = 30 + (i + 1) * 10
                time.sleep(0.5)  # Simulate processing time
            except Exception as e:
                logger.warning(f"Error simulating trade for {symbol}: {e}")
        
        JOBS[job_id]['progress'] = 80
        JOBS[job_id]['message'] = 'Calculating metrics...'
        
        # Get final summary
        summary = trader.get_summary()
        
        # Simulate benchmark comparison
        benchmark_return = 0.12  # 12% return for benchmark
        portfolio_return = summary['return_percentage'] / 100
        alpha = portfolio_return - benchmark_return
        
        # Store results
        JOBS[job_id]['results'] = summary
        JOBS[job_id]['trades'] = trader.trades
        JOBS[job_id]['metrics'] = {
            'total_return': summary['return_percentage'],
            'benchmark_return': benchmark_return * 100,
            'alpha': alpha * 100,
            'sharpe_ratio': 1.2,  # Simulated
            'max_drawdown': -8.5,  # Simulated
            'volatility': 15.2  # Simulated
        }
        JOBS[job_id]['summary'] = {
            'symbols_traded': symbols,
            'benchmark_symbol': benchmark,
            'period': f"{start_date} to {end_date}",
            'total_trades': len(trader.trades)
        }
        
        JOBS[job_id]['progress'] = 100
        JOBS[job_id]['status'] = 'completed'
        JOBS[job_id]['end_time'] = datetime.utcnow().isoformat()
        JOBS[job_id]['message'] = 'Backtest completed successfully'
        
        logger.info(f"Backtest {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in backtest job {job_id}: {e}")
        JOBS[job_id]['status'] = 'failed'
        JOBS[job_id]['end_time'] = datetime.utcnow().isoformat()
        JOBS[job_id]['message'] = f'Backtest failed: {str(e)}'

def run_optimization_job(job_id, config):
    """Run optimization job in background"""
    try:
        import time
        
        # Update job status
        JOBS[job_id]['status'] = 'running'
        JOBS[job_id]['message'] = 'Starting parameter optimization...'
        
        # Simulate optimization progress
        for i in range(10):
            JOBS[job_id]['progress'] = (i + 1) * 10
            JOBS[job_id]['message'] = f'Testing parameter set {i + 1}/10...'
            time.sleep(0.5)  # Simulate optimization work
        
        # Store optimization results
        JOBS[job_id]['results'] = {
            'best_score': 0.245,  # Best Sharpe ratio found
            'trials_completed': 100,
            'optimization_time': 45.2
        }
        JOBS[job_id]['best_parameters'] = {
            'momentum_window': 14,
            'mean_reversion_window': 20,
            'stop_loss': 0.05,
            'take_profit': 0.15
        }
        JOBS[job_id]['performance'] = {
            'sharpe_ratio': 0.245,
            'total_return': 0.18,
            'max_drawdown': -0.08,
            'win_rate': 0.65
        }
        
        JOBS[job_id]['progress'] = 100
        JOBS[job_id]['status'] = 'completed'
        JOBS[job_id]['end_time'] = datetime.utcnow().isoformat()
        JOBS[job_id]['message'] = 'Optimization completed successfully'
        
        logger.info(f"Optimization {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Error in optimization job {job_id}: {e}")
        JOBS[job_id]['status'] = 'failed'
        JOBS[job_id]['end_time'] = datetime.utcnow().isoformat()
        JOBS[job_id]['message'] = f'Optimization failed: {str(e)}'

def handle_system_endpoints(req, path):
    """Handle system-related endpoints"""
    # Remove 'system/' prefix
    endpoint = path[7:]  # Remove 'system/'
    
    if endpoint == 'status':
        return handle_status(req)
    elif endpoint == 'start':
        return handle_system_start(req)
    elif endpoint == 'stop':
        return handle_system_stop(req)
    else:
        return jsonify({'error': 'System endpoint not found'}), 404

def handle_system_start(req):
    """Handle system start request"""
    if req.method != 'POST':
        return jsonify({'error': 'Method not allowed'}), 405
    
    return jsonify({
        'status': 'success',
        'message': 'Trading system started',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

def handle_system_stop(req):
    """Handle system stop request"""
    if req.method != 'POST':
        return jsonify({'error': 'Method not allowed'}), 405
    
    return jsonify({
        'status': 'success', 
        'message': 'Trading system stopped',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }), 200

def handle_strategy_endpoints(req, path):
    """Handle strategy-related endpoints"""
    # Remove 'strategies/' prefix, handle both 'strategies' and 'strategies/'
    if path == 'strategies':
        endpoint = ''
    elif path.startswith('strategies/'):
        endpoint = path[11:]  # Remove 'strategies/'
    else:
        endpoint = 'list'
    
    if endpoint == '' or endpoint == 'list':
        return handle_get_strategies(req)
    elif endpoint == 'available':
        return handle_get_strategies(req)
    elif endpoint == 'parameters':
        return handle_get_strategy_parameters(req)
    elif endpoint.startswith('parameters/'):
        strategy_name = endpoint[11:]  # Remove 'parameters/'
        return handle_get_strategy_parameters(req, strategy_name)
    else:
        return jsonify({'error': 'Strategy endpoint not found'}), 404

def handle_get_strategies(req):
    """Get available trading strategies"""
    try:
        # Import and get available strategies
        from backend.optimization.parameter_space import get_parameter_space
        param_space = get_parameter_space()
        
        # Get strategy categories and available strategies
        strategies = [
            {
                'name': 'momentum_strategy',
                'description': 'Momentum-based trading using technical indicators',
                'parameters': ['sma_periods', 'rsi_threshold', 'momentum_window'],
                'category': 'technical'
            },
            {
                'name': 'mean_reversion_strategy', 
                'description': 'Mean reversion strategy using statistical analysis',
                'parameters': ['lookback_period', 'zscore_threshold', 'exit_threshold'],
                'category': 'statistical'
            },
            {
                'name': 'ml_strategy',
                'description': 'Machine learning-based predictions',
                'parameters': ['hidden_layers', 'learning_rate', 'feature_window'],
                'category': 'ml'
            },
            {
                'name': 'risk_parity_strategy',
                'description': 'Risk-based portfolio allocation',
                'parameters': ['rebalance_frequency', 'volatility_window', 'max_weight'],
                'category': 'portfolio'
            }
        ]
        
        return jsonify({
            'strategies': strategies,
            'total_count': len(strategies),
            'categories': ['technical', 'statistical', 'ml', 'portfolio'],
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting strategies: {e}")
        return jsonify({
            'error': 'Failed to get strategies',
            'message': str(e),
            'strategies': []
        }), 500

def handle_get_strategy_parameters(req, strategy_name=None):
    """Get strategy parameters"""
    try:
        from backend.optimization.parameter_space import get_parameter_space, get_all_parameters, get_strategy_parameters
        
        def serialize_parameter_def(param_def):
            """Convert ParameterDefinition to serializable dict"""
            return {
                'name': param_def.name,
                'type': param_def.param_type.value if hasattr(param_def.param_type, 'value') else str(param_def.param_type),
                'bounds': param_def.bounds,
                'default': param_def.default,
                'description': param_def.description
            }
        
        def serialize_parameters(params_dict):
            """Convert parameter space to serializable format"""
            serialized = {}
            for category, param_dict in params_dict.items():
                serialized[category] = {}
                for param_name, param_def in param_dict.items():
                    serialized[category][param_name] = serialize_parameter_def(param_def)
            return serialized
        
        if strategy_name:
            # Get parameters for specific strategy
            strategy_params = get_strategy_parameters(strategy_name)
            serialized_params = {}
            for param_name, param_def in strategy_params.items():
                serialized_params[param_name] = serialize_parameter_def(param_def)
            
            return jsonify({
                'strategy': strategy_name,
                'parameters': serialized_params,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
        else:
            # Get all parameter categories
            all_params = get_all_parameters()
            serialized_params = serialize_parameters(all_params)
            
            return jsonify({
                'parameter_categories': list(all_params.keys()),
                'parameters': serialized_params,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }), 200
            
    except Exception as e:
        logger.error(f"Error getting strategy parameters: {e}")
        return jsonify({
            'error': 'Failed to get strategy parameters',
            'message': str(e),
            'parameters': {}
        }), 500

def handle_data_endpoints(req, path):
    """Handle data-related endpoints"""
    # Remove 'data/' prefix
    endpoint = path[5:]  # Remove 'data/'
    
    if endpoint == 'market':
        return handle_market_data(req)
    elif endpoint == 'news':
        return handle_news_data(req)
    elif endpoint == 'earnings':
        return handle_earnings_data(req)
    elif endpoint.startswith('autonomous-selection'):
        return handle_autonomous_selection(req)
    else:
        return jsonify({'error': 'Data endpoint not found'}), 404

def handle_news_data(req):
    """Get news data for symbols"""
    if FIREBASE_MODE:
        symbols = req.args.get('symbols', '').split(',')
        limit = int(req.args.get('limit', 50))
    else:
        symbols = getattr(req, 'args', {}).get('symbols', '').split(',')
        limit = int(getattr(req, 'args', {}).get('limit', 50))
    
    symbols = [s.strip() for s in symbols if s.strip()]
    
    try:
        # Mock news data for now - in production this would fetch real news
        news_data = []
        for symbol in symbols[:5]:  # Limit to 5 symbols
            for i in range(min(limit // len(symbols), 10)):
                news_data.append({
                    'symbol': symbol,
                    'headline': f'Breaking: {symbol} reports strong earnings growth',
                    'summary': f'Analysis shows positive momentum for {symbol} stock',
                    'source': 'Financial News',
                    'published_at': (datetime.utcnow() - timedelta(hours=i)).isoformat() + 'Z',
                    'sentiment': 'positive' if i % 2 == 0 else 'neutral',
                    'relevance_score': 0.8 - (i * 0.1)
                })
        
        return jsonify({
            'news': news_data,
            'symbols': symbols,
            'total_count': len(news_data),
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting news data: {e}")
        return jsonify({
            'error': 'Failed to get news data',
            'message': str(e),
            'news': []
        }), 500

def handle_earnings_data(req):
    """Get earnings data for symbols"""
    if FIREBASE_MODE:
        symbols = req.args.get('symbols', '').split(',')
    else:
        symbols = getattr(req, 'args', {}).get('symbols', '').split(',')
    
    symbols = [s.strip() for s in symbols if s.strip()]
    
    try:
        # Mock earnings data - in production this would fetch real earnings
        earnings_data = {}
        for symbol in symbols:
            earnings_data[symbol] = {
                'next_earnings_date': (datetime.utcnow() + timedelta(days=30)).strftime('%Y-%m-%d'),
                'last_earnings_date': (datetime.utcnow() - timedelta(days=90)).strftime('%Y-%m-%d'),
                'eps_estimate': 1.25,
                'eps_actual': 1.32,
                'revenue_estimate': 50000000000,
                'revenue_actual': 52000000000,
                'surprise_percent': 5.6
            }
        
        return jsonify({
            'earnings': earnings_data,
            'symbols': symbols,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting earnings data: {e}")
        return jsonify({
            'error': 'Failed to get earnings data',
            'message': str(e),
            'earnings': {}
        }), 500

# For testing without Firebase
if not FIREBASE_MODE and __name__ == "__main__":
    app.run(debug=True, port=5001)