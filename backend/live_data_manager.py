"""
Enhanced Market Data Manager with Live-Only Data Integration

This module provides comprehensive market data management with multiple providers,
robust error handling, self-recovery mechanisms, and live-only data enforcement.
No mock or demo data is used - all data must be live and fresh.

Features:
- Multiple data provider support with automatic failover
- Live data verification and freshness checks
- Robust error handling and connection recovery
- Comprehensive data aggregation (technical, fundamental, sentiment, news)
- Real-time monitoring and alerting
- Data quality validation
- Rate limiting and connection management
"""

import asyncio
import aiohttp
import logging
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import yfinance as yf
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import threading
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Data source types"""
    YAHOO_FINANCE = "yahoo_finance"
    ALPHA_VANTAGE = "alpha_vantage"
    IEX_CLOUD = "iex_cloud"
    NEWS_API = "news_api"
    REDDIT_API = "reddit_api"
    TWITTER_API = "twitter_api"


class DataFreshness(Enum):
    """Data freshness levels"""
    REAL_TIME = "real_time"      # < 1 minute old
    FRESH = "fresh"              # < 5 minutes old
    STALE = "stale"              # < 15 minutes old
    EXPIRED = "expired"          # > 15 minutes old


@dataclass
class DataQuality:
    """Data quality metrics"""
    freshness: DataFreshness
    completeness: float  # 0.0 to 1.0
    accuracy: float      # 0.0 to 1.0
    source: DataSource
    timestamp: datetime
    error_count: int = 0


@dataclass  
class MarketDataPoint:
    """Individual market data point with quality metrics"""
    symbol: str
    data: Dict[str, Any]
    quality: DataQuality
    source: DataSource
    timestamp: datetime


class ConnectionMonitor:
    """Monitors and manages connection health for data providers"""
    
    def __init__(self):
        self.connection_status = {}
        self.error_counts = {}
        self.last_success = {}
        self.recovery_attempts = {}
        self.max_errors = 5
        self.recovery_cooldown = 300  # 5 minutes
    
    def record_success(self, source: DataSource):
        """Record successful connection"""
        self.connection_status[source] = True
        self.error_counts[source] = 0
        self.last_success[source] = datetime.now()
        self.recovery_attempts[source] = 0
        logger.debug(f"Successful connection to {source.value}")
    
    def record_error(self, source: DataSource, error: Exception):
        """Record connection error"""
        self.error_counts[source] = self.error_counts.get(source, 0) + 1
        self.connection_status[source] = False
        
        logger.warning(f"Connection error for {source.value}: {error}")
        
        if self.error_counts[source] >= self.max_errors:
            logger.error(f"Max errors reached for {source.value}, marking as down")
    
    def is_healthy(self, source: DataSource) -> bool:
        """Check if connection is healthy"""
        return (self.connection_status.get(source, False) and 
                self.error_counts.get(source, 0) < self.max_errors)
    
    def can_retry(self, source: DataSource) -> bool:
        """Check if retry is allowed"""
        if source not in self.last_success:
            return True
        
        time_since_last = datetime.now() - self.last_success[source]
        return time_since_last.seconds > self.recovery_cooldown
    
    def start_recovery(self, source: DataSource):
        """Start recovery attempt"""
        self.recovery_attempts[source] = self.recovery_attempts.get(source, 0) + 1
        logger.info(f"Starting recovery attempt #{self.recovery_attempts[source]} for {source.value}")


class LiveMarketDataManager:
    """
    Enhanced market data manager ensuring live-only data with robust error handling
    """
    
    def __init__(self, config_path: str = "market_data_config.json"):
        self.config_path = config_path
        self.config = self._load_config()
        self.connection_monitor = ConnectionMonitor()
        self.session_pool = {}
        self.data_cache = {}
        self.cache_ttl = 60  # 1 minute TTL for live data
        self.max_concurrent_requests = 10
        self.request_semaphore = asyncio.Semaphore(self.max_concurrent_requests)
        
        # Rate limiting
        self.rate_limits = {
            DataSource.YAHOO_FINANCE: {"requests": 100, "window": 60, "current": 0, "reset_time": time.time()},
            DataSource.ALPHA_VANTAGE: {"requests": 5, "window": 60, "current": 0, "reset_time": time.time()},
            DataSource.IEX_CLOUD: {"requests": 100, "window": 60, "current": 0, "reset_time": time.time()}
        }
        
        # Initialize session pools
        self._initialize_sessions()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration with live-only enforcement"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            # Enforce live-only settings
            config.setdefault('live_only_mode', True)
            config.setdefault('allow_mock_data', False)
            config.setdefault('max_data_age_seconds', 300)  # 5 minutes max
            config.setdefault('require_real_time', True)
            
            return config
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default live-only configuration"""
        return {
            "providers": {
                "yahoo_finance": {
                    "enabled": True,
                    "priority": 1,
                    "timeout": 10,
                    "base_url": "https://query1.finance.yahoo.com/v8/finance/chart/",
                    "api_key": None
                },
                "alpha_vantage": {
                    "enabled": True,
                    "priority": 2,
                    "timeout": 15,
                    "base_url": "https://www.alphavantage.co/query",
                    "api_key": "demo"  # Should be replaced with real key
                },
                "iex_cloud": {
                    "enabled": True,
                    "priority": 3,
                    "timeout": 12,
                    "base_url": "https://cloud.iexapis.com/stable/stock/",
                    "api_key": "demo"  # Should be replaced with real key
                }
            },
            "live_only_mode": True,
            "allow_mock_data": False,
            "max_data_age_seconds": 300,
            "require_real_time": True,
            "fallback_settings": {
                "max_retries": 3,
                "retry_delay": 2.0,
                "exponential_backoff": True
            }
        }
    
    def _initialize_sessions(self):
        """Initialize HTTP session pools for each provider"""
        for source in DataSource:
            self.session_pool[source] = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
            )
    
    async def close_sessions(self):
        """Close all HTTP sessions"""
        for session in self.session_pool.values():
            await session.close()
    
    def _check_rate_limit(self, source: DataSource) -> bool:
        """Check if request is within rate limits"""
        if source not in self.rate_limits:
            return True
        
        limit_info = self.rate_limits[source]
        current_time = time.time()
        
        # Reset counter if window has passed
        if current_time - limit_info["reset_time"] >= limit_info["window"]:
            limit_info["current"] = 0
            limit_info["reset_time"] = current_time
        
        # Check if within limits
        if limit_info["current"] >= limit_info["requests"]:
            logger.warning(f"Rate limit exceeded for {source.value}")
            return False
        
        limit_info["current"] += 1
        return True
    
    def _validate_data_freshness(self, data: Dict[str, Any], source: DataSource) -> DataFreshness:
        """Validate data freshness and ensure it's live"""
        try:
            # Check for timestamp in data
            timestamp = None
            
            # Try to extract timestamp from different possible fields
            for field in ['timestamp', 'time', 'last_updated', 'date']:
                if field in data:
                    timestamp = pd.to_datetime(data[field])
                    # Convert to timezone-naive datetime if it's timezone-aware
                    if timestamp.tz is not None:
                        timestamp = timestamp.tz_convert('UTC').tz_localize(None)
                    break
            
            if timestamp is None:
                # If no timestamp, assume current time (risky but necessary)
                timestamp = datetime.now()
                logger.warning(f"No timestamp found in data from {source.value}, assuming current time")
            
            # Calculate age (ensure both are timezone-naive)
            current_time = datetime.now()
            age_seconds = (current_time - timestamp).total_seconds()
            
            # Determine freshness
            if age_seconds < 60:
                return DataFreshness.REAL_TIME
            elif age_seconds < 300:
                return DataFreshness.FRESH
            elif age_seconds < 900:
                return DataFreshness.STALE
            else:
                return DataFreshness.EXPIRED
                
        except Exception as e:
            logger.error(f"Error validating data freshness: {e}")
            return DataFreshness.EXPIRED
    
    def _validate_data_quality(self, data: Dict[str, Any], source: DataSource) -> DataQuality:
        """Comprehensive data quality validation"""
        freshness = self._validate_data_freshness(data, source)
        
        # Check completeness (what percentage of expected fields are present)
        expected_fields = ['price', 'volume', 'open', 'high', 'low']
        present_fields = sum(1 for field in expected_fields if field in data and data[field] is not None)
        completeness = present_fields / len(expected_fields)
        
        # Check accuracy (basic sanity checks)
        accuracy = 1.0
        try:
            if 'price' in data and 'open' in data:
                price_diff = abs(data['price'] - data['open']) / data['open']
                if price_diff > 0.5:  # 50% change in one day is suspicious
                    accuracy *= 0.5
            
            if 'high' in data and 'low' in data and 'price' in data:
                if not (data['low'] <= data['price'] <= data['high']):
                    accuracy *= 0.3  # Price outside high/low range
                    
        except (TypeError, ZeroDivisionError, KeyError):
            accuracy *= 0.7
        
        return DataQuality(
            freshness=freshness,
            completeness=completeness,
            accuracy=accuracy,
            source=source,
            timestamp=datetime.now(),
            error_count=0
        )
    
    async def _fetch_yahoo_finance_data(self, symbols: List[str]) -> Dict[str, MarketDataPoint]:
        """Fetch live data from Yahoo Finance"""
        if not self._check_rate_limit(DataSource.YAHOO_FINANCE):
            raise Exception("Rate limit exceeded for Yahoo Finance")
        
        results = {}
        
        try:
            # Use yfinance for reliable data
            for symbol in symbols:
                try:
                    ticker = yf.Ticker(symbol)
                    
                    # Get real-time data
                    info = ticker.info
                    hist = ticker.history(period="1d", interval="1m")  # 1-minute intervals for freshness
                    
                    if not hist.empty:
                        latest = hist.iloc[-1]
                        
                        data = {
                            'price': float(latest['Close']),
                            'volume': int(latest['Volume']),
                            'open': float(latest['Open']),
                            'high': float(latest['High']),
                            'low': float(latest['Low']),
                            'market_cap': info.get('marketCap', 0),
                            'pe_ratio': info.get('trailingPE', 0),
                            'timestamp': hist.index[-1].to_pydatetime()
                        }
                        
                        quality = self._validate_data_quality(data, DataSource.YAHOO_FINANCE)
                        
                        # Only accept fresh data
                        if quality.freshness in [DataFreshness.REAL_TIME, DataFreshness.FRESH]:
                            results[symbol] = MarketDataPoint(
                                symbol=symbol,
                                data=data,
                                quality=quality,
                                source=DataSource.YAHOO_FINANCE,
                                timestamp=datetime.now()
                            )
                            self.connection_monitor.record_success(DataSource.YAHOO_FINANCE)
                        else:
                            logger.warning(f"Data for {symbol} from Yahoo Finance is not fresh enough: {quality.freshness}")
                    
                except Exception as e:
                    logger.error(f"Error fetching {symbol} from Yahoo Finance: {e}")
                    self.connection_monitor.record_error(DataSource.YAHOO_FINANCE, e)
                    continue
                    
        except Exception as e:
            self.connection_monitor.record_error(DataSource.YAHOO_FINANCE, e)
            raise
        
        return results
    
    async def _fetch_alpha_vantage_data(self, symbols: List[str]) -> Dict[str, MarketDataPoint]:
        """Fetch live data from Alpha Vantage"""
        if not self._check_rate_limit(DataSource.ALPHA_VANTAGE):
            raise Exception("Rate limit exceeded for Alpha Vantage")
        
        api_key = self.config.get('providers', {}).get('alpha_vantage', {}).get('api_key', 'demo')
        
        if api_key == 'demo':
            raise Exception("Alpha Vantage requires a real API key - demo keys not allowed in live mode")
        
        results = {}
        base_url = "https://www.alphavantage.co/query"
        
        session = self.session_pool[DataSource.ALPHA_VANTAGE]
        
        for symbol in symbols:
            try:
                # Get real-time quote
                params = {
                    'function': 'GLOBAL_QUOTE',
                    'symbol': symbol,
                    'apikey': api_key
                }
                
                async with session.get(base_url, params=params) as response:
                    if response.status == 200:
                        data_json = await response.json()
                        
                        if 'Global Quote' in data_json:
                            quote = data_json['Global Quote']
                            
                            data = {
                                'price': float(quote.get('05. price', 0)),
                                'volume': int(quote.get('06. volume', 0)),
                                'open': float(quote.get('02. open', 0)),
                                'high': float(quote.get('03. high', 0)),
                                'low': float(quote.get('04. low', 0)),
                                'timestamp': datetime.now()  # Alpha Vantage doesn't provide exact timestamp
                            }
                            
                            quality = self._validate_data_quality(data, DataSource.ALPHA_VANTAGE)
                            
                            if quality.freshness in [DataFreshness.REAL_TIME, DataFreshness.FRESH]:
                                results[symbol] = MarketDataPoint(
                                    symbol=symbol,
                                    data=data,
                                    quality=quality,
                                    source=DataSource.ALPHA_VANTAGE,
                                    timestamp=datetime.now()
                                )
                                self.connection_monitor.record_success(DataSource.ALPHA_VANTAGE)
                        else:
                            raise Exception(f"Unexpected response format from Alpha Vantage for {symbol}")
                    else:
                        raise Exception(f"HTTP {response.status} from Alpha Vantage for {symbol}")
                        
            except Exception as e:
                logger.error(f"Error fetching {symbol} from Alpha Vantage: {e}")
                self.connection_monitor.record_error(DataSource.ALPHA_VANTAGE, e)
                continue
        
        return results
    
    async def _fetch_iex_cloud_data(self, symbols: List[str]) -> Dict[str, MarketDataPoint]:
        """Fetch live data from IEX Cloud"""
        if not self._check_rate_limit(DataSource.IEX_CLOUD):
            raise Exception("Rate limit exceeded for IEX Cloud")
        
        api_key = self.config.get('providers', {}).get('iex_cloud', {}).get('api_key', 'demo')
        
        if api_key == 'demo':
            raise Exception("IEX Cloud requires a real API key - demo keys not allowed in live mode")
        
        results = {}
        base_url = "https://cloud.iexapis.com/stable/stock"
        
        session = self.session_pool[DataSource.IEX_CLOUD]
        
        for symbol in symbols:
            try:
                # Get real-time quote
                url = f"{base_url}/{symbol}/quote"
                params = {'token': api_key}
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        quote = await response.json()
                        
                        data = {
                            'price': float(quote.get('latestPrice', 0)),
                            'volume': int(quote.get('volume', 0)),
                            'open': float(quote.get('open', 0)),
                            'high': float(quote.get('high', 0)),
                            'low': float(quote.get('low', 0)),
                            'market_cap': int(quote.get('marketCap', 0)),
                            'pe_ratio': float(quote.get('peRatio', 0)) if quote.get('peRatio') else 0,
                            'timestamp': pd.to_datetime(quote.get('latestUpdate', 0), unit='ms').tz_localize(None)
                        }
                        
                        quality = self._validate_data_quality(data, DataSource.IEX_CLOUD)
                        
                        if quality.freshness in [DataFreshness.REAL_TIME, DataFreshness.FRESH]:
                            results[symbol] = MarketDataPoint(
                                symbol=symbol,
                                data=data,
                                quality=quality,
                                source=DataSource.IEX_CLOUD,
                                timestamp=datetime.now()
                            )
                            self.connection_monitor.record_success(DataSource.IEX_CLOUD)
                        else:
                            logger.warning(f"Data for {symbol} from IEX Cloud is not fresh enough: {quality.freshness}")
                    else:
                        raise Exception(f"HTTP {response.status} from IEX Cloud for {symbol}")
                        
            except Exception as e:
                logger.error(f"Error fetching {symbol} from IEX Cloud: {e}")
                self.connection_monitor.record_error(DataSource.IEX_CLOUD, e)
                continue
        
        return results
    
    async def fetch_live_market_data(self, symbols: List[str]) -> Dict[str, MarketDataPoint]:
        """
        Fetch live market data with automatic failover and quality validation
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary of symbol -> MarketDataPoint with live data only
        """
        if not symbols:
            raise ValueError("Symbols list cannot be empty")
        
        # Ensure we're in live-only mode
        if not self.config.get('live_only_mode', True):
            raise Exception("Live-only mode is disabled - this violates the requirement for live data only")
        
        results = {}
        failed_symbols = set(symbols)
        
        # Try providers in priority order
        providers = [
            (DataSource.YAHOO_FINANCE, self._fetch_yahoo_finance_data),
            (DataSource.ALPHA_VANTAGE, self._fetch_alpha_vantage_data),
            (DataSource.IEX_CLOUD, self._fetch_iex_cloud_data)
        ]
        
        for source, fetch_func in providers:
            if not failed_symbols:
                break
                
            if not self.connection_monitor.is_healthy(source):
                if self.connection_monitor.can_retry(source):
                    self.connection_monitor.start_recovery(source)
                else:
                    logger.warning(f"Skipping {source.value} - in recovery cooldown")
                    continue
            
            try:
                logger.info(f"Fetching data for {len(failed_symbols)} symbols from {source.value}")
                
                # Fetch data with timeout
                async with asyncio.timeout(30):
                    source_results = await fetch_func(list(failed_symbols))
                
                # Merge results and update failed symbols
                for symbol, data_point in source_results.items():
                    if data_point.quality.freshness in [DataFreshness.REAL_TIME, DataFreshness.FRESH]:
                        results[symbol] = data_point
                        failed_symbols.discard(symbol)
                        logger.debug(f"Successfully fetched {symbol} from {source.value}")
                    else:
                        logger.warning(f"Rejected stale data for {symbol} from {source.value}")
                
            except asyncio.TimeoutError:
                logger.error(f"Timeout fetching data from {source.value}")
                self.connection_monitor.record_error(source, Exception("Timeout"))
            except Exception as e:
                logger.error(f"Error fetching data from {source.value}: {e}")
                self.connection_monitor.record_error(source, e)
        
        # Log results
        if failed_symbols:
            logger.error(f"Failed to fetch live data for symbols: {failed_symbols}")
            # In live-only mode, we fail completely rather than return partial results
            raise Exception(f"Failed to fetch live data for symbols: {failed_symbols}")
        
        logger.info(f"Successfully fetched live data for {len(results)} symbols")
        return results
    
    async def fetch_historical_data(self, symbol: str, period: str = "1mo", 
                                  interval: str = "1d") -> pd.DataFrame:
        """
        Fetch historical data for technical analysis
        
        Args:
            symbol: Stock symbol
            period: Time period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: Data interval (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            DataFrame with OHLCV data
        """
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                raise Exception(f"No historical data available for {symbol}")
            
            # Validate data freshness for the most recent point
            latest_timestamp = hist.index[-1].to_pydatetime()
            # Ensure timezone-naive comparison
            if latest_timestamp.tzinfo is not None:
                latest_timestamp = latest_timestamp.replace(tzinfo=None)
            
            current_time = datetime.now()
            age_seconds = (current_time - latest_timestamp).total_seconds()
            
            # For historical data, we're more lenient but still enforce reasonable freshness
            max_age = 86400  # 24 hours for daily data
            if interval in ['1m', '2m', '5m']:
                max_age = 3600  # 1 hour for minute data
            elif interval in ['15m', '30m', '60m']:
                max_age = 7200  # 2 hours for sub-hourly data
            
            if age_seconds > max_age:
                logger.warning(f"Historical data for {symbol} may be stale (age: {age_seconds/3600:.1f} hours)")
            
            return hist
            
        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise
    
    async def fetch_fundamental_data(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamental data for a symbol
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with fundamental data
        """
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # Extract relevant fundamental data
            fundamental_data = {
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'peg_ratio': info.get('pegRatio', 0),
                'price_to_book': info.get('priceToBook', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'roe': info.get('returnOnEquity', 0),
                'profit_margin': info.get('profitMargins', 0),
                'revenue_growth': info.get('revenueGrowth', 0),
                'earnings_growth': info.get('earningsGrowth', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 1.0),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'timestamp': datetime.now()
            }
            
            return fundamental_data
            
        except Exception as e:
            logger.error(f"Error fetching fundamental data for {symbol}: {e}")
            return {}
    
    async def fetch_news_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch news sentiment data for a symbol
        Note: This is a placeholder - would integrate with actual news APIs
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with news sentiment data
        """
        try:
            # This would integrate with actual news APIs like NewsAPI, Benzinga, etc.
            # For now, return a structure showing what would be provided
            
            logger.warning(f"News sentiment fetching not fully implemented for {symbol}")
            
            return {
                'sentiment_score': 0.0,  # -1.0 to 1.0
                'article_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'sources': [],
                'timestamp': datetime.now(),
                'error': 'News sentiment API not fully implemented'
            }
            
        except Exception as e:
            logger.error(f"Error fetching news sentiment for {symbol}: {e}")
            return {'error': str(e)}
    
    async def fetch_social_sentiment(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch social media sentiment data for a symbol
        Note: This is a placeholder - would integrate with social media APIs
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Dictionary with social sentiment data
        """
        try:
            # This would integrate with Reddit, Twitter, Discord APIs, etc.
            # For now, return a structure showing what would be provided
            
            logger.warning(f"Social sentiment fetching not fully implemented for {symbol}")
            
            return {
                'sentiment_score': 0.0,  # -1.0 to 1.0
                'mention_count': 0,
                'positive_mentions': 0,
                'negative_mentions': 0,
                'neutral_mentions': 0,
                'platforms': [],
                'timestamp': datetime.now(),
                'error': 'Social sentiment API not fully implemented'
            }
            
        except Exception as e:
            logger.error(f"Error fetching social sentiment for {symbol}: {e}")
            return {'error': str(e)}
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get current connection status for all providers"""
        status = {}
        
        for source in DataSource:
            status[source.value] = {
                'healthy': self.connection_monitor.is_healthy(source),
                'error_count': self.connection_monitor.error_counts.get(source, 0),
                'last_success': self.connection_monitor.last_success.get(source),
                'can_retry': self.connection_monitor.can_retry(source),
                'recovery_attempts': self.connection_monitor.recovery_attempts.get(source, 0)
            }
        
        return status
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check"""
        health_status = {
            'overall_health': 'healthy',
            'timestamp': datetime.now(),
            'providers': {},
            'issues': []
        }
        
        # Test each provider with a simple request
        test_symbol = 'AAPL'
        healthy_providers = 0
        
        for source in [DataSource.YAHOO_FINANCE, DataSource.ALPHA_VANTAGE, DataSource.IEX_CLOUD]:
            try:
                if source == DataSource.YAHOO_FINANCE:
                    test_data = await self._fetch_yahoo_finance_data([test_symbol])
                elif source == DataSource.ALPHA_VANTAGE:
                    test_data = await self._fetch_alpha_vantage_data([test_symbol])
                elif source == DataSource.IEX_CLOUD:
                    test_data = await self._fetch_iex_cloud_data([test_symbol])
                
                if test_symbol in test_data:
                    health_status['providers'][source.value] = 'healthy'
                    healthy_providers += 1
                else:
                    health_status['providers'][source.value] = 'unhealthy'
                    health_status['issues'].append(f"{source.value}: No data returned")
                    
            except Exception as e:
                health_status['providers'][source.value] = 'error'
                health_status['issues'].append(f"{source.value}: {str(e)}")
        
        # Determine overall health
        if healthy_providers == 0:
            health_status['overall_health'] = 'critical'
        elif healthy_providers == 1:
            health_status['overall_health'] = 'degraded'
        
        return health_status


# Singleton instance for global use
live_market_data_manager = None

def get_live_market_data_manager() -> LiveMarketDataManager:
    """Get singleton instance of live market data manager"""
    global live_market_data_manager
    if live_market_data_manager is None:
        live_market_data_manager = LiveMarketDataManager()
    return live_market_data_manager