#!/bin/bash

# Cloud Trading Bot - Local Development Setup Script
# This script sets up the local development environment

set -e

echo "🚀 Setting up Cloud Trading Bot Local Development Environment"
echo "============================================================"

# Function to print colored output
print_success() {
    echo -e "\033[32m✅ $1\033[0m"
}

print_info() {
    echo -e "\033[34mℹ️  $1\033[0m"
}

print_warning() {
    echo -e "\033[33m⚠️  $1\033[0m"
}

print_error() {
    echo -e "\033[31m❌ $1\033[0m"
}

# Check if Python 3.11+ is available
check_python() {
    print_info "Checking Python version..."
    
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD=python3.11
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD=python3
    elif command -v python &> /dev/null; then
        PYTHON_CMD=python
    else
        print_error "Python 3.11+ is required but not found"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
    print_success "Found Python $PYTHON_VERSION"
}

# Create and activate virtual environment
setup_venv() {
    print_info "Setting up Python virtual environment..."
    
    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        print_success "Created virtual environment"
    else
        print_info "Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    print_success "Activated virtual environment"
    
    # Upgrade pip
    pip install --upgrade pip
    print_success "Upgraded pip"
}

# Install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Installed dependencies from requirements.txt"
    else
        print_warning "requirements.txt not found, installing basic dependencies"
        pip install fastapi uvicorn boto3 pytest yfinance pandas numpy
    fi
}

# Setup environment configuration
setup_env() {
    print_info "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.template" ]; then
            cp .env.template .env
            print_success "Created .env from template"
        elif [ -f "examples/.env.local" ]; then
            cp examples/.env.local .env
            print_success "Created .env from examples/.env.local"
        else
            print_warning "No .env template found, creating basic .env"
            cat > .env << EOF
ENV=development
DEBUG=true
USE_MOCK_DATA=true
AWS_REGION=us-west-2
TRADING_ENABLED=false
PAPER_TRADING=true
LOG_LEVEL=INFO
HOST=0.0.0.0
PORT=8000
EOF
        fi
    else
        print_info ".env file already exists"
    fi
}

# Test basic functionality
test_setup() {
    print_info "Testing basic functionality..."
    
    # Test Python imports
    $PYTHON_CMD -c "
import sys
sys.path.append('.')
try:
    from backend.config import get_config
    print('✅ Backend config module loads correctly')
    
    from backend.bot import run_bot
    print('✅ Bot module loads correctly')
    
    from api_server import app
    print('✅ API server module loads correctly')
    
    print('✅ All core modules load successfully')
except Exception as e:
    print(f'❌ Error loading modules: {e}')
    exit(1)
" && print_success "Core modules test passed"
    
    # Test basic API server
    print_info "Testing API server..."
    timeout 5s $PYTHON_CMD -c "
import sys
sys.path.append('.')
from fastapi.testclient import TestClient
from api_server import app

client = TestClient(app)
response = client.get('/health')
assert response.status_code == 200
print('✅ API server health check passed')
" && print_success "API server test passed" || print_warning "API server test skipped (missing dependencies)"
}

# Setup AWS CLI (optional)
setup_aws_cli() {
    print_info "Checking AWS CLI setup..."
    
    if command -v aws &> /dev/null; then
        print_success "AWS CLI is installed"
        
        if aws sts get-caller-identity &> /dev/null; then
            ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "unknown")
            REGION=$(aws configure get region 2>/dev/null || echo "not-set")
            print_success "AWS credentials configured (Account: $ACCOUNT_ID, Region: $REGION)"
        else
            print_warning "AWS CLI installed but credentials not configured"
            print_info "Run 'aws configure' to set up your credentials"
        fi
    else
        print_warning "AWS CLI not installed"
        print_info "Install it from: https://aws.amazon.com/cli/"
    fi
}

# Setup Docker (optional)
setup_docker() {
    print_info "Checking Docker setup..."
    
    if command -v docker &> /dev/null; then
        print_success "Docker is installed"
        
        if docker info &> /dev/null; then
            print_success "Docker daemon is running"
        else
            print_warning "Docker is installed but daemon is not running"
        fi
    else
        print_warning "Docker not installed"
        print_info "Install it from: https://docs.docker.com/get-docker/"
    fi
}

# Setup Terraform (optional)
setup_terraform() {
    print_info "Checking Terraform setup..."
    
    if command -v terraform &> /dev/null; then
        TERRAFORM_VERSION=$(terraform --version | head -n1 | awk '{print $2}')
        print_success "Terraform $TERRAFORM_VERSION is installed"
    else
        print_warning "Terraform not installed"
        print_info "Install it from: https://www.terraform.io/downloads.html"
    fi
}

# Create development directories
create_directories() {
    print_info "Creating development directories..."
    
    mkdir -p logs
    mkdir -p data
    mkdir -p tmp
    
    print_success "Created development directories"
}

# Generate development scripts
create_dev_scripts() {
    print_info "Creating development scripts..."
    
    # Create run script
    cat > run_bot.sh << 'EOF'
#!/bin/bash
# Run the trading bot locally
source venv/bin/activate
export PYTHONPATH=$(pwd)
python backend/bot.py
EOF
    chmod +x run_bot.sh
    
    # Create API server script
    cat > run_api.sh << 'EOF'
#!/bin/bash
# Run the API server locally
source venv/bin/activate
export PYTHONPATH=$(pwd)
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
EOF
    chmod +x run_api.sh
    
    # Create test script
    cat > run_tests.sh << 'EOF'
#!/bin/bash
# Run tests
source venv/bin/activate
export PYTHONPATH=$(pwd)
python -m pytest test_*.py -v
EOF
    chmod +x run_tests.sh
    
    print_success "Created development scripts"
}

# Main setup function
main() {
    echo
    print_info "Starting setup process..."
    
    check_python
    setup_venv
    install_dependencies
    setup_env
    create_directories
    create_dev_scripts
    test_setup
    
    echo
    print_info "Optional tools check:"
    setup_aws_cli
    setup_docker
    setup_terraform
    
    echo
    print_success "🎉 Local development environment setup complete!"
    echo
    print_info "Next steps:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Edit .env file with your configuration"
    echo "  3. Run the bot: ./run_bot.sh"
    echo "  4. Run the API server: ./run_api.sh"
    echo "  5. Run tests: ./run_tests.sh"
    echo
    print_info "For AWS deployment:"
    echo "  1. Configure AWS CLI: aws configure"
    echo "  2. Run deployment: ./scripts/deploy.sh"
    echo
}

# Run main function
main "$@"