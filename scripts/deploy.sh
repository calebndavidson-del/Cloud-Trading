#!/bin/bash

# AWS Trading Bot Deployment Script
# This script deploys the complete AWS infrastructure using Terraform

set -e  # Exit on any error

# Configuration
PROJECT_NAME="cloud-trading-bot"
AWS_REGION="${AWS_REGION:-us-east-1}"
ENVIRONMENT="${ENVIRONMENT:-prod}"

echo "🚀 Starting AWS Trading Bot Deployment"
echo "Project: $PROJECT_NAME"
echo "Region: $AWS_REGION"
echo "Environment: $ENVIRONMENT"
echo ""

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check if AWS CLI is installed and configured
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install it first."
    exit 1
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Please run 'aws configure' first."
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Create Lambda deployment package
echo "📦 Creating Lambda deployment package..."
cd "$(dirname "$0")/.."

# Create temporary directory for Lambda package
rm -rf /tmp/lambda_package
mkdir -p /tmp/lambda_package

# Copy backend modules
cp -r backend /tmp/lambda_package/
cp -r aws /tmp/lambda_package/

# Copy requirements for Lambda
cat > /tmp/lambda_package/requirements.txt << EOF
yfinance
requests
boto3
numpy
pandas
EOF

# Install dependencies
cd /tmp/lambda_package
pip install -r requirements.txt -t .

# Create zip file
zip -r lambda_deployment.zip . -x "*.pyc" "*/__pycache__/*"

# Move zip to terraform directory
mv lambda_deployment.zip "$(dirname "$0")/../infrastructure/terraform/"

cd "$(dirname "$0")/.."
echo "✅ Lambda package created"
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
terraform output -json > terraform_outputs.json

echo ""
echo "✅ Infrastructure deployment completed"
echo ""

# Build and push Docker image to ECR
echo "🐳 Building and pushing Docker image..."

# Get ECR repository URL from Terraform output
ECR_REPO_URL=$(terraform output -raw ecr_repository_url)

if [ -n "$ECR_REPO_URL" ]; then
    echo "ECR Repository: $ECR_REPO_URL"
    
    # Login to ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URL
    
    # Build Docker image
    cd ../..
    docker build -f infrastructure/docker/Dockerfile -t $PROJECT_NAME-strategy .
    
    # Tag and push image
    docker tag $PROJECT_NAME-strategy:latest $ECR_REPO_URL:latest
    docker push $ECR_REPO_URL:latest
    
    echo "✅ Docker image pushed to ECR"
else
    echo "⚠️  ECR repository URL not found in Terraform outputs"
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

cd infrastructure/terraform