# Data sources for existing resources
# These can be used to reference existing resources instead of creating new ones
# to help resolve "resource already exists" errors.

# Data source for existing VPC (optional)
# Uncomment if you want to use an existing VPC instead of creating a new one
# data "aws_vpc" "existing" {
#   filter {
#     name   = "tag:Name"
#     values = ["${var.project_name}-vpc"]
#   }
# }

# Data source for existing subnets (optional)
# data "aws_subnets" "existing" {
#   filter {
#     name   = "vpc-id"
#     values = [data.aws_vpc.existing.id]
#   }
# }

# Data source for existing IAM roles (if they already exist)
# data "aws_iam_role" "existing_lambda_role" {
#   name = "${var.project_name}-lambda-role"
# }

# Data source for existing DynamoDB tables
# data "aws_dynamodb_table" "existing_config" {
#   name = "${var.project_name}-config"
# }

# Data source for existing ECR repository
# data "aws_ecr_repository" "existing_strategy" {
#   name = "${var.project_name}-strategy"
# }

# Data source for existing CloudWatch log groups
# data "aws_cloudwatch_log_group" "existing_lambda_logs" {
#   name = "/aws/lambda/${var.project_name}-market-data-fetcher"
# }

# Data source for existing S3 buckets (if you know the exact names)
# data "aws_s3_bucket" "existing_logs" {
#   bucket = "your-existing-logs-bucket-name"
# }

# Usage examples:
# To use existing resources instead of creating new ones, replace resource blocks with data sources:
# 
# Instead of:
#   resource "aws_iam_role" "lambda_role" { ... }
# Use:
#   data "aws_iam_role" "lambda_role" { name = "${var.project_name}-lambda-role" }
#
# Then reference it the same way:
#   role = data.aws_iam_role.lambda_role.arn

# Helper variables for conditional resource creation
variable "use_existing_vpc" {
  description = "Whether to use an existing VPC instead of creating a new one"
  type        = bool
  default     = false
}

variable "use_existing_iam_roles" {
  description = "Whether to use existing IAM roles instead of creating new ones"
  type        = bool
  default     = false
}

variable "existing_vpc_id" {
  description = "ID of existing VPC to use (when use_existing_vpc is true)"
  type        = string
  default     = ""
}

variable "existing_subnet_ids" {
  description = "List of existing subnet IDs to use (when use_existing_vpc is true)"
  type        = list(string)
  default     = []
}