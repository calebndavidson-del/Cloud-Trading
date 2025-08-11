# Terraform Troubleshooting Guide

This guide helps resolve common Terraform deployment issues for the Cloud Trading Bot infrastructure.

## 🔐 Permission Issues

### Missing ec2:DescribeVpcAttribute Permission

**Error:**
```
Error: UnauthorizedOperation: You are not authorized to perform this operation
```

**Solution:**
1. Ensure your IAM user/role has the `ec2:DescribeVpcAttribute` permission
2. Use the updated `terraform-iam-policy-minimal.json` which includes this permission
3. Attach the policy to your user:
   ```bash
   aws iam attach-user-policy \
     --user-name your-terraform-user \
     --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/CloudTradingBotTerraformPolicyMinimal
   ```

### Missing s3:GetAccelerateConfiguration Permission

**Error:**
```
Error: AccessDenied: User is not authorized to perform: s3:GetAccelerateConfiguration
```

**Solution:**
1. The `s3:GetAccelerateConfiguration` permission is now included in the minimal IAM policy
2. If using custom policies, add this permission to your S3 statement

## 🏗️ Resource Already Exists Errors

### IAM Roles Already Exist

**Error:**
```
Error: EntityAlreadyExists: Role with name cloud-trading-bot-lambda-role already exists
```

**Solutions:**

#### Option 1: Import Existing Resources (Recommended)
```bash
cd infrastructure/terraform
./import-existing-resources.sh
```

#### Option 2: Use Different Names
The updated configuration now includes random suffixes for all resources to prevent conflicts.

#### Option 3: Manual Cleanup (Use with Caution)
```bash
# Delete existing IAM roles (only if safe to do so)
aws iam delete-role-policy --role-name cloud-trading-bot-lambda-role --policy-name cloud-trading-bot-lambda-policy
aws iam delete-role --role-name cloud-trading-bot-lambda-role
```

### DynamoDB Tables Already Exist

**Error:**
```
Error: ResourceInUseException: Table already exists: cloud-trading-bot-config
```

**Solutions:**

#### Option 1: Import Existing Tables
```bash
terraform import aws_dynamodb_table.config cloud-trading-bot-config
terraform import aws_dynamodb_table.state cloud-trading-bot-state
terraform import aws_dynamodb_table.trades cloud-trading-bot-trades
```

#### Option 2: Delete Existing Tables (Data Loss!)
```bash
aws dynamodb delete-table --table-name cloud-trading-bot-config
aws dynamodb delete-table --table-name cloud-trading-bot-state
aws dynamodb delete-table --table-name cloud-trading-bot-trades
```

### ECR Repository Already Exists

**Error:**
```
Error: RepositoryAlreadyExistsException: The repository with name 'cloud-trading-bot-strategy' already exists
```

**Solution:**
```bash
terraform import aws_ecr_repository.trading_bot_strategy cloud-trading-bot-strategy
```

### S3 Buckets Already Exist

**Error:**
```
Error: BucketAlreadyOwnedByYou: Your previous request to create the named bucket succeeded
```

**Solution:**
Find the exact bucket name and import:
```bash
# List your S3 buckets to find the exact names
aws s3 ls | grep cloud-trading-bot

# Import the buckets (replace with actual names)
terraform import aws_s3_bucket.trading_bot_logs cloud-trading-bot-logs-abc12345
terraform import aws_s3_bucket.trading_bot_data cloud-trading-bot-data-abc12345
```

### CloudWatch Log Groups Already Exist

**Error:**
```
Error: ResourceAlreadyExistsException: The specified log group already exists
```

**Solution:**
```bash
terraform import aws_cloudwatch_log_group.lambda_logs "/aws/lambda/cloud-trading-bot-market-data-fetcher"
terraform import aws_cloudwatch_log_group.ecs_logs "/aws/ecs/cloud-trading-bot-strategy"
```

## 🚫 AWS Reserved Environment Variables

### InvalidParameterValueException for AWS_REGION

**Error:**
```
InvalidParameterValueException: The environment variable 'AWS_REGION' is reserved by the Lambda runtime and cannot be set by the customer.
```

**Root Cause:**
AWS Lambda automatically provides certain environment variables like `AWS_REGION`, `AWS_LAMBDA_FUNCTION_NAME`, etc. These cannot be explicitly set in the Terraform configuration.

**Solution:**
1. Remove reserved environment variables from the Lambda function's environment block:
   ```hcl
   # ❌ Don't do this:
   environment {
     variables = {
       AWS_REGION = var.aws_region  # This causes the error
     }
   }
   
   # ✅ Do this instead:
   environment {
     variables = {
       ENV = var.environment
       # AWS_REGION is automatically provided by AWS
     }
   }
   ```

2. Your Lambda function code can still access `AWS_REGION` using `os.getenv("AWS_REGION")` - it will be automatically available.

**Reserved Environment Variables (Cannot be set manually):**
- `AWS_REGION`
- `AWS_LAMBDA_FUNCTION_NAME`
- `AWS_LAMBDA_FUNCTION_VERSION`
- `AWS_LAMBDA_LOG_GROUP_NAME`
- `AWS_LAMBDA_LOG_STREAM_NAME`
- `_AWS_XRAY_TRACING_NAME`
- And others starting with `AWS_` or `_AWS`

## 🔄 State Management Best Practices

### Set Up Remote State Backend

1. Create S3 bucket for state:
   ```bash
   aws s3 mb s3://your-terraform-state-bucket --region us-west-2
   aws s3api put-bucket-versioning --bucket your-terraform-state-bucket --versioning-configuration Status=Enabled
   ```

2. Create DynamoDB table for locking:
   ```bash
   aws dynamodb create-table \
     --table-name terraform-state-lock \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --billing-mode PAY_PER_REQUEST
   ```

3. Configure backend in `backend.tf` and run:
   ```bash
   terraform init -migrate-state
   ```

### Backup State Before Changes

```bash
# Always backup state before major changes
cp terraform.tfstate terraform.tfstate.backup
```

## 🚀 Deployment Workflow

### Clean Deployment Process

1. **Check Prerequisites:**
   ```bash
   aws sts get-caller-identity  # Verify AWS access
   terraform version            # Verify Terraform
   ```

2. **Initialize and Plan:**
   ```bash
   cd infrastructure/terraform
   terraform init
   terraform plan -out=tfplan
   ```

3. **Handle Existing Resources:**
   ```bash
   # If you see "already exists" errors in plan:
   ./import-existing-resources.sh
   terraform plan -out=tfplan  # Re-plan after import
   ```

4. **Apply Changes:**
   ```bash
   terraform apply tfplan
   ```

### Incremental Deployment

For large infrastructures, deploy in stages:

1. **Core Infrastructure First:**
   ```bash
   terraform apply -target=aws_vpc.trading_bot_vpc
   terraform apply -target=aws_subnet.trading_bot_public_subnet
   ```

2. **IAM Resources:**
   ```bash
   terraform apply -target=aws_iam_role.lambda_role
   terraform apply -target=aws_iam_role.ecs_task_role
   ```

3. **Storage Resources:**
   ```bash
   terraform apply -target=aws_s3_bucket.trading_bot_logs
   terraform apply -target=aws_dynamodb_table.config
   ```

4. **Compute Resources:**
   ```bash
   terraform apply -target=aws_lambda_function.market_data_fetcher
   terraform apply -target=aws_ecs_cluster.trading_bot_cluster
   ```

## 🔍 Common Debug Commands

### Check Resource Status
```bash
# List all resources in state
terraform state list

# Show specific resource
terraform state show aws_iam_role.lambda_role

# Check if resource exists in AWS
aws iam get-role --role-name cloud-trading-bot-lambda-role
```

### Refresh State
```bash
# Sync state with actual AWS resources
terraform refresh
```

### Validate Configuration
```bash
# Check syntax and configuration
terraform validate
terraform fmt -check
```

## 🆘 Emergency Recovery

### State Corruption
```bash
# Pull state from remote backend
terraform state pull > terraform.tfstate

# Push state to remote backend
terraform state push terraform.tfstate
```

### Complete Reset (Nuclear Option)
```bash
# ⚠️ This destroys everything!
terraform destroy -auto-approve

# Remove state files
rm -f terraform.tfstate*
rm -rf .terraform/

# Start fresh
terraform init
```

## 📞 Getting Help

1. **Check Terraform logs:**
   ```bash
   TF_LOG=DEBUG terraform apply
   ```

2. **AWS CloudTrail:**
   Check AWS CloudTrail for detailed error messages about permission issues.

3. **Community Resources:**
   - [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
   - [AWS IAM Policy Simulator](https://policysim.aws.amazon.com/)
   - [Terraform GitHub Issues](https://github.com/hashicorp/terraform/issues)