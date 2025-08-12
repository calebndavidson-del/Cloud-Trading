# Cloud Trading Bot - AWS Fully Managed Backend

A sophisticated, cloud-native trading bot with a fully managed AWS backend infrastructure. This system provides continuous market data fetching, strategy optimization, and automated trading capabilities using serverless and containerized AWS services.

## 🏗️ Architecture Overview

### Core Components

- **AWS Lambda**: Serverless market data fetcher with automatic failover
- **Amazon ECS**: Always-on strategy engine running in containers
- **Amazon DynamoDB**: Configuration, state, and trade data storage
- **Amazon S3**: Log storage and data archival
- **AWS Secrets Manager**: Secure API key management
- **Amazon CloudWatch**: Monitoring and logging
- **Amazon EventBridge**: Scheduled data fetching

### AWS Services Used

| Service | Purpose | Features |
|---------|---------|----------|
| AWS Lambda | Market Data Fetching | Serverless, automatic scaling, scheduled execution, S3-based deployment |
| Amazon ECS (Fargate) | Strategy Engine | Containerized, always-on, auto-scaling |
| Amazon DynamoDB | Data Storage | NoSQL, fast queries, TTL for data cleanup |
| Amazon S3 | Log & Data Archive + Lambda Packages | Durable storage, lifecycle policies, Lambda deployment |
| AWS Secrets Manager | API Key Storage | Secure, rotatable secrets |
| Amazon CloudWatch | Monitoring | Logs, metrics, alarms |
| Amazon EventBridge | Scheduling | Cron-like triggers for Lambda |

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with appropriate permissions (see [Required IAM Permissions](#-required-iam-permissions))
2. **AWS CLI** installed and configured
3. **Terraform** (>= 1.0) for infrastructure deployment
4. **Docker** for container builds
5. **Python 3.11+** for local development

### Interactive Deployment (Recommended for New Users)

Use the interactive deployment script for a guided experience:

```bash
# Clone the repository
git clone <repository-url>
cd Cloud-Trading

# Run the interactive deployment script
./scripts/quick_deploy.sh
```

The script provides these options:
- **Full Automated Deployment** - Complete setup with guided prompts (includes automatic import)
- **Lambda Package Only** - Create deployment package for testing
- **Infrastructure Only** - Deploy AWS resources without Lambda code
- **View Documentation** - Access built-in help and guides
- **Test Current Setup** - Validate configuration before deployment

### Advanced Deployment

For experienced users or automation scenarios:

#### Recommended Workflow (Prevents Resource Conflicts)

```bash
# Clone the repository
git clone <repository-url>
cd Cloud-Trading

# 1. First-time setup with automatic resource import
./scripts/deploy.sh
```

**The deployment script now automatically handles resource imports** to prevent common errors like "BucketAlreadyOwnedByYou".

#### Manual Import Process (For Granular Control)

If you need more control over the import process:

```bash
cd Cloud-Trading/infrastructure/terraform

# 1. Validate import setup
./validate-import.sh

# 2. Preview what would be imported (safe)
./import-existing-resources.sh --dry-run

# 3. Import existing resources to prevent conflicts
./import-existing-resources.sh

# 4. Deploy infrastructure
cd ../..
./scripts/deploy.sh
```

**Import Script Capabilities:**
- 🔍 **Smart Discovery**: Automatically finds existing AWS resources
- 🛡️ **Safe Operations**: Dry-run mode for safe testing
- 📊 **Extensible**: Easy to add new resource types (VPCs, IAM roles, etc.)
- 🎯 **Selective**: Import only specific resource types when needed
- 📝 **Detailed Logging**: Comprehensive operation logs

**Supported Resource Types:**
- S3 buckets (deployment, logs, data)
- IAM roles and policies
- DynamoDB tables
- ECR repositories
- Lambda functions
- CloudWatch log groups
- Secrets Manager secrets
- ECS clusters

### 1. Deploy AWS Infrastructure

```bash
# Clone the repository
git clone <repository-url>
cd Cloud-Trading

# Run the deployment script
./scripts/deploy.sh
```

The deployment script will:
- Create Lambda deployment package (supports packages >70MB via S3)
- Deploy infrastructure using Terraform
- Upload Lambda package to dedicated S3 bucket
- Build and push Docker image to ECR
- Set up all AWS services

#### Detailed Lambda Deployment Process

The system uses S3-based deployment for Lambda functions, which provides several advantages:
- **Large Package Support**: Supports packages up to 250MB (vs 70MB limit for direct uploads)
- **Reliable Deployment**: More reliable for large packages with dependencies
- **Version Management**: Better tracking of Lambda package versions
- **CI/CD Integration**: Easier integration with automated deployment pipelines

**Step-by-step Lambda deployment process:**

1. **Package Creation**: The deployment script creates a ZIP package containing:
   - All Python source files from `backend/` and `aws/` directories
   - All required dependencies from `requirements_Version9.txt`
   - Optimized for size (removes test files, documentation, etc.)

2. **Infrastructure Deployment**: Terraform creates:
   - S3 bucket for Lambda packages (`{project-name}-lambda-deployment-{suffix}`)
   - Lambda function configured to use S3-based deployment
   - IAM roles and permissions for S3 access

3. **Package Upload**: The package is uploaded to the dedicated S3 bucket with:
   - Automatic size validation (max 250MB)
   - Upload verification and integrity checking
   - Metadata tagging for deployment tracking

4. **Function Update**: Lambda function is updated to reference the S3 object:
   ```
   S3 Bucket: {project-name}-lambda-deployment-{random-suffix}
   S3 Key: lambda/lambda_deployment.zip
   ```

**Manual Lambda Package Creation (Advanced):**

For custom packages or testing:

```bash
# Create a custom Lambda package
./scripts/package_lambda.sh my_custom_lambda.zip

# Upload to S3 (get bucket name from Terraform outputs)
./scripts/upload_lambda_to_s3.sh my_custom_lambda.zip <lambda-bucket-name> lambda/lambda_deployment.zip

# Update Lambda function via Terraform
cd infrastructure/terraform
terraform apply -auto-approve
```

**Matching S3 Paths with Terraform Configuration:**

The Terraform configuration uses these key components:

```hcl
# Terraform variables (infrastructure/terraform/main.tf)
variable "lambda_s3_key" {
  default = "lambda/lambda_deployment.zip"  # This must match upload path
}

# Lambda function configuration
resource "aws_lambda_function" "market_data_fetcher" {
  s3_bucket = aws_s3_bucket.lambda_deployment.bucket  # Auto-created bucket
  s3_key    = var.lambda_s3_key                       # Matches upload path
}

# Outputs for deployment scripts
output "lambda_deployment_bucket" {
  value = aws_s3_bucket.lambda_deployment.bucket
}
output "lambda_s3_key" {
  value = var.lambda_s3_key
}
```

To change the S3 path, update the `lambda_s3_key` variable and ensure your upload script uses the same path.

### 2. Configure API Keys

Update the secrets in AWS Secrets Manager:

```bash
# Get the secret ARN from Terraform outputs
aws secretsmanager get-secret-value --secret-id <secret-arn>

# Update with your API keys
aws secretsmanager update-secret --secret-id <secret-arn> --secret-string '{
  "yahoo_api_key": "your_yahoo_key",
  "alpha_vantage_key": "your_alpha_vantage_key",
  "trading_api_key": "your_trading_key",
  "trading_api_secret": "your_trading_secret"
}'
```

### 3. Monitor the System

```bash
# View Lambda logs
aws logs tail /aws/lambda/cloud-trading-bot-market-data-fetcher --follow

# View ECS strategy engine logs
aws logs tail /aws/ecs/cloud-trading-bot-strategy --follow

# Check DynamoDB tables
aws dynamodb scan --table-name cloud-trading-bot-trades --limit 10
```

### 4. Manual Lambda Package Upload (Advanced)

For advanced users who want to upload custom Lambda packages:

```bash
# Create your custom Lambda package
zip -r custom_lambda.zip . -x "*.pyc" "*/__pycache__/*"

# Upload to S3 (get bucket name from Terraform outputs)
./scripts/upload_lambda_to_s3.sh custom_lambda.zip <lambda-bucket-name> lambda/lambda_deployment.zip

# Update Lambda function via Terraform
cd infrastructure/terraform
terraform apply -auto-approve
```

The upload script provides:
- Package size validation (max 250MB)
- Upload verification
- Metadata tagging for tracking
- Error handling and rollback

## 🔐 Required IAM Permissions

### Terraform Deployment Permissions

The IAM user or role used for Terraform deployment requires specific permissions to create and manage AWS resources. The most critical permission that users often encounter issues with is:

```json
{
  "Effect": "Allow",
  "Action": ["ec2:DescribeAvailabilityZones"],
  "Resource": "*"
}
```

This permission is required because the Terraform configuration uses the `aws_availability_zones` data source to create subnets across multiple availability zones.

### Complete IAM Policy

Two IAM policy options are provided in the repository:

📄 **[infrastructure/terraform-iam-policy.json](infrastructure/terraform-iam-policy.json)** - Full permissions (recommended for simplicity)

📄 **[infrastructure/terraform-iam-policy-minimal.json](infrastructure/terraform-iam-policy-minimal.json)** - Minimal permissions (recommended for production)

Both policies include all necessary permissions for:
- **EC2**: VPC, subnets, security groups, availability zones
- **ECS**: Cluster, services, task definitions  
- **ECR**: Container registry
- **IAM**: Roles and policies for services
- **Lambda**: Functions and execution
- **DynamoDB**: Tables and indexes
- **S3**: Buckets and objects
- **Secrets Manager**: Secrets and versions
- **CloudWatch**: Logs and monitoring
- **EventBridge**: Scheduled events

The minimal policy uses more restrictive resource constraints and only includes the specific actions needed for this project.

### Setting Up IAM Permissions

#### Option 1: Attach Policy to Existing User/Role

```bash
# Option A: Use the full permissions policy (easier setup)
aws iam create-policy \
  --policy-name CloudTradingBotTerraformPolicy \
  --policy-document file://infrastructure/terraform-iam-policy.json

# Option B: Use the minimal permissions policy (more secure)
aws iam create-policy \
  --policy-name CloudTradingBotTerraformPolicyMinimal \
  --policy-document file://infrastructure/terraform-iam-policy-minimal.json

# Attach to your user (replace with your username and chosen policy)
aws iam attach-user-policy \
  --user-name your-terraform-user \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/CloudTradingBotTerraformPolicy

# Or attach to a role (replace with your role name and chosen policy)
aws iam attach-role-policy \
  --role-name your-terraform-role \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/CloudTradingBotTerraformPolicy
```

#### Option 2: Create New IAM User for Terraform

```bash
# Create a new user for Terraform
aws iam create-user --user-name terraform-cloud-trading-bot

# Create and attach the policy (choose full or minimal)
aws iam create-policy \
  --policy-name CloudTradingBotTerraformPolicy \
  --policy-document file://infrastructure/terraform-iam-policy.json

aws iam attach-user-policy \
  --user-name terraform-cloud-trading-bot \
  --policy-arn arn:aws:iam::YOUR-ACCOUNT-ID:policy/CloudTradingBotTerraformPolicy

# Create access keys
aws iam create-access-key --user-name terraform-cloud-trading-bot
```

#### Option 3: Use AWS CLI Profiles

```bash
# Configure a profile with the Terraform user credentials
aws configure --profile terraform-cloud-trading-bot

# Use the profile for deployment
export AWS_PROFILE=terraform-cloud-trading-bot
./scripts/deploy.sh
```

### Troubleshooting Permission Issues

If you encounter permission errors during deployment:

1. **Check the specific error**: The error message will indicate which permission is missing
2. **Verify current permissions**: Use `aws iam get-user-policy` or `aws iam list-attached-user-policies`
3. **Add missing permissions**: Update your IAM policy to include the required actions
4. **Common missing permissions**:
   - `ec2:DescribeAvailabilityZones` - Required for subnet creation
   - `iam:PassRole` - Required for service role creation
   - `logs:CreateLogGroup` - Required for CloudWatch log groups

### Security Best Practices

- **Principle of Least Privilege**: Only grant permissions necessary for deployment
- **Separate Users**: Use a dedicated IAM user or role for Terraform operations
- **Temporary Credentials**: Consider using AWS STS assume-role for temporary access
- **Policy Versioning**: Keep track of policy changes and test in non-production first

## 📁 Project Structure

```
Cloud-Trading/
├── backend/                    # Core trading logic
│   ├── __init__.py
│   ├── bot.py                 # Main bot orchestrator
│   ├── config.py              # Configuration management
│   ├── data_collector.py      # Market data fetching
│   ├── metrics.py             # Financial calculations
│   ├── optimizer.py           # Strategy optimization
│   └── paper_trader.py        # Paper trading simulation
├── aws/                       # AWS-specific components
│   ├── lambda_market_data.py  # Lambda function for data fetching
│   ├── services.py            # AWS services integration
│   └── strategy_engine.py     # ECS strategy engine
├── infrastructure/            # Infrastructure as Code
│   ├── terraform/
│   │   ├── main.tf           # Main Terraform configuration
│   │   └── ecs.tf            # ECS infrastructure
│   └── docker/
│       └── Dockerfile        # Container definition
├── scripts/                  # Deployment and setup scripts
│   ├── quick_deploy.sh       # Interactive deployment assistant
│   ├── deploy.sh            # Main deployment script  
│   ├── package_lambda.sh    # Lambda package creation
│   ├── upload_lambda_to_s3.sh # S3 upload utility
│   └── setup_local.sh       # Local development setup
├── examples/                 # Configuration examples
│   ├── .env.local           # Local development config
│   └── .env.aws             # AWS production config
└── README.md
```

## 🛠️ Local Development

### Setup Local Environment

```bash
# Run the local setup script
./scripts/setup_local.sh

# Activate virtual environment
source venv/bin/activate

# Set environment variables
source .env

# Test the bot locally
export PYTHONPATH=$(pwd)
python backend/bot.py
```

### Test Individual Components

```bash
# Test market data collection
python -c "from backend.data_collector import fetch_market_data; print(fetch_market_data())"

# Test paper trading
python -c "from backend.paper_trader import paper_trade; print(paper_trade({}))"

# Test strategy optimization
python -c "from backend.optimizer import optimize_strategy; from backend.data_collector import fetch_market_data; print(optimize_strategy(fetch_market_data(), 5))"

# Run local tests
python test_local.py
```

### Local AWS Testing with LocalStack

```bash
# Install LocalStack
pip install localstack

# Start LocalStack
localstack start

# Use local AWS endpoints
export AWS_ENDPOINT_URL=http://localhost:4566
```

## 📚 Deployment Examples

### Example 1: First-Time Setup (Recommended)

```bash
# 1. Clone and navigate to the repository
git clone <repository-url>
cd Cloud-Trading

# 2. Use the interactive deployment assistant
./scripts/quick_deploy.sh

# 3. Follow the prompts to deploy infrastructure
# 4. Configure API keys in AWS Secrets Manager
# 5. Monitor the system via CloudWatch logs
```

### Example 2: Custom Lambda Package

```bash
# Create a custom Lambda package
./scripts/package_lambda.sh my_custom_lambda.zip

# View package contents
unzip -l my_custom_lambda.zip

# Upload to S3 (after infrastructure is deployed)
./scripts/upload_lambda_to_s3.sh my_custom_lambda.zip my-lambda-bucket lambda/custom.zip

# Update Lambda function
cd infrastructure/terraform
terraform apply -auto-approve
```

### Example 3: Development Workflow

```bash
# 1. Test package creation without deployment
./scripts/test_package_lambda.sh

# 2. Create and test Lambda package locally
./scripts/package_lambda.sh test_lambda.zip

# 3. Deploy infrastructure only
cd infrastructure/terraform
terraform init
terraform plan
terraform apply

# 4. Upload Lambda package
BUCKET=$(terraform output -raw lambda_deployment_bucket)
S3_KEY=$(terraform output -raw lambda_s3_key)
../scripts/upload_lambda_to_s3.sh test_lambda.zip $BUCKET $S3_KEY

# 5. Update Lambda function
terraform apply -auto-approve
```

### Example 4: CI/CD Pipeline Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy Cloud Trading Bot
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install Terraform
        uses: hashicorp/setup-terraform@v2
        
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
          
      - name: Create Lambda Package
        run: ./scripts/package_lambda.sh lambda_deployment.zip
        
      - name: Deploy Infrastructure
        run: ./scripts/deploy.sh
```

## 🔧 Configuration

### Lambda Deployment S3 Path Configuration

Understanding and configuring S3 paths for Lambda deployment:

#### Default Configuration
- **Terraform Variable**: `lambda_s3_key = "lambda/lambda_deployment.zip"`  
- **S3 Bucket**: Auto-generated with pattern `{project-name}-lambda-deployment-{random-suffix}`
- **Upload Path**: `lambda/lambda_deployment.zip`

#### Customizing S3 Paths
To use different S3 paths, update the Terraform variable:

```hcl
# In infrastructure/terraform/main.tf or terraform.tfvars
variable "lambda_s3_key" {
  default = "custom/path/my-lambda.zip"
}
```

Then ensure your upload command matches:
```bash
./scripts/upload_lambda_to_s3.sh lambda_deployment.zip $BUCKET custom/path/my-lambda.zip
```

#### Environment-Specific Paths
For multiple environments:

```bash
# Development
terraform apply -var="lambda_s3_key=lambda/dev/lambda_deployment.zip"

# Production  
terraform apply -var="lambda_s3_key=lambda/prod/lambda_deployment.zip"
```

#### Path Verification
Always verify S3 paths match between Terraform and upload:

```bash
# Check Terraform outputs
cd infrastructure/terraform
terraform output lambda_deployment_bucket
terraform output lambda_s3_key

# Verify S3 object exists
aws s3 ls s3://$(terraform output -raw lambda_deployment_bucket)/$(terraform output -raw lambda_s3_key)
```

### Environment Variables

#### Core Configuration
- `ENV`: Environment (development, staging, production)
- `DEBUG`: Enable debug logging (true/false)
- `AWS_REGION`: AWS region for deployment
- `USE_MOCK_DATA`: Use mock data for testing (true/false)

#### AWS Resources
- `DYNAMODB_CONFIG_TABLE`: Configuration table name
- `DYNAMODB_STATE_TABLE`: State storage table name
- `DYNAMODB_TRADES_TABLE`: Trades history table name
- `S3_BUCKET_LOGS`: Logs storage bucket
- `S3_BUCKET_DATA`: Data storage bucket
- `LAMBDA_DEPLOYMENT_BUCKET`: Lambda deployment packages bucket
- `SECRETS_MANAGER_ARN`: Secrets Manager ARN
- `LAMBDA_FUNCTION_NAME`: Market data Lambda function
- `ECS_CLUSTER_NAME`: ECS cluster name
- `ECS_SERVICE_NAME`: ECS service name

#### Trading Configuration
- `TRADING_ENABLED`: Enable actual trading (true/false)
- `PAPER_TRADING`: Use paper trading mode (true/false)
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### AWS Secrets Configuration

Store sensitive information in AWS Secrets Manager:

```json
{
  "yahoo_api_key": "your_yahoo_finance_api_key",
  "alpha_vantage_key": "your_alpha_vantage_api_key",
  "trading_api_key": "your_brokerage_api_key",
  "trading_api_secret": "your_brokerage_api_secret"
}
```

## 📊 Monitoring and Observability

### CloudWatch Dashboards

The deployment creates CloudWatch dashboards for:
- Lambda function metrics (invocations, errors, duration)
- ECS service metrics (CPU, memory, task count)
- DynamoDB metrics (read/write capacity, throttles)
- Custom trading metrics (trades executed, portfolio value)

### Alarms and Notifications

Automated alarms for:
- High error rates in Lambda functions
- ECS service health issues
- DynamoDB throttling events
- Trading strategy performance anomalies

### Log Analysis

Structured logging with:
- Centralized log aggregation in CloudWatch
- Log retention policies
- Error tracking and alerting
- Performance monitoring

## 💰 Cost Optimization

### Resource Optimization
- **Lambda**: Pay-per-request, automatic scaling
- **ECS Fargate**: Right-sized containers, spot instances option
- **DynamoDB**: On-demand billing, TTL for data cleanup
- **S3**: Intelligent tiering, lifecycle policies

### Estimated Monthly Costs
- **Lambda**: ~$5-20 (depending on execution frequency)
- **ECS**: ~$30-100 (single task, varies by region)
- **DynamoDB**: ~$5-25 (depends on data volume)
- **S3**: ~$1-10 (depends on log volume)
- **Other AWS services**: ~$5-15

**Total estimated cost**: $50-170/month for typical usage

## 🔒 Security Best Practices

### IAM Policies
- Least privilege access for all services
- Service-specific roles with minimal permissions
- No hardcoded credentials in code

### Data Protection
- Encryption at rest for all data stores
- Encryption in transit for all communications
- Secure secrets management with AWS Secrets Manager

### Network Security
- VPC isolation for ECS tasks
- Security groups with minimal required access
- Private subnets for sensitive components

## 📈 Scaling and Performance

### Automatic Scaling
- **Lambda**: Concurrent execution scaling
- **ECS**: Auto-scaling based on CPU/memory metrics
- **DynamoDB**: On-demand scaling or provisioned capacity

### Performance Optimization
- Efficient data structures and algorithms
- Caching strategies for frequently accessed data
- Optimized database queries and indexes

## 🚨 Disaster Recovery

### Backup Strategy
- **DynamoDB**: Point-in-time recovery enabled
- **S3**: Cross-region replication for critical data
- **Code**: Version controlled in Git

### High Availability
- Multi-AZ deployment for ECS services
- Lambda automatic failover across AZs
- DynamoDB global tables for cross-region replication

## 🔧 Troubleshooting

### Common Issues

#### Lambda Deployment Issues

**Package Too Large Error:**
```bash
# Check package size
ls -lh lambda_deployment.zip

# If > 250MB, optimize the package
./scripts/package_lambda.sh optimized_lambda.zip

# Or remove unnecessary dependencies from requirements_Version9.txt
```

#### Lambda Deployment Issues

**Package Creation Problems:**
```bash
# Test package creation without dependencies
./scripts/test_package_lambda.sh

# Check Python environment
python --version
pip --version

# Verify project structure
ls -la backend/ aws/

# Check and fix requirements
cat requirements_Version9.txt
```

**S3 Upload Problems:**
```bash
# Check if S3 bucket exists
aws s3 ls s3://your-lambda-deployment-bucket/

# Verify AWS credentials and region
aws sts get-caller-identity
aws configure get region

# Check IAM permissions for S3 access
aws iam get-user-policy --user-name your-user --policy-name your-policy
```

**Lambda Function Update Failures:**
```bash
# Check if S3 object exists
aws s3 ls s3://your-lambda-deployment-bucket/lambda/lambda_deployment.zip

# Verify Lambda function configuration
aws lambda get-function --function-name your-lambda-function-name

# Check Terraform state
cd infrastructure/terraform
terraform plan
```

**S3 Path Mismatch:**
Ensure the S3 path in your upload matches the Terraform configuration:
- Terraform variable: `lambda_s3_key = "lambda/lambda_deployment.zip"`
- Upload command: `./scripts/upload_lambda_to_s3.sh package.zip bucket-name lambda/lambda_deployment.zip`

#### Lambda Function Errors
```bash
# Check Lambda logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/cloud-trading-bot"
aws logs tail /aws/lambda/cloud-trading-bot-market-data-fetcher --follow

# Check function configuration
aws lambda get-function --function-name cloud-trading-bot-market-data-fetcher
```

#### ECS Service Issues
```bash
# Check service status
aws ecs describe-services --cluster cloud-trading-bot-cluster --services cloud-trading-bot-strategy-service

# Check task logs
aws logs tail /aws/ecs/cloud-trading-bot-strategy --follow

# Update service
aws ecs update-service --cluster cloud-trading-bot-cluster --service cloud-trading-bot-strategy-service --desired-count 1
```

#### DynamoDB Issues
```bash
# Check table status
aws dynamodb describe-table --table-name cloud-trading-bot-config

# Scan recent data
aws dynamodb scan --table-name cloud-trading-bot-state --limit 10
```

**Deployment Validation:**
```bash
# Validate all components
./scripts/quick_deploy.sh  # Choose option 5 for testing

# Test Lambda function after deployment
aws lambda invoke \
  --function-name $(terraform output -raw lambda_function_name) \
  --payload '{"test": true}' \
  response.json && cat response.json

# Check Lambda logs
aws logs tail /aws/lambda/$(terraform output -raw lambda_function_name | sed 's/.*-//') --follow

# Verify S3 objects
aws s3 ls s3://$(terraform output -raw lambda_deployment_bucket)/
```

### Performance Tuning

#### Lambda Optimization
- Increase memory for faster execution
- Use provisioned concurrency for consistent performance
- Optimize package size for faster cold starts

#### ECS Optimization
- Right-size CPU and memory allocation
- Use spot instances for cost savings
- Implement health checks for reliability

## 📚 API Reference

### Lambda Function Interface

The market data Lambda function accepts:

```json
{
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "include_trends": true
}
```

Returns:
```json
{
  "statusCode": 200,
  "body": {
    "timestamp": "2024-01-01T12:00:00Z",
    "market_data": {
      "AAPL": {
        "price": 150.00,
        "volume": 1000000,
        "market_cap": 2500000000000
      }
    },
    "trends": {
      "sp500": {
        "current_price": 4500.00,
        "change_percent": 1.5,
        "trend": "up"
      }
    }
  }
}
```

### DynamoDB Schema

#### Configuration Table
```json
{
  "id": "bot_config",
  "timestamp": "2024-01-01T12:00:00Z",
  "config": "{\"trading_enabled\": true}",
  "updated_by": "system"
}
```

#### Trades Table
```json
{
  "trade_id": "trade_20240101_120000_AAPL",
  "symbol": "AAPL",
  "action": "buy",
  "price": 150.00,
  "shares": 100,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## 🔄 CI/CD Pipeline

### Automated Deployment

```yaml
# Example GitHub Actions workflow
name: Deploy Trading Bot
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Configure AWS
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-west-2
      - name: Deploy Infrastructure
        run: ./scripts/deploy.sh
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This trading bot is for educational and research purposes only. Trading involves significant risk of loss. Always use paper trading mode for testing. Never risk more than you can afford to lose. The authors are not responsible for any financial losses.

## 📞 Support

- 📧 Email: support@example.com
- 💬 Discord: [Trading Bot Community](https://discord.gg/example)
- 📖 Documentation: [Wiki](https://github.com/example/wiki)
- 🐛 Issues: [GitHub Issues](https://github.com/example/issues)