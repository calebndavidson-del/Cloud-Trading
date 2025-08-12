# Lambda S3 Deployment Guide for Cloud Trading Bot

This guide provides comprehensive instructions for packaging and deploying AWS Lambda functions using S3-based deployment for the Cloud Trading Bot.

## Single Bucket Architecture

**Important**: This project uses a single S3 bucket (`cloud-trading-bot-lambda-deployment-m6x4p8e`) for all storage needs:
- **Lambda deployment packages** (under `lambda/` prefix)
- **Application logs** (under `logs/` prefix)
- **Market data storage** (under `data/` prefix)

This consolidation simplifies management, reduces costs, and ensures consistent permissions across all S3 operations.

## Overview

S3-based Lambda deployment allows for larger package sizes (up to 250MB) compared to direct deployment (70MB limit). This is essential for Python applications with multiple dependencies like the Cloud Trading Bot.

## Prerequisites

- AWS CLI installed and configured
- Terraform installed (>= 1.0)
- Python 3.11+ with pip
- zip utility
- Appropriate IAM permissions (see [IAM Requirements](#iam-requirements))

## Quick Start

### Option 1: Automated Full Deployment
```bash
# Deploy everything automatically
./scripts/deploy.sh
```

### Option 2: Manual Step-by-Step Deployment

1. **Create Lambda Package:**
   ```bash
   ./scripts/package_lambda.sh
   ```

2. **Deploy Infrastructure:**
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform plan
   terraform apply
   ```

3. **Upload Lambda Package:**
   ```bash
   # Get bucket name from Terraform outputs
   BUCKET=$(terraform output -raw lambda_deployment_bucket)
   S3_KEY=$(terraform output -raw lambda_s3_key)
   
   # Upload package
   ./scripts/upload_lambda_to_s3.sh lambda_deployment.zip $BUCKET $S3_KEY
   ```

4. **Update Lambda Function:**
   ```bash
   terraform apply -auto-approve
   ```

## Detailed Process

### 1. Lambda Package Creation

The package creation process includes:

#### Source Files Included:
- `backend/` - Core trading logic modules
- `aws/` - AWS-specific Lambda functions
- `*.py` - Root-level Python files (if any)

#### Dependencies:
- Uses `requirements_Version9.txt` (fallback to basic requirements)
- Installs to package root for Lambda compatibility
- Removes unnecessary files (tests, docs, cache) to reduce size

#### Package Optimization:
- Removes `__pycache__` directories
- Deletes `.pyc` files
- Excludes test directories and documentation
- Strips unnecessary metadata

### 2. S3 Bucket Configuration

**Important: This project uses a single, dedicated S3 bucket for all purposes:**

```hcl
resource "aws_s3_bucket" "lambda_deployment" {
  bucket = "cloud-trading-bot-lambda-deployment-m6x4p8e"
}
```

**Single Bucket Architecture:**
- **Bucket Name**: `cloud-trading-bot-lambda-deployment-m6x4p8e` (fixed, no random suffix)
- **Lambda Packages**: Stored under `lambda/` prefix
- **Application Logs**: Stored under `logs/` prefix  
- **Market Data**: Stored under `data/` prefix
- **Public access blocked** for security
- **Versioning enabled** for rollback capability
- **Lifecycle policies** configured for automatic cleanup

### 3. Lambda Function Configuration

The Lambda function is configured for S3-based deployment:

```hcl
resource "aws_lambda_function" "market_data_fetcher" {
  s3_bucket        = aws_s3_bucket.lambda_deployment.bucket
  s3_key          = var.lambda_s3_key
  source_code_hash = filebase64sha256("lambda_deployment.zip")
  # ... other configuration
}
```

**Key Components:**
- `s3_bucket`: References the created S3 bucket
- `s3_key`: Path within bucket (default: `lambda/lambda_deployment.zip`)
- `source_code_hash`: Triggers updates when package changes

### 4. Path Matching Configuration

Ensure consistency between upload and Terraform configuration:

| Component | Configuration | Default Value |
|-----------|---------------|---------------|
| Terraform Variable | `var.lambda_s3_key` | `lambda/lambda_deployment.zip` |
| Upload Script | `S3_KEY` parameter | Must match Terraform variable |
| S3 Object Path | `s3://bucket/key` | `s3://bucket/lambda/lambda_deployment.zip` |

## Scripts Reference

### package_lambda.sh

Creates optimized Lambda deployment packages.

**Usage:**
```bash
./scripts/package_lambda.sh [output_file.zip]
```

**Features:**
- Automatic dependency resolution
- Package size optimization
- Size validation and warnings
- Cross-platform compatibility

**Output:**
- Creates ZIP file in project root
- Shows package size and deployment recommendations
- Provides next-step instructions

### upload_lambda_to_s3.sh

Uploads Lambda packages to S3 with validation.

**Usage:**
```bash
./scripts/upload_lambda_to_s3.sh <zip_file> <s3_bucket> <s3_key> [aws_region]
```

**Features:**
- Size validation (250MB limit)
- Bucket existence verification
- Upload integrity checking
- Metadata tagging for tracking

**Example:**
```bash
./scripts/upload_lambda_to_s3.sh lambda_deployment.zip my-lambda-bucket lambda/deployment.zip us-west-2
```

### deploy.sh

Complete deployment automation script.

**Features:**
- End-to-end deployment
- Prerequisite checking
- Error handling and rollback
- Multi-service deployment (Lambda + ECS)

## Package Size Guidelines

| Size Range | Deployment Method | Use Case |
|------------|------------------|----------|
| < 70MB | Direct or S3 | Simple Lambda functions |
| 70MB - 250MB | S3 only | Complex applications with dependencies |
| > 250MB | Not supported | Consider optimization or Lambda Layers |

**Optimization Tips:**
- Remove unused dependencies from requirements
- Use Lambda Layers for common libraries
- Exclude test files and documentation
- Consider using smaller package alternatives

## IAM Requirements

### Minimum Permissions for Deployment:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:CreateBucket",
        "s3:PutObject",
        "s3:GetObject",
        "s3:PutBucketPublicAccessBlock"
      ],
      "Resource": [
        "arn:aws:s3:::*lambda-deployment*",
        "arn:aws:s3:::*lambda-deployment*/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:UpdateFunctionConfiguration"
      ],
      "Resource": "arn:aws:lambda:*:*:function:*trading-bot*"
    }
  ]
}
```

### Lambda Execution Permissions:

The Lambda function requires permissions to:
- Access DynamoDB tables
- Read/write S3 buckets
- Retrieve secrets from Secrets Manager
- Write CloudWatch logs

## Troubleshooting

### Common Issues and Solutions

#### Package Creation Fails
```bash
# Check Python and pip installation
python --version
pip --version

# Verify project structure
ls -la backend/ aws/

# Check requirements file
cat requirements_Version9.txt
```

#### Upload Fails
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check S3 bucket exists
aws s3 ls s3://your-bucket-name/

# Verify IAM permissions
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::account:user/username \
  --action-names s3:PutObject \
  --resource-arns arn:aws:s3:::bucket/key
```

#### Lambda Function Doesn't Update
```bash
# Check Terraform state
cd infrastructure/terraform
terraform refresh

# Verify S3 object exists
aws s3 ls s3://bucket/lambda/lambda_deployment.zip

# Force Lambda update
terraform taint aws_lambda_function.market_data_fetcher
terraform apply
```

#### Package Too Large
```bash
# Check current size
ls -lh lambda_deployment.zip

# Optimize requirements
# Remove unnecessary packages from requirements_Version9.txt

# Use package optimization
./scripts/package_lambda.sh optimized.zip
```

### Debug Mode

Enable verbose output for troubleshooting:

```bash
# Enable debug mode
export DEBUG=true

# Run with verbose output
bash -x ./scripts/deploy.sh
```

## Best Practices

### Security
- Never include credentials in packages
- Use AWS Secrets Manager for API keys
- Restrict S3 bucket access
- Follow principle of least privilege for IAM

### Performance
- Minimize package size for faster cold starts
- Use environment variables for configuration
- Implement proper error handling
- Monitor CloudWatch metrics

### Maintenance
- Regular dependency updates
- Package size monitoring
- Version control for packages
- Automated testing of deployments

## Advanced Configuration

### Custom S3 Key Patterns

Modify the Terraform variable for different S3 key patterns:

```hcl
variable "lambda_s3_key" {
  description = "S3 key for Lambda deployment package"
  type        = string
  default     = "lambda/v1.0/lambda_deployment.zip"  # Custom versioning
}
```

### Multi-Environment Deployment

Use different S3 keys for different environments:

```bash
# Development
terraform apply -var="lambda_s3_key=lambda/dev/lambda_deployment.zip"

# Production
terraform apply -var="lambda_s3_key=lambda/prod/lambda_deployment.zip"
```

### Automated CI/CD Integration

Example GitHub Actions workflow:

```yaml
name: Deploy Lambda
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Create Lambda Package
        run: ./scripts/package_lambda.sh
        
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
          
      - name: Deploy
        run: ./scripts/deploy.sh
```

## Validation and Testing

### Package Validation
```bash
# Test package contents
unzip -l lambda_deployment.zip | head -20

# Verify dependencies
python -c "import boto3, yfinance; print('Dependencies OK')"
```

### Deployment Testing
```bash
# Test Lambda function
aws lambda invoke \
  --function-name your-function-name \
  --payload '{"test": true}' \
  response.json

# Check response
cat response.json
```

### Performance Testing
```bash
# Monitor cold start times
aws logs filter-log-events \
  --log-group-name /aws/lambda/your-function \
  --filter-pattern "REPORT"
```