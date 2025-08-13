"""
Advanced trading bot with comprehensive decision engine.
- Uses live data only (no mock data)
- Implements candlestick pattern recognition
- Aggregates technical, fundamental, sentiment, and news analysis
- Provides transparent decision logic with risk assessment
"""
import asyncio
import logging
from typing import Dict, List, Any
from datetime import datetime

from backend.data_collector import (
    fetch_market_data, fetch_market_trends, 
    make_trading_decisions, fetch_comprehensive_market_data
)
from backend.config import get_config
from backend.decision_engine import DecisionEngine
from backend.live_data_manager import get_live_market_data_manager

# Set up logging with enhanced format for decision transparency
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s"
)
logger = logging.getLogger(__name__)

def run_bot():
    """
    Main bot execution function with comprehensive decision making.
    """
    try:
        config = get_config()
        logger.info(f"Starting ADVANCED trading bot in {config['env']} environment")
        logger.info("LIVE DATA ONLY MODE - No mock data allowed")
        
        # Use autonomous stock selection instead of hardcoded symbols
        from backend.market_scanner import get_autonomous_stock_selection
        
        max_positions = config.get('trading', {}).get('max_positions', 10)
        logger.info("🔍 Performing autonomous stock selection...")
        
        # Get autonomously selected symbols
        symbols = get_autonomous_stock_selection(max_stocks=max_positions)
        
        if not symbols:
            logger.warning("No stocks selected by autonomous scanner, using fallback")
            symbols = ['AAPL', 'MSFT', 'GOOGL']  # Minimal fallback
            
        logger.info(f"✅ Autonomously selected {len(symbols)} symbols for analysis: {symbols}")
        
        # Run comprehensive analysis
        decisions = asyncio.run(run_comprehensive_analysis(symbols))
        
        # Display detailed results
        display_trading_decisions(decisions)
        
        # Execute trading recommendations (if enabled)
        if config.get('trading', {}).get('auto_execute', False):
            logger.info("Auto-execution is enabled")
            execute_trading_decisions(decisions, config)
        else:
            logger.info("Auto-execution is disabled - showing recommendations only")
        
        logger.info("Bot execution completed successfully")
        
    except Exception as e:
        logger.error(f"Bot execution failed: {e}")
        raise

async def run_comprehensive_analysis(symbols: List[str]) -> Dict[str, Any]:
    """
    Run comprehensive analysis with live data and decision engine.
    
    Args:
        symbols: List of stock symbols to analyze
        
    Returns:
        Dictionary with trading decisions for each symbol
    """
    logger.info("=== STARTING COMPREHENSIVE MARKET ANALYSIS ===")
    
    try:
        # 1. Fetch comprehensive market data (all sources)
        logger.info("Fetching comprehensive market data...")
        comprehensive_data = await fetch_comprehensive_market_data(symbols)
        
        # 2. Make trading decisions using decision engine
        logger.info("Making trading decisions...")
        decisions = await make_trading_decisions(symbols)
        
        # 3. Validate data quality and decision transparency
        validate_decision_quality(decisions, comprehensive_data)
        
        logger.info("=== COMPREHENSIVE ANALYSIS COMPLETED ===")
        return decisions
        
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise

def validate_decision_quality(decisions: Dict[str, Any], data: Dict[str, Any]):
    """
    Validate decision quality and data freshness for transparency.
    
    Args:
        decisions: Trading decisions
        data: Comprehensive market data
    """
    logger.info("=== VALIDATING DECISION QUALITY ===")
    
    for symbol in decisions:
        decision = decisions[symbol]
        symbol_data = data.get(symbol, {})
        
        # Check decision completeness
        required_fields = ['signal', 'confidence', 'reasoning', 'timestamp']
        missing_fields = [field for field in required_fields if field not in decision]
        
        if missing_fields:
            logger.warning(f"{symbol}: Missing decision fields: {missing_fields}")
        
        # Check data freshness if available
        if 'live_data' in symbol_data and 'data_quality' in symbol_data['live_data']:
            data_quality = symbol_data['live_data']['data_quality']
            freshness = data_quality.get('freshness', 'unknown')
            
            if freshness in ['stale', 'expired']:
                logger.warning(f"{symbol}: Using {freshness} data for decisions")
            else:
                logger.info(f"{symbol}: Using {freshness} data ✓")
        
        # Check factor transparency
        if 'factors' in decision and len(decision['factors']) > 0:
            logger.info(f"{symbol}: Decision based on {len(decision['factors'])} factors ✓")
            
            for factor in decision['factors'][:3]:  # Log first 3 factors
                logger.debug(f"  - {factor['name']}: {factor['signal']} (confidence: {factor['confidence']:.2f})")
        else:
            logger.warning(f"{symbol}: No decision factors available")

def display_trading_decisions(decisions: Dict[str, Any]):
    """
    Display trading decisions with detailed reasoning.
    
    Args:
        decisions: Trading decisions for each symbol
    """
    logger.info("=== TRADING DECISIONS SUMMARY ===")
    
    if not decisions:
        print("\nNo trading decisions available")
        return
    
    print(f"\n{'='*80}")
    print(f"{'TRADING DECISIONS':^80}")
    print(f"{'='*80}")
    print(f"{'Symbol':<8} {'Signal':<12} {'Confidence':<10} {'Risk':<8} {'Position':<10} {'Reasoning'}")
    print(f"{'-'*80}")
    
    for symbol, decision in decisions.items():
        if 'error' in decision:
            print(f"{symbol:<8} {'ERROR':<12} {'N/A':<10} {'N/A':<8} {'N/A':<10} {decision['error']}")
            continue
        
        signal = decision.get('signal', 'N/A')
        confidence = decision.get('confidence', 0.0)
        risk_score = decision.get('risk_score', 0.0)
        position_size = decision.get('position_size', 0.0)
        reasoning = decision.get('reasoning', 'No reasoning available')
        
        # Truncate reasoning for display
        display_reasoning = reasoning[:50] + "..." if len(reasoning) > 50 else reasoning
        
        print(f"{symbol:<8} {signal:<12} {confidence:<10.2f} {risk_score:<8.2f} {position_size:<10.1%} {display_reasoning}")
    
    print(f"{'-'*80}")
    
    # Display detailed analysis for each symbol
    print(f"\n{'DETAILED ANALYSIS':^80}")
    print(f"{'='*80}")
    
    for symbol, decision in decisions.items():
        if 'error' in decision:
            continue
            
        print(f"\n{symbol} - {decision.get('signal', 'N/A')} (Confidence: {decision.get('confidence', 0):.1%})")
        print(f"Risk Score: {decision.get('risk_score', 0):.1%} | Position Size: {decision.get('position_size', 0):.1%}")
        print(f"Reasoning: {decision.get('reasoning', 'N/A')}")
        
        # Display contributing factors
        factors = decision.get('factors', [])
        if factors:
            print("Contributing Factors:")
            for factor in factors:
                print(f"  • {factor['name']}: {factor['signal']} ({factor['confidence']:.1%} confidence)")
                print(f"    Source: {factor['data_source']} | Weight: {factor['weight']:.1%}")
                print(f"    Reasoning: {factor['reasoning']}")
        
        print("-" * 60)

def execute_trading_decisions(decisions: Dict[str, Any], config: Dict[str, Any]):
    """
    Execute trading decisions (paper trading or live trading).
    
    Args:
        decisions: Trading decisions
        config: Bot configuration
    """
    logger.info("=== EXECUTING TRADING DECISIONS ===")
    
    paper_trading = config.get('trading', {}).get('paper_trading', True)
    initial_capital = config.get('trading', {}).get('initial_capital', 10000)
    
    logger.info(f"Execution mode: {'Paper Trading' if paper_trading else 'Live Trading'}")
    logger.info(f"Initial capital: ${initial_capital:,.2f}")
    
    executed_trades = []
    
    for symbol, decision in decisions.items():
        if 'error' in decision:
            logger.warning(f"Skipping {symbol} due to decision error: {decision['error']}")
            continue
        
        signal = decision.get('signal', 'HOLD')
        confidence = decision.get('confidence', 0.0)
        position_size = decision.get('position_size', 0.0)
        
        # Only execute high-confidence decisions
        min_confidence = config.get('trading', {}).get('min_confidence', 0.6)
        
        if confidence < min_confidence:
            logger.info(f"Skipping {symbol}: Confidence {confidence:.1%} below threshold {min_confidence:.1%}")
            continue
        
        if signal in ['BUY', 'STRONG_BUY'] and position_size > 0:
            trade_amount = initial_capital * position_size
            
            if paper_trading:
                logger.info(f"PAPER TRADE: BUY ${trade_amount:,.2f} of {symbol}")
            else:
                logger.info(f"LIVE TRADE: BUY ${trade_amount:,.2f} of {symbol}")
                # Here would be actual trade execution logic
            
            executed_trades.append({
                'symbol': symbol,
                'action': 'BUY',
                'amount': trade_amount,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            })
        
        elif signal in ['SELL', 'STRONG_SELL']:
            if paper_trading:
                logger.info(f"PAPER TRADE: SELL {symbol}")
            else:
                logger.info(f"LIVE TRADE: SELL {symbol}")
                # Here would be actual trade execution logic
            
            executed_trades.append({
                'symbol': symbol,
                'action': 'SELL',
                'confidence': confidence,
                'timestamp': datetime.now().isoformat()
            })
    
    if executed_trades:
        logger.info(f"Executed {len(executed_trades)} trades")
        for trade in executed_trades:
            logger.info(f"  {trade['action']} {trade['symbol']} (confidence: {trade['confidence']:.1%})")
    else:
        logger.info("No trades executed (low confidence or HOLD signals)")

def run_simple_bot():
    """
    Simplified bot execution for backward compatibility.
    """
    try:
        config = get_config()
        logger.info(f"Starting simplified trading bot in {config['env']} environment")
        
        # Fetch basic market data (live only)
        logger.info("Fetching live market data...")
        symbols = config['trading']['default_symbols']
        market_data = fetch_market_data(symbols)
        
        logger.info(f"Successfully fetched data for {len(market_data)} symbols")
        
        # Fetch market trends (live only)
        logger.info("Fetching live market trends...")
        trends = fetch_market_trends()
        
        # Display basic results
        print("\n=== LIVE MARKET DATA ===")
        for symbol, data in market_data.items():
            if 'error' not in data:
                age_info = ""
                if 'data_age_seconds' in data:
                    age_minutes = data['data_age_seconds'] / 60
                    age_info = f" ({age_minutes:.1f}min old)"
                
                print(f"{symbol}: ${data['price']:.2f} (Volume: {data['volume']:,}){age_info}")
            else:
                print(f"{symbol}: ERROR - {data['error']}")
        
        print("\n=== LIVE MARKET TRENDS ===")
        if 'error' not in trends and 'sp500' in trends:
            sp500_data = trends['sp500']
            age_info = ""
            if 'data_age_seconds' in sp500_data:
                age_minutes = sp500_data['data_age_seconds'] / 60
                age_info = f" ({age_minutes:.1f}min old)"
            
            print(f"S&P 500: ${sp500_data['current_price']:.2f} ({sp500_data['change_percent']:+.2f}%) - Trend: {sp500_data['trend']}{age_info}")
        else:
            print(f"Market trend data unavailable: {trends.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"Simple bot execution failed: {e}")
        raise
        
        logger.info("Bot execution completed successfully")
        
    except Exception as e:
        logger.error(f"Error in bot execution: {e}")
        raise

if __name__ == "__main__":
    run_bot()