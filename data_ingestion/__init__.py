"""
Data Ingestion Module

This module provides specialized data collectors for various financial data sources
including market data, news, earnings, regulatory filings, and alternative datasets.
Each collector is designed to be cloud-deployable and supports various data providers.
"""

from .market import MarketDataCollector
from .news import NewsDataCollector
from .earnings import EarningsDataCollector
from .filings import FilingsDataCollector
from .order_book import OrderBookDataCollector
from .social import SocialDataCollector
from .options import OptionsDataCollector
from .macro import MacroDataCollector
from .short_interest import ShortInterestDataCollector
from .etf_flows import ETFFlowDataCollector

__all__ = [
    'MarketDataCollector',
    'NewsDataCollector', 
    'EarningsDataCollector',
    'FilingsDataCollector',
    'OrderBookDataCollector',
    'SocialDataCollector',
    'OptionsDataCollector',
    'MacroDataCollector',
    'ShortInterestDataCollector',
    'ETFFlowDataCollector'
]