# S3-Based Lambda Deployment for Cloud Trading Bot

## Overview

This implementation refactors the AWS Lambda function deployment from file-based to S3-based deployment to support packages larger than 70MB (up to 250MB).

## Key Changes Made

### 1. Terraform Configuration Updates

**File: `infrastructure/terraform/main.tf`**

- **Added new S3 bucket** for Lambda deployment packages:
  ```hcl
  resource "aws_s3_bucket" "lambda_deployment" {
    bucket = "${var.project_name}-lambda-deployment-${random_string.suffix.result}"
  }
  ```

- **Refactored Lambda function** to use S3-based deployment:
  ```hcl
  resource "aws_lambda_function" "market_data_fetcher" {
    # S3-based deployment configuration
    s3_bucket     = aws_s3_bucket.lambda_deployment.bucket
    s3_key        = var.lambda_s3_key
    
    # Track changes to the deployment package
    source_code_hash = filebase64sha256("lambda_deployment.zip")
    # ... rest of configuration
  }
  ```

- **Added new variable** for S3 key configuration:
  ```hcl
  variable "lambda_s3_key" {
    description = "S3 key for Lambda deployment package"
    type        = string
    default     = "lambda/lambda_deployment.zip"
  }
  ```

- **Updated IAM permissions** to include access to the Lambda deployment bucket
- **Added new outputs** for the deployment bucket and S3 key

### 2. Enhanced Deployment Script

**File: `scripts/deploy.sh`**

- Modified to upload Lambda package to S3 after infrastructure deployment
- Uses dedicated upload script for better error handling and validation
- Implements two-stage deployment:
  1. Deploy infrastructure (including S3 bucket)
  2. Upload Lambda package and update function

### 3. New Lambda Upload Script

**File: `scripts/upload_lambda_to_s3.sh`**

A dedicated script for uploading Lambda packages with:
- **Package size validation** (max 250MB for S3-based deployment)
- **Upload verification** with size checking
- **Error handling** and rollback capabilities
- **Metadata tagging** for deployment tracking
- **AWS credentials validation**

### 4. Comprehensive Testing

**File: `scripts/test_lambda_deployment.sh`**

Test script that validates:
- Support for packages from small (< 70MB) to large (up to 250MB)
- Error handling for oversized packages
- Argument validation and error cases
- Integration with existing deployment workflows

### 5. Updated Documentation

**File: `README.md`**

- Added S3-based Lambda deployment documentation
- Explained advantages of S3 approach
- Added manual upload instructions for advanced users
- Updated environment variables documentation

## Benefits of S3-Based Deployment

1. **Large Package Support**: Supports packages up to 250MB (vs 70MB limit for direct uploads)
2. **Reliability**: More reliable for large packages with dependencies
3. **Version Management**: Better tracking of Lambda package versions
4. **CI/CD Integration**: Easier integration with automated deployment pipelines
5. **Cost Efficiency**: More efficient for frequent deployments

## Package Size Support

| Approach | Size Limit | Use Case |
|----------|------------|----------|
| Direct Upload (filename) | 70MB | Small Lambda functions |
| S3-based (s3_bucket/s3_key) | 250MB | Large packages with dependencies |

## Usage Examples

### Automatic Deployment
```bash
./scripts/deploy.sh
```

### Manual Package Upload
```bash
# Create your custom Lambda package
zip -r custom_lambda.zip . -x "*.pyc" "*/__pycache__/*"

# Upload to S3
./scripts/upload_lambda_to_s3.sh custom_lambda.zip <bucket-name> lambda/deployment.zip

# Update Lambda function
cd infrastructure/terraform
terraform apply -auto-approve
```

## Validation Results

- ✅ Terraform configuration validates successfully
- ✅ All scripts pass syntax validation
- ✅ Package size validation works correctly
- ✅ Error handling functions as expected
- ✅ Integration with existing deployment workflow maintained
- ✅ Supports packages from 1KB to 250MB
- ✅ Backward compatibility maintained

## Security Considerations

- Lambda deployment bucket has public access blocked
- IAM permissions follow least privilege principle
- Package validation prevents oversized uploads
- Upload verification ensures integrity

## Future Enhancements

The S3-based approach enables future enhancements such as:
- Lambda package versioning and rollback
- Blue/green deployments
- Automated package optimization
- Integration with CI/CD pipelines for automatic deployments