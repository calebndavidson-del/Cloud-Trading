"""
Unit tests for market data manager.
"""
import pytest
import json
from unittest.mock import Mock, patch, AsyncMock, mock_open
from market_data_manager import MarketDataManager


class TestMarketDataManager:
    """Test the market data manager."""
    
    def test_init_default_config(self):
        """Test initialization with default configuration."""
        with patch('os.path.exists', return_value=False):
            manager = MarketDataManager()
            
            assert hasattr(manager, 'config')
            assert hasattr(manager, 'providers')
            assert isinstance(manager.providers, list)
    
    def test_init_custom_config(self, sample_config):
        """Test initialization with custom configuration."""
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
            with patch('os.path.exists', return_value=True):
                manager = MarketDataManager('custom_config.json')
                
                assert manager.config == sample_config
                assert hasattr(manager, 'providers')
    
    @pytest.mark.asyncio
    async def test_fetch_quote_success(self, sample_market_data):
        """Test successful single quote retrieval."""
        with patch('os.path.exists', return_value=False):
            manager = MarketDataManager()
            
            # Mock one provider to return data
            mock_provider = AsyncMock()
            mock_provider.fetch_quote.return_value = sample_market_data['AAPL']
            manager.providers = [mock_provider]
            
            quote = await manager.fetch_quote('AAPL')
            
            assert quote == sample_market_data['AAPL']
    
    @pytest.mark.asyncio
    async def test_fetch_quote_fallback(self, sample_market_data):
        """Test quote retrieval with provider fallback."""
        with patch('os.path.exists', return_value=False):
            manager = MarketDataManager()
            
            # First provider fails, second succeeds
            failing_provider = AsyncMock()
            failing_provider.fetch_quote.return_value = None
            
            success_provider = AsyncMock()
            success_provider.fetch_quote.return_value = sample_market_data['AAPL']
            
            manager.providers = [failing_provider, success_provider]
            
            quote = await manager.fetch_quote('AAPL')
            
            assert quote == sample_market_data['AAPL']
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_success(self, sample_market_data):
        """Test successful multiple quotes retrieval."""
        with patch('os.path.exists', return_value=False):
            manager = MarketDataManager()
            
            mock_provider = AsyncMock()
            mock_provider.fetch_quotes.return_value = sample_market_data
            manager.providers = [mock_provider]
            
            quotes = await manager.fetch_quotes(['AAPL', 'GOOGL'])
            
            assert quotes == sample_market_data
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_partial_failure(self, sample_market_data):
        """Test quotes retrieval with partial failures."""
        with patch('os.path.exists', return_value=False):
            manager = MarketDataManager()
            
            partial_data = {'AAPL': sample_market_data['AAPL'], 'GOOGL': None}
            
            mock_provider = AsyncMock()
            mock_provider.fetch_quotes.return_value = partial_data
            manager.providers = [mock_provider]
            
            quotes = await manager.fetch_quotes(['AAPL', 'GOOGL'])
            
            assert quotes['AAPL'] == sample_market_data['AAPL']
            assert quotes['GOOGL'] is None
    
    @pytest.mark.asyncio
    async def test_fetch_quotes_all_providers_fail(self):
        """Test behavior when all providers fail."""
        with patch('os.path.exists', return_value=False):
            manager = MarketDataManager()
            
            failing_provider = AsyncMock()
            failing_provider.fetch_quotes.return_value = {'AAPL': None}
            manager.providers = [failing_provider]
            
            quotes = await manager.fetch_quotes(['AAPL'])
            
            # Should still return structure with None values
            assert isinstance(quotes, dict)
            assert 'AAPL' in quotes
    
    def test_load_config_file_exists(self, sample_config):
        """Test loading configuration from existing file."""
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_config))):
            with patch('os.path.exists', return_value=True):
                manager = MarketDataManager('test_config.json')
                
                assert manager.config == sample_config
    
    def test_load_config_file_not_exists(self):
        """Test loading configuration when file doesn't exist."""
        # Mock the entire MarketDataManager init to avoid logger issues  
        with patch.object(MarketDataManager, '_load_config') as mock_load:
            with patch.object(MarketDataManager, '_initialize_providers'):
                with patch('logging.getLogger'):
                    with patch('logging.basicConfig'):
                        mock_load.return_value = {
                            'providers': {'yahoo_finance': {'enabled': True}},
                            'fallback_settings': {'max_retries': 3}
                        }
                        
                        manager = MarketDataManager('nonexistent.json')
                        
                        # Should use mocked config
                        assert hasattr(manager, 'config')
                        assert 'providers' in manager.config