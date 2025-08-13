#!/bin/bash
# Local development setup script for Cloud Trading Bot

set -e

echo "🚀 Setting up Cloud Trading Bot for local development..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "✅ Python version: $python_version"

# Check Node.js version
if command -v node >/dev/null 2>&1; then
    node_version=$(node --version)
    echo "✅ Node.js version: $node_version"
else
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

# Create .env.local if it doesn't exist
if [ ! -f .env.local ]; then
    echo "📝 Creating .env.local from template..."
    cp .env.example .env.local
    echo "✅ Created .env.local - please edit with your API keys if needed"
else
    echo "✅ .env.local already exists"
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements_Version9.txt
pip install flask flask-cors gunicorn

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo "  Backend:  PYTHONPATH=\$(pwd) python api.py"
echo "  Frontend: cd frontend && npm start"
echo ""
echo "URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8080"
echo "  API Test: http://localhost:8080/api/status"
echo ""
echo "📚 See DEPLOYMENT.md for cloud deployment instructions"