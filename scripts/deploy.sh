#!/bin/bash

# AWS Trading Bot Deployment Script
# This script deploys the complete AWS infrastructure using Terraform

set -e  # Exit on any error

# Function to print error and exit
function error_exit() {
    echo "❌ $1"
    exit 1
}

# Configuration
PROJECT_NAME="cloud-trading-bot"
AWS_REGION="${AWS_REGION:-us-west-2}"
ENVIRONMENT="${ENVIRONMENT:-prod}"

echo "🚀 Starting AWS Trading Bot Deployment"
echo "Project: $PROJECT_NAME"
echo "Region: $AWS_REGION"
echo "Environment: $ENVIRONMENT"
echo ""

# Save original directory
ORIGINAL_DIR="$(pwd)"

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    error_exit "AWS CLI is not installed. Please install it first."
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    error_exit "Terraform is not installed. Please install it first."
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    error_exit "Docker is not installed. Please install it first."
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    error_exit "pip is not installed. Please install it first."
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    error_exit "AWS credentials not configured. Please run 'aws configure' first."
fi

echo "✅ Prerequisites check passed"
echo ""

# Create Lambda deployment package
echo "📦 Creating Lambda deployment package..."
cd "$(dirname "$0")/.."

# Check for backend and aws directories
if [ ! -d "backend" ]; then
    error_exit "'backend' directory not found in project root."
fi
if [ ! -d "aws" ]; then
    error_exit "'aws' directory not found in project root."
fi

# Check for infrastructure/terraform directory
if [ ! -d "infrastructure/terraform" ]; then
    error_exit "'infrastructure/terraform' directory not found."
fi

# Create temporary directory for Lambda package
rm -rf /tmp/lambda_package
mkdir -p /tmp/lambda_package

# Copy backend modules
cp -r backend /tmp/lambda_package/
cp -r aws /tmp/lambda_package/

# Use optimized requirements for Lambda
cp aws/lambda_requirements.txt /tmp/lambda_package/requirements.txt

# Install dependencies
cd /tmp/lambda_package
pip install -r requirements.txt -t . || error_exit "pip install failed."

# Check for zip utility
if ! command -v zip &> /dev/null; then
    error_exit "zip utility is not installed. Please install it first."
fi

# Create zip file
echo "Creating Lambda deployment package..."
zip -r lambda_deployment.zip . -x "*.pyc" "*/__pycache__/*" "*.git*" "*.DS_Store"

# Get package size
PACKAGE_SIZE=$(du -sh lambda_deployment.zip | cut -f1)
echo "Lambda package size: $PACKAGE_SIZE"

# Move zip to terraform directory
mv lambda_deployment.zip "$ORIGINAL_DIR/infrastructure/terraform/"

cd "$ORIGINAL_DIR"
echo "✅ Lambda package created and ready for S3 deployment"
echo ""

# Optionally build Lambda layer for heavy dependencies
read -p "Do you want to build the Lambda layer for heavy dependencies (pandas, numpy, etc.)? [y/N]: " build_layer
if [[ $build_layer =~ ^[Yy]$ ]]; then
    echo "🏗️  Building Lambda layer..."
    ./scripts/build_layer.sh
else
    echo "⏭️  Skipping Lambda layer build"
fi
echo ""

# Deploy infrastructure with Terraform
echo "🏗️  Deploying infrastructure with Terraform..."
cd infrastructure/terraform

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Plan deployment
echo "Planning Terraform deployment..."
terraform plan \
    -var="aws_region=$AWS_REGION" \
    -var="environment=$ENVIRONMENT" \
    -var="project_name=$PROJECT_NAME" \
    -out=tfplan

# Apply deployment
echo "Applying Terraform deployment..."
terraform apply tfplan

# Get outputs
echo ""
echo "📊 Deployment outputs:"
terraform output

# Store outputs for later use
if ! terraform output -json > terraform_outputs.json; then
    error_exit "Failed to write terraform_outputs.json"
fi

echo ""
echo "✅ Infrastructure deployment completed"
echo ""

# Build and push Docker image to ECR
echo "🐳 Building and pushing Docker image..."

# Get ECR repository URL from Terraform output
ECR_REPO_URL=$(terraform output -raw ecr_repository_url 2>/dev/null || true)

if [ -n "$ECR_REPO_URL" ]; then
    echo "ECR Repository: $ECR_REPO_URL"
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URL
    
    # Build Docker image
    cd "$ORIGINAL_DIR"
    if [ ! -f "infrastructure/docker/Dockerfile" ]; then
        error_exit "'infrastructure/docker/Dockerfile' not found."
    fi
    docker build -f infrastructure/docker/Dockerfile -t $PROJECT_NAME-strategy .
    
    # Tag and push image
    docker tag $PROJECT_NAME-strategy:latest $ECR_REPO_URL:latest
    docker push $ECR_REPO_URL:latest
    
    echo "✅ Docker image pushed to ECR"
else
    echo "⚠️  ECR repository URL not found in Terraform outputs. Skipping Docker build and push."
fi

echo ""
echo "🎉 Deployment completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Update API keys in AWS Secrets Manager"
echo "2. Monitor CloudWatch logs for Lambda and ECS"
echo "3. Check DynamoDB tables for trading data"
echo "4. Review S3 buckets for logs and data"
echo ""
echo "🔧 Useful commands:"
echo "- View Lambda logs: aws logs tail /aws/lambda/$PROJECT_NAME-market-data-fetcher --follow"
echo "- View ECS logs: aws logs tail /aws/ecs/$PROJECT_NAME-strategy --follow"
echo "- Update ECS service: aws ecs update-service --cluster $PROJECT_NAME-cluster --service $PROJECT_NAME-strategy-service --desired-count 1"
echo ""

# Restore original directory
cd "$ORIGINAL_DIR"
