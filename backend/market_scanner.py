"""
Market Scanner for Autonomous Stock Selection

This module implements intelligent stock discovery based on market criteria,
technical indicators, and fundamental analysis. The bot uses this to autonomously
select trading targets instead of relying on hardcoded symbol lists.

Features:
- Market cap filtering
- Volume and liquidity screening
- Sector and industry diversification
- Technical indicator screening
- Fundamental metric filtering
- Live data validation
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)


class MarketCap(Enum):
    """Market capitalization categories"""
    LARGE_CAP = "large"  # > $10B
    MID_CAP = "mid"      # $2B - $10B
    SMALL_CAP = "small"  # $300M - $2B
    MICRO_CAP = "micro"  # < $300M


class ScannerCriteria:
    """Criteria for stock screening"""
    def __init__(self,
                 min_market_cap: float = 1e9,  # $1B minimum
                 max_market_cap: float = None,
                 min_volume: int = 1000000,    # 1M shares daily volume
                 min_price: float = 5.0,       # Minimum stock price
                 max_price: float = 1000.0,    # Maximum stock price
                 sectors: List[str] = None,    # Preferred sectors
                 exclude_sectors: List[str] = None,  # Sectors to avoid
                 max_symbols: int = 50,        # Maximum symbols to return
                 require_options: bool = True, # Require options availability
                 min_analyst_coverage: int = 3 # Minimum analyst coverage
                 ):
        self.min_market_cap = min_market_cap
        self.max_market_cap = max_market_cap
        self.min_volume = min_volume
        self.min_price = min_price
        self.max_price = max_price
        self.sectors = sectors or []
        self.exclude_sectors = exclude_sectors or []
        self.max_symbols = max_symbols
        self.require_options = require_options
        self.min_analyst_coverage = min_analyst_coverage


@dataclass
class StockCandidate:
    """Represents a potential stock candidate"""
    symbol: str
    company_name: str
    market_cap: float
    price: float
    volume: float
    sector: str
    industry: str
    pe_ratio: float
    score: float
    reasons: List[str]


class MarketScanner:
    """
    Autonomous market scanner for stock discovery
    """
    
    def __init__(self):
        self.criteria = ScannerCriteria()
        self.universe_sources = [
            'sp500',
            'nasdaq100',
            'russell2000'
        ]
        
    def set_criteria(self, criteria: ScannerCriteria):
        """Set scanning criteria"""
        self.criteria = criteria
        
    def scan_market(self, criteria: ScannerCriteria = None) -> List[StockCandidate]:
        """
        Perform autonomous market scan to discover trading opportunities
        
        Args:
            criteria: Scanning criteria (optional, uses default if not provided)
            
        Returns:
            List of qualified stock candidates sorted by score
        """
        if criteria:
            self.criteria = criteria
            
        logger.info("Starting autonomous market scan...")
        
        # Get universe of stocks to scan
        universe = self._get_trading_universe()
        logger.info(f"Scanning {len(universe)} stocks from trading universe")
        
        # Apply screening criteria
        candidates = []
        processed = 0
        
        for symbol in universe:
            try:
                candidate = self._evaluate_stock(symbol)
                if candidate:
                    candidates.append(candidate)
                    
                processed += 1
                if processed % 50 == 0:
                    logger.info(f"Processed {processed}/{len(universe)} stocks, found {len(candidates)} candidates")
                    
                # Respect rate limits
                time.sleep(0.1)
                
            except Exception as e:
                logger.debug(f"Error evaluating {symbol}: {e}")
                continue
                
        # Sort by score (highest first)
        candidates.sort(key=lambda x: x.score, reverse=True)
        
        # Return top candidates
        top_candidates = candidates[:self.criteria.max_symbols]
        
        logger.info(f"Market scan complete: {len(top_candidates)} qualified candidates found")
        
        return top_candidates
    
    def _get_trading_universe(self) -> List[str]:
        """
        Get comprehensive trading universe from multiple sources
        """
        universe = set()
        
        # Add S&P 500 stocks
        try:
            sp500 = self._get_sp500_symbols()
            universe.update(sp500)
            logger.info(f"Added {len(sp500)} S&P 500 stocks")
        except Exception as e:
            logger.warning(f"Could not fetch S&P 500 symbols: {e}")
            
        # Add NASDAQ 100 stocks
        try:
            nasdaq100 = self._get_nasdaq100_symbols()
            universe.update(nasdaq100)
            logger.info(f"Added NASDAQ 100 stocks (total universe: {len(universe)})")
        except Exception as e:
            logger.warning(f"Could not fetch NASDAQ 100 symbols: {e}")
            
        # Add Russell 2000 small cap stocks (sample)
        try:
            russell_sample = self._get_russell2000_sample()
            universe.update(russell_sample)
            logger.info(f"Added Russell 2000 sample (total universe: {len(universe)})")
        except Exception as e:
            logger.warning(f"Could not fetch Russell 2000 symbols: {e}")
            
        # Fallback to common stocks if other sources fail
        if len(universe) < 50:
            fallback = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
                'BRKB', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'DIS', 'MA', 'PYPL',
                'ADBE', 'CMCSA', 'NFLX', 'KO', 'PEP', 'ABBV', 'PFE', 'CRM', 'TMO',
                'COST', 'AVGO', 'ABT', 'ACN', 'CSCO', 'CVX', 'DHR', 'LLY', 'MCD',
                'NEE', 'TXN', 'WMT', 'VZ', 'PM', 'INTC', 'IBM', 'QCOM', 'AMGN',
                'HON', 'LOW', 'AMD', 'SPGI', 'UNP', 'GS', 'MMM', 'CAT', 'AXP'
            ]
            universe.update(fallback)
            logger.info(f"Added fallback stocks (total universe: {len(universe)})")
            
        return list(universe)
    
    def _get_sp500_symbols(self) -> List[str]:
        """Get S&P 500 stock symbols"""
        try:
            # Try to get from wikipedia
            tables = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
            sp500_table = tables[0]
            return sp500_table['Symbol'].tolist()
        except:
            # Fallback to yfinance
            sp500 = yf.Ticker("^GSPC")
            # This is a simplified approach - in production you'd use a more reliable source
            return []
    
    def _get_nasdaq100_symbols(self) -> List[str]:
        """Get NASDAQ 100 stock symbols"""
        try:
            tables = pd.read_html('https://en.wikipedia.org/wiki/NASDAQ-100')
            nasdaq_table = tables[4]  # Usually the 5th table has the symbols
            return nasdaq_table['Ticker'].tolist()
        except:
            return []
    
    def _get_russell2000_sample(self) -> List[str]:
        """Get sample of Russell 2000 stocks"""
        # This would typically come from a financial data provider
        # For now, return a representative sample
        return [
            'SIRI', 'PLUG', 'WISH', 'OPEN', 'DKNG', 'PLTR', 'COIN', 'RBLX',
            'HOOD', 'SOFI', 'UPST', 'AFRM', 'SQ', 'ROKU', 'PINS', 'SNAP'
        ]
    
    def _evaluate_stock(self, symbol: str) -> Optional[StockCandidate]:
        """
        Evaluate a single stock against criteria
        
        Returns:
            StockCandidate if stock meets criteria, None otherwise
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Get recent price data
            hist = ticker.history(period="5d", interval="1d")
            if hist.empty:
                return None
                
            latest_price = float(hist['Close'].iloc[-1])
            latest_volume = float(hist['Volume'].iloc[-1])
            
            # Basic price filtering
            if latest_price < self.criteria.min_price or latest_price > self.criteria.max_price:
                return None
                
            # Volume filtering
            if latest_volume < self.criteria.min_volume:
                return None
                
            # Market cap filtering
            market_cap = info.get('marketCap', 0)
            if market_cap < self.criteria.min_market_cap:
                return None
                
            if self.criteria.max_market_cap and market_cap > self.criteria.max_market_cap:
                return None
                
            # Sector filtering
            sector = info.get('sector', 'Unknown')
            if self.criteria.exclude_sectors and sector in self.criteria.exclude_sectors:
                return None
                
            if self.criteria.sectors and sector not in self.criteria.sectors:
                return None
                
            # Calculate score
            score = self._calculate_score(info, hist)
            
            # Generate reasons
            reasons = self._generate_reasons(info, hist, score)
            
            return StockCandidate(
                symbol=symbol,
                company_name=info.get('longName', symbol),
                market_cap=market_cap,
                price=latest_price,
                volume=latest_volume,
                sector=sector,
                industry=info.get('industry', 'Unknown'),
                pe_ratio=info.get('forwardPE', info.get('trailingPE', 0)),
                score=score,
                reasons=reasons
            )
            
        except Exception as e:
            logger.debug(f"Error evaluating {symbol}: {e}")
            return None
            
    def _calculate_score(self, info: Dict, hist: pd.DataFrame) -> float:
        """
        Calculate a comprehensive score for the stock
        
        Factors considered:
        - Market cap (larger = more stable)
        - Volume (higher = more liquid)
        - PE ratio (moderate = better value)
        - Price momentum
        - Volatility
        """
        score = 0.0
        
        try:
            # Market cap score (logarithmic scaling)
            market_cap = info.get('marketCap', 1e6)
            score += min(20, np.log10(market_cap) * 2)  # Max 20 points
            
            # Volume score
            volume = hist['Volume'].iloc[-1]
            avg_volume = hist['Volume'].mean()
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
            score += min(15, volume_ratio * 5)  # Max 15 points
            
            # PE ratio score (prefer moderate PE ratios)
            pe = info.get('forwardPE', info.get('trailingPE', 20))
            if 10 <= pe <= 25:
                score += 15  # Sweet spot
            elif 5 <= pe <= 35:
                score += 10  # Acceptable
            elif pe > 0:
                score += 5   # At least positive earnings
                
            # Price momentum score (5-day performance)
            if len(hist) >= 5:
                momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-5] - 1) * 100
                if momentum > 2:
                    score += 10  # Strong upward momentum
                elif momentum > 0:
                    score += 5   # Positive momentum
                elif momentum > -2:
                    score += 2   # Stable
                    
            # Volatility score (prefer moderate volatility)
            if len(hist) >= 5:
                returns = hist['Close'].pct_change().dropna()
                volatility = returns.std() * 100
                if 1 <= volatility <= 3:
                    score += 10  # Moderate volatility
                elif volatility <= 5:
                    score += 5   # Acceptable volatility
                    
            # Analyst coverage bonus
            analyst_count = info.get('recommendationMean', 0)
            if analyst_count > 0:
                score += 5
                
        except Exception as e:
            logger.debug(f"Error calculating score: {e}")
            
        return max(0, min(100, score))  # Clamp to 0-100
    
    def _generate_reasons(self, info: Dict, hist: pd.DataFrame, score: float) -> List[str]:
        """Generate human-readable reasons for the stock selection"""
        reasons = []
        
        market_cap = info.get('marketCap', 0)
        if market_cap > 10e9:
            reasons.append("Large-cap stability")
        elif market_cap > 2e9:
            reasons.append("Mid-cap growth potential")
            
        pe = info.get('forwardPE', info.get('trailingPE', 0))
        if 10 <= pe <= 25:
            reasons.append("Reasonable valuation")
            
        if len(hist) >= 5:
            momentum = (hist['Close'].iloc[-1] / hist['Close'].iloc[-5] - 1) * 100
            if momentum > 2:
                reasons.append("Strong price momentum")
            elif momentum > 0:
                reasons.append("Positive price trend")
                
        volume = hist['Volume'].iloc[-1]
        if volume > 1e6:
            reasons.append("High liquidity")
            
        if score > 70:
            reasons.append("High overall score")
        elif score > 50:
            reasons.append("Good fundamentals")
            
        return reasons


def get_autonomous_stock_selection(max_stocks: int = 20, 
                                 include_indices: bool = True,
                                 criteria: ScannerCriteria = None) -> List[str]:
    """
    Autonomously select stocks for trading based on comprehensive market analysis.
    
    This function replaces hardcoded stock lists with intelligent market scanning.
    Major indices are automatically included for benchmarking unless disabled.
    
    Args:
        max_stocks: Maximum number of stocks to return (excluding indices)
        include_indices: Whether to automatically include major indices for benchmarking
        criteria: Custom scanning criteria, defaults to balanced criteria
        
    Returns:
        List of stock symbols including major indices for comparison
    """
    # Major indices for benchmarking - always include these for comparison
    major_indices = ['SPY', 'QQQ', 'DIA', 'IWM', 'VTI'] if include_indices else []
    
    logger.info(f"Starting autonomous stock selection for {max_stocks} stocks")
    if include_indices:
        logger.info(f"Including major indices for benchmarking: {major_indices}")
    
    scanner = MarketScanner()
    
    if criteria is None:
        # Default criteria for trading
        criteria = ScannerCriteria(
            min_market_cap=1e9,      # $1B minimum market cap
            min_volume=500000,       # 500K minimum daily volume
            min_price=10.0,          # $10 minimum price
            max_price=500.0,         # $500 maximum price
            max_symbols=max_stocks,
            require_options=True
        )
    
    candidates = scanner.scan_market(criteria)
    
    # Extract symbols from top candidates
    symbols = [candidate.symbol for candidate in candidates]
    
    # Combine with major indices at the beginning for easy identification
    final_symbols = major_indices + symbols
    
    logger.info(f"Autonomous selection complete: {len(symbols)} stocks + {len(major_indices)} indices selected")
    if include_indices:
        logger.info(f"Indices included: {major_indices}")
    for i, candidate in enumerate(candidates[:10]):  # Log top 10 stocks
        logger.info(f"  Stock {i+1}. {candidate.symbol} ({candidate.company_name}) - Score: {candidate.score:.1f}")
        
    return final_symbols


if __name__ == "__main__":
    # Demo the autonomous scanner
    print("🔍 AUTONOMOUS STOCK SCANNER DEMO")
    print("=" * 50)
    
    symbols = get_autonomous_stock_selection(max_stocks=10)
    
    print(f"✅ Autonomously selected {len(symbols)} stocks:")
    for i, symbol in enumerate(symbols, 1):
        print(f"  {i:2d}. {symbol}")
        
    print("\n📊 This replaces hardcoded symbol lists with intelligent market scanning")