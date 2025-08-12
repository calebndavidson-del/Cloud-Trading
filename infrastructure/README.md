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

### 🔍 Verifying AWS Credential Permissions

Before running Terraform imports or deployments, verify your AWS credentials have the required permissions:

#### 1. Check Current Identity

Verify you're using the correct AWS credentials:

```bash
# Check your current AWS identity
aws sts get-caller-identity

# Expected output:
# {
#     "UserId": "AIDAXXXXXXXXXXXXXXXX",
#     "Account": "123456789012",
#     "Arn": "arn:aws:iam::123456789012:user/your-terraform-user"
# }
```

#### 2. Verify IAM Policy Attachment

Check if the required IAM policy is attached to your user or role:

```bash
# List policies attached to your user
aws iam list-attached-user-policies --user-name your-terraform-user

# List policies attached to a role (if using role-based access)
aws iam list-attached-role-policies --role-name your-terraform-role

# Verify specific policy exists
aws iam get-policy --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/CloudTradingBotTerraformPolicyMinimal
```

#### 3. Test Critical Permissions

Test key permissions required for Terraform imports and S3 operations:

```bash
# Test S3 permissions (critical for bucket imports)
aws s3api list-buckets --query "Buckets[?starts_with(Name, 'cloud-trading-bot')].Name"

# Test specific S3 bucket operations
aws s3api get-bucket-location --bucket your-bucket-name
aws s3api get-bucket-versioning --bucket your-bucket-name

# Test IAM permissions
aws iam list-roles --query "Roles[?starts_with(RoleName, 'cloud-trading-bot')].RoleName"

# Test DynamoDB permissions
aws dynamodb list-tables --query "TableNames[?starts_with(@, 'cloud-trading-bot')]"

# Test ECR permissions
aws ecr describe-repositories --query "repositories[?starts_with(repositoryName, 'cloud-trading-bot')].repositoryName"
```

#### 4. Simulate IAM Policy Actions (Advanced)

For comprehensive permission testing, use AWS IAM policy simulator:

```bash
# Get your user ARN first
USER_ARN=$(aws sts get-caller-identity --query "Arn" --output text)

# Test S3 permissions
aws iam simulate-principal-policy \
  --policy-source-arn "$USER_ARN" \
  --action-names "s3:ListAllMyBuckets" "s3:CreateBucket" "s3:GetBucketLocation" \
  --resource-arns "arn:aws:s3:::*"

# Test IAM permissions  
aws iam simulate-principal-policy \
  --policy-source-arn "$USER_ARN" \
  --action-names "iam:GetRole" "iam:CreateRole" "iam:AttachRolePolicy" \
  --resource-arns "arn:aws:iam::*:role/*"
```

#### 5. AWS Console Verification

You can also verify permissions using the AWS Console:

1. **IAM Dashboard** → **Users** → Select your user → **Permissions** tab
2. Check if `CloudTradingBotTerraformPolicyMinimal` or `CloudTradingBotTerraformPolicy` is attached
3. **IAM** → **Policies** → Search for your policy → **Policy usage** tab to see attached users/roles
4. **IAM** → **Access analyzer** → **Policy simulator** for comprehensive permission testing

### Required Permissions

The minimal policy includes these critical permissions:

#### S3 Operations (Essential for Terraform imports)
- `s3:CreateBucket`, `s3:DeleteBucket` - Bucket lifecycle management
- `s3:GetBucketVersioning`, `s3:PutBucketVersioning` - Version control
- `s3:GetAccelerateConfiguration` - Required for S3 bucket configuration
- `s3:GetBucketLifecycleConfiguration`, `s3:PutBucketLifecycleConfiguration` - Lifecycle rules
- `s3:GetBucketTagging`, `s3:PutBucketTagging` - Tagging operations

#### IAM Operations
- `iam:GetRole`, `iam:CreateRole`, `iam:DeleteRole` - Role management
- `iam:AttachRolePolicy`, `iam:DetachRolePolicy` - Policy attachment
- `iam:PassRole` - Allow services to assume roles

#### Infrastructure Operations
- `ec2:DescribeVpcAttribute` - Required for VPC operations
- `ecs:CreateCluster`, `ecs:DescribeClusters` - ECS management
- `lambda:CreateFunction`, `lambda:GetFunction` - Lambda management
- `dynamodb:CreateTable`, `dynamodb:DescribeTable` - DynamoDB operations

### 🚨 Troubleshooting Permission Errors

#### Common "AccessDenied" Errors and Solutions

**Error:** `AccessDenied: User: arn:aws:iam::ACCOUNT:user/USER is not authorized to perform: s3:CreateBucket`

**Solution:**
1. Verify S3 permissions in your IAM policy
2. Check if the minimal policy is properly attached:
   ```bash
   aws iam list-attached-user-policies --user-name your-terraform-user
   ```
3. Ensure your AWS region matches the bucket region

**Error:** `AccessDenied: User is not authorized to perform: iam:GetRole`

**Solution:**
1. Verify IAM permissions in your policy
2. Check if you're trying to access roles outside the allowed resource scope
3. Ensure the role name matches the pattern `*cloud-trading-bot*`

**Error:** `BucketAlreadyOwnedByYou` during Terraform apply

**Solution:**
1. This indicates insufficient import permissions or missing import step
2. Use the import process: See [IMPORT.md](./IMPORT.md)
3. Verify you have `s3:GetBucketLocation` permission

#### Permission Debugging Steps

1. **Enable CloudTrail** to see which API calls are being denied
2. **Check CloudTrail Event History** in AWS Console for detailed error messages
3. **Use verbose AWS CLI output:**
   ```bash
   aws s3api list-buckets --debug
   ```
4. **Test with AWS CLI before Terraform:**
   ```bash
   # Test the exact operation that's failing
   aws s3api create-bucket --bucket test-bucket-name --region us-west-2
   ```

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