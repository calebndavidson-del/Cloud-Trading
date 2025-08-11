# Terraform Backend Configuration
# This file configures remote state storage for better state management
# and team collaboration.

# Uncomment and configure the S3 backend for production use:
# terraform {
#   backend "s3" {
#     bucket         = "your-terraform-state-bucket"
#     key            = "cloud-trading-bot/terraform.tfstate"
#     region         = "us-west-2"
#     encrypt        = true
#     dynamodb_table = "terraform-state-lock"
#   }
# }

# To set up the S3 backend:
# 1. Create an S3 bucket for state storage:
#    aws s3 mb s3://your-terraform-state-bucket --region us-west-2
#    aws s3api put-bucket-versioning --bucket your-terraform-state-bucket --versioning-configuration Status=Enabled
#    aws s3api put-bucket-encryption --bucket your-terraform-state-bucket --server-side-encryption-configuration '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
#
# 2. Create a DynamoDB table for state locking:
#    aws dynamodb create-table \
#      --table-name terraform-state-lock \
#      --attribute-definitions AttributeName=LockID,AttributeType=S \
#      --key-schema AttributeName=LockID,KeyType=HASH \
#      --billing-mode PAY_PER_REQUEST
#
# 3. Uncomment the backend configuration above and update with your bucket name
# 4. Run: terraform init -migrate-state
#
# This will prevent state conflicts and "resource already exists" errors
# when multiple developers work on the infrastructure or when re-deploying.

# Alternative: Use Terraform Cloud
# terraform {
#   cloud {
#     organization = "your-organization"
#     workspaces {
#       name = "cloud-trading-bot"
#     }
#   }
# }