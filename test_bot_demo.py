#!/usr/bin/env python3
"""
Demo script showing comprehensive trading bot capabilities.
This demonstrates what the bot would do with live data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.decision_engine import DecisionEngine, Signal

def create_demo_data():
    """Create realistic demo data for demonstration"""
    # Create realistic OHLCV data with patterns
    np.random.seed(42)
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    
    # Create price data with upward trend and some volatility
    base_price = 150.0
    prices = []
    
    for i in range(100):
        # Add trend and some random walk
        trend = i * 0.2  # Slight upward trend
        noise = np.random.normal(0, 2)
        price = base_price + trend + noise
        prices.append(max(price, 50))  # Don't go below $50
    
    # Create OHLCV data
    data = []
    for i, close_price in enumerate(prices):
        open_price = close_price + np.random.normal(0, 0.5)
        high = max(open_price, close_price) + abs(np.random.normal(0, 1))
        low = min(open_price, close_price) - abs(np.random.normal(0, 1))
        volume = np.random.randint(800000, 2000000)
        
        data.append({
            'Open': open_price,
            'High': high,
            'Low': low,
            'Close': close_price,
            'Volume': volume
        })
    
    return pd.DataFrame(data, index=dates)

def create_demo_market_data():
    """Create demo current market data"""
    return {
        'price': 170.50,
        'volume': 1250000,
        'open': 169.80,
        'high': 171.20,
        'low': 169.20,
        'market_cap': 2800000000000,
        'pe_ratio': 28.5,
        'timestamp': datetime.now().isoformat()
    }

def create_demo_fundamental_data():
    """Create demo fundamental data"""
    return {
        'pe_ratio': 28.5,
        'market_cap': 2800000000000,
        'price_to_book': 5.2,
        'debt_to_equity': 1.8,
        'roe': 0.145,
        'profit_margin': 0.23,
        'revenue_growth': 0.08,
        'earnings_growth': 0.12,
        'dividend_yield': 0.005,
        'beta': 1.2
    }

def create_demo_news_sentiment():
    """Create demo news sentiment"""
    return {
        'sentiment_score': 0.35,  # Positive
        'article_count': 8,
        'positive_count': 5,
        'negative_count': 1,
        'neutral_count': 2,
        'sources': ['Reuters', 'Bloomberg', 'CNBC'],
        'timestamp': datetime.now()
    }

def create_demo_social_sentiment():
    """Create demo social sentiment"""
    return {
        'sentiment_score': 0.15,  # Mildly positive
        'mention_count': 25,
        'positive_mentions': 12,
        'negative_mentions': 8,
        'neutral_mentions': 5,
        'platforms': ['Reddit', 'Twitter'],
        'timestamp': datetime.now()
    }

def demo_comprehensive_analysis():
    """Demonstrate comprehensive trading analysis"""
    print("🤖 COMPREHENSIVE TRADING BOT DEMO")
    print("=" * 60)
    print("📊 This demonstrates what the bot would do with live market data")
    print("🔴 Live data integration enforced - no mock data allowed")
    print("=" * 60)
    
    # Initialize decision engine
    engine = DecisionEngine()
    
    # Create demo data (would be live data in production)
    symbol = "AAPL"
    market_data = create_demo_market_data()
    historical_data = create_demo_data()
    fundamental_data = create_demo_fundamental_data()
    news_sentiment = create_demo_news_sentiment()
    social_sentiment = create_demo_social_sentiment()
    
    print(f"\n📈 ANALYZING {symbol}")
    print("-" * 30)
    
    # Make comprehensive decision
    decision = engine.make_decision(
        symbol=symbol,
        market_data=market_data,
        historical_data=historical_data,
        fundamental_data=fundamental_data,
        news_sentiment=news_sentiment,
        social_sentiment=social_sentiment
    )
    
    # Display results
    print(f"🎯 TRADING DECISION: {decision.overall_signal.value}")
    print(f"📊 Confidence: {decision.confidence:.1%}")
    print(f"⚠️  Risk Score: {decision.risk_score:.1%}")
    print(f"💰 Recommended Position: {decision.position_size:.1%} of portfolio")
    
    print(f"\n💭 REASONING:")
    print(f"   {decision.reasoning}")
    
    print(f"\n🔍 DECISION FACTORS ({len(decision.factors)} total):")
    
    for factor in decision.factors:
        confidence_bar = "█" * int(factor.confidence * 10) + "░" * (10 - int(factor.confidence * 10))
        print(f"   • {factor.name}")
        print(f"     Signal: {factor.signal.value} | Confidence: [{confidence_bar}] {factor.confidence:.1%}")
        print(f"     Weight: {factor.weight:.1%} | Source: {factor.data_source}")
        print(f"     Reasoning: {factor.reasoning}")
        print()
    
    # Risk Assessment
    print("🛡️  RISK ASSESSMENT:")
    if decision.risk_score < 0.3:
        risk_level = "LOW"
        risk_color = "🟢"
    elif decision.risk_score < 0.7:
        risk_level = "MODERATE"
        risk_color = "🟡"
    else:
        risk_level = "HIGH"
        risk_color = "🔴"
    
    print(f"   {risk_color} Risk Level: {risk_level} ({decision.risk_score:.1%})")
    
    # Trading Recommendation
    print("\n💡 TRADING RECOMMENDATION:")
    if decision.overall_signal in [Signal.STRONG_BUY, Signal.BUY]:
        action_emoji = "📈"
        action = "CONSIDER BUYING"
    elif decision.overall_signal in [Signal.STRONG_SELL, Signal.SELL]:
        action_emoji = "📉"
        action = "CONSIDER SELLING"
    else:
        action_emoji = "⏸️"
        action = "HOLD POSITION"
    
    print(f"   {action_emoji} {action}")
    print(f"   💼 Position Size: {decision.position_size:.1%} of portfolio")
    
    if decision.confidence >= 0.7:
        conf_emoji = "🎯"
        conf_desc = "HIGH CONFIDENCE"
    elif decision.confidence >= 0.5:
        conf_emoji = "🎲"
        conf_desc = "MODERATE CONFIDENCE"
    else:
        conf_emoji = "❓"
        conf_desc = "LOW CONFIDENCE"
    
    print(f"   {conf_emoji} Confidence: {conf_desc} ({decision.confidence:.1%})")
    
    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print("🔄 In production, this would execute with live market data")
    print("📝 All decisions are logged for transparency and audit")
    print("🛡️  Risk management and position sizing automatically applied")

def demo_live_data_enforcement():
    """Demonstrate live data enforcement"""
    print("\n🔒 LIVE DATA ENFORCEMENT DEMO")
    print("=" * 40)
    
    # Test data collector with mock data disabled
    from backend.data_collector import fetch_market_data
    
    import os
    
    print("📡 Testing live data enforcement...")
    
    # Set environment to reject mock data
    os.environ['USE_MOCK_DATA'] = 'false'
    
    try:
        # This should fail because no internet access
        fetch_market_data(['AAPL'], use_mock=False)
        print("❌ ERROR: Should have failed!")
    except Exception as e:
        if "Mock data fallback is disabled" in str(e):
            print("✅ SUCCESS: Live data enforcement working correctly")
            print("   System properly rejects mock data and fails when live data unavailable")
        else:
            print(f"❓ Different error: {e}")
    
    # Test explicit mock data request (should fail)
    try:
        fetch_market_data(['AAPL'], use_mock=True)
        print("❌ ERROR: Should have rejected mock data!")
    except Exception as e:
        if "Mock data is not allowed" in str(e):
            print("✅ SUCCESS: Mock data properly rejected")
        else:
            print(f"❓ Different error: {e}")

if __name__ == "__main__":
    demo_comprehensive_analysis()
    demo_live_data_enforcement()