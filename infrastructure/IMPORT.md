# Terraform Import Guide

This guide explains how to use the robust Terraform import process to seamlessly import existing AWS resources into Terraform state, preventing errors like "BucketAlreadyOwnedByYou" and "ResourceAlreadyExists".

## 🔐 Prerequisites: Verify AWS Credentials and Permissions

**IMPORTANT:** Before running any import commands, verify your AWS credentials have the required permissions to avoid "AccessDenied" errors.

### 1. Check Your AWS Identity

Ensure you're using the correct AWS credentials:

```bash
# Verify your current AWS identity and account
aws sts get-caller-identity
```

Expected output should show your user/role ARN and the correct AWS account ID.

### 2. Verify Required Permissions for Import Operations

Test critical permissions needed for the import process:

```bash
# Test S3 discovery permissions (essential for S3 bucket imports)
aws s3api list-buckets --query "Buckets[?starts_with(Name, 'cloud-trading-bot')].Name" --output table

# Test IAM discovery permissions
aws iam list-roles --query "Roles[?starts_with(RoleName, 'cloud-trading-bot')].RoleName" --output table

# Test DynamoDB discovery permissions  
aws dynamodb list-tables --query "TableNames[?starts_with(@, 'cloud-trading-bot')]" --output table

# Test ECR discovery permissions
aws ecr describe-repositories --query "repositories[?starts_with(repositoryName, 'cloud-trading-bot')].repositoryName" --output table 2>/dev/null || echo "No ECR repositories found or insufficient permissions"

# Test Lambda discovery permissions
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'cloud-trading-bot')].FunctionName" --output table 2>/dev/null || echo "No Lambda functions found or insufficient permissions"
```

### 3. Essential S3 Permissions Check

Since S3 bucket imports are common, specifically test S3 permissions:

```bash
# Test S3 bucket-specific permissions that are required for imports
aws s3api get-bucket-location --bucket $(aws s3api list-buckets --query "Buckets[?starts_with(Name, 'cloud-trading-bot')].Name" --output text | head -1) 2>/dev/null || echo "No accessible S3 buckets found - check permissions"

# Test S3 bucket configuration access
aws s3api get-bucket-versioning --bucket $(aws s3api list-buckets --query "Buckets[?starts_with(Name, 'cloud-trading-bot')].Name" --output text | head -1) 2>/dev/null || echo "Cannot access bucket configuration - check permissions"
```

### 4. Verify IAM Policy Attachment

Ensure the required IAM policy is attached to your user or role:

```bash
# Check attached policies for your user (replace 'your-username' with actual username)
aws iam list-attached-user-policies --user-name $(aws sts get-caller-identity --query "Arn" --output text | cut -d'/' -f2) 2>/dev/null || echo "Using role-based access or unable to determine user policies"

# Alternative: Check if you can perform a policy simulation (indicates proper IAM access)
aws iam simulate-principal-policy \
  --policy-source-arn $(aws sts get-caller-identity --query "Arn" --output text) \
  --action-names "s3:ListAllMyBuckets" \
  --resource-arns "arn:aws:s3:::*" \
  --query "EvaluationResults[0].EvalDecision" --output text 2>/dev/null || echo "Unable to simulate policies - check IAM permissions"
```

### 🚨 Permission Troubleshooting

If any of the above commands fail with "AccessDenied":

1. **Review the minimal IAM policy:** Check [terraform-iam-policy-minimal.json](./terraform-iam-policy-minimal.json) and ensure it's attached to your user/role
2. **Verify policy attachment:**
   ```bash
   # List all policies attached to your user
   aws iam list-attached-user-policies --user-name your-username
   ```
3. **Check the policy content:**
   ```bash
   # Get the policy version and content
   aws iam get-policy --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/CloudTradingBotTerraformPolicyMinimal
   ```
4. **See detailed troubleshooting:** Refer to the [README.md](./README.md#-troubleshooting-permission-errors) for comprehensive permission debugging steps

## 🎯 Overview

The enhanced import script (`import-existing-resources.sh`) automatically discovers and imports existing AWS resources that match your project configuration. This prevents Terraform from attempting to create resources that already exist in your AWS account.

## 🚀 Quick Start

### Basic Import (Recommended)

```bash
cd infrastructure/terraform
./import-existing-resources.sh
```

This will:
- Automatically discover existing resources with your project prefix
- Import them into Terraform state if they match expected resources
- Provide detailed logging of all operations
- Skip resources that don't exist or are already in state

### Dry Run Mode

Before making any changes, use dry run mode to see what would be imported:

```bash
./import-existing-resources.sh --dry-run
```

This shows you exactly what resources would be imported without making any actual changes.

## 🔧 Advanced Usage

### Import Specific Resource Types

```bash
# Import only S3 buckets
./import-existing-resources.sh --resource-type s3

# Import only IAM resources
./import-existing-resources.sh --resource-type iam

# Import only DynamoDB tables
./import-existing-resources.sh --resource-type dynamodb
```

**Supported resource types:**
- `s3` - S3 buckets
- `iam` - IAM roles and policies
- `dynamodb` - DynamoDB tables
- `ecr` - ECR repositories
- `lambda` - Lambda functions
- `cloudwatch` - CloudWatch log groups
- `secrets` - Secrets Manager secrets
- `ecs` - ECS clusters

### Custom Project Configuration

```bash
# Use different project name
./import-existing-resources.sh --project-name my-trading-bot

# Use different AWS region
./import-existing-resources.sh --region us-east-1

# Use custom log file
./import-existing-resources.sh --log-file /tmp/my-import.log
```

### Discovery Only Mode

To see what resources exist without importing:

```bash
./import-existing-resources.sh --discover-only
```

This is useful for:
- Understanding what resources exist in your account
- Planning manual imports for custom resources
- Troubleshooting resource naming issues

### Environment Variables

```bash
# Set via environment variables
export PROJECT_NAME="my-custom-bot"
export AWS_REGION="eu-west-1"
export DRY_RUN="true"
export VERBOSE="true"

./import-existing-resources.sh
```

## 📋 Complete Command Reference

```bash
./import-existing-resources.sh [OPTIONS]

OPTIONS:
    -h, --help              Show help message
    -p, --project-name      Project name prefix (default: cloud-trading-bot)
    -r, --region           AWS region (default: us-west-2)
    -d, --dry-run          Show what would be imported without importing
    -v, --verbose          Enable verbose logging
    -l, --log-file         Log file path (default: import_resources.log)
    --discover-only        Only discover resources, don't import
    --resource-type        Import only specific resource type

EXAMPLES:
    # Basic import
    ./import-existing-resources.sh

    # Dry run to see what would be imported
    ./import-existing-resources.sh --dry-run

    # Import only S3 resources
    ./import-existing-resources.sh --resource-type s3

    # Discover all resources without importing
    ./import-existing-resources.sh --discover-only
```

## 🔍 How Resource Discovery Works

The script uses AWS CLI commands to discover existing resources:

### S3 Buckets
```bash
aws s3api list-buckets --query "Buckets[?starts_with(Name, 'cloud-trading-bot')].Name"
```

### IAM Roles
```bash
aws iam list-roles --query "Roles[?starts_with(RoleName, 'cloud-trading-bot')].RoleName"
```

### DynamoDB Tables
```bash
aws dynamodb list-tables --query "TableNames[?starts_with(@, 'cloud-trading-bot')]"
```

### Lambda Functions
```bash
aws lambda list-functions --query "Functions[?starts_with(FunctionName, 'cloud-trading-bot')].FunctionName"
```

## 🎯 Resource Matching Logic

The script matches discovered resources to Terraform resources using naming patterns:

| AWS Resource Pattern | Terraform Resource | Description |
|---------------------|-------------------|-------------|
| `*lambda-deployment*` or `*cloud-trading-bot-lambda-deployment-m6x4p8e*` | `aws_s3_bucket.lambda_deployment` | Single S3 bucket for all purposes (Lambda, logs, data) |
| `*lambda-role*` | `aws_iam_role.lambda_role` | Lambda execution role |
| `*ecs-task-role*` | `aws_iam_role.ecs_task_role` | ECS task role |
| `*config*` | `aws_dynamodb_table.config` | Configuration table |
| `*state*` | `aws_dynamodb_table.state` | State storage table |
| `*trades*` | `aws_dynamodb_table.trades` | Trades history table |
| `*market-data-fetcher*` | `aws_lambda_function.market_data_fetcher` | Market data Lambda |
| `*strategy*` | `aws_ecr_repository.trading_bot_strategy` | Strategy container repo |

**Note**: The previous separate buckets for logs (`*logs*`) and data (`*data*`) have been consolidated into the single `lambda_deployment` bucket.

## 🔧 Extending for New Resource Types

To add support for new resource types:

### 1. Add Discovery Function

```bash
# Function to discover new resource type
discover_new_resource() {
    local prefix="$1"
    aws service-name list-resources --query "Resources[?starts_with(Name, '$prefix')].Name" --output text 2>/dev/null || true
}
```

### 2. Add Existence Check

```bash
# Add case to aws_resource_exists function
"new_resource_type")
    aws service-name describe-resource --resource-name "$resource_id" >/dev/null 2>&1
    ;;
```

### 3. Add Import Function

```bash
# Import new resource type
import_new_resources() {
    log "INFO" "🔧 Discovering new resources..."
    
    local resources
    resources=$(discover_new_resource "$PROJECT_NAME")
    
    if [ -n "$resources" ]; then
        for resource in $resources; do
            case "$resource" in
                *"pattern"*)
                    import_if_missing "aws_service_resource.terraform_name" "$resource" "Resource Description" "new_resource_type"
                    ;;
            esac
        done
    fi
}
```

### 4. Add to Main Function

```bash
# Add to main() function
if [ -z "$RESOURCE_TYPE" ] || [ "$RESOURCE_TYPE" = "new" ]; then
    import_new_resources
fi
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Permission Denied Errors

**Error:** `AccessDenied: User is not authorized to perform: service:Action`

**Solution:** Ensure your AWS user has the required permissions. The minimal IAM policy should include:

```json
{
    "Effect": "Allow",
    "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucketLocation",
        "s3:GetBucketVersioning",
        "s3:GetAccelerateConfiguration",
        "iam:ListRoles",
        "iam:GetRole",
        "iam:GetRolePolicy",
        "dynamodb:ListTables",
        "dynamodb:DescribeTable",
        "ecr:DescribeRepositories",
        "lambda:ListFunctions",
        "lambda:GetFunction",
        "logs:DescribeLogGroups",
        "secretsmanager:ListSecrets",
        "secretsmanager:DescribeSecret",
        "ecs:ListClusters",
        "ecs:DescribeClusters"
    ],
    "Resource": "*"
}
```

**Verification steps:**
1. Check if the minimal policy is attached:
   ```bash
   aws iam list-attached-user-policies --user-name your-username
   ```
2. Test specific permission:
   ```bash
   aws s3api list-buckets  # Test S3 access
   aws iam list-roles      # Test IAM access
   ```
3. Use policy simulator:
   ```bash
   aws iam simulate-principal-policy \
     --policy-source-arn $(aws sts get-caller-identity --query "Arn" --output text) \
     --action-names "s3:ListAllMyBuckets" \
     --resource-arns "arn:aws:s3:::*"
   ```

#### 2. Resource Not Found

**Error:** Resource discovered but import fails

**Possible causes:**
- Resource exists but has different name than expected
- Resource is in different region
- Resource has different tags or configuration

**Solution:**
```bash
# Use discovery mode to see exact resource names
./import-existing-resources.sh --discover-only

# Check the log file for detailed discovery results
cat import_resources.log
```

#### 3. Already in State

**Message:** `Resource already in Terraform state`

This is normal and expected. The script skips resources that are already managed by Terraform.

#### 4. Import Fails

**Error:** `Failed to import resource`

**Troubleshooting steps:**
1. Verify the resource exists in AWS:
   ```bash
   aws s3 ls | grep your-bucket-name
   aws iam get-role --role-name your-role-name
   ```

2. Check Terraform resource configuration matches AWS resource
3. Try manual import:
   ```bash
   terraform import aws_s3_bucket.bucket_name actual-bucket-name
   ```

#### 5. jq Not Found

**Warning:** `jq is not installed. Some features may not work properly.`

**Solution:**
```bash
# Install jq
sudo apt-get install jq  # Ubuntu/Debian
brew install jq          # macOS
```

## 📊 Logging and Monitoring

### Log File Analysis

The script creates detailed logs in `import_resources.log` (or your specified log file):

```bash
# View the log
cat import_resources.log

# Filter for errors only
grep "ERROR" import_resources.log

# Filter for successful imports
grep "Successfully imported" import_resources.log

# View discovery results
grep "Found.*:" import_resources.log
```

### Verbose Mode

Enable verbose mode for detailed output:

```bash
./import-existing-resources.sh --verbose
```

This provides additional information about:
- AWS CLI commands being executed
- Detailed resource discovery results
- Step-by-step import progress

## 🔄 Integration with CI/CD

### GitHub Actions Integration

The import script can be integrated into your CI/CD pipeline:

```yaml
# In .github/workflows/deploy.yml
- name: Import existing resources
  run: |
    cd infrastructure/terraform
    ./import-existing-resources.sh --dry-run
    ./import-existing-resources.sh
```

### Pre-deployment Checks

Always run the import script before `terraform apply`:

```bash
#!/bin/bash
# deployment script

cd infrastructure/terraform

# Import existing resources
./import-existing-resources.sh

# Verify state
terraform plan

# Apply changes
terraform apply
```

## 🔐 Security Best Practices

### Credentials Management

- Never run the script with overly permissive AWS credentials
- Use IAM roles with minimum required permissions
- Consider using AWS CLI profiles for different environments

### State File Protection

- Always backup Terraform state before running imports
- Use remote state backends for team environments
- Enable state file encryption

### Audit Trail

- Keep import logs for audit purposes
- Review what resources were imported
- Verify imported resources match expectations

## 📚 Related Documentation

- [Main README.md](../README.md) - Overall project setup
- [TROUBLESHOOTING.md](./TROUBLESHOOTING.md) - General troubleshooting
- [infrastructure/README.md](./README.md) - Infrastructure overview
- [Terraform Import Documentation](https://www.terraform.io/cli/import)

## 🤝 Contributing

To improve the import script:

1. Test your changes with `--dry-run` mode
2. Add appropriate error handling
3. Update this documentation
4. Add examples for new resource types
5. Test with different AWS regions and configurations

## ⚠️ Important Notes

- Always test imports in a non-production environment first
- The script is designed to be safe - it won't overwrite existing state
- Resources with random suffixes may require manual mapping
- Some resource types may need special handling for complex identifiers
- Keep your AWS CLI and Terraform versions up to date for best compatibility