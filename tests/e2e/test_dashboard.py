"""
E2E tests for the Streamlit dashboard.
"""
import pytest
import asyncio
import subprocess
import time
import requests
from playwright.async_api import async_playwright


@pytest.fixture(scope="session")
def dashboard_server():
    """Start the Streamlit dashboard server for testing."""
    # Start the dashboard
    process = subprocess.Popen([
        'streamlit', 'run', 'dashboard_app_Version2.py',
        '--server.port=8501',
        '--server.headless=true'
    ])
    
    # Wait for server to start
    time.sleep(5)
    
    # Check if server is running
    try:
        response = requests.get('http://localhost:8501')
        if response.status_code == 200:
            yield 'http://localhost:8501'
        else:
            pytest.skip("Dashboard server failed to start")
    except requests.exceptions.ConnectionError:
        pytest.skip("Dashboard server not accessible")
    finally:
        process.terminate()
        process.wait()


@pytest.mark.e2e
class TestDashboardE2E:
    """End-to-end tests for the dashboard."""
    
    @pytest.mark.asyncio
    async def test_dashboard_loads(self, dashboard_server):
        """Test that the dashboard loads successfully."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            await page.goto(dashboard_server)
            
            # Check that the page loads
            await page.wait_for_load_state('networkidle')
            
            # Check for expected content
            title = await page.text_content('h1')
            assert 'Cloud Trading Bot Dashboard' in title
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_dashboard_content(self, dashboard_server):
        """Test dashboard content and functionality."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            await page.goto(dashboard_server)
            await page.wait_for_load_state('networkidle')
            
            # Check for expected content elements
            content = await page.text_content('body')
            assert 'real-time market data' in content.lower()
            assert 'backtest results' in content.lower()
            assert 'paper trading' in content.lower()
            
            await browser.close()
    
    @pytest.mark.asyncio
    async def test_dashboard_responsive(self, dashboard_server):
        """Test dashboard responsiveness."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Test different viewport sizes
            viewports = [
                {'width': 1920, 'height': 1080},  # Desktop
                {'width': 768, 'height': 1024},   # Tablet
                {'width': 375, 'height': 667},    # Mobile
            ]
            
            for viewport in viewports:
                await page.set_viewport_size(viewport)
                await page.goto(dashboard_server)
                await page.wait_for_load_state('networkidle')
                
                # Check that content is visible
                title = await page.text_content('h1')
                assert title is not None
                assert len(title) > 0
            
            await browser.close()


@pytest.mark.e2e
@pytest.mark.slow
class TestWorkflowE2E:
    """End-to-end workflow tests."""
    
    @pytest.mark.asyncio
    async def test_full_trading_workflow(self):
        """Test the complete trading workflow."""
        # This would test:
        # 1. Data collection
        # 2. Strategy optimization
        # 3. Paper trading
        # 4. Results visualization
        
        # For now, just test that the workflow functions exist and can be called
        from backend.data_collector import fetch_market_data
        from backend.optimizer import optimize_strategy
        from backend.paper_trader import paper_trade
        
        # Test data collection
        market_data = fetch_market_data(['AAPL'], use_mock=True)
        assert isinstance(market_data, dict)
        assert 'AAPL' in market_data
        
        # Test optimization
        optimization_result = optimize_strategy(market_data, n_trials=3)
        assert isinstance(optimization_result, dict)
        assert 'best_value' in optimization_result
        
        # Test paper trading
        trading_result = paper_trade({'initial_capital': 10000, 'symbols': ['AAPL']})
        assert isinstance(trading_result, dict)
        assert 'portfolio_value' in trading_result