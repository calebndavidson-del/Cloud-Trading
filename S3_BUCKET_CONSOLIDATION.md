# S3 Bucket Consolidation Documentation

## Overview

This document describes the S3 bucket consolidation implemented for the Cloud Trading Bot project. The consolidation reduces the number of S3 buckets from 3 separate buckets to a single, well-organized bucket.

## Before Consolidation

The project previously used 3 separate S3 buckets:

1. **Lambda Deployment Bucket**: `cloud-trading-bot-lambda-deployment-{random-suffix}`
   - Purpose: Store Lambda deployment packages
   - Configuration: `aws_s3_bucket.lambda_deployment`

2. **Logs Bucket**: `cloud-trading-bot-logs-{random-suffix}`  
   - Purpose: Store application logs
   - Configuration: `aws_s3_bucket.trading_bot_logs`

3. **Data Bucket**: `cloud-trading-bot-data-{random-suffix}`
   - Purpose: Store market data and trading data
   - Configuration: `aws_s3_bucket.trading_bot_data`

## After Consolidation

The project now uses a **single S3 bucket** with organized prefixes:

### Bucket Details
- **Name**: `cloud-trading-bot-lambda-deployment-m6x4p8e` (fixed, no random suffix)
- **Configuration**: `aws_s3_bucket.lambda_deployment` (only remaining bucket resource)

### Organization Structure
```
cloud-trading-bot-lambda-deployment-m6x4p8e/
├── lambda/                    # Lambda deployment packages
│   └── lambda_deployment.zip
├── logs/                      # Application logs
│   ├── bot/2024/01/15/...    
│   ├── trades/2024/01/15/...
│   └── errors/2024/01/15/...
└── data/                      # Market data and trading data
    └── market_data/2024/01/15/...
```

## Changes Made

### 1. Terraform Infrastructure (`infrastructure/terraform/`)

#### `main.tf`
- **Removed**: `aws_s3_bucket.trading_bot_logs` and `aws_s3_bucket.trading_bot_data` resources
- **Updated**: All S3 references to use `aws_s3_bucket.lambda_deployment`
- **Modified**: IAM policies to reference single bucket
- **Enhanced**: Lifecycle configuration with prefix-based rules for logs and data
- **Updated**: Environment variables `S3_BUCKET_LOGS` and `S3_BUCKET_DATA` to use single bucket
- **Modified**: Terraform outputs to reflect single bucket usage

#### `ecs.tf`
- **Updated**: IAM task role policies to reference single bucket
- **Modified**: Container environment variables to use single bucket

### 2. Application Code

#### `backend/config.py`
- **Updated**: Default values for `S3_BUCKET_LOGS` and `S3_BUCKET_DATA`
- **Added**: S3 prefix constants (`S3_PREFIX_LOGS`, `S3_PREFIX_DATA`, `S3_PREFIX_LAMBDA`)
- **Enhanced**: Configuration structure to include prefix information

#### `aws/lambda_market_data.py`
- **Modified**: `store_market_data_s3()` function to use data prefix from configuration
- **Enhanced**: S3 key generation to include configurable prefix

### 3. Infrastructure Scripts

#### `import-existing-resources.sh`
- **Updated**: Resource matching logic to handle single bucket approach
- **Removed**: Import logic for separate logs and data buckets
- **Enhanced**: Bucket name matching to include the specific bucket name

### 4. Documentation

#### Major Updates
- `README.md`: Updated environment variables section and S3 architecture explanation
- `LAMBDA_S3_DEPLOYMENT.md`: Added single bucket architecture documentation
- `IMPORT.md`: Updated resource matching table
- `TROUBLESHOOTING.md`: Updated bucket import examples

## Benefits of Consolidation

### 1. **Simplified Management**
- Single bucket to manage instead of three
- Unified IAM permissions and policies
- Consistent lifecycle and retention policies

### 2. **Cost Optimization**
- Reduced S3 request costs (fewer buckets to list/manage)
- Simplified billing and cost tracking
- More efficient cross-object operations

### 3. **Better Organization**
- Logical separation using prefixes
- Consistent naming and structure
- Easier to browse and understand in AWS console

### 4. **Operational Benefits**
- Fewer resources to monitor
- Simplified backup and replication strategies
- Reduced complexity in disaster recovery

### 5. **Development Benefits**
- Single bucket configuration in environment variables
- Consistent S3 operations across all components
- Simplified testing and local development

## Environment Variables

The consolidation maintains backward compatibility with environment variables:

```bash
# All point to the same bucket now
S3_BUCKET_LOGS=cloud-trading-bot-lambda-deployment-m6x4p8e
S3_BUCKET_DATA=cloud-trading-bot-lambda-deployment-m6x4p8e
```

## Prefix Organization

The single bucket uses prefixes for logical separation:

- **`lambda/`**: Lambda deployment packages and related files
- **`logs/`**: All application logs with date-based sub-organization
- **`data/`**: Market data, trading data, and analytics with date-based sub-organization

## Migration Considerations

### For Existing Deployments
1. **Data Migration**: If existing separate buckets contain data, it will need to be migrated to the new bucket structure
2. **IAM Updates**: Existing IAM policies referencing old bucket names will be automatically updated
3. **Application Restart**: Applications may need restart to pick up new bucket configuration

### For New Deployments
- No migration needed
- Single bucket will be created automatically
- All operations will use the consolidated structure from the start

## Testing

A comprehensive test suite (`test_s3_consolidation.py`) validates:
- Configuration consistency across all components
- Proper prefix usage in S3 operations
- Environment variable defaults
- Backward compatibility

## Future Considerations

1. **Cross-Region Replication**: Easier to set up for single bucket
2. **Versioning Strategy**: Unified versioning across all data types
3. **Monitoring**: Single bucket to monitor for all S3 metrics
4. **Security**: Unified security policies and access controls

## Rollback Plan

If needed, the consolidation can be reverted by:
1. Restoring the original Terraform configuration
2. Creating separate buckets again  
3. Migrating data back to separate buckets
4. Updating application configurations

However, the benefits of the single bucket approach make rollback unlikely to be necessary.