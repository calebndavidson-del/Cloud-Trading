# Infrastructure Setup

This directory contains the infrastructure code and configuration for the Cloud Trading Bot.

## 🏗️ Contents

- `terraform/` - Terraform configuration files
- `docker/` - Docker configuration files
- `terraform-iam-policy.json` - Full IAM policy for Terraform deployment
- `terraform-iam-policy-minimal.json` - Minimal IAM policy for Terraform deployment

## 🔐 IAM Permissions for Terraform

Before deploying the infrastructure, ensure your AWS user or role has the required permissions.

### Quick Setup

Choose one of the IAM policies and create it:

```bash
# For full permissions (easier setup)
aws iam create-policy \
  --policy-name CloudTradingBotTerraformPolicy \
  --policy-document file://terraform-iam-policy.json

# For minimal permissions (more secure)
aws iam create-policy \
  --policy-name CloudTradingBotTerraformPolicyMinimal \
  --policy-document file://terraform-iam-policy-minimal.json
```

Then attach it to your user or role:

```bash
# Replace YOUR-ACCOUNT-ID and your-terraform-user
aws iam attach-user-policy \
  --user-name your-terraform-user \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/CloudTradingBotTerraformPolicy
```

### Required Permissions

The minimal policy includes these critical permissions:
- `ec2:DescribeVpcAttribute` - Required for VPC operations
- `s3:GetAccelerateConfiguration` - Required for S3 bucket configuration
- Standard permissions for ECS, Lambda, DynamoDB, IAM, etc.

### Troubleshooting Permissions

If you encounter permission errors, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for detailed solutions.

## 🚀 Deployment

From the project root directory:

```bash
./scripts/deploy.sh
```

This will:
1. Create the Lambda deployment package
2. **Import existing resources automatically** to prevent conflicts
3. Deploy infrastructure using Terraform
4. Build and push the Docker image to ECR
5. Set up all AWS services

### 🔄 Robust Import Process (Recommended Workflow)

**Before running any Terraform commands**, use the enhanced import script to prevent "resource already exists" errors:

```bash
cd infrastructure/terraform

# 1. Validate your import setup
./validate-import.sh

# 2. See what resources would be imported (safe dry run)
./import-existing-resources.sh --dry-run

# 3. Import existing resources
./import-existing-resources.sh

# 4. Run Terraform as usual
terraform plan
terraform apply
```

**Quick one-liner for experienced users:**
```bash
cd infrastructure/terraform && ./import-existing-resources.sh && terraform apply
```

### 📋 Import Script Features

The enhanced import script (`import-existing-resources.sh`) provides:

- **🔍 Automatic Resource Discovery**: Finds existing AWS resources by project prefix
- **🛡️ Safe Operation**: Dry-run mode to preview changes before importing
- **📊 Extensible Design**: Easy to add new resource types (VPCs, more IAM roles, etc.)
- **📝 Detailed Logging**: Comprehensive logs of all operations
- **🎯 Selective Import**: Import only specific resource types when needed
- **⚡ Smart Matching**: Automatically matches discovered resources to Terraform configurations

**Supported Resource Types:**
- S3 buckets (including deployment and logs buckets)
- IAM roles and policies
- DynamoDB tables
- ECR repositories
- Lambda functions
- CloudWatch log groups
- Secrets Manager secrets
- ECS clusters

### Advanced Import Options

```bash
# Import only S3 buckets to fix BucketAlreadyOwnedByYou errors
./import-existing-resources.sh --resource-type s3

# Import with different project name
./import-existing-resources.sh --project-name my-custom-bot

# Import with verbose logging
./import-existing-resources.sh --verbose

# Just discover what exists without importing
./import-existing-resources.sh --discover-only
```

### Handling Existing Resources

If you encounter "resource already exists" errors:

1. **Use the enhanced import script (Recommended):**
   ```bash
   cd infrastructure/terraform
   ./import-existing-resources.sh
   ```

2. **For comprehensive guidance:**
   See [IMPORT.md](./IMPORT.md) for detailed import documentation and troubleshooting.

3. **For traditional troubleshooting:**
   See [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) for manual resolution steps.

### State Management

For production deployments, configure remote state backend:
1. See `terraform/backend.tf` for setup instructions
2. This prevents state conflicts and resource duplication issues

## 📖 For More Details

See the main [README.md](../README.md) for complete setup instructions and troubleshooting.