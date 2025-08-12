#!/bin/bash

# Cloud Trading Bot - Quick Deployment Script
# This script provides an interactive deployment experience with clear guidance
# Usage: ./quick_deploy.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local missing_tools=()
    
    # Check required tools
    if ! command -v aws &> /dev/null; then
        missing_tools+=("AWS CLI")
    fi
    
    if ! command -v terraform &> /dev/null; then
        missing_tools+=("Terraform")
    fi
    
    if ! command -v docker &> /dev/null; then
        missing_tools+=("Docker")
    fi
    
    if ! command -v python &> /dev/null; then
        missing_tools+=("Python")
    fi
    
    if ! command -v pip &> /dev/null; then
        missing_tools+=("pip")
    fi
    
    if ! command -v zip &> /dev/null; then
        missing_tools+=("zip utility")
    fi
    
    if [ ${#missing_tools[@]} -eq 0 ]; then
        print_success "All required tools are installed"
    else
        print_error "Missing required tools: ${missing_tools[*]}"
        echo ""
        echo "Please install the missing tools:"
        echo "- AWS CLI: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html"
        echo "- Terraform: https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli"
        echo "- Docker: https://docs.docker.com/get-docker/"
        echo "- Python: https://www.python.org/downloads/"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        print_error "AWS credentials not configured"
        echo ""
        echo "Please configure AWS credentials:"
        echo "1. Run: aws configure"
        echo "2. Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
        echo "3. Or use AWS profiles: export AWS_PROFILE=your-profile"
        exit 1
    else
        print_success "AWS credentials configured"
        local account_id=$(aws sts get-caller-identity --query Account --output text)
        local region=$(aws configure get region || echo "us-west-2")
        print_info "Account: $account_id, Region: $region"
    fi
}

# Function to display deployment options
show_deployment_options() {
    print_header "Deployment Options"
    
    echo "Choose your deployment method:"
    echo ""
    echo "1. 🚀 Full Automated Deployment (Recommended)"
    echo "   - Deploys complete infrastructure"
    echo "   - Creates Lambda package automatically"
    echo "   - Sets up all AWS services"
    echo ""
    echo "2. 📦 Lambda Package Only"
    echo "   - Creates optimized Lambda deployment package"
    echo "   - For manual upload or testing"
    echo ""
    echo "3. ⚙️  Infrastructure Only"
    echo "   - Deploys Terraform infrastructure"
    echo "   - Requires manual Lambda package upload"
    echo ""
    echo "4. 📚 View Documentation"
    echo "   - Show detailed deployment instructions"
    echo ""
    echo "5. 🧪 Test Current Setup"
    echo "   - Validate configuration and test package creation"
    echo ""
    
    read -p "Enter your choice (1-5): " choice
    echo ""
    
    case $choice in
        1) full_deployment ;;
        2) lambda_package_only ;;
        3) infrastructure_only ;;
        4) view_documentation ;;
        5) test_setup ;;
        *) print_error "Invalid choice. Please run the script again."; exit 1 ;;
    esac
}

# Function for full deployment
full_deployment() {
    print_header "Full Automated Deployment"
    
    print_info "This will deploy the complete Cloud Trading Bot infrastructure"
    print_warning "This may incur AWS charges. Continue only if you understand the costs."
    echo ""
    
    read -p "Continue with full deployment? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
    
    echo ""
    print_info "Starting full deployment..."
    
    # Run the main deployment script
    if ./scripts/deploy.sh; then
        print_success "Deployment completed successfully!"
        show_next_steps
    else
        print_error "Deployment failed. Check the output above for details."
        exit 1
    fi
}

# Function for Lambda package only
lambda_package_only() {
    print_header "Creating Lambda Package"
    
    read -p "Enter output filename (default: lambda_deployment.zip): " filename
    filename=${filename:-lambda_deployment.zip}
    
    print_info "Creating Lambda package: $filename"
    
    if ./scripts/package_lambda.sh "$filename"; then
        print_success "Lambda package created: $filename"
        echo ""
        print_info "Next steps:"
        echo "1. Upload to S3: ./scripts/upload_lambda_to_s3.sh $filename <bucket> <key>"
        echo "2. Deploy infrastructure: ./scripts/deploy.sh"
    else
        print_error "Failed to create Lambda package"
        exit 1
    fi
}

# Function for infrastructure only
infrastructure_only() {
    print_header "Infrastructure Deployment"
    
    print_warning "This will deploy infrastructure without Lambda code."
    print_info "You'll need to upload Lambda package separately."
    echo ""
    
    read -p "Continue? (y/N): " confirm
    if [[ ! $confirm =~ ^[Yy]$ ]]; then
        print_info "Deployment cancelled"
        exit 0
    fi
    
    cd infrastructure/terraform
    
    print_info "Initializing Terraform..."
    terraform init
    
    print_info "Planning deployment..."
    terraform plan -out=tfplan
    
    print_info "Applying infrastructure..."
    if terraform apply tfplan; then
        print_success "Infrastructure deployed successfully!"
        echo ""
        print_info "To complete deployment:"
        echo "1. Create Lambda package: ../scripts/package_lambda.sh"
        echo "2. Upload to S3: ../scripts/upload_lambda_to_s3.sh lambda_deployment.zip \$(terraform output -raw lambda_deployment_bucket) \$(terraform output -raw lambda_s3_key)"
        echo "3. Update Lambda: terraform apply -auto-approve"
    else
        print_error "Infrastructure deployment failed"
        exit 1
    fi
}

# Function to view documentation
view_documentation() {
    print_header "Documentation"
    
    echo "Available documentation:"
    echo ""
    echo "1. README.md - Complete project documentation"
    echo "2. LAMBDA_S3_DEPLOYMENT.md - Detailed Lambda deployment guide"
    echo "3. infrastructure/terraform-iam-policy.json - Required IAM permissions"
    echo ""
    
    read -p "Which document would you like to view? (1-3): " doc_choice
    
    case $doc_choice in
        1) 
            if command -v less &> /dev/null; then
                less README.md
            else
                cat README.md
            fi
            ;;
        2) 
            if command -v less &> /dev/null; then
                less LAMBDA_S3_DEPLOYMENT.md
            else
                cat LAMBDA_S3_DEPLOYMENT.md
            fi
            ;;
        3) 
            if command -v less &> /dev/null; then
                less infrastructure/terraform-iam-policy.json
            else
                cat infrastructure/terraform-iam-policy.json
            fi
            ;;
        *) print_error "Invalid choice" ;;
    esac
}

# Function to test setup
test_setup() {
    print_header "Testing Current Setup"
    
    print_info "Testing Lambda package creation..."
    if ./scripts/test_package_lambda.sh test_output.zip; then
        print_success "Package creation test passed"
        
        # Show package contents
        echo ""
        print_info "Package contents preview:"
        unzip -l test_output.zip | head -10
        
        # Clean up test file
        rm -f test_output.zip
    else
        print_error "Package creation test failed"
    fi
    
    print_info "Testing Terraform configuration..."
    cd infrastructure/terraform
    if terraform validate; then
        print_success "Terraform configuration is valid"
    else
        print_error "Terraform configuration has errors"
    fi
    cd ../..
    
    print_info "Testing AWS connectivity..."
    if aws sts get-caller-identity > /dev/null; then
        print_success "AWS connectivity test passed"
    else
        print_error "AWS connectivity test failed"
    fi
}

# Function to show next steps
show_next_steps() {
    print_header "Next Steps"
    
    echo "Your Cloud Trading Bot has been deployed! Here's what to do next:"
    echo ""
    echo "1. 🔑 Configure API Keys:"
    echo "   - Update secrets in AWS Secrets Manager"
    echo "   - Get the secret ARN from Terraform outputs"
    echo ""
    echo "2. 📊 Monitor the System:"
    echo "   - Check CloudWatch logs for Lambda and ECS"
    echo "   - View DynamoDB tables for trading data"
    echo "   - Monitor S3 buckets for logs"
    echo ""
    echo "3. 🧪 Test the Lambda Function:"
    echo "   - Use AWS Console to test the market data fetcher"
    echo "   - Check the function logs for any errors"
    echo ""
    echo "4. 💰 Cost Monitoring:"
    echo "   - Set up billing alerts in AWS"
    echo "   - Monitor usage in AWS Cost Explorer"
    echo ""
    
    print_info "Estimated monthly cost: \$50-170 (varies by usage)"
    print_warning "Remember to use paper trading mode for testing!"
}

# Main execution
main() {
    clear
    print_header "Cloud Trading Bot - Quick Deployment"
    echo ""
    echo "Welcome to the Cloud Trading Bot deployment assistant!"
    echo "This script will guide you through the deployment process."
    echo ""
    
    check_prerequisites
    echo ""
    show_deployment_options
}

# Run main function
main "$@"