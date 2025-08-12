#!/bin/bash

# Upload Lambda Package to S3
# This script uploads a Lambda deployment package to S3
# Usage: ./upload_lambda_to_s3.sh <lambda_zip_file> <s3_bucket> <s3_key> [aws_region]

set -e

# Function to print error and exit
function error_exit() {
    echo "❌ $1"
    exit 1
}

# Check arguments
if [ $# -lt 3 ]; then
    echo "Usage: $0 <lambda_zip_file> <s3_bucket> <s3_key> [aws_region]"
    echo ""
    echo "Arguments:"
    echo "  lambda_zip_file  Path to the Lambda deployment ZIP file"
    echo "  s3_bucket        S3 bucket name for Lambda packages"
    echo "  s3_key          S3 key/path for the Lambda package"
    echo "  aws_region      AWS region (optional, defaults to us-west-2)"
    echo ""
    echo "Example:"
    echo "  $0 lambda_deployment.zip my-lambda-bucket lambda/deployment.zip us-west-2"
    exit 1
fi

LAMBDA_ZIP_FILE="$1"
S3_BUCKET="$2"
S3_KEY="$3"
AWS_REGION="${4:-us-west-2}"

echo "🚀 Uploading Lambda package to S3"
echo "File: $LAMBDA_ZIP_FILE"
echo "Bucket: $S3_BUCKET"
echo "Key: $S3_KEY"
echo "Region: $AWS_REGION"
echo ""

# Check if the Lambda zip file exists
if [ ! -f "$LAMBDA_ZIP_FILE" ]; then
    error_exit "Lambda deployment file not found: $LAMBDA_ZIP_FILE"
fi

# Get file size for validation
FILE_SIZE=$(stat -c%s "$LAMBDA_ZIP_FILE")
FILE_SIZE_MB=$((FILE_SIZE / 1024 / 1024))

echo "📦 Package size: ${FILE_SIZE_MB}MB"

# AWS Lambda has a 250MB limit for S3-based deployment
if [ $FILE_SIZE_MB -gt 250 ]; then
    error_exit "Lambda package is too large (${FILE_SIZE_MB}MB). Maximum size is 250MB."
fi

# Check if AWS CLI is available
if ! command -v aws &> /dev/null; then
    error_exit "AWS CLI is not installed. Please install it first."
fi

# Verify AWS credentials
if ! aws sts get-caller-identity &> /dev/null; then
    error_exit "AWS credentials not configured. Please run 'aws configure' first."
fi

# Check if S3 bucket exists
echo "🔍 Checking if S3 bucket exists..."
if ! aws s3api head-bucket --bucket "$S3_BUCKET" --region "$AWS_REGION" 2>/dev/null; then
    echo "⚠️  S3 bucket '$S3_BUCKET' does not exist or is not accessible in region '$AWS_REGION'"
    echo "   Make sure you have:"
    echo "   1. Deployed the Terraform infrastructure first (./scripts/deploy.sh)"
    echo "   2. Correct AWS credentials and region"
    echo "   3. Proper IAM permissions for S3 access"
    exit 1
fi

# Upload the Lambda package to S3
echo "⬆️  Uploading Lambda package..."
if aws s3 cp "$LAMBDA_ZIP_FILE" "s3://$S3_BUCKET/$S3_KEY" \
    --region "$AWS_REGION" \
    --metadata "uploaded-by=cloud-trading-deploy,package-size=$FILE_SIZE"; then
    
    echo "✅ Lambda package uploaded successfully!"
    echo "   S3 URI: s3://$S3_BUCKET/$S3_KEY"
    
    # Verify the upload
    echo "🔍 Verifying upload..."
    UPLOADED_SIZE=$(aws s3api head-object --bucket "$S3_BUCKET" --key "$S3_KEY" --region "$AWS_REGION" --query 'ContentLength' --output text)
    
    if [ "$UPLOADED_SIZE" = "$FILE_SIZE" ]; then
        echo "✅ Upload verification successful (size: $UPLOADED_SIZE bytes)"
    else
        error_exit "Upload verification failed. Expected: $FILE_SIZE bytes, Got: $UPLOADED_SIZE bytes"
    fi
    
else
    error_exit "Failed to upload Lambda package to S3"
fi

echo ""
echo "🎉 Lambda package upload completed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. Update your Terraform Lambda function to reference the S3 object"
echo "2. Apply Terraform changes to deploy the updated Lambda function"
echo "3. Test the Lambda function to ensure it works correctly"