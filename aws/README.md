# Lambda Package Size Optimization

This document explains the optimizations made to resolve AWS Lambda deployment package size issues.

## Problem

The original deployment approach included heavy ML dependencies (pandas, numpy, scikit-learn, streamlit, optuna) in the Lambda deployment package, causing it to exceed AWS Lambda's 50MB direct upload limit.

## Solution

### 1. S3-Based Deployment

Instead of direct file upload, the Lambda function now uses S3 for deployment packages:

```hcl
resource "aws_lambda_function" "market_data_fetcher" {
  s3_bucket     = aws_s3_bucket.lambda_deployments.bucket
  s3_key        = aws_s3_object.lambda_deployment.key
  # ... other configuration
}
```

Benefits:
- Supports packages up to 10GB (vs 50MB for direct upload)
- Versioning through S3 object versioning
- Better deployment pipeline integration

### 2. Optimized Dependencies

Created separate requirements files:

- `aws/lambda_requirements.txt`: Essential packages only (yfinance, requests, boto3)
- `aws/layer_requirements.txt`: Heavy dependencies for optional Lambda layer

### 3. Lambda Layers (Optional)

Heavy dependencies can be packaged as Lambda layers:
- Reduces main package size
- Reusable across multiple functions
- Up to 250MB unzipped per layer

## Usage

### Standard Deployment (Recommended)
```bash
./scripts/deploy.sh
```

The script will:
1. Create optimized Lambda package (~20KB base + minimal dependencies)
2. Upload to S3 automatically via Terraform
3. Deploy Lambda function with S3 reference

### With Lambda Layer (Optional)
```bash
./scripts/build_layer.sh  # Build heavy dependencies layer
./scripts/deploy.sh       # Deploy with layer support
```

## File Structure

```
aws/
├── lambda_requirements.txt    # Minimal dependencies for Lambda
├── layer_requirements.txt     # Heavy dependencies for layer
└── lambda_market_data.py      # Lambda function code

scripts/
├── deploy.sh                  # Main deployment script
└── build_layer.sh            # Layer building script

infrastructure/terraform/
├── main.tf                   # Infrastructure with S3-based deployment
└── lambda_deployment.zip     # Generated package (created by deploy.sh)
```

## Package Sizes

- Base code package: ~20KB
- With minimal dependencies: ~5-10MB (well under 50MB limit)
- Heavy dependencies layer: ~100-200MB (separate from main package)

## Benefits

1. **No size limit issues**: S3 supports much larger packages
2. **Faster deployments**: Smaller main packages deploy faster
3. **Better separation**: Core logic separate from heavy dependencies
4. **Reusable layers**: Heavy dependencies can be shared across functions
5. **Improved cold starts**: Smaller packages may start faster