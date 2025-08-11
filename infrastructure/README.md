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

### Critical Permission

The most common error is missing the `ec2:DescribeAvailabilityZones` permission, which is required for the Terraform data source used in subnet creation.

## 🚀 Deployment

From the project root directory:

```bash
./scripts/deploy.sh
```

This will:
1. Create the Lambda deployment package
2. Deploy infrastructure using Terraform
3. Build and push the Docker image to ECR
4. Set up all AWS services

## 📖 For More Details

See the main [README.md](../README.md) for complete setup instructions and troubleshooting.