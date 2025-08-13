"""
Unit tests for the decision engine and candlestick pattern recognition.
Tests live data integration and decision logic transparency.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from backend.decision_engine import (
    DecisionEngine, CandlestickAnalyzer, TechnicalAnalyzer,
    Signal, CandlestickPattern, DecisionFactor, TradingDecision
)


class TestCandlestickAnalyzer:
    """Test candlestick pattern recognition"""
    
    def setup_method(self):
        self.analyzer = CandlestickAnalyzer()
    
    def create_test_data(self, patterns):
        """Create test OHLCV data for specific patterns"""
        data = []
        
        for pattern in patterns:
            if pattern == 'doji':
                # Doji: open ≈ close, long shadows
                data.append({
                    'Open': 100.0,
                    'High': 102.0,
                    'Low': 98.0,
                    'Close': 100.1,  # Very small body
                    'Volume': 1000000
                })
            elif pattern == 'hammer':
                # Hammer: small body (20% of range), long lower shadow (70% of range), minimal upper shadow (10%)
                # Total range = 100.5 - 94.0 = 6.5
                # Body = |99.3 - 100.0| = 0.7 (0.7/6.5 = 10.8% < 30% ✓)
                # Lower shadow = min(99.3, 100.0) - 94.0 = 99.3 - 94.0 = 5.3 (5.3/6.5 = 81.5% > 60% ✓)  
                # Upper shadow = 100.5 - max(99.3, 100.0) = 100.5 - 100.0 = 0.5 (0.5/6.5 = 7.7% < 10% ✓)
                data.append({
                    'Open': 100.0,
                    'High': 100.5,   # Small upper shadow
                    'Low': 94.0,     # Long lower shadow
                    'Close': 99.3,   # Small body, close near open
                    'Volume': 1000000
                })
            elif pattern == 'bullish_engulfing':
                # Two candles: bearish then bullish engulfing
                data.extend([
                    {
                        'Open': 100.0,
                        'High': 100.5,
                        'Low': 98.0,
                        'Close': 98.5,   # Bearish
                        'Volume': 800000
                    },
                    {
                        'Open': 98.0,    # Opens below previous close
                        'High': 102.0,
                        'Low': 97.5,
                        'Close': 101.0,  # Closes above previous open (engulfing)
                        'Volume': 1200000
                    }
                ])
        
        return pd.DataFrame(data)
    
    def test_doji_detection(self):
        """Test Doji pattern detection"""
        data = self.create_test_data(['doji'])
        patterns = self.analyzer.analyze_patterns(data)
        
        # Should detect Doji pattern
        doji_patterns = [p for p in patterns if p[0] == CandlestickPattern.DOJI]
        assert len(doji_patterns) > 0
        
        pattern, confidence, reasoning = doji_patterns[0]
        assert confidence > 0.5
        assert 'Doji' in reasoning
        assert 'body ratio' in reasoning
    
    def test_hammer_detection(self):
        """Test Hammer pattern detection"""
        data = self.create_test_data(['hammer'])
        patterns = self.analyzer.analyze_patterns(data)
        
        # Should detect Hammer pattern
        hammer_patterns = [p for p in patterns if p[0] == CandlestickPattern.HAMMER]
        assert len(hammer_patterns) > 0
        
        pattern, confidence, reasoning = hammer_patterns[0]
        assert confidence > 0.5
        assert 'Hammer' in reasoning
        assert 'lower shadow' in reasoning
    
    def test_bullish_engulfing_detection(self):
        """Test Bullish Engulfing pattern detection"""
        data = self.create_test_data(['bullish_engulfing'])
        patterns = self.analyzer.analyze_patterns(data)
        
        # Should detect Bullish Engulfing pattern
        engulfing_patterns = [p for p in patterns if p[0] == CandlestickPattern.BULLISH_ENGULFING]
        assert len(engulfing_patterns) > 0
        
        pattern, confidence, reasoning = engulfing_patterns[0]
        assert confidence > 0.3
        assert 'Bullish Engulfing' in reasoning
    
    def test_no_pattern_detection(self):
        """Test that no patterns are detected in normal data"""
        # Create normal candle data without clear patterns
        data = pd.DataFrame([
            {
                'Open': 100.0,
                'High': 101.0,
                'Low': 99.5,
                'Close': 100.5,
                'Volume': 1000000
            }
        ])
        
        patterns = self.analyzer.analyze_patterns(data)
        
        # Should not detect strong patterns in normal data
        high_confidence_patterns = [p for p in patterns if p[1] > 0.7]
        assert len(high_confidence_patterns) == 0


class TestTechnicalAnalyzer:
    """Test technical indicator analysis"""
    
    def setup_method(self):
        self.analyzer = TechnicalAnalyzer()
    
    def create_test_price_data(self, trend='neutral', periods=50):
        """Create test price data with specific trend"""
        np.random.seed(42)  # For reproducible results
        
        dates = pd.date_range(start='2024-01-01', periods=periods, freq='D')
        
        if trend == 'uptrend':
            prices = 100 + np.cumsum(np.random.normal(0.5, 1, periods))
        elif trend == 'downtrend':
            prices = 100 + np.cumsum(np.random.normal(-0.5, 1, periods))
        else:  # neutral
            prices = 100 + np.cumsum(np.random.normal(0, 1, periods))
        
        # Create OHLCV data
        data = []
        for i, price in enumerate(prices):
            open_price = price + np.random.normal(0, 0.5)
            high = max(price, open_price) + abs(np.random.normal(0, 0.5))
            low = min(price, open_price) - abs(np.random.normal(0, 0.5))
            volume = np.random.randint(500000, 2000000)
            
            data.append({
                'Open': open_price,
                'High': high,
                'Low': low,
                'Close': price,
                'Volume': volume
            })
        
        return pd.DataFrame(data, index=dates)
    
    def test_rsi_analysis_oversold(self):
        """Test RSI analysis for oversold conditions"""
        # Create data that will result in low RSI (oversold)
        data = self.create_test_price_data('downtrend', 30)
        
        factors = self.analyzer.analyze_technical_indicators(data)
        
        # Should have RSI factor
        rsi_factors = [f for f in factors if f.name == 'RSI_Analysis']
        assert len(rsi_factors) > 0
        
        rsi_factor = rsi_factors[0]
        # For downtrend data, RSI should suggest BUY (oversold)
        assert rsi_factor.signal in [Signal.BUY, Signal.HOLD]
        assert rsi_factor.confidence > 0
        assert 'RSI' in rsi_factor.reasoning
    
    def test_moving_average_analysis(self):
        """Test moving average analysis"""
        data = self.create_test_price_data('uptrend', 60)
        
        factors = self.analyzer.analyze_technical_indicators(data)
        
        # Should have moving average factor
        ma_factors = [f for f in factors if f.name == 'Moving_Average_Analysis']
        assert len(ma_factors) > 0
        
        ma_factor = ma_factors[0]
        assert ma_factor.signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
        assert ma_factor.confidence > 0
        assert 'MA' in ma_factor.reasoning
    
    def test_insufficient_data(self):
        """Test behavior with insufficient data"""
        # Create data with only 5 periods (insufficient for most indicators)
        data = self.create_test_price_data('neutral', 5)
        
        factors = self.analyzer.analyze_technical_indicators(data)
        
        # Should return empty or very few factors
        assert len(factors) <= 1  # Maybe volume analysis only


class TestDecisionEngine:
    """Test the main decision engine"""
    
    def setup_method(self):
        self.engine = DecisionEngine()
    
    def create_test_market_data(self):
        """Create test market data"""
        return {
            'price': 150.0,
            'volume': 1000000,
            'open': 149.0,
            'high': 151.0,
            'low': 148.5,
            'market_cap': 2500000000000,
            'pe_ratio': 25.0
        }
    
    def create_test_historical_data(self):
        """Create test historical data"""
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0, 1, 100))
        
        data = []
        for price in prices:
            data.append({
                'Open': price + np.random.normal(0, 0.5),
                'High': price + abs(np.random.normal(1, 0.5)),
                'Low': price - abs(np.random.normal(1, 0.5)),
                'Close': price,
                'Volume': np.random.randint(500000, 2000000)
            })
        
        return pd.DataFrame(data, index=dates)
    
    def create_test_fundamental_data(self):
        """Create test fundamental data"""
        return {
            'pe_ratio': 20.0,
            'market_cap': 100000000000,  # 100B (mid cap)
            'price_to_book': 3.0,
            'debt_to_equity': 0.5
        }
    
    def create_test_news_sentiment(self):
        """Create test news sentiment data"""
        return {
            'sentiment_score': 0.4,  # Positive
            'article_count': 5,
            'positive_count': 3,
            'negative_count': 1,
            'neutral_count': 1
        }
    
    def test_comprehensive_decision_making(self):
        """Test comprehensive decision making with all factors"""
        decision = self.engine.make_decision(
            symbol='AAPL',
            market_data=self.create_test_market_data(),
            historical_data=self.create_test_historical_data(),
            fundamental_data=self.create_test_fundamental_data(),
            news_sentiment=self.create_test_news_sentiment(),
            social_sentiment={'sentiment_score': 0.2, 'mention_count': 15}
        )
        
        # Should return a valid decision
        assert isinstance(decision, TradingDecision)
        assert decision.symbol == 'AAPL'
        assert decision.overall_signal in [Signal.STRONG_BUY, Signal.BUY, Signal.HOLD, Signal.SELL, Signal.STRONG_SELL]
        assert 0.0 <= decision.confidence <= 1.0
        assert 0.0 <= decision.risk_score <= 1.0
        assert 0.0 <= decision.position_size <= 0.25  # Max 25% position
        assert len(decision.factors) > 0
        assert decision.reasoning is not None
    
    def test_decision_with_missing_data(self):
        """Test decision making with missing optional data"""
        decision = self.engine.make_decision(
            symbol='AAPL',
            market_data=self.create_test_market_data(),
            historical_data=self.create_test_historical_data(),
            fundamental_data=None,  # Missing
            news_sentiment=None,    # Missing
            social_sentiment=None   # Missing
        )
        
        # Should still return a valid decision
        assert isinstance(decision, TradingDecision)
        assert decision.overall_signal in [Signal.STRONG_BUY, Signal.BUY, Signal.HOLD, Signal.SELL, Signal.STRONG_SELL]
        assert len(decision.factors) > 0  # Should have technical factors at least
    
    def test_decision_transparency(self):
        """Test that decision includes transparent reasoning"""
        decision = self.engine.make_decision(
            symbol='AAPL',
            market_data=self.create_test_market_data(),
            historical_data=self.create_test_historical_data(),
            fundamental_data=self.create_test_fundamental_data(),
            news_sentiment=self.create_test_news_sentiment()
        )
        
        # Check transparency requirements
        assert decision.reasoning is not None
        assert len(decision.reasoning) > 0
        
        # Each factor should have reasoning
        for factor in decision.factors:
            assert factor.reasoning is not None
            assert len(factor.reasoning) > 0
            assert factor.data_source is not None
            assert factor.timestamp is not None
    
    def test_risk_score_calculation(self):
        """Test risk score calculation"""
        # Create high volatility data
        np.random.seed(42)
        dates = pd.date_range(start='2024-01-01', periods=50, freq='D')
        prices = 100 + np.cumsum(np.random.normal(0, 3, 50))  # High volatility
        
        high_vol_data = []
        for price in prices:
            high_vol_data.append({
                'Open': price,
                'High': price + abs(np.random.normal(2, 1)),
                'Low': price - abs(np.random.normal(2, 1)),
                'Close': price,
                'Volume': np.random.randint(100000, 500000)  # Low volume
            })
        
        high_vol_df = pd.DataFrame(high_vol_data, index=dates)
        
        decision = self.engine.make_decision(
            symbol='VOLATILE_STOCK',
            market_data={**self.create_test_market_data(), 'volume': 100000},  # Low volume
            historical_data=high_vol_df,
            fundamental_data=self.create_test_fundamental_data()
        )
        
        # High volatility and low volume should result in higher risk score
        assert decision.risk_score > 0.3
    
    def test_position_sizing(self):
        """Test position sizing logic"""
        # High confidence, low risk scenario
        with patch.object(self.engine, '_calculate_overall_decision') as mock_decision:
            mock_decision.return_value = (Signal.BUY, 0.9, "High confidence signal")
            
            with patch.object(self.engine, '_calculate_risk_score') as mock_risk:
                mock_risk.return_value = 0.2  # Low risk
                
                decision = self.engine.make_decision(
                    symbol='LOW_RISK_STOCK',
                    market_data=self.create_test_market_data(),
                    historical_data=self.create_test_historical_data()
                )
                
                # Should recommend larger position for high confidence, low risk
                assert decision.position_size > 0.1
                
        # Low confidence, high risk scenario
        with patch.object(self.engine, '_calculate_overall_decision') as mock_decision:
            mock_decision.return_value = (Signal.BUY, 0.3, "Low confidence signal")
            
            with patch.object(self.engine, '_calculate_risk_score') as mock_risk:
                mock_risk.return_value = 0.8  # High risk
                
                decision = self.engine.make_decision(
                    symbol='HIGH_RISK_STOCK',
                    market_data=self.create_test_market_data(),
                    historical_data=self.create_test_historical_data()
                )
                
                # Should recommend smaller position for low confidence, high risk
                assert decision.position_size < 0.05


class TestSignalAggregation:
    """Test signal aggregation and conflict resolution"""
    
    def setup_method(self):
        self.engine = DecisionEngine()
    
    def test_conflicting_signals(self):
        """Test handling of conflicting signals between factors"""
        # Create conflicting factors
        factors = [
            DecisionFactor(
                name="Technical_Bullish",
                signal=Signal.BUY,
                confidence=0.8,
                weight=0.3,
                reasoning="Technical indicators suggest buying",
                data_source="Technical",
                timestamp=datetime.now()
            ),
            DecisionFactor(
                name="Fundamental_Bearish",
                signal=Signal.SELL,
                confidence=0.7,
                weight=0.3,
                reasoning="Overvalued based on fundamentals",
                data_source="Fundamental",
                timestamp=datetime.now()
            ),
            DecisionFactor(
                name="News_Neutral",
                signal=Signal.HOLD,
                confidence=0.5,
                weight=0.2,
                reasoning="Mixed news sentiment",
                data_source="News",
                timestamp=datetime.now()
            )
        ]
        
        signal, confidence, reasoning = self.engine._calculate_overall_decision(factors)
        
        # With conflicting signals, confidence should be reduced
        assert confidence < 0.7  # Should be less than individual factor confidence
        assert signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
        assert reasoning is not None
    
    def test_unanimous_signals(self):
        """Test handling of unanimous signals"""
        # Create unanimous BUY signals
        factors = [
            DecisionFactor(
                name="Technical_Bullish",
                signal=Signal.BUY,
                confidence=0.8,
                weight=0.4,
                reasoning="Technical indicators suggest buying",
                data_source="Technical",
                timestamp=datetime.now()
            ),
            DecisionFactor(
                name="Fundamental_Bullish",
                signal=Signal.BUY,
                confidence=0.7,
                weight=0.3,
                reasoning="Undervalued based on fundamentals",
                data_source="Fundamental",
                timestamp=datetime.now()
            ),
            DecisionFactor(
                name="News_Bullish",
                signal=Signal.BUY,
                confidence=0.6,
                weight=0.3,
                reasoning="Positive news sentiment",
                data_source="News",
                timestamp=datetime.now()
            )
        ]
        
        signal, confidence, reasoning = self.engine._calculate_overall_decision(factors)
        
        # Unanimous signals should result in high confidence
        assert signal == Signal.BUY
        assert confidence > 0.6  # Should be high with unanimous agreement
        assert reasoning is not None
    
    def test_empty_factors(self):
        """Test handling of empty factors list"""
        signal, confidence, reasoning = self.engine._calculate_overall_decision([])
        
        assert signal == Signal.HOLD
        assert confidence == 0.0
        assert "No decision factors available" in reasoning


if __name__ == '__main__':
    pytest.main([__file__])