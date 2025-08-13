#!/usr/bin/env python3
"""
Enhanced Trading Bot Analytics Demo

Demonstrates the new analytics capabilities including:
1. Live bid-ask spread monitoring
2. Market liquidity prediction 
3. Tail risk analysis (VaR, CVaR, drawdown analysis)

This replaces simple standard deviation-based risk metrics with
comprehensive tail risk analysis for better extreme event risk management.
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import time
import logging

from analytics import SpreadMonitor, LiquidityPredictor, TailRiskAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AnalyticsDemo:
    """Demonstration of enhanced trading bot analytics."""
    
    def __init__(self):
        """Initialize analytics demo."""
        # Configuration for analytics modules
        self.symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA']
        
        # Spread monitoring configuration
        spread_config = {
            'symbols': self.symbols,
            'window_size': 50,
            'alert_thresholds': {
                'default': {
                    'max_spread_pct': 0.5,
                    'min_liquidity_score': 40
                }
            },
            'update_interval': 1.0
        }
        self.spread_monitor = SpreadMonitor(spread_config)
        
        # Liquidity prediction configuration
        liquidity_config = {
            'symbols': self.symbols,
            'prediction_horizon': 5,
            'feature_window': 30,
            'model_type': 'ensemble',
            'retrain_interval': 60
        }
        self.liquidity_predictor = LiquidityPredictor(liquidity_config)
        
        # Tail risk analysis configuration
        risk_config = {
            'confidence_levels': [0.95, 0.99, 0.995],
            'lookback_periods': [30, 90, 252],
            'portfolio_value': 1000000,
            'stress_scenarios': {
                'market_crash_2008': {'market_shock': -0.37, 'vol_multiplier': 3.0},
                'covid_crash_2020': {'market_shock': -0.34, 'vol_multiplier': 2.5}
            },
            'update_frequency': 15
        }
        self.tail_risk_analyzer = TailRiskAnalyzer(risk_config)
    
    def simulate_market_data(self, symbol: str, days: int = 100) -> pd.DataFrame:
        """
        Simulate realistic market data for demonstration.
        
        Args:
            symbol: Stock symbol
            days: Number of days to simulate
            
        Returns:
            DataFrame with simulated market data
        """
        np.random.seed(hash(symbol) % 2**31)  # Consistent data per symbol
        
        # Simulate price path with realistic characteristics
        initial_price = 100 + np.random.uniform(-50, 200)
        daily_returns = np.random.normal(0.0005, 0.018, days)  # ~13% annual vol
        
        # Add some volatility clustering and extreme events
        for i in range(1, len(daily_returns)):
            if np.random.random() < 0.02:  # 2% chance of extreme event
                daily_returns[i] = np.random.normal(0, 0.08)  # High volatility event
        
        # Calculate prices
        prices = [initial_price]
        for ret in daily_returns:
            prices.append(prices[-1] * (1 + ret))
        
        # Generate timestamps
        start_date = datetime.now() - timedelta(days=days)
        timestamps = [start_date + timedelta(days=i) for i in range(days + 1)]
        
        # Create DataFrame
        data = pd.DataFrame({
            'timestamp': timestamps,
            'price': prices,
            'return': [0] + list(daily_returns),
            'volume': np.random.lognormal(14, 0.5, days + 1)  # Realistic volume
        })
        
        # Add bid/ask spreads
        data['spread_pct'] = np.random.uniform(0.02, 0.15, len(data))  # 2-15 bp spreads
        data['bid'] = data['price'] * (1 - data['spread_pct'] / 200)
        data['ask'] = data['price'] * (1 + data['spread_pct'] / 200)
        
        return data
    
    async def demonstrate_spread_monitoring(self):
        """Demonstrate real-time spread monitoring capabilities."""
        logger.info("=== Demonstrating Bid-Ask Spread Monitoring ===")
        
        # Simulate real-time spread updates
        for symbol in self.symbols[:2]:  # Demo with 2 symbols
            data = self.simulate_market_data(symbol, 20)
            
            logger.info(f"\nProcessing spread data for {symbol}...")
            
            # Process last 10 data points as "real-time" updates
            for _, row in data.tail(10).iterrows():
                quote = {
                    'bid': row['bid'],
                    'ask': row['ask'],
                    'price': row['price'],
                    'volume': row['volume'],
                    'timestamp': row['timestamp'].timestamp()
                }
                
                self.spread_monitor._process_quote(symbol, quote)
            
            # Update metrics and get results
            self.spread_monitor._update_spread_metrics(symbol)
            
            # Display spread analytics
            current_spreads = self.spread_monitor.get_current_spreads()
            if symbol in current_spreads:
                metrics = current_spreads[symbol]
                logger.info(f"{symbol} Spread Analytics:")
                logger.info(f"  Current Spread: {metrics['current_spread_pct']:.3f}%")
                logger.info(f"  Average Spread: {metrics['avg_spread_pct']:.3f}%")
                logger.info(f"  Liquidity Score: {metrics['liquidity_score']:.1f}/100")
                logger.info(f"  Market Impact Cost: {metrics['market_impact_cost']:.2f} bp")
                logger.info(f"  Spread Trend: {metrics['spread_trend']}")
                
                # Calculate trading cost for $10,000 trade
                cost_estimate = self.spread_monitor.calculate_trading_cost_estimate(symbol, 10000)
                if 'total_cost_dollar' in cost_estimate:
                    logger.info(f"  Est. Trading Cost ($10K): ${cost_estimate['total_cost_dollar']:.2f}")
        
        # Get overall liquidity summary
        liquidity_summary = self.spread_monitor.get_liquidity_summary()
        logger.info(f"\nOverall Market Liquidity:")
        logger.info(f"  Symbols Monitored: {liquidity_summary.get('symbols_monitored', 0)}")
        logger.info(f"  Average Liquidity Score: {liquidity_summary.get('avg_liquidity_score', 0):.1f}")
        logger.info(f"  Market Condition: {liquidity_summary.get('market_condition', 'unknown')}")
    
    async def demonstrate_liquidity_prediction(self):
        """Demonstrate market liquidity prediction capabilities."""
        logger.info("\n=== Demonstrating Market Liquidity Prediction ===")
        
        # Initialize models
        await self.liquidity_predictor._initialize_models()
        
        # Simulate historical data for training
        for symbol in self.symbols[:2]:
            data = self.simulate_market_data(symbol, 100)
            
            # Add spread and order flow data to history
            for _, row in data.iterrows():
                spread_data = {
                    'timestamp': row['timestamp'],
                    'spread_pct': row['spread_pct'],
                    'spread': row['ask'] - row['bid']
                }
                self.liquidity_predictor.spread_data_history[symbol].append(spread_data)
                
                # Simulate order flow
                order_flow = self.liquidity_predictor._simulate_order_flow_data(symbol)
                self.liquidity_predictor.order_flow_history[symbol].append(order_flow)
                
                market_data = {
                    'price': row['price'],
                    'volume': row['volume'],
                    'timestamp': row['timestamp']
                }
                self.liquidity_predictor.market_data_history[symbol].append(market_data)
        
        # Generate predictions
        for symbol in self.symbols[:2]:
            try:
                # Train model if enough data
                if len(self.liquidity_predictor.spread_data_history[symbol]) >= 50:
                    await self.liquidity_predictor._retrain_model(symbol)
                
                # Generate prediction
                prediction = await self.liquidity_predictor._generate_prediction(symbol)
                
                if prediction:
                    logger.info(f"\n{symbol} Liquidity Prediction:")
                    logger.info(f"  Predicted Liquidity Score: {prediction['predicted_liquidity_score']:.1f}/100")
                    logger.info(f"  Confidence: {prediction['confidence']:.2f}")
                    logger.info(f"  Liquidity Trend: {prediction['liquidity_trend']}")
                    logger.info(f"  Current Spread: {prediction['current_spread_pct']:.3f}%")
                    
                    # Get optimal trading timing
                    timing_rec = self.liquidity_predictor.predict_optimal_trade_timing(symbol, 25000)
                    logger.info(f"  Trading Recommendation: {timing_rec['timing_recommendation']}")
                    logger.info(f"  Reason: {timing_rec['reason']}")
                    logger.info(f"  Est. Cost ($25K trade): ${timing_rec['estimated_cost_dollar']:.2f}")
                else:
                    logger.info(f"{symbol}: Insufficient data for prediction")
                    
            except Exception as e:
                logger.warning(f"Prediction failed for {symbol}: {e}")
        
        # Get prediction summary
        summary = self.liquidity_predictor.get_prediction_summary()
        if summary.get('status') != 'no_predictions':
            logger.info(f"\nLiquidity Prediction Summary:")
            logger.info(f"  Average Predicted Liquidity: {summary.get('avg_predicted_liquidity', 0):.1f}")
            logger.info(f"  Average Confidence: {summary.get('avg_confidence', 0):.2f}")
            logger.info(f"  Dominant Trend: {summary.get('dominant_trend', 'unknown')}")
            logger.info(f"  Market Liquidity Condition: {summary.get('market_liquidity_condition', 'unknown')}")
    
    def demonstrate_tail_risk_analysis(self):
        """Demonstrate comprehensive tail risk analysis."""
        logger.info("\n=== Demonstrating Tail Risk Analysis ===")
        
        # Simulate portfolio data
        portfolio_values = []
        positions = {}
        
        for symbol in self.symbols:
            data = self.simulate_market_data(symbol, 150)
            
            # Update individual asset data
            for _, row in data.iterrows():
                self.tail_risk_analyzer.update_market_data(symbol, {
                    'price': row['price'],
                    'timestamp': row['timestamp']
                })
            
            # Create position (25% allocation each)
            current_price = data.iloc[-1]['price']
            position_size = 250000 / current_price  # $250K position
            positions[symbol] = position_size
        
        # Simulate portfolio value history
        base_value = 1000000
        for i in range(100):
            # Simulate portfolio fluctuation
            daily_return = np.random.normal(0.0008, 0.015)
            portfolio_value = base_value * (1 + daily_return)
            
            # Update portfolio with position values
            position_values = {}
            for symbol, qty in positions.items():
                if symbol in self.tail_risk_analyzer.price_history:
                    prices = [p['price'] for p in self.tail_risk_analyzer.price_history[symbol]]
                    if prices:
                        current_price = prices[-1] + np.random.normal(0, prices[-1] * 0.01)
                        position_values[symbol] = qty * current_price
            
            self.tail_risk_analyzer.update_portfolio_value(portfolio_value, position_values)
            base_value = portfolio_value
        
        # Calculate comprehensive risk metrics
        risk_metrics = self.tail_risk_analyzer.calculate_comprehensive_risk_metrics()
        
        # Display portfolio risk metrics
        if 'portfolio' in risk_metrics:
            portfolio_metrics = risk_metrics['portfolio']
            
            logger.info(f"\nPortfolio Risk Analysis (Value: ${risk_metrics['portfolio_value']:,.0f}):")
            
            # VaR estimates
            if 'var_estimates' in portfolio_metrics:
                logger.info(f"  Value at Risk (VaR):")
                for confidence, estimates in portfolio_metrics['var_estimates'].items():
                    if 'historical' in estimates:
                        var_pct = estimates['historical'] * 100
                        var_dollar = estimates['historical'] * risk_metrics['portfolio_value']
                        logger.info(f"    {confidence} Historical: {var_pct:.2f}% (${var_dollar:,.0f})")
            
            # CVaR estimates
            if 'cvar_estimates' in portfolio_metrics:
                logger.info(f"  Conditional VaR (Expected Shortfall):")
                for confidence, estimates in portfolio_metrics['cvar_estimates'].items():
                    if 'historical' in estimates:
                        cvar_pct = estimates['historical'] * 100
                        cvar_dollar = estimates['historical'] * risk_metrics['portfolio_value']
                        logger.info(f"    {confidence} Historical: {cvar_pct:.2f}% (${cvar_dollar:,.0f})")
            
            # Drawdown analysis
            if 'drawdown_analysis' in portfolio_metrics:
                dd_metrics = portfolio_metrics['drawdown_analysis']
                logger.info(f"  Drawdown Analysis:")
                logger.info(f"    Current Drawdown: {abs(dd_metrics.get('current_drawdown', 0)) * 100:.2f}%")
                logger.info(f"    Max Drawdown: {abs(dd_metrics.get('max_drawdown', 0)) * 100:.2f}%")
                if 'drawdown_probabilities' in dd_metrics:
                    probs = dd_metrics['drawdown_probabilities']
                    logger.info(f"    P(Drawdown > 5%): {probs.get('5%', 0):.1f}%")
                    logger.info(f"    P(Drawdown > 10%): {probs.get('10%', 0):.1f}%")
            
            # Risk-adjusted returns
            if 'risk_adjusted_returns' in portfolio_metrics:
                rar = portfolio_metrics['risk_adjusted_returns']
                logger.info(f"  Risk-Adjusted Returns:")
                logger.info(f"    Sharpe Ratio: {rar.get('sharpe_ratio', 0):.3f}")
                logger.info(f"    Sortino Ratio: {rar.get('sortino_ratio', 0):.3f}")
                logger.info(f"    Calmar Ratio: {rar.get('calmar_ratio', 0):.3f}")
        
        # Display stress test results
        if 'stress_tests' in risk_metrics:
            logger.info(f"\n  Stress Test Results:")
            for scenario, result in risk_metrics['stress_tests'].items():
                if isinstance(result, dict) and 'loss_percentage' in result:
                    logger.info(f"    {scenario}: {result['loss_percentage']:.1f}% loss")
        
        # Display individual asset risk
        if 'individual_assets' in risk_metrics:
            logger.info(f"\nIndividual Asset Risk Summary:")
            for symbol, asset_metrics in risk_metrics['individual_assets'].items():
                if 'var_estimates' in asset_metrics and '95.0%' in asset_metrics['var_estimates']:
                    var_95 = asset_metrics['var_estimates']['95.0%'].get('historical', 0)
                    logger.info(f"  {symbol}: VaR(95%) = {var_95 * 100:.2f}%")
        
        # Risk dashboard summary
        dashboard = self.tail_risk_analyzer.get_risk_dashboard_summary()
        if dashboard.get('status') != 'no_data':
            logger.info(f"\nRisk Dashboard Summary:")
            logger.info(f"  Overall Risk Level: {dashboard.get('risk_level', 'unknown').upper()}")
            logger.info(f"  Active Risk Alerts: {dashboard.get('active_alerts', 0)}")
            
            key_metrics = dashboard.get('key_metrics', {})
            logger.info(f"  Portfolio VaR(95%): ${key_metrics.get('var_95_dollar', 0):,.0f}")
            logger.info(f"  Portfolio CVaR(95%): ${key_metrics.get('cvar_95_dollar', 0):,.0f}")
    
    async def run_comprehensive_demo(self):
        """Run complete demonstration of all analytics features."""
        logger.info("Starting Enhanced Trading Bot Analytics Demonstration")
        logger.info("=" * 60)
        
        try:
            # Demonstrate each analytics component
            await self.demonstrate_spread_monitoring()
            await self.demonstrate_liquidity_prediction()
            self.demonstrate_tail_risk_analysis()
            
            logger.info("\n" + "=" * 60)
            logger.info("Enhanced Analytics Demonstration Complete!")
            logger.info("\nKey Features Demonstrated:")
            logger.info("✓ Live bid-ask spread monitoring with liquidity scoring")
            logger.info("✓ Market liquidity prediction using ML models")
            logger.info("✓ Comprehensive tail risk analysis (VaR, CVaR, drawdowns)")
            logger.info("✓ Stress testing and scenario analysis")
            logger.info("✓ Trading cost estimation and optimal timing")
            logger.info("✓ Risk-adjusted performance metrics")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise


async def main():
    """Main function to run the analytics demonstration."""
    demo = AnalyticsDemo()
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    asyncio.run(main())