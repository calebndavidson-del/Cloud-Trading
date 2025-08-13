"""
Comprehensive Decision Engine for Trading Bot

This module implements a sophisticated decision-making system that aggregates
multiple data sources including technical indicators, candlestick patterns,
fundamental analysis, sentiment analysis, and news sentiment to make 
informed trading decisions.

Features:
- Candlestick pattern recognition
- Technical indicator analysis  
- Fundamental data analysis
- News sentiment analysis
- Social media sentiment analysis
- Multi-factor decision aggregation
- Transparent decision logging
- Risk-adjusted recommendations
"""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class Signal(Enum):
    """Trading signals enum"""
    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY" 
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class CandlestickPattern(Enum):
    """Candlestick pattern types"""
    DOJI = "DOJI"
    HAMMER = "HAMMER"
    HANGING_MAN = "HANGING_MAN"
    BULLISH_ENGULFING = "BULLISH_ENGULFING"
    BEARISH_ENGULFING = "BEARISH_ENGULFING"
    MORNING_STAR = "MORNING_STAR"
    EVENING_STAR = "EVENING_STAR"
    SHOOTING_STAR = "SHOOTING_STAR"
    INVERTED_HAMMER = "INVERTED_HAMMER"
    DARK_CLOUD_COVER = "DARK_CLOUD_COVER"
    PIERCING_PATTERN = "PIERCING_PATTERN"


@dataclass
class DecisionFactor:
    """Represents a single decision factor"""
    name: str
    signal: Signal
    confidence: float  # 0.0 to 1.0
    weight: float      # Factor weight in final decision
    reasoning: str     # Human-readable explanation
    data_source: str   # Source of the data
    timestamp: datetime


@dataclass  
class TradingDecision:
    """Complete trading decision with all factors"""
    symbol: str
    overall_signal: Signal
    confidence: float
    factors: List[DecisionFactor]
    risk_score: float  # 0.0 to 1.0, higher = riskier
    position_size: float  # Recommended position size (0.0 to 1.0 of portfolio)
    timestamp: datetime
    reasoning: str


class CandlestickAnalyzer:
    """Analyzes candlestick patterns from OHLCV data"""
    
    def __init__(self):
        self.patterns = {
            CandlestickPattern.DOJI: self._detect_doji,
            CandlestickPattern.HAMMER: self._detect_hammer,
            CandlestickPattern.HANGING_MAN: self._detect_hanging_man,
            CandlestickPattern.BULLISH_ENGULFING: self._detect_bullish_engulfing,
            CandlestickPattern.BEARISH_ENGULFING: self._detect_bearish_engulfing,
            CandlestickPattern.MORNING_STAR: self._detect_morning_star,
            CandlestickPattern.EVENING_STAR: self._detect_evening_star,
            CandlestickPattern.SHOOTING_STAR: self._detect_shooting_star,
            CandlestickPattern.INVERTED_HAMMER: self._detect_inverted_hammer,
            CandlestickPattern.DARK_CLOUD_COVER: self._detect_dark_cloud_cover,
            CandlestickPattern.PIERCING_PATTERN: self._detect_piercing_pattern,
        }
    
    def analyze_patterns(self, ohlcv_data: pd.DataFrame) -> List[Tuple[CandlestickPattern, float, str]]:
        """
        Analyze candlestick patterns in OHLCV data
        
        Args:
            ohlcv_data: DataFrame with columns [Open, High, Low, Close, Volume]
            
        Returns:
            List of (pattern, confidence, reasoning) tuples
        """
        detected_patterns = []
        
        for pattern, detector in self.patterns.items():
            try:
                confidence, reasoning = detector(ohlcv_data)
                if confidence > 0.3:  # Only include patterns with reasonable confidence
                    detected_patterns.append((pattern, confidence, reasoning))
            except Exception as e:
                logger.warning(f"Error detecting pattern {pattern}: {e}")
        
        return detected_patterns
    
    def _detect_doji(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Doji pattern - indecision signal"""
        if len(data) < 1:
            return 0.0, "Insufficient data"
        
        last = data.iloc[-1]
        body_size = abs(last['Close'] - last['Open'])
        candle_range = last['High'] - last['Low']
        
        if candle_range == 0:
            return 0.0, "No price movement"
        
        body_ratio = body_size / candle_range
        
        if body_ratio <= 0.1:  # Very small body relative to range
            confidence = 1.0 - (body_ratio / 0.1)
            return confidence, f"Doji detected - body ratio: {body_ratio:.3f}, indicates indecision"
        
        return 0.0, "No Doji pattern detected"
    
    def _detect_hammer(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Hammer pattern - bullish reversal at bottom"""
        if len(data) < 1:
            return 0.0, "Insufficient data"
        
        last = data.iloc[-1]
        open_price, high, low, close = last['Open'], last['High'], last['Low'], last['Close']
        
        body_size = abs(close - open_price)
        lower_shadow = min(open_price, close) - low
        upper_shadow = high - max(open_price, close)
        total_range = high - low
        
        if total_range == 0:
            return 0.0, "No price movement"
        
        # Hammer criteria: small body, long lower shadow, minimal upper shadow
        body_ratio = body_size / total_range
        lower_ratio = lower_shadow / total_range
        upper_ratio = upper_shadow / total_range
        
        if (body_ratio <= 0.3 and lower_ratio >= 0.6 and upper_ratio <= 0.1):
            confidence = min(lower_ratio, 1.0 - body_ratio)
            return confidence, f"Hammer pattern - long lower shadow ({lower_ratio:.2f}), small body ({body_ratio:.2f})"
        
        return 0.0, "No Hammer pattern detected"
    
    def _detect_hanging_man(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Hanging Man pattern - bearish reversal at top"""
        # Same structure as hammer but appears at top of uptrend
        hammer_confidence, hammer_reasoning = self._detect_hammer(data)
        
        if hammer_confidence > 0:
            # Check if we're in an uptrend (simplified check)
            if len(data) >= 5:
                recent_trend = data['Close'].iloc[-5:].pct_change().mean()
                if recent_trend > 0.01:  # Upward trend
                    return hammer_confidence, hammer_reasoning.replace("Hammer", "Hanging Man")
        
        return 0.0, "No Hanging Man pattern detected"
    
    def _detect_bullish_engulfing(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Bullish Engulfing pattern - two candle bullish reversal"""
        if len(data) < 2:
            return 0.0, "Insufficient data for two-candle pattern"
        
        prev = data.iloc[-2]
        curr = data.iloc[-1]
        
        # Previous candle should be bearish (red)
        prev_bearish = prev['Close'] < prev['Open']
        # Current candle should be bullish (green) 
        curr_bullish = curr['Close'] > curr['Open']
        
        if prev_bearish and curr_bullish:
            # Current candle should engulf previous candle
            engulfs = (curr['Open'] < prev['Close'] and curr['Close'] > prev['Open'])
            
            if engulfs:
                # Calculate confidence based on how much it engulfs
                prev_body = abs(prev['Close'] - prev['Open'])
                curr_body = abs(curr['Close'] - curr['Open'])
                engulf_ratio = curr_body / prev_body if prev_body > 0 else 1.0
                
                confidence = min(engulf_ratio / 2.0, 1.0)  # Max confidence when 2x engulfing
                return confidence, f"Bullish Engulfing - current body {engulf_ratio:.2f}x previous body"
        
        return 0.0, "No Bullish Engulfing pattern detected"
    
    def _detect_bearish_engulfing(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Bearish Engulfing pattern - two candle bearish reversal"""
        if len(data) < 2:
            return 0.0, "Insufficient data for two-candle pattern"
        
        prev = data.iloc[-2]
        curr = data.iloc[-1]
        
        # Previous candle should be bullish (green)
        prev_bullish = prev['Close'] > prev['Open']
        # Current candle should be bearish (red)
        curr_bearish = curr['Close'] < curr['Open']
        
        if prev_bullish and curr_bearish:
            # Current candle should engulf previous candle
            engulfs = (curr['Open'] > prev['Close'] and curr['Close'] < prev['Open'])
            
            if engulfs:
                prev_body = abs(prev['Close'] - prev['Open'])
                curr_body = abs(curr['Close'] - curr['Open'])
                engulf_ratio = curr_body / prev_body if prev_body > 0 else 1.0
                
                confidence = min(engulf_ratio / 2.0, 1.0)
                return confidence, f"Bearish Engulfing - current body {engulf_ratio:.2f}x previous body"
        
        return 0.0, "No Bearish Engulfing pattern detected"
    
    def _detect_morning_star(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Morning Star pattern - three candle bullish reversal"""
        if len(data) < 3:
            return 0.0, "Insufficient data for three-candle pattern"
        
        first = data.iloc[-3]
        middle = data.iloc[-2]
        last = data.iloc[-1]
        
        # First candle: bearish (red)
        first_bearish = first['Close'] < first['Open']
        # Middle candle: small body (star)
        middle_body = abs(middle['Close'] - middle['Open'])
        middle_range = middle['High'] - middle['Low']
        middle_small = middle_body / middle_range <= 0.3 if middle_range > 0 else False
        # Last candle: bullish (green)
        last_bullish = last['Close'] > last['Open']
        
        if first_bearish and middle_small and last_bullish:
            # Middle should gap down from first, last should close into first's body
            gap_down = middle['High'] < first['Close']
            closes_into_body = last['Close'] > (first['Open'] + first['Close']) / 2
            
            if gap_down and closes_into_body:
                # Calculate confidence
                first_body = abs(first['Close'] - first['Open'])
                last_body = abs(last['Close'] - last['Open'])
                recovery_ratio = last_body / first_body if first_body > 0 else 1.0
                
                confidence = min(recovery_ratio, 1.0)
                return confidence, f"Morning Star - recovery ratio {recovery_ratio:.2f}"
        
        return 0.0, "No Morning Star pattern detected"
    
    def _detect_evening_star(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Evening Star pattern - three candle bearish reversal"""
        if len(data) < 3:
            return 0.0, "Insufficient data for three-candle pattern"
        
        first = data.iloc[-3]
        middle = data.iloc[-2]
        last = data.iloc[-1]
        
        # First candle: bullish (green)
        first_bullish = first['Close'] > first['Open']
        # Middle candle: small body (star)
        middle_body = abs(middle['Close'] - middle['Open'])
        middle_range = middle['High'] - middle['Low']
        middle_small = middle_body / middle_range <= 0.3 if middle_range > 0 else False
        # Last candle: bearish (red)
        last_bearish = last['Close'] < last['Open']
        
        if first_bullish and middle_small and last_bearish:
            # Middle should gap up from first, last should close into first's body
            gap_up = middle['Low'] > first['Close']
            closes_into_body = last['Close'] < (first['Open'] + first['Close']) / 2
            
            if gap_up and closes_into_body:
                first_body = abs(first['Close'] - first['Open'])
                last_body = abs(last['Close'] - last['Open'])
                decline_ratio = last_body / first_body if first_body > 0 else 1.0
                
                confidence = min(decline_ratio, 1.0)
                return confidence, f"Evening Star - decline ratio {decline_ratio:.2f}"
        
        return 0.0, "No Evening Star pattern detected"
    
    def _detect_shooting_star(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Shooting Star pattern - bearish reversal at top"""
        if len(data) < 1:
            return 0.0, "Insufficient data"
        
        last = data.iloc[-1]
        open_price, high, low, close = last['Open'], last['High'], last['Low'], last['Close']
        
        body_size = abs(close - open_price)
        upper_shadow = high - max(open_price, close)
        lower_shadow = min(open_price, close) - low
        total_range = high - low
        
        if total_range == 0:
            return 0.0, "No price movement"
        
        # Shooting star criteria: small body, long upper shadow, minimal lower shadow
        body_ratio = body_size / total_range
        upper_ratio = upper_shadow / total_range
        lower_ratio = lower_shadow / total_range
        
        if (body_ratio <= 0.3 and upper_ratio >= 0.6 and lower_ratio <= 0.1):
            confidence = min(upper_ratio, 1.0 - body_ratio)
            return confidence, f"Shooting Star - long upper shadow ({upper_ratio:.2f}), small body ({body_ratio:.2f})"
        
        return 0.0, "No Shooting Star pattern detected"
    
    def _detect_inverted_hammer(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Inverted Hammer pattern - bullish reversal at bottom"""
        # Same structure as shooting star but appears at bottom of downtrend
        shooting_star_confidence, shooting_star_reasoning = self._detect_shooting_star(data)
        
        if shooting_star_confidence > 0:
            # Check if we're in a downtrend (simplified check)
            if len(data) >= 5:
                recent_trend = data['Close'].iloc[-5:].pct_change().mean()
                if recent_trend < -0.01:  # Downward trend
                    return shooting_star_confidence, shooting_star_reasoning.replace("Shooting Star", "Inverted Hammer")
        
        return 0.0, "No Inverted Hammer pattern detected"
    
    def _detect_dark_cloud_cover(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Dark Cloud Cover pattern - bearish reversal"""
        if len(data) < 2:
            return 0.0, "Insufficient data for two-candle pattern"
        
        prev = data.iloc[-2]
        curr = data.iloc[-1]
        
        # Previous candle: bullish (green)
        prev_bullish = prev['Close'] > prev['Open']
        # Current candle: bearish (red)
        curr_bearish = curr['Close'] < curr['Open']
        
        if prev_bullish and curr_bearish:
            # Current opens above previous high, closes below previous midpoint
            opens_above = curr['Open'] > prev['High']
            prev_midpoint = (prev['Open'] + prev['Close']) / 2
            closes_below_mid = curr['Close'] < prev_midpoint
            
            if opens_above and closes_below_mid:
                # Calculate penetration depth
                penetration = (prev_midpoint - curr['Close']) / (prev['Close'] - prev['Open'])
                confidence = min(penetration, 1.0)
                return confidence, f"Dark Cloud Cover - penetration {penetration:.2f}"
        
        return 0.0, "No Dark Cloud Cover pattern detected"
    
    def _detect_piercing_pattern(self, data: pd.DataFrame) -> Tuple[float, str]:
        """Detect Piercing Pattern - bullish reversal"""
        if len(data) < 2:
            return 0.0, "Insufficient data for two-candle pattern"
        
        prev = data.iloc[-2]
        curr = data.iloc[-1]
        
        # Previous candle: bearish (red)
        prev_bearish = prev['Close'] < prev['Open']
        # Current candle: bullish (green)
        curr_bullish = curr['Close'] > curr['Open']
        
        if prev_bearish and curr_bullish:
            # Current opens below previous low, closes above previous midpoint
            opens_below = curr['Open'] < prev['Low']
            prev_midpoint = (prev['Open'] + prev['Close']) / 2
            closes_above_mid = curr['Close'] > prev_midpoint
            
            if opens_below and closes_above_mid:
                # Calculate penetration depth
                penetration = (curr['Close'] - prev_midpoint) / (prev['Open'] - prev['Close'])
                confidence = min(penetration, 1.0)
                return confidence, f"Piercing Pattern - penetration {penetration:.2f}"
        
        return 0.0, "No Piercing Pattern pattern detected"


class TechnicalAnalyzer:
    """Analyzes technical indicators"""
    
    def __init__(self):
        pass
    
    def analyze_technical_indicators(self, price_data: pd.DataFrame) -> List[DecisionFactor]:
        """
        Analyze technical indicators and return decision factors
        
        Args:
            price_data: DataFrame with OHLCV data
            
        Returns:
            List of technical analysis decision factors
        """
        factors = []
        
        try:
            # RSI Analysis
            rsi_factor = self._analyze_rsi(price_data)
            if rsi_factor:
                factors.append(rsi_factor)
            
            # Moving Average Analysis
            ma_factor = self._analyze_moving_averages(price_data)
            if ma_factor:
                factors.append(ma_factor)
            
            # MACD Analysis
            macd_factor = self._analyze_macd(price_data)
            if macd_factor:
                factors.append(macd_factor)
            
            # Volume Analysis
            volume_factor = self._analyze_volume(price_data)
            if volume_factor:
                factors.append(volume_factor)
                
        except Exception as e:
            logger.error(f"Error in technical analysis: {e}")
        
        return factors
    
    def _analyze_rsi(self, data: pd.DataFrame) -> Optional[DecisionFactor]:
        """Analyze RSI indicator"""
        if len(data) < 14:
            return None
        
        try:
            # Calculate RSI
            closes = data['Close'].astype(float)
            delta = closes.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]
            
            # Determine signal based on RSI value
            if current_rsi > 70:
                signal = Signal.SELL
                confidence = min((current_rsi - 70) / 20, 1.0)
                reasoning = f"RSI overbought at {current_rsi:.1f}"
            elif current_rsi < 30:
                signal = Signal.BUY
                confidence = min((30 - current_rsi) / 20, 1.0)
                reasoning = f"RSI oversold at {current_rsi:.1f}"
            else:
                signal = Signal.HOLD
                confidence = 1.0 - abs(current_rsi - 50) / 20
                reasoning = f"RSI neutral at {current_rsi:.1f}"
            
            return DecisionFactor(
                name="RSI_Analysis",
                signal=signal,
                confidence=confidence,
                weight=0.15,
                reasoning=reasoning,
                data_source="Technical_Indicators",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating RSI: {e}")
            return None
    
    def _analyze_moving_averages(self, data: pd.DataFrame) -> Optional[DecisionFactor]:
        """Analyze moving average crossovers"""
        if len(data) < 50:
            return None
        
        try:
            closes = data['Close'].astype(float)
            ma_20 = closes.rolling(window=20).mean()
            ma_50 = closes.rolling(window=50).mean()
            
            current_price = closes.iloc[-1]
            current_ma20 = ma_20.iloc[-1]
            current_ma50 = ma_50.iloc[-1]
            
            # Determine signal based on price relative to MAs and MA crossover
            if current_price > current_ma20 > current_ma50:
                signal = Signal.BUY
                confidence = 0.8
                reasoning = f"Price above both MAs, bullish trend"
            elif current_price < current_ma20 < current_ma50:
                signal = Signal.SELL
                confidence = 0.8
                reasoning = f"Price below both MAs, bearish trend"
            elif ma_20.iloc[-1] > ma_20.iloc[-2] and ma_20.iloc[-2] <= ma_50.iloc[-2] and ma_20.iloc[-1] > ma_50.iloc[-1]:
                signal = Signal.BUY
                confidence = 0.9
                reasoning = f"Golden cross - MA20 crossing above MA50"
            elif ma_20.iloc[-1] < ma_20.iloc[-2] and ma_20.iloc[-2] >= ma_50.iloc[-2] and ma_20.iloc[-1] < ma_50.iloc[-1]:
                signal = Signal.SELL
                confidence = 0.9
                reasoning = f"Death cross - MA20 crossing below MA50"
            else:
                signal = Signal.HOLD
                confidence = 0.5
                reasoning = f"Mixed MA signals"
            
            return DecisionFactor(
                name="Moving_Average_Analysis",
                signal=signal,
                confidence=confidence,
                weight=0.20,
                reasoning=reasoning,
                data_source="Technical_Indicators",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating moving averages: {e}")
            return None
    
    def _analyze_macd(self, data: pd.DataFrame) -> Optional[DecisionFactor]:
        """Analyze MACD indicator"""
        if len(data) < 26:
            return None
        
        try:
            closes = data['Close'].astype(float)
            ema_12 = closes.ewm(span=12).mean()
            ema_26 = closes.ewm(span=26).mean()
            macd_line = ema_12 - ema_26
            signal_line = macd_line.ewm(span=9).mean()
            histogram = macd_line - signal_line
            
            current_macd = macd_line.iloc[-1]
            current_signal = signal_line.iloc[-1]
            current_histogram = histogram.iloc[-1]
            prev_histogram = histogram.iloc[-2] if len(histogram) > 1 else 0
            
            # Analyze MACD signals
            if current_macd > current_signal and prev_histogram <= 0 and current_histogram > 0:
                signal = Signal.BUY
                confidence = 0.8
                reasoning = f"MACD bullish crossover"
            elif current_macd < current_signal and prev_histogram >= 0 and current_histogram < 0:
                signal = Signal.SELL
                confidence = 0.8
                reasoning = f"MACD bearish crossover"
            elif current_histogram > 0:
                signal = Signal.BUY
                confidence = 0.6
                reasoning = f"MACD above signal line"
            elif current_histogram < 0:
                signal = Signal.SELL
                confidence = 0.6
                reasoning = f"MACD below signal line"
            else:
                signal = Signal.HOLD
                confidence = 0.5
                reasoning = f"MACD neutral"
            
            return DecisionFactor(
                name="MACD_Analysis",
                signal=signal,
                confidence=confidence,
                weight=0.15,
                reasoning=reasoning,
                data_source="Technical_Indicators",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error calculating MACD: {e}")
            return None
    
    def _analyze_volume(self, data: pd.DataFrame) -> Optional[DecisionFactor]:
        """Analyze volume patterns"""
        if len(data) < 20:
            return None
        
        try:
            volumes = data['Volume'].astype(float)
            prices = data['Close'].astype(float)
            
            avg_volume = volumes.rolling(window=20).mean().iloc[-1]
            current_volume = volumes.iloc[-1]
            volume_ratio = current_volume / avg_volume
            
            price_change = (prices.iloc[-1] - prices.iloc[-2]) / prices.iloc[-2]
            
            # Analyze volume confirmation
            if volume_ratio > 1.5 and price_change > 0.02:
                signal = Signal.BUY
                confidence = min(volume_ratio / 3.0, 1.0)
                reasoning = f"High volume ({volume_ratio:.1f}x avg) with price increase"
            elif volume_ratio > 1.5 and price_change < -0.02:
                signal = Signal.SELL
                confidence = min(volume_ratio / 3.0, 1.0)
                reasoning = f"High volume ({volume_ratio:.1f}x avg) with price decrease"
            elif volume_ratio < 0.5:
                signal = Signal.HOLD
                confidence = 0.3
                reasoning = f"Low volume ({volume_ratio:.1f}x avg), lack of conviction"
            else:
                signal = Signal.HOLD
                confidence = 0.5
                reasoning = f"Normal volume ({volume_ratio:.1f}x avg)"
            
            return DecisionFactor(
                name="Volume_Analysis",
                signal=signal,
                confidence=confidence,
                weight=0.10,
                reasoning=reasoning,
                data_source="Technical_Indicators",
                timestamp=datetime.now()
            )
            
        except Exception as e:
            logger.error(f"Error analyzing volume: {e}")
            return None


class DecisionEngine:
    """
    Main decision engine that aggregates all analysis components
    """
    
    def __init__(self):
        self.candlestick_analyzer = CandlestickAnalyzer()
        self.technical_analyzer = TechnicalAnalyzer()
        
        # Default weights for different analysis types
        self.analysis_weights = {
            'technical': 0.3,
            'candlestick': 0.2,
            'fundamental': 0.2,
            'sentiment': 0.15,
            'news': 0.15
        }
    
    def make_decision(self, symbol: str, market_data: Dict[str, Any], 
                     historical_data: pd.DataFrame, 
                     fundamental_data: Optional[Dict] = None,
                     news_sentiment: Optional[Dict] = None,
                     social_sentiment: Optional[Dict] = None) -> TradingDecision:
        """
        Make a comprehensive trading decision based on all available data
        
        Args:
            symbol: Stock symbol
            market_data: Real-time market data
            historical_data: Historical OHLCV data
            fundamental_data: Fundamental analysis data
            news_sentiment: News sentiment analysis
            social_sentiment: Social media sentiment analysis
            
        Returns:
            TradingDecision with all factors and reasoning
        """
        factors = []
        
        try:
            # Technical Analysis
            technical_factors = self.technical_analyzer.analyze_technical_indicators(historical_data)
            factors.extend(technical_factors)
            
            # Candlestick Pattern Analysis
            candlestick_factors = self._analyze_candlestick_patterns(historical_data)
            factors.extend(candlestick_factors)
            
            # Fundamental Analysis
            if fundamental_data:
                fundamental_factors = self._analyze_fundamental_data(fundamental_data)
                factors.extend(fundamental_factors)
            
            # News Sentiment Analysis
            if news_sentiment:
                news_factors = self._analyze_news_sentiment(news_sentiment)
                factors.extend(news_factors)
            
            # Social Sentiment Analysis  
            if social_sentiment:
                social_factors = self._analyze_social_sentiment(social_sentiment)
                factors.extend(social_factors)
            
            # Calculate overall decision
            overall_signal, confidence, reasoning = self._calculate_overall_decision(factors)
            
            # Calculate risk score
            risk_score = self._calculate_risk_score(market_data, historical_data, factors)
            
            # Calculate position size based on confidence and risk
            position_size = self._calculate_position_size(confidence, risk_score)
            
            return TradingDecision(
                symbol=symbol,
                overall_signal=overall_signal,
                confidence=confidence,
                factors=factors,
                risk_score=risk_score,
                position_size=position_size,
                timestamp=datetime.now(),
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error making decision for {symbol}: {e}")
            
            # Return safe default decision
            return TradingDecision(
                symbol=symbol,
                overall_signal=Signal.HOLD,
                confidence=0.0,
                factors=[],
                risk_score=1.0,
                position_size=0.0,
                timestamp=datetime.now(),
                reasoning=f"Error in decision making: {e}"
            )
    
    def _analyze_candlestick_patterns(self, historical_data: pd.DataFrame) -> List[DecisionFactor]:
        """Analyze candlestick patterns and convert to decision factors"""
        factors = []
        
        try:
            patterns = self.candlestick_analyzer.analyze_patterns(historical_data)
            
            for pattern, confidence, reasoning in patterns:
                # Map pattern to signal
                signal = self._pattern_to_signal(pattern)
                
                factor = DecisionFactor(
                    name=f"Candlestick_{pattern.value}",
                    signal=signal,
                    confidence=confidence,
                    weight=0.1,
                    reasoning=reasoning,
                    data_source="Candlestick_Patterns",
                    timestamp=datetime.now()
                )
                factors.append(factor)
                
        except Exception as e:
            logger.error(f"Error analyzing candlestick patterns: {e}")
        
        return factors
    
    def _pattern_to_signal(self, pattern: CandlestickPattern) -> Signal:
        """Map candlestick patterns to trading signals"""
        bullish_patterns = {
            CandlestickPattern.HAMMER,
            CandlestickPattern.BULLISH_ENGULFING,
            CandlestickPattern.MORNING_STAR,
            CandlestickPattern.INVERTED_HAMMER,
            CandlestickPattern.PIERCING_PATTERN
        }
        
        bearish_patterns = {
            CandlestickPattern.HANGING_MAN,
            CandlestickPattern.BEARISH_ENGULFING,
            CandlestickPattern.EVENING_STAR,
            CandlestickPattern.SHOOTING_STAR,
            CandlestickPattern.DARK_CLOUD_COVER
        }
        
        if pattern in bullish_patterns:
            return Signal.BUY
        elif pattern in bearish_patterns:
            return Signal.SELL
        else:
            return Signal.HOLD
    
    def _analyze_fundamental_data(self, fundamental_data: Dict) -> List[DecisionFactor]:
        """Analyze fundamental data and return decision factors"""
        factors = []
        
        try:
            # P/E Ratio Analysis
            pe_ratio = fundamental_data.get('pe_ratio', 0)
            if pe_ratio > 0:
                if pe_ratio < 15:
                    signal = Signal.BUY
                    confidence = 0.7
                    reasoning = f"Low P/E ratio of {pe_ratio:.1f} suggests undervaluation"
                elif pe_ratio > 30:
                    signal = Signal.SELL
                    confidence = 0.7
                    reasoning = f"High P/E ratio of {pe_ratio:.1f} suggests overvaluation"
                else:
                    signal = Signal.HOLD
                    confidence = 0.5
                    reasoning = f"Moderate P/E ratio of {pe_ratio:.1f}"
                
                factors.append(DecisionFactor(
                    name="PE_Ratio_Analysis",
                    signal=signal,
                    confidence=confidence,
                    weight=0.15,
                    reasoning=reasoning,
                    data_source="Fundamental_Data",
                    timestamp=datetime.now()
                ))
            
            # Market Cap Analysis
            market_cap = fundamental_data.get('market_cap', 0)
            if market_cap > 0:
                if market_cap > 200_000_000_000:  # Large cap
                    signal = Signal.HOLD
                    confidence = 0.6
                    reasoning = f"Large cap stock (${market_cap/1e9:.1f}B) - stable but limited growth"
                elif market_cap < 2_000_000_000:  # Small cap
                    signal = Signal.BUY
                    confidence = 0.5
                    reasoning = f"Small cap stock (${market_cap/1e9:.1f}B) - higher growth potential"
                else:  # Mid cap
                    signal = Signal.BUY
                    confidence = 0.7
                    reasoning = f"Mid cap stock (${market_cap/1e9:.1f}B) - good growth/stability balance"
                
                factors.append(DecisionFactor(
                    name="Market_Cap_Analysis",
                    signal=signal,
                    confidence=confidence,
                    weight=0.10,
                    reasoning=reasoning,
                    data_source="Fundamental_Data",
                    timestamp=datetime.now()
                ))
                
        except Exception as e:
            logger.error(f"Error analyzing fundamental data: {e}")
        
        return factors
    
    def _analyze_news_sentiment(self, news_sentiment: Dict) -> List[DecisionFactor]:
        """Analyze news sentiment and return decision factors"""
        factors = []
        
        try:
            sentiment_score = news_sentiment.get('sentiment_score', 0.0)  # -1.0 to 1.0
            article_count = news_sentiment.get('article_count', 0)
            
            if article_count > 0:
                if sentiment_score > 0.3:
                    signal = Signal.BUY
                    confidence = min(sentiment_score, 0.8)
                    reasoning = f"Positive news sentiment ({sentiment_score:.2f}) from {article_count} articles"
                elif sentiment_score < -0.3:
                    signal = Signal.SELL
                    confidence = min(abs(sentiment_score), 0.8)
                    reasoning = f"Negative news sentiment ({sentiment_score:.2f}) from {article_count} articles"
                else:
                    signal = Signal.HOLD
                    confidence = 0.5
                    reasoning = f"Neutral news sentiment ({sentiment_score:.2f}) from {article_count} articles"
                
                factors.append(DecisionFactor(
                    name="News_Sentiment_Analysis",
                    signal=signal,
                    confidence=confidence,
                    weight=0.15,
                    reasoning=reasoning,
                    data_source="News_Sentiment",
                    timestamp=datetime.now()
                ))
                
        except Exception as e:
            logger.error(f"Error analyzing news sentiment: {e}")
        
        return factors
    
    def _analyze_social_sentiment(self, social_sentiment: Dict) -> List[DecisionFactor]:
        """Analyze social media sentiment and return decision factors"""
        factors = []
        
        try:
            sentiment_score = social_sentiment.get('sentiment_score', 0.0)  # -1.0 to 1.0
            mention_count = social_sentiment.get('mention_count', 0)
            
            if mention_count > 10:  # Only consider if sufficient mentions
                if sentiment_score > 0.2:
                    signal = Signal.BUY
                    confidence = min(sentiment_score * 0.8, 0.6)  # Lower confidence than news
                    reasoning = f"Positive social sentiment ({sentiment_score:.2f}) from {mention_count} mentions"
                elif sentiment_score < -0.2:
                    signal = Signal.SELL
                    confidence = min(abs(sentiment_score) * 0.8, 0.6)
                    reasoning = f"Negative social sentiment ({sentiment_score:.2f}) from {mention_count} mentions"
                else:
                    signal = Signal.HOLD
                    confidence = 0.4
                    reasoning = f"Neutral social sentiment ({sentiment_score:.2f}) from {mention_count} mentions"
                
                factors.append(DecisionFactor(
                    name="Social_Sentiment_Analysis",
                    signal=signal,
                    confidence=confidence,
                    weight=0.10,
                    reasoning=reasoning,
                    data_source="Social_Sentiment",
                    timestamp=datetime.now()
                ))
                
        except Exception as e:
            logger.error(f"Error analyzing social sentiment: {e}")
        
        return factors
    
    def _calculate_overall_decision(self, factors: List[DecisionFactor]) -> Tuple[Signal, float, str]:
        """Calculate overall trading decision from all factors"""
        if not factors:
            return Signal.HOLD, 0.0, "No decision factors available"
        
        # Calculate weighted scores for each signal type
        signal_scores = {
            Signal.STRONG_BUY: 0.0,
            Signal.BUY: 0.0,
            Signal.HOLD: 0.0,
            Signal.SELL: 0.0,
            Signal.STRONG_SELL: 0.0
        }
        
        total_weight = 0.0
        reasoning_parts = []
        
        for factor in factors:
            weighted_confidence = factor.confidence * factor.weight
            signal_scores[factor.signal] += weighted_confidence
            total_weight += factor.weight
            
            reasoning_parts.append(f"{factor.name}: {factor.signal.value} ({factor.confidence:.2f})")
        
        # Normalize scores
        if total_weight > 0:
            for signal in signal_scores:
                signal_scores[signal] /= total_weight
        
        # Find the signal with highest score
        best_signal = max(signal_scores, key=signal_scores.get)
        best_score = signal_scores[best_signal]
        
        # Calculate overall confidence with improved logic for unanimous signals
        buy_signals = signal_scores[Signal.STRONG_BUY] + signal_scores[Signal.BUY]
        sell_signals = signal_scores[Signal.STRONG_SELL] + signal_scores[Signal.SELL]
        hold_signals = signal_scores[Signal.HOLD]
        
        # Calculate signal agreement (higher when signals agree)
        total_directional = buy_signals + sell_signals
        if total_directional > 0:
            # For directional signals, confidence is higher when they agree
            signal_agreement = max(buy_signals, sell_signals) / total_directional
            overall_confidence = best_score * (0.5 + 0.5 * signal_agreement)  # Boost for agreement
        else:
            # All HOLD signals
            overall_confidence = best_score
        
        # Create reasoning summary
        reasoning = f"Overall: {best_signal.value} (confidence: {overall_confidence:.2f}). " + \
                   f"Factors: {'; '.join(reasoning_parts[:3])}"  # Limit reasoning length
        
        return best_signal, overall_confidence, reasoning
    
    def _calculate_risk_score(self, market_data: Dict, historical_data: pd.DataFrame, 
                            factors: List[DecisionFactor]) -> float:
        """Calculate risk score for the decision"""
        risk_score = 0.0
        
        try:
            # Volatility risk
            if len(historical_data) >= 20:
                returns = historical_data['Close'].pct_change().dropna()
                volatility = returns.std() * np.sqrt(252)  # Annualized volatility
                risk_score += min(volatility * 2, 1.0) * 0.4  # Cap at 1.0
            
            # Volume risk (low volume = higher risk)
            current_volume = market_data.get('volume', 0)
            if len(historical_data) >= 20:
                avg_volume = historical_data['Volume'].mean()
                volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
                if volume_ratio < 0.5:  # Low volume
                    risk_score += 0.3
            
            # Factor disagreement risk
            if factors:
                buy_factors = sum(1 for f in factors if f.signal in [Signal.BUY, Signal.STRONG_BUY])
                sell_factors = sum(1 for f in factors if f.signal in [Signal.SELL, Signal.STRONG_SELL])
                total_factors = len(factors)
                
                if total_factors > 0:
                    disagreement = min(buy_factors, sell_factors) / total_factors
                    risk_score += disagreement * 0.3
            
        except Exception as e:
            logger.error(f"Error calculating risk score: {e}")
            risk_score = 0.8  # High risk if we can't calculate
        
        return min(risk_score, 1.0)  # Cap at 1.0
    
    def _calculate_position_size(self, confidence: float, risk_score: float) -> float:
        """Calculate recommended position size based on confidence and risk"""
        # Kelly criterion inspired position sizing
        base_size = confidence * 0.5  # Max 50% of portfolio even with full confidence
        risk_adjustment = 1.0 - risk_score
        
        position_size = base_size * risk_adjustment
        
        # Apply additional safety constraints
        if confidence < 0.6:
            position_size *= 0.5  # Reduce size for low confidence
        
        return min(max(position_size, 0.0), 0.25)  # Cap at 25% of portfolio