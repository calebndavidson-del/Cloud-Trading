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
| AWS Lambda | Market Data Fetching | Serverless, automatic scaling, scheduled execution |
| Amazon ECS (Fargate) | Strategy Engine | Containerized, always-on, auto-scaling |
| Amazon DynamoDB | Data Storage | NoSQL, fast queries, TTL for data cleanup |
| Amazon S3 | Log & Data Archive | Durable storage, lifecycle policies |
| AWS Secrets Manager | API Key Storage | Secure, rotatable secrets |
| Amazon CloudWatch | Monitoring | Logs, metrics, alarms |
| Amazon EventBridge | Scheduling | Cron-like triggers for Lambda |

## 🚀 Quick Start

### Prerequisites

1. **AWS Account** with appropriate permissions
2. **AWS CLI** installed and configured
3. **Terraform** (>= 1.0) for infrastructure deployment
4. **Docker** for container builds
5. **Python 3.11+** for local development

### 1. Deploy AWS Infrastructure

```bash
# Clone the repository
git clone <repository-url>
cd Cloud-Trading

# Run the deployment script
./scripts/deploy.sh
```

The deployment script will:
- Create Lambda deployment package
- Deploy infrastructure using Terraform
- Build and push Docker image to ECR
- Set up all AWS services

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
│   ├── deploy.sh            # Main deployment script
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

## 🔧 Configuration

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
          aws-region: us-east-1
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