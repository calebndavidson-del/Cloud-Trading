# Trading Bot Decision Factors

This document provides a comprehensive overview of all data sources, decision logic, candlestick pattern analysis, and aggregation strategies used by the Cloud Trading Bot to make informed trading decisions.

## Overview

The trading bot uses a multi-factor decision engine that aggregates data from various sources to generate trading signals. All data sources provide **live, real-time data only** - no mock, demo, or simulated data is used in production decisions.

## Data Sources

### 1. Technical Indicators (Weight: 30%)

**Primary Sources:**
- Yahoo Finance (Priority 1)
- Alpha Vantage (Priority 2) 
- IEX Cloud (Priority 3)

**Indicators Used:**

#### RSI (Relative Strength Index)
- **Weight:** 15%
- **Calculation:** 14-period RSI
- **Signal Logic:**
  - RSI > 70: SELL (Overbought)
  - RSI < 30: BUY (Oversold)
  - 30 ≤ RSI ≤ 70: HOLD (Neutral)
- **Confidence:** Higher when RSI is extreme (>80 or <20)

#### Moving Averages
- **Weight:** 20%
- **Calculation:** 20-period and 50-period simple moving averages
- **Signal Logic:**
  - Price > MA20 > MA50: BUY (Bullish trend)
  - Price < MA20 < MA50: SELL (Bearish trend)
  - MA20 crosses above MA50: STRONG BUY (Golden Cross)
  - MA20 crosses below MA50: STRONG SELL (Death Cross)
- **Confidence:** Higher during clear crossover events

#### MACD (Moving Average Convergence Divergence)
- **Weight:** 15%
- **Calculation:** 12-period EMA - 26-period EMA, 9-period signal line
- **Signal Logic:**
  - MACD crosses above signal line: BUY
  - MACD crosses below signal line: SELL
  - MACD above zero line: Bullish bias
  - MACD below zero line: Bearish bias
- **Confidence:** Higher during strong directional moves

#### Volume Analysis
- **Weight:** 10%
- **Calculation:** Current volume vs 20-period average volume
- **Signal Logic:**
  - High volume (>1.5x avg) + price increase: BUY
  - High volume (>1.5x avg) + price decrease: SELL
  - Low volume (<0.5x avg): HOLD (Lack of conviction)
- **Confidence:** Increases with volume ratio

### 2. Candlestick Patterns (Weight: 20%)

**Data Freshness Requirement:** Maximum 1-minute old data for pattern recognition

#### Single Candle Patterns

**Doji**
- **Signal:** HOLD (Indecision)
- **Detection:** Body size ≤ 10% of total candle range
- **Confidence:** Inversely related to body size ratio
- **Weight:** 10%

**Hammer**
- **Signal:** BUY (Bullish reversal at bottom)
- **Detection:** 
  - Small body (≤30% of range)
  - Long lower shadow (≥60% of range)
  - Minimal upper shadow (≤10% of range)
- **Confidence:** Based on shadow-to-body ratio
- **Weight:** 10%

**Hanging Man**
- **Signal:** SELL (Bearish reversal at top)
- **Detection:** Same as Hammer but in uptrend context
- **Confidence:** Enhanced by trend context
- **Weight:** 10%

**Shooting Star**
- **Signal:** SELL (Bearish reversal at top)
- **Detection:**
  - Small body (≤30% of range)
  - Long upper shadow (≥60% of range)  
  - Minimal lower shadow (≤10% of range)
- **Confidence:** Based on shadow-to-body ratio
- **Weight:** 10%

**Inverted Hammer**
- **Signal:** BUY (Bullish reversal at bottom)
- **Detection:** Same as Shooting Star but in downtrend context
- **Confidence:** Enhanced by trend context
- **Weight:** 10%

#### Two Candle Patterns

**Bullish Engulfing**
- **Signal:** BUY (Bullish reversal)
- **Detection:**
  - Previous candle: Bearish (red)
  - Current candle: Bullish (green)
  - Current body completely engulfs previous body
- **Confidence:** Based on engulfing ratio (current body / previous body)
- **Weight:** 10%

**Bearish Engulfing**
- **Signal:** SELL (Bearish reversal)
- **Detection:**
  - Previous candle: Bullish (green)
  - Current candle: Bearish (red)
  - Current body completely engulfs previous body
- **Confidence:** Based on engulfing ratio
- **Weight:** 10%

**Dark Cloud Cover**
- **Signal:** SELL (Bearish reversal)
- **Detection:**
  - Previous candle: Bullish
  - Current candle: Bearish, opens above previous high, closes below previous midpoint
- **Confidence:** Based on penetration depth
- **Weight:** 10%

**Piercing Pattern**
- **Signal:** BUY (Bullish reversal)
- **Detection:**
  - Previous candle: Bearish
  - Current candle: Bullish, opens below previous low, closes above previous midpoint
- **Confidence:** Based on penetration depth
- **Weight:** 10%

#### Three Candle Patterns

**Morning Star**
- **Signal:** BUY (Bullish reversal)
- **Detection:**
  - First candle: Bearish
  - Second candle: Small body (star), gaps down
  - Third candle: Bullish, closes into first candle's body
- **Confidence:** Based on recovery ratio
- **Weight:** 10%

**Evening Star**
- **Signal:** SELL (Bearish reversal)
- **Detection:**
  - First candle: Bullish
  - Second candle: Small body (star), gaps up
  - Third candle: Bearish, closes into first candle's body
- **Confidence:** Based on decline ratio
- **Weight:** 10%

### 3. Fundamental Analysis (Weight: 20%)

**Data Sources:**
- Yahoo Finance Company Info
- Financial statements (when available)
- Market cap data

#### P/E Ratio Analysis
- **Weight:** 15%
- **Signal Logic:**
  - P/E < 15: BUY (Potentially undervalued)
  - P/E > 30: SELL (Potentially overvalued)
  - 15 ≤ P/E ≤ 30: HOLD (Fair value)
- **Confidence:** 70% for extreme values

#### Market Cap Analysis
- **Weight:** 10%
- **Signal Logic:**
  - Large cap (>$200B): HOLD (Stable, limited growth)
  - Mid cap ($2B-$200B): BUY (Growth/stability balance)
  - Small cap (<$2B): BUY (High growth potential, higher risk)
- **Confidence:** Varies by market conditions

#### Additional Metrics (When Available)
- PEG Ratio
- Price-to-Book Ratio
- Debt-to-Equity Ratio
- Return on Equity (ROE)
- Profit Margins
- Revenue Growth
- Earnings Growth

### 4. News Sentiment Analysis (Weight: 15%)

**Data Sources:**
- News APIs (NewsAPI, Benzinga, etc.)
- Financial news aggregators
- Company press releases

#### Sentiment Scoring
- **Range:** -1.0 (Very Negative) to +1.0 (Very Positive)
- **Signal Logic:**
  - Sentiment > 0.3: BUY
  - Sentiment < -0.3: SELL
  - -0.3 ≤ Sentiment ≤ 0.3: HOLD
- **Confidence:** Based on sentiment strength and article count
- **Minimum Articles:** 3 articles required for reliable signal

#### News Quality Factors
- Source credibility
- Article freshness (max 24 hours old)
- Relevance to company/sector
- Market-moving potential

### 5. Social Media Sentiment (Weight: 15%)

**Data Sources:**
- Reddit (r/investing, r/stocks, r/SecurityAnalysis)
- Twitter financial discussions
- Discord trading communities
- StockTwits

#### Sentiment Scoring
- **Range:** -1.0 (Very Negative) to +1.0 (Very Positive)
- **Signal Logic:**
  - Sentiment > 0.2: BUY (Lower threshold than news)
  - Sentiment < -0.2: SELL
  - -0.2 ≤ Sentiment ≤ 0.2: HOLD
- **Confidence:** 60% max (lower than news due to noise)
- **Minimum Mentions:** 10 mentions required for signal

#### Social Quality Factors
- Account credibility
- Message recency (max 6 hours old)
- Community engagement level
- Bot detection and filtering

## Decision Aggregation Strategy

### 1. Factor Weighting
Each decision factor contributes to the final decision based on its assigned weight:

```
Final Score = Σ(Factor Signal × Factor Confidence × Factor Weight)
```

### 2. Signal Mapping
- **STRONG_BUY:** Final Score > 0.7
- **BUY:** 0.3 < Final Score ≤ 0.7
- **HOLD:** -0.3 ≤ Final Score ≤ 0.3
- **SELL:** -0.7 ≤ Final Score < -0.3
- **STRONG_SELL:** Final Score < -0.7

### 3. Confidence Calculation
Overall confidence is calculated considering:
- Individual factor confidence levels
- Agreement between factors (reduced confidence for conflicting signals)
- Data quality and freshness
- Historical accuracy of similar patterns

### 4. Risk Adjustment
Risk score (0.0 to 1.0) is calculated based on:
- **Volatility Risk:** Historical price volatility (40% weight)
- **Volume Risk:** Current volume vs average (30% weight)  
- **Factor Disagreement:** Conflicting signals between factors (30% weight)

### 5. Position Sizing
Recommended position size calculated using:
```
Position Size = Base Size × Confidence × Risk Adjustment
Base Size = min(Confidence × 0.5, 0.25)  // Max 25% of portfolio
Risk Adjustment = 1.0 - Risk Score
```

## Data Quality Assurance

### Freshness Requirements
- **Real-time data:** < 1 minute old (preferred)
- **Fresh data:** < 5 minutes old (acceptable)
- **Stale data:** < 15 minutes old (warning issued)
- **Expired data:** > 15 minutes old (rejected)

### Data Validation
1. **Completeness Check:** All required fields present
2. **Sanity Check:** Values within reasonable ranges
3. **Consistency Check:** Cross-validation between sources
4. **Timestamp Validation:** Data freshness verification

### Error Handling
1. **Connection Monitoring:** Track provider health and errors
2. **Automatic Failover:** Switch to backup providers on failure
3. **Rate Limiting:** Respect API rate limits
4. **Recovery Mechanisms:** Automatic retry with exponential backoff

## Live Data Enforcement

### No Mock Data Policy
- **Production Mode:** Mock data usage is completely disabled
- **Validation:** All data sources verified for live feeds
- **Fallback:** System fails safely if live data unavailable
- **Monitoring:** Continuous validation of data freshness

### Connection Recovery
1. **Error Detection:** Monitor for failed API calls
2. **Health Checking:** Regular provider health validation
3. **Automatic Recovery:** Retry failed connections with backoff
4. **Alerting:** Log and alert on persistent connection issues

## Transparency and Logging

### Decision Logging
Each trading decision includes:
- All contributing factors with individual signals and confidence
- Data sources and timestamps for each factor
- Overall confidence calculation
- Risk assessment details
- Position sizing rationale

### Audit Trail
- Complete decision history with timestamps
- Data source performance metrics
- Error logs and recovery actions
- Factor weight adjustments over time

### Performance Monitoring
- Decision accuracy tracking
- Factor contribution analysis
- Risk-adjusted returns
- Data quality metrics

## Configuration and Customization

### Adjustable Parameters
- Factor weights for different market conditions
- Confidence thresholds for signal generation
- Risk tolerance levels
- Position sizing constraints
- Data freshness requirements

### Market Regime Adaptation
- Bull market factor weights
- Bear market factor weights
- High volatility adjustments
- Low liquidity considerations

## Integration Points

### External APIs
- Market data providers (Yahoo Finance, Alpha Vantage, IEX Cloud)
- News APIs (NewsAPI, Benzinga)
- Social media APIs (Reddit, Twitter)
- Fundamental data providers

### Internal Systems
- Portfolio management system
- Risk management system
- Order execution system
- Performance tracking system

## Compliance and Risk Management

### Risk Controls
- Maximum position size limits
- Sector concentration limits
- Daily loss limits
- Volatility-based position sizing

### Regulatory Compliance
- Trade reporting requirements
- Position disclosure requirements
- Risk management documentation
- Audit trail maintenance

---

*This document is automatically updated when decision logic changes. Last updated: [Timestamp will be inserted automatically]*