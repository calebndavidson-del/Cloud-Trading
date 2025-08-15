#!/bin/bash

# Local development setup script for Cloud Trading Bot

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Setup local development environment
setup_local() {
    log_info "Setting up local development environment..."
    
    # Install Python dependencies
    log_info "Installing Python dependencies..."
    if [ -f requirements.txt ]; then
        pip install -r requirements.txt
    else
        log_warn "requirements.txt not found. Skipping Python dependency installation."
    fi
    
    # Create .env file if it doesn't exist
    if [ ! -f .env ]; then
        log_info "Creating .env file..."
        cat > .env << EOF
# Cloud Trading Bot Configuration
ENVIRONMENT=development
PYTHONPATH=.

# API Keys (add your actual keys here)
# ALPHA_VANTAGE_API_KEY=your_key_here
# IEX_CLOUD_API_KEY=your_key_here
# YAHOO_API_KEY=not_required

# Google Cloud (for deployment)
# GOOGLE_CLOUD_PROJECT=your-project-id
# GOOGLE_CLOUD_REGION=us-central1
EOF
        log_warn "Please edit .env file and add your API keys"
    fi
    
    log_info "Local setup complete!"
}

# Test local setup
test_local() {
    log_info "Testing local setup..."
    
    # Test Python imports
    python -c "
import sys
sys.path.append('.')
from backend.config import get_config
from backend.bot import run_bot
print('✓ Backend imports successful')
"
    
    log_info "Local testing complete!"
}

# Run local development server
run_local() {
    log_info "Starting local development server..."
    log_info "Dashboard will be available at: http://localhost:8080"
    log_info "API endpoints will be available at: http://localhost:8080/api/"
    log_info "Press Ctrl+C to stop the server"
    
    export ENVIRONMENT=development
    export PYTHONPATH=.
    if [ ! -f api.py ]; then
        log_warn "api.py not found. Cannot start local development server."
        exit 1
    fi
    python api.py
}

# Main function
case "${1:-setup}" in
    "setup")
        setup_local
        ;;
    "test")
        test_local
        ;;
    "run")
        run_local
        ;;
    *)
        echo "Usage: $0 [setup|test|run]"
        echo ""
        echo "Commands:"
        echo "  setup - Setup local development environment (default)"
        echo "  test  - Test local setup"
        echo "  run   - Run local development server"
        exit 1
        ;;
esac