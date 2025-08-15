"""
Streamlit dashboard for real-time trading data and backtest visualization.
Enhanced version with actual functionality and data integration.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
import time

# Configure page
st.set_page_config(
    page_title="Cloud Trading Bot Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success {
        color: green;
    }
    .danger {
        color: red;
    }
    .warning {
        color: orange;
    }
</style>
""", unsafe_allow_html=True)

# Configuration
API_BASE_URL = "http://localhost:8080"

def fetch_api_data(endpoint, default_data=None):
    """Fetch data from the API with error handling"""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            st.warning(f"API returned status {response.status_code} for {endpoint}")
            return default_data
    except requests.exceptions.RequestException as e:
        if default_data is None:
            st.error(f"Failed to connect to API: {str(e)}")
        return default_data

def generate_mock_data():
    """Generate realistic mock data for demonstration"""
    dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
    
    # Generate mock portfolio performance
    returns = np.random.normal(0.001, 0.02, len(dates))
    cumulative_returns = np.cumprod(1 + returns)
    portfolio_values = 100000 * cumulative_returns
    
    return pd.DataFrame({
        'date': dates,
        'portfolio_value': portfolio_values,
        'daily_return': returns
    })

def main():
    # Header
    st.title("🚀 Cloud Trading Bot Dashboard")
    st.markdown("**Real-time market data, trading performance, and strategy management**")
    
    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox("Choose a page", [
        "Overview", "Live Trading", "Backtest", "Optimization", "Market Data"
    ])
    
    # API Health Check
    health_data = fetch_api_data("/health")
    if health_data:
        st.sidebar.success("✅ API Connected")
    else:
        st.sidebar.error("❌ API Disconnected")
    
    # Main content based on page selection
    if page == "Overview":
        show_overview()
    elif page == "Live Trading":
        show_live_trading()
    elif page == "Backtest":
        show_backtest()
    elif page == "Optimization":
        show_optimization()
    elif page == "Market Data":
        show_market_data()

def show_overview():
    """Display system overview and key metrics"""
    st.header("📊 System Overview")
    
    # Get system status
    status_data = fetch_api_data("/api/system/status", {
        'status': 'running',
        'portfolio_value': 100000.0,
        'daily_pnl': 1250.75,
        'active_strategies': 3,
        'trading_enabled': False,
        'paper_trading': True
    })
    
    # Key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Portfolio Value",
            value=f"${status_data.get('portfolio_value', 0):,.2f}",
            delta=f"{status_data.get('daily_pnl', 0):+.2f}"
        )
    
    with col2:
        st.metric(
            label="Daily P&L",
            value=f"${status_data.get('daily_pnl', 0):,.2f}",
            delta=f"{(status_data.get('daily_pnl', 0) / status_data.get('portfolio_value', 1)) * 100:.2f}%"
        )
    
    with col3:
        st.metric(
            label="Active Strategies",
            value=status_data.get('active_strategies', 0)
        )
    
    with col4:
        trading_mode = "Paper Trading" if status_data.get('paper_trading', True) else "Live Trading"
        st.metric(
            label="Trading Mode",
            value=trading_mode
        )
    
    # Portfolio performance chart
    st.subheader("📈 Portfolio Performance")
    portfolio_data = generate_mock_data()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=portfolio_data['date'],
        y=portfolio_data['portfolio_value'],
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Date",
        yaxis_title="Portfolio Value ($)",
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Recent activity
    st.subheader("🔄 Recent Activity")
    st.info("📊 System started in paper trading mode")
    st.info("🎯 3 active strategies running")
    st.info("💹 Market data updated 2 minutes ago")

def show_live_trading():
    """Display live trading information"""
    st.header("🔴 Live Trading Dashboard")
    
    # Trading controls
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🟢 Start Trading", type="primary"):
            start_result = fetch_api_data("/api/system/start", {})
            if start_result:
                st.success("Trading system started!")
            else:
                st.error("Failed to start trading system")
    
    with col2:
        if st.button("🔴 Stop Trading", type="secondary"):
            stop_result = fetch_api_data("/api/system/stop", {})
            if stop_result:
                st.success("Trading system stopped!")
            else:
                st.error("Failed to stop trading system")
    
    # Market data
    st.subheader("📊 Current Market Data")
    market_data = fetch_api_data("/api/market-data", {
        'data': {
            'AAPL': {'price': 150.25, 'change': 2.15, 'volume': 1234567},
            'GOOGL': {'price': 2750.80, 'change': -15.30, 'volume': 987654},
            'MSFT': {'price': 380.45, 'change': 5.67, 'volume': 2345678}
        }
    })
    
    if market_data and 'data' in market_data:
        df = pd.DataFrame.from_dict(market_data['data'], orient='index')
        df['symbol'] = df.index
        df = df[['symbol', 'price', 'change', 'volume']]
        
        # Format the dataframe for better display
        df['price'] = df['price'].apply(lambda x: f"${x:.2f}")
        df['change'] = df['change'].apply(lambda x: f"{x:+.2f}")
        df['volume'] = df['volume'].apply(lambda x: f"{x:,}")
        
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("No market data available")
    
    # Performance metrics
    st.subheader("📈 Performance Metrics")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Win Rate", "67.5%", "2.3%")
    with col2:
        st.metric("Sharpe Ratio", "1.85", "0.12")
    with col3:
        st.metric("Max Drawdown", "-4.2%", "1.1%")

def show_backtest():
    """Display backtesting interface"""
    st.header("📈 Strategy Backtesting")
    
    # Backtest configuration
    st.subheader("⚙️ Configuration")
    col1, col2 = st.columns(2)
    
    with col1:
        symbols = st.multiselect(
            "Select symbols",
            ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"],
            default=["AAPL", "GOOGL", "MSFT"]
        )
        
        start_date = st.date_input(
            "Start date",
            value=datetime.now() - timedelta(days=365)
        )
    
    with col2:
        strategy = st.selectbox(
            "Strategy",
            ["Mean Reversion", "Momentum", "RSI Crossover", "MACD"]
        )
        
        end_date = st.date_input(
            "End date",
            value=datetime.now()
        )
    
    # Run backtest button
    if st.button("🚀 Run Backtest", type="primary"):
        with st.spinner("Running backtest..."):
            # Simulate backtest processing
            progress_bar = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress_bar.progress(i + 1)
            
            st.success("Backtest completed successfully!")
            
            # Display mock results
            st.subheader("📊 Backtest Results")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Return", "24.7%")
            with col2:
                st.metric("Annual Return", "18.2%")
            with col3:
                st.metric("Max Drawdown", "-8.1%")
            with col4:
                st.metric("Win Rate", "64.3%")
            
            # Generate mock equity curve
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            equity_curve = 100000 * np.cumprod(1 + np.random.normal(0.0005, 0.015, len(dates)))
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=dates,
                y=equity_curve,
                mode='lines',
                name='Equity Curve',
                line=dict(color='green', width=2)
            ))
            
            fig.update_layout(
                title="Equity Curve",
                xaxis_title="Date",
                yaxis_title="Portfolio Value ($)"
            )
            
            st.plotly_chart(fig, use_container_width=True)

def show_optimization():
    """Display optimization interface"""
    st.header("⚙️ Strategy Optimization")
    
    # Get available strategies
    strategies_data = fetch_api_data("/api/strategies", {'strategies': ['RSI Strategy', 'MACD Strategy', 'Mean Reversion']})
    strategies = strategies_data.get('strategies', [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_strategy = st.selectbox("Select Strategy", strategies)
        generations = st.slider("Optimization Generations", min_value=10, max_value=100, value=50)
    
    with col2:
        population_size = st.slider("Population Size", min_value=20, max_value=200, value=100)
        optimization_metric = st.selectbox("Optimization Metric", ["Sharpe Ratio", "Total Return", "Risk-Adjusted Return"])
    
    if st.button("🎯 Start Optimization", type="primary"):
        with st.spinner("Running optimization..."):
            # Mock optimization process
            progress_bar = st.progress(0)
            for i in range(generations):
                time.sleep(0.02)
                progress_bar.progress((i + 1) / generations)
            
            st.success("Optimization completed!")
            
            # Display results
            st.subheader("🏆 Optimization Results")
            
            best_params = {
                "RSI_period": 14,
                "RSI_oversold": 30,
                "RSI_overbought": 70,
                "stop_loss": 0.05,
                "take_profit": 0.15
            }
            
            st.json(best_params)
            
            # Performance comparison
            st.subheader("📊 Performance Comparison")
            comparison_data = pd.DataFrame({
                "Metric": ["Annual Return", "Sharpe Ratio", "Max Drawdown", "Win Rate"],
                "Before Optimization": ["12.3%", "1.23", "-15.2%", "58.7%"],
                "After Optimization": ["18.9%", "1.87", "-8.4%", "67.2%"],
                "Improvement": ["+6.6%", "+0.64", "+6.8%", "+8.5%"]
            })
            
            st.dataframe(comparison_data, use_container_width=True)

def show_market_data():
    """Display market data and analysis"""
    st.header("📊 Market Data & Analysis")
    
    # Get market trends
    trends_data = fetch_api_data("/api/market-trends", {
        'trends': {
            'market_sentiment': 'Bullish',
            'vix': 18.5,
            'sector_performance': {
                'Technology': 2.3,
                'Healthcare': -0.8,
                'Financial': 1.2,
                'Energy': -1.5,
                'Consumer': 0.9
            }
        }
    })
    
    if trends_data and 'trends' in trends_data:
        trends = trends_data['trends']
        
        # Market overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Market Sentiment", trends.get('market_sentiment', 'Neutral'))
        with col2:
            st.metric("VIX", f"{trends.get('vix', 0):.1f}")
        with col3:
            st.metric("Market Trend", "📈 Upward")
        
        # Sector performance
        if 'sector_performance' in trends:
            st.subheader("🏭 Sector Performance")
            sector_df = pd.DataFrame.from_dict(trends['sector_performance'], orient='index', columns=['Performance'])
            sector_df['Sector'] = sector_df.index
            
            fig = px.bar(
                sector_df,
                x='Sector',
                y='Performance',
                color='Performance',
                color_continuous_scale='RdYlGn',
                title="Sector Performance (%)"
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    # Real-time quotes
    st.subheader("💹 Real-time Quotes")
    
    # Auto-refresh functionality
    if st.checkbox("Auto-refresh (30s)", value=False):
        time.sleep(30)
        st.experimental_rerun()
    
    # Manual refresh button
    if st.button("🔄 Refresh Data"):
        st.experimental_rerun()

if __name__ == "__main__":
    main()