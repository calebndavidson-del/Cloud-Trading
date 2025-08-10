#!/bin/bash

# Local Development Setup Script
# This script sets up the trading bot for local development

set -e

echo "🛠️  Setting up Cloud Trading Bot for local development"
echo ""

# Create Python virtual environment
echo "📦 Setting up Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install -r requirements_Version9.txt
pip install boto3 watchtower python-dotenv

echo "✅ Dependencies installed"
echo ""

# Create local environment file
if [ ! -f .env ]; then
    echo "📝 Creating local environment file..."
    cp examples/.env.local .env
    echo "✅ Created .env file. Please update it with your configuration."
else
    echo "ℹ️  .env file already exists"
fi

echo ""

# Test local setup
echo "🧪 Testing local setup..."
source .env

export PYTHONPATH="$(pwd)"
python backend/bot.py

echo ""
echo "✅ Local setup completed successfully!"
echo ""
echo "📝 Next steps for local development:"
echo "1. Update .env file with your API keys"
echo "2. Install LocalStack for local AWS services testing:"
echo "   pip install localstack"
echo "   localstack start"
echo "3. Run the bot locally:"
echo "   source venv/bin/activate"
echo "   source .env"
echo "   export PYTHONPATH=\$(pwd)"
echo "   python backend/bot.py"
echo ""
echo "4. Test individual components:"
echo "   python -c 'from backend.data_collector import fetch_market_data; print(fetch_market_data())'"
echo "   python -c 'from backend.paper_trader import paper_trade; print(paper_trade({}))'"
echo ""
echo "5. Run the Lambda function locally:"
echo "   python aws/lambda_market_data.py"
echo ""
echo "6. Test the strategy engine locally:"
echo "   python aws/strategy_engine.py"
echo ""

# Create test script
cat > test_local.py << 'EOF'
#!/usr/bin/env python3
"""
Local testing script for the trading bot.
"""
import os
import sys

# Add current directory to Python path
sys.path.append(os.getcwd())

def test_data_collection():
    """Test market data collection."""
    print("Testing market data collection...")
    from backend.data_collector import fetch_market_data, fetch_market_trends
    
    data = fetch_market_data(['AAPL', 'GOOGL'])
    print(f"Market data: {len(data)} symbols fetched")
    
    trends = fetch_market_trends()
    print(f"Market trends: {trends}")
    print("✅ Data collection test passed\n")

def test_paper_trading():
    """Test paper trading."""
    print("Testing paper trading...")
    from backend.paper_trader import paper_trade
    
    result = paper_trade({
        'initial_capital': 10000,
        'symbols': ['AAPL', 'GOOGL']
    })
    
    print(f"Paper trading result: {result.get('portfolio_value', 'N/A')}")
    print("✅ Paper trading test passed\n")

def test_strategy_optimization():
    """Test strategy optimization."""
    print("Testing strategy optimization...")
    from backend.optimizer import optimize_strategy
    from backend.data_collector import fetch_market_data
    
    market_data = fetch_market_data(['AAPL'])
    result = optimize_strategy(market_data, n_trials=10)
    
    print(f"Optimization result: {result.get('best_value', 'N/A')}")
    print("✅ Strategy optimization test passed\n")

if __name__ == "__main__":
    print("🧪 Running local tests...\n")
    
    # Set mock data for testing
    os.environ['USE_MOCK_DATA'] = 'true'
    
    test_data_collection()
    test_paper_trading()
    test_strategy_optimization()
    
    print("🎉 All local tests passed!")
EOF

chmod +x test_local.py

echo "📋 Created test_local.py for testing components locally"
echo "   Run: python test_local.py"
echo ""