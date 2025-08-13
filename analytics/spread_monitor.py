"""
Live Bid-Ask Spread Monitor

Real-time monitoring and analysis of bid-ask spreads for market liquidity assessment
and trading cost optimization. Integrates with live market data feeds to provide
continuous spread analytics.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict, deque


class SpreadMonitor:
    """
    Monitors bid-ask spreads in real-time for market liquidity analysis.
    
    Features:
    - Real-time spread calculation and tracking
    - Spread volatility analysis
    - Market impact cost estimation
    - Liquidity score computation
    - Historical spread pattern analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize spread monitor.
        
        Args:
            config: Configuration dictionary containing:
                - symbols: List of symbols to monitor
                - window_size: Rolling window size for calculations
                - alert_thresholds: Spread alert thresholds
                - update_interval: Data update frequency in seconds
        """
        self.config = config
        self.symbols = config.get('symbols', [])
        self.window_size = config.get('window_size', 100)
        self.alert_thresholds = config.get('alert_thresholds', {})
        self.update_interval = config.get('update_interval', 1.0)
        
        # Data storage
        self.spread_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.window_size))
        self.quote_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=self.window_size))
        self.spread_metrics: Dict[str, Dict[str, float]] = {}
        
        # Monitoring state
        self.is_monitoring = False
        self.last_update = {}
        self.alerts = []
        
        self.logger = logging.getLogger(__name__)
        
    async def start_monitoring(self, market_data_manager) -> None:
        """
        Start real-time spread monitoring.
        
        Args:
            market_data_manager: Market data manager instance for live data
        """
        self.is_monitoring = True
        self.market_data_manager = market_data_manager
        self.logger.info(f"Starting spread monitoring for {len(self.symbols)} symbols")
        
        while self.is_monitoring:
            try:
                await self._update_spreads()
                await asyncio.sleep(self.update_interval)
            except Exception as e:
                self.logger.error(f"Error in spread monitoring: {e}")
                await asyncio.sleep(self.update_interval)
    
    def stop_monitoring(self) -> None:
        """Stop spread monitoring."""
        self.is_monitoring = False
        self.logger.info("Spread monitoring stopped")
    
    async def _update_spreads(self) -> None:
        """Update spread data for all monitored symbols."""
        # Fetch latest quotes for all symbols
        quotes = await self._fetch_live_quotes()
        
        for symbol, quote_data in quotes.items():
            if quote_data and self._is_valid_quote(quote_data):
                self._process_quote(symbol, quote_data)
                self._update_spread_metrics(symbol)
                self._check_alerts(symbol)
    
    async def _fetch_live_quotes(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """Fetch live quotes with bid/ask data."""
        if not hasattr(self, 'market_data_manager'):
            return {}
        
        # Fetch quotes from market data manager
        quotes = await self.market_data_manager.fetch_quotes(self.symbols)
        
        # Enhance quotes with bid/ask data if not available
        enhanced_quotes = {}
        for symbol, quote in quotes.items():
            if quote:
                enhanced_quote = await self._enhance_quote_with_spread_data(symbol, quote)
                enhanced_quotes[symbol] = enhanced_quote
            else:
                enhanced_quotes[symbol] = None
        
        return enhanced_quotes
    
    async def _enhance_quote_with_spread_data(self, symbol: str, quote: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance quote data with bid/ask information.
        
        For live trading, this would connect to real bid/ask feeds.
        For demonstration, we'll simulate realistic bid/ask spreads.
        """
        if 'bid' in quote and 'ask' in quote:
            return quote
        
        # Simulate realistic bid/ask spreads based on market conditions
        price = quote.get('price', quote.get('regularMarketPrice', 100.0))
        
        # Estimate spread based on price and volatility
        base_spread_pct = self._estimate_spread_percentage(symbol, price, quote)
        spread_amount = price * base_spread_pct / 100
        
        quote['bid'] = price - spread_amount / 2
        quote['ask'] = price + spread_amount / 2
        quote['spread'] = quote['ask'] - quote['bid']  # Ensure consistency
        quote['spread_pct'] = base_spread_pct
        quote['timestamp'] = time.time()
        
        return quote
    
    def _estimate_spread_percentage(self, symbol: str, price: float, quote: Dict[str, Any]) -> float:
        """
        Estimate realistic bid-ask spread percentage based on market conditions.
        
        This uses market microstructure principles to estimate spreads.
        In live trading, this would be replaced with actual bid/ask data.
        """
        # Base spread by price range (smaller spreads for higher-priced stocks)
        if price > 100:
            base_spread = 0.02  # 2 basis points for large caps
        elif price > 50:
            base_spread = 0.04  # 4 basis points for mid caps
        elif price > 10:
            base_spread = 0.08  # 8 basis points for small caps
        else:
            base_spread = 0.15  # 15 basis points for penny stocks
        
        # Adjust for volatility
        volatility = quote.get('regularMarketDayHigh', price) - quote.get('regularMarketDayLow', price)
        if volatility > 0 and price > 0:
            volatility_pct = (volatility / price) * 100
            volatility_adjustment = min(volatility_pct * 0.1, 0.1)  # Max 10bp adjustment
        else:
            volatility_adjustment = 0
        
        # Adjust for volume (lower volume = wider spreads)
        volume = quote.get('regularMarketVolume', 1000000)
        if volume < 100000:
            volume_adjustment = 0.05  # 5bp for low volume
        elif volume < 500000:
            volume_adjustment = 0.02  # 2bp for medium volume
        else:
            volume_adjustment = 0  # No adjustment for high volume
        
        total_spread = base_spread + volatility_adjustment + volume_adjustment
        return min(total_spread, 0.5)  # Cap at 50bp
    
    def _is_valid_quote(self, quote: Dict[str, Any]) -> bool:
        """Check if quote has valid bid/ask data."""
        required_fields = ['bid', 'ask', 'price']
        return all(field in quote and quote[field] is not None for field in required_fields)
    
    def _process_quote(self, symbol: str, quote: Dict[str, Any]) -> None:
        """Process new quote and update spread history."""
        timestamp = quote.get('timestamp', time.time())
        
        spread_data = {
            'timestamp': timestamp,
            'bid': quote['bid'],
            'ask': quote['ask'],
            'price': quote['price'],
            'spread': quote['ask'] - quote['bid'],
            'spread_pct': ((quote['ask'] - quote['bid']) / quote['price']) * 100,
            'mid_price': (quote['bid'] + quote['ask']) / 2
        }
        
        self.spread_history[symbol].append(spread_data)
        self.quote_history[symbol].append(quote)
        self.last_update[symbol] = timestamp
    
    def _update_spread_metrics(self, symbol: str) -> None:
        """Update calculated metrics for symbol."""
        if len(self.spread_history[symbol]) < 2:
            return
        
        spreads = [s['spread'] for s in self.spread_history[symbol]]
        spread_pcts = [s['spread_pct'] for s in self.spread_history[symbol]]
        prices = [s['price'] for s in self.spread_history[symbol]]
        
        metrics = {
            'current_spread': spreads[-1],
            'current_spread_pct': spread_pcts[-1],
            'avg_spread': np.mean(spreads),
            'avg_spread_pct': np.mean(spread_pcts),
            'spread_volatility': np.std(spread_pcts),
            'min_spread': min(spreads),
            'max_spread': max(spreads),
            'spread_trend': self._calculate_spread_trend(spread_pcts),
            'liquidity_score': self._calculate_liquidity_score(symbol),
            'market_impact_cost': self._estimate_market_impact_cost(symbol),
            'last_update': self.last_update[symbol]
        }
        
        self.spread_metrics[symbol] = metrics
    
    def _calculate_spread_trend(self, spread_pcts: List[float]) -> str:
        """Calculate spread trend direction."""
        if len(spread_pcts) < 10:
            return 'insufficient_data'
        
        recent = np.mean(spread_pcts[-5:])
        earlier = np.mean(spread_pcts[-10:-5])
        
        if recent > earlier * 1.1:
            return 'widening'
        elif recent < earlier * 0.9:
            return 'tightening'
        else:
            return 'stable'
    
    def _calculate_liquidity_score(self, symbol: str) -> float:
        """
        Calculate liquidity score (0-100) based on spread characteristics.
        
        Higher scores indicate better liquidity (tighter spreads).
        """
        if len(self.spread_history[symbol]) < 5:
            return 50.0  # Neutral score for insufficient data
        
        spreads = [s['spread_pct'] for s in self.spread_history[symbol]]
        avg_spread = np.mean(spreads)
        spread_volatility = np.std(spreads)
        
        # Score based on spread tightness (lower spreads = higher score)
        spread_score = max(0, 100 - (avg_spread * 100))
        
        # Penalty for high spread volatility
        volatility_penalty = min(spread_volatility * 50, 30)
        
        liquidity_score = max(0, min(100, spread_score - volatility_penalty))
        return liquidity_score
    
    def _estimate_market_impact_cost(self, symbol: str) -> float:
        """
        Estimate market impact cost for typical trade sizes.
        
        Returns estimated cost in basis points for a $10,000 trade.
        """
        if len(self.spread_history[symbol]) < 5:
            return 0.0
        
        current_spread_pct = self.spread_metrics.get(symbol, {}).get('current_spread_pct', 0)
        spread_volatility = self.spread_metrics.get(symbol, {}).get('spread_volatility', 0)
        
        # Base impact is half the spread
        base_impact = current_spread_pct / 2
        
        # Additional impact from volatility and market conditions
        volatility_impact = spread_volatility * 0.5
        
        total_impact = base_impact + volatility_impact
        return min(total_impact, 50)  # Cap at 50bp
    
    def _check_alerts(self, symbol: str) -> None:
        """Check for spread alerts and notifications."""
        if symbol not in self.spread_metrics:
            return
        
        metrics = self.spread_metrics[symbol]
        thresholds = self.alert_thresholds.get(symbol, self.alert_thresholds.get('default', {}))
        
        # Check spread width alerts
        if 'max_spread_pct' in thresholds:
            if metrics['current_spread_pct'] > thresholds['max_spread_pct']:
                self._add_alert(symbol, 'wide_spread', 
                              f"Spread {metrics['current_spread_pct']:.3f}% exceeds threshold {thresholds['max_spread_pct']:.3f}%")
        
        # Check liquidity score alerts
        if 'min_liquidity_score' in thresholds:
            if metrics['liquidity_score'] < thresholds['min_liquidity_score']:
                self._add_alert(symbol, 'low_liquidity',
                              f"Liquidity score {metrics['liquidity_score']:.1f} below threshold {thresholds['min_liquidity_score']}")
    
    def _add_alert(self, symbol: str, alert_type: str, message: str) -> None:
        """Add alert to alert queue."""
        alert = {
            'symbol': symbol,
            'type': alert_type,
            'message': message,
            'timestamp': datetime.now(),
            'severity': 'warning'
        }
        
        self.alerts.append(alert)
        self.logger.warning(f"Spread Alert [{symbol}]: {message}")
        
        # Keep only recent alerts
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.alerts = [a for a in self.alerts if a['timestamp'] > cutoff_time]
    
    def get_current_spreads(self) -> Dict[str, Dict[str, Any]]:
        """Get current spread metrics for all symbols."""
        return dict(self.spread_metrics)
    
    def get_spread_history(self, symbol: str, periods: int = None) -> pd.DataFrame:
        """
        Get historical spread data for a symbol.
        
        Args:
            symbol: Symbol to get history for
            periods: Number of recent periods (None for all available)
            
        Returns:
            DataFrame with spread history
        """
        if symbol not in self.spread_history:
            return pd.DataFrame()
        
        history = list(self.spread_history[symbol])
        if periods:
            history = history[-periods:]
        
        return pd.DataFrame(history)
    
    def get_liquidity_summary(self) -> Dict[str, Any]:
        """Get summary of current market liquidity conditions."""
        if not self.spread_metrics:
            return {'status': 'no_data'}
        
        liquidity_scores = [m['liquidity_score'] for m in self.spread_metrics.values()]
        spread_pcts = [m['current_spread_pct'] for m in self.spread_metrics.values()]
        
        summary = {
            'timestamp': datetime.now(),
            'symbols_monitored': len(self.spread_metrics),
            'avg_liquidity_score': np.mean(liquidity_scores),
            'avg_spread_pct': np.mean(spread_pcts),
            'min_liquidity_score': min(liquidity_scores),
            'max_spread_pct': max(spread_pcts),
            'active_alerts': len(self.alerts),
            'market_condition': self._assess_market_condition()
        }
        
        return summary
    
    def _assess_market_condition(self) -> str:
        """Assess overall market liquidity condition."""
        if not self.spread_metrics:
            return 'unknown'
        
        avg_liquidity = np.mean([m['liquidity_score'] for m in self.spread_metrics.values()])
        
        if avg_liquidity >= 80:
            return 'excellent'
        elif avg_liquidity >= 60:
            return 'good'
        elif avg_liquidity >= 40:
            return 'fair'
        elif avg_liquidity >= 20:
            return 'poor'
        else:
            return 'very_poor'
    
    def get_recent_alerts(self, hours: int = 1) -> List[Dict[str, Any]]:
        """Get recent alerts within specified time window."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alerts if a['timestamp'] > cutoff_time]
    
    def calculate_trading_cost_estimate(self, symbol: str, trade_size: float) -> Dict[str, float]:
        """
        Calculate estimated trading costs for a given trade size.
        
        Args:
            symbol: Symbol to trade
            trade_size: Trade size in dollars
            
        Returns:
            Dictionary with cost estimates
        """
        if symbol not in self.spread_metrics:
            return {'error': 'No data available for symbol'}
        
        metrics = self.spread_metrics[symbol]
        
        # Base spread cost (half spread for market orders)
        spread_cost_bp = metrics['current_spread_pct'] * 100 / 2
        spread_cost_dollar = trade_size * spread_cost_bp / 10000
        
        # Market impact cost
        impact_cost_bp = metrics['market_impact_cost']
        impact_cost_dollar = trade_size * impact_cost_bp / 10000
        
        # Total estimated cost
        total_cost_bp = spread_cost_bp + impact_cost_bp
        total_cost_dollar = spread_cost_dollar + impact_cost_dollar
        
        return {
            'trade_size': trade_size,
            'spread_cost_bp': spread_cost_bp,
            'spread_cost_dollar': spread_cost_dollar,
            'impact_cost_bp': impact_cost_bp,
            'impact_cost_dollar': impact_cost_dollar,
            'total_cost_bp': total_cost_bp,
            'total_cost_dollar': total_cost_dollar,
            'liquidity_score': metrics['liquidity_score']
        }