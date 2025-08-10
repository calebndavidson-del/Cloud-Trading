# ECS Infrastructure for Trading Bot Strategy Engine

# VPC and Networking
resource "aws_vpc" "trading_bot_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_internet_gateway" "trading_bot_igw" {
  vpc_id = aws_vpc.trading_bot_vpc.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_subnet" "trading_bot_public_subnet" {
  count                   = 2
  vpc_id                  = aws_vpc.trading_bot_vpc.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-subnet-${count.index + 1}"
  }
}

resource "aws_route_table" "trading_bot_public_rt" {
  vpc_id = aws_vpc.trading_bot_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.trading_bot_igw.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "trading_bot_public_rta" {
  count          = length(aws_subnet.trading_bot_public_subnet)
  subnet_id      = aws_subnet.trading_bot_public_subnet[count.index].id
  route_table_id = aws_route_table.trading_bot_public_rt.id
}

data "aws_availability_zones" "available" {
  state = "available"
}

# Security Group for ECS
resource "aws_security_group" "ecs_service_sg" {
  name        = "${var.project_name}-ecs-service-sg"
  description = "Security group for ECS service"
  vpc_id      = aws_vpc.trading_bot_vpc.id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-service-sg"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "trading_bot_cluster" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# IAM Role for ECS Task
resource "aws_iam_role" "ecs_task_role" {
  name = "${var.project_name}-ecs-task-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  name = "${var.project_name}-ecs-task-policy"
  role = aws_iam_role.ecs_task_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Scan",
          "dynamodb:Query"
        ]
        Resource = [
          aws_dynamodb_table.config.arn,
          aws_dynamodb_table.state.arn,
          aws_dynamodb_table.trades.arn,
          "${aws_dynamodb_table.trades.arn}/index/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.trading_bot_logs.arn,
          "${aws_s3_bucket.trading_bot_logs.arn}/*",
          aws_s3_bucket.trading_bot_data.arn,
          "${aws_s3_bucket.trading_bot_data.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.trading_bot_secrets.arn
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = aws_lambda_function.market_data_fetcher.arn
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.ecs_logs.arn}:*"
      }
    ]
  })
}

# IAM Role for ECS Task Execution
resource "aws_iam_role" "ecs_execution_role" {
  name = "${var.project_name}-ecs-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_role_policy" {
  role       = aws_iam_role.ecs_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECR Repository for container images
resource "aws_ecr_repository" "trading_bot_strategy" {
  name                 = "${var.project_name}-strategy"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name = "${var.project_name}-strategy"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "trading_bot_strategy" {
  family                   = "${var.project_name}-strategy"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_execution_role.arn
  task_role_arn           = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name  = "trading-bot-strategy"
      image = "${aws_ecr_repository.trading_bot_strategy.repository_url}:latest"
      
      environment = [
        {
          name  = "DYNAMODB_CONFIG_TABLE"
          value = aws_dynamodb_table.config.name
        },
        {
          name  = "DYNAMODB_STATE_TABLE"
          value = aws_dynamodb_table.state.name
        },
        {
          name  = "DYNAMODB_TRADES_TABLE"
          value = aws_dynamodb_table.trades.name
        },
        {
          name  = "S3_BUCKET_LOGS"
          value = aws_s3_bucket.trading_bot_logs.bucket
        },
        {
          name  = "S3_BUCKET_DATA"
          value = aws_s3_bucket.trading_bot_data.bucket
        },
        {
          name  = "SECRETS_MANAGER_ARN"
          value = aws_secretsmanager_secret.trading_bot_secrets.arn
        },
        {
          name  = "AWS_REGION"
          value = var.aws_region
        },
        {
          name  = "ENV"
          value = var.environment
        },
        {
          name  = "LAMBDA_FUNCTION_NAME"
          value = aws_lambda_function.market_data_fetcher.function_name
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs_logs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }

      essential = true
    }
  ])

  tags = {
    Name = "${var.project_name}-strategy-task"
  }
}

# ECS Service
resource "aws_ecs_service" "trading_bot_strategy" {
  name            = "${var.project_name}-strategy-service"
  cluster         = aws_ecs_cluster.trading_bot_cluster.id
  task_definition = aws_ecs_task_definition.trading_bot_strategy.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.trading_bot_public_subnet[*].id
    security_groups  = [aws_security_group.ecs_service_sg.id]
    assign_public_ip = true
  }

  deployment_configuration {
    maximum_percent         = 200
    minimum_healthy_percent = 100
  }

  tags = {
    Name = "${var.project_name}-strategy-service"
  }

  depends_on = [
    aws_iam_role_policy.ecs_task_policy,
    aws_iam_role_policy_attachment.ecs_execution_role_policy
  ]
}

# CloudWatch Alarms for monitoring
resource "aws_cloudwatch_metric_alarm" "ecs_cpu_utilization" {
  alarm_name          = "${var.project_name}-ecs-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ECS"
  period              = "300"
  statistic           = "Average"
  threshold           = "80"
  alarm_description   = "This metric monitors ECS CPU utilization"

  dimensions = {
    ServiceName = aws_ecs_service.trading_bot_strategy.name
    ClusterName = aws_ecs_cluster.trading_bot_cluster.name
  }

  tags = {
    Name = "${var.project_name}-ecs-cpu-alarm"
  }
}

# Additional outputs for ECS
output "ecs_cluster_name" {
  value = aws_ecs_cluster.trading_bot_cluster.name
}

output "ecs_service_name" {
  value = aws_ecs_service.trading_bot_strategy.name
}

output "ecr_repository_url" {
  value = aws_ecr_repository.trading_bot_strategy.repository_url
}