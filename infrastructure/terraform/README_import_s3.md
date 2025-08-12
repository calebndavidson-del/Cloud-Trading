# AWS S3 Bucket Import Script

## Overview

This script (`import_s3.sh`) safely imports the S3 bucket `cloud-trading-bot-lambda-deployment-m6x4p8e` into Terraform state using the resource name `aws_s3_bucket.lambda_deployment`. It includes comprehensive validation and is designed to be idempotent and safe to run multiple times.

## Features

- ✅ **AWS credential validation** with clear error messages
- ✅ **S3 bucket existence verification** before import
- ✅ **Terraform state checking** for idempotency
- ✅ **Color-coded logging** with timestamps
- ✅ **Detailed help** and usage instructions
- ✅ **Dry-run capability** for safe testing
- ✅ **Verbose mode** for debugging
- ✅ **Robust error handling** and logging to file
- ✅ **Clear next steps guidance** for users
- ✅ **Directory validation** to ensure running from correct location

## Usage

### Prerequisites

1. AWS CLI installed and configured
2. Terraform installed (version >= 1.0)
3. Valid AWS credentials configured
4. Run from the `infrastructure/terraform` directory

### Basic Usage

```bash
# Navigate to the correct directory
cd infrastructure/terraform

# Import the S3 bucket (basic usage)
./import_s3.sh

# Preview what would be imported (safe to run)
./import_s3.sh --dry-run

# Enable verbose logging for debugging
./import_s3.sh --verbose

# Use a different AWS region
./import_s3.sh --region us-east-1
```

### Advanced Usage

```bash
# Override bucket name and resource name
./import_s3.sh --bucket-name custom-bucket --resource-name aws_s3_bucket.custom

# Dry run with verbose logging
./import_s3.sh --dry-run --verbose

# Get help
./import_s3.sh --help
```

## What the Script Does

1. **Validates directory structure** - ensures you're running from the correct Terraform directory
2. **Checks required tools** - verifies AWS CLI and Terraform are installed
3. **Validates AWS credentials** - tests credentials and shows account info
4. **Checks bucket existence** - verifies the S3 bucket exists in AWS
5. **Initializes Terraform** - runs `terraform init` if needed
6. **Checks Terraform state** - determines if the resource is already imported
7. **Performs import** - imports the bucket if not already in state
8. **Verifies import** - confirms the import was successful
9. **Shows next steps** - provides guidance on what to do next

## Example Output

```
🚀 Starting Safe AWS Terraform S3 Import
======================================

Configuration:
  Bucket Name:     cloud-trading-bot-lambda-deployment-m6x4p8e
  Resource Name:   aws_s3_bucket.lambda_deployment
  AWS Region:      us-west-2
  Dry Run:         false
  Verbose:         false
  Log File:        import_s3.log

🔄 Validating directory structure...
✅ Running from correct directory: /path/to/infrastructure/terraform

🔄 Validating required tools...
✅ AWS CLI available: aws-cli/2.28.2
✅ Terraform available: Terraform v1.12.2

🔄 Validating AWS credentials...
✅ AWS credentials valid
ℹ️  AWS Account ID: 123456789012
ℹ️  AWS User/Role: arn:aws:iam::123456789012:user/username
ℹ️  AWS Region: us-west-2

🔄 Checking if S3 bucket exists in AWS...
✅ S3 bucket 'cloud-trading-bot-lambda-deployment-m6x4p8e' exists in AWS

🔄 Checking Terraform initialization...
✅ Terraform already initialized

🔄 Checking if resource exists in Terraform state...
ℹ️  Resource 'aws_s3_bucket.lambda_deployment' not found in Terraform state
ℹ️  Import is needed

🔄 Importing S3 bucket into Terraform state...
✅ S3 bucket imported successfully into Terraform state

🔄 Verifying import was successful...
✅ Import verification successful - resource is now in Terraform state

🎉 S3 bucket import completed successfully!

📝 Next steps:
1. Run 'terraform plan' to verify the current state matches your configuration
2. If the plan shows no changes, your import was successful
3. If the plan shows changes, you may need to update your Terraform configuration
4. Run 'terraform apply' to apply any necessary changes
```

## Error Handling

The script includes comprehensive error handling for common scenarios:

- **Missing AWS credentials** - clear instructions on how to configure
- **Wrong directory** - ensures you're in the correct Terraform directory
- **Missing tools** - checks for AWS CLI and Terraform installation
- **Bucket doesn't exist** - verifies bucket exists before attempting import
- **Already imported** - safely detects if resource is already in state
- **Import failures** - captures and logs Terraform import errors

## Logging

All operations are logged to `import_s3.log` with timestamps. The log includes:

- All validation steps
- AWS API calls
- Terraform operations
- Error messages and stack traces
- Configuration used

## Testing

A test suite is provided to verify the script functionality:

```bash
# Run the test suite
./test_import_s3.sh
```

The test suite covers:
- Help functionality
- Invalid option handling
- Directory validation
- Main.tf content validation
- Custom parameter handling
- Credential validation

## Troubleshooting

### Common Issues

1. **"No main.tf found"**
   - Ensure you're running the script from the `infrastructure/terraform` directory

2. **"AWS credentials not configured"**
   - Run `aws configure` or set AWS environment variables
   - Verify credentials with `aws sts get-caller-identity`

3. **"S3 bucket does not exist"**
   - Verify the bucket name is correct
   - Check you have permission to access the bucket
   - Ensure you're using the correct AWS region

4. **"Failed to import S3 bucket"**
   - Check the Terraform resource configuration matches the actual bucket
   - Verify you have the necessary IAM permissions
   - Review the detailed error in the log file

### Getting Help

- Use `./import_s3.sh --help` for usage information
- Run with `--dry-run` to preview actions without making changes
- Use `--verbose` for detailed logging
- Check the `import_s3.log` file for detailed operation logs

## Security

- The script validates credentials but never logs sensitive information
- All AWS operations are read-only during validation
- The import operation only modifies Terraform state, not AWS resources
- Dry-run mode allows safe testing without making any changes