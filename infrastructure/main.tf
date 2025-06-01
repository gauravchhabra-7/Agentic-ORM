# AWS ORM Platform Infrastructure
# This creates all AWS resources needed for the MVP

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "orm-platform"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# Data sources
data "aws_caller_identity" "current" {}

# DynamoDB Tables
resource "aws_dynamodb_table" "comments" {
  name           = "${var.project_name}-comments-${var.environment}"
  billing_mode   = "PAY_PER_REQUEST"  # Free tier friendly
  hash_key       = "comment_id"
  stream_enabled = true
  stream_view_type = "NEW_AND_OLD_IMAGES"

  attribute {
    name = "comment_id"
    type = "S"
  }

  attribute {
    name = "client_id"
    type = "S"
  }

  attribute {
    name = "created_at"
    type = "S"
  }

  global_secondary_index {
    name     = "ClientIndex"
    hash_key = "client_id"
    range_key = "created_at"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-comments"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "config" {
  name         = "${var.project_name}-config-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "client_id"
  range_key    = "config_type"

  attribute {
    name = "client_id"
    type = "S"
  }

  attribute {
    name = "config_type"
    type = "S"
  }

  tags = {
    Name        = "${var.project_name}-config"
    Environment = var.environment
  }
}

resource "aws_dynamodb_table" "audit_logs" {
  name         = "${var.project_name}-audit-${var.environment}"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "log_id"

  attribute {
    name = "log_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  attribute {
    name = "action_type"
    type = "S"
  }

  global_secondary_index {
    name     = "TimestampIndex"
    hash_key = "action_type"
    range_key = "timestamp"
    projection_type = "ALL"
  }

  tags = {
    Name        = "${var.project_name}-audit"
    Environment = var.environment
  }
}

# SQS Queue for comment processing
resource "aws_sqs_queue" "comment_processing" {
  name                       = "${var.project_name}-comments-${var.environment}"
  visibility_timeout_seconds = 300
  message_retention_seconds  = 1209600  # 14 days
  
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.comment_processing_dlq.arn
    maxReceiveCount     = 3
  })

  tags = {
    Name        = "${var.project_name}-queue"
    Environment = var.environment
  }
}

# Dead Letter Queue
resource "aws_sqs_queue" "comment_processing_dlq" {
  name = "${var.project_name}-comments-dlq-${var.environment}"

  tags = {
    Name        = "${var.project_name}-dlq"
    Environment = var.environment
  }
}

# S3 Bucket for static assets and artifacts
resource "aws_s3_bucket" "assets" {
  bucket = "${var.project_name}-assets-${var.environment}-${random_string.bucket_suffix.result}"

  tags = {
    Name        = "${var.project_name}-assets"
    Environment = var.environment
  }
}

resource "random_string" "bucket_suffix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket_versioning" "assets_versioning" {
  bucket = aws_s3_bucket.assets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "assets_encryption" {
  bucket = aws_s3_bucket.assets.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Secrets Manager for API keys
resource "aws_secretsmanager_secret" "api_keys" {
  name        = "${var.project_name}-api-keys-${var.environment}"
  description = "API keys for ORM platform"

  tags = {
    Name        = "${var.project_name}-secrets"
    Environment = var.environment
  }
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    openai_api_key    = "PLACEHOLDER_OPENAI_KEY"
    meta_app_id       = "PLACEHOLDER_META_APP_ID"
    meta_app_secret   = "PLACEHOLDER_META_APP_SECRET"
    meta_access_token = "PLACEHOLDER_META_TOKEN"
    slack_webhook_url = "PLACEHOLDER_SLACK_WEBHOOK"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# IAM Role for Lambda functions
resource "aws_iam_role" "lambda_execution_role" {
  name = "${var.project_name}-lambda-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-lambda-role"
    Environment = var.environment
  }
}

# Lambda execution policy
resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.project_name}-lambda-policy-${var.environment}"
  role = aws_iam_role.lambda_execution_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:${data.aws_caller_identity.current.account_id}:*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          aws_dynamodb_table.comments.arn,
          aws_dynamodb_table.config.arn,
          aws_dynamodb_table.audit_logs.arn,
          "${aws_dynamodb_table.comments.arn}/*",
          "${aws_dynamodb_table.config.arn}/*",
          "${aws_dynamodb_table.audit_logs.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = [
          aws_sqs_queue.comment_processing.arn,
          aws_sqs_queue.comment_processing_dlq.arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = aws_secretsmanager_secret.api_keys.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.assets.arn}/*"
      }
    ]
  })
}

# EventBridge rule for scheduled ingestion
resource "aws_cloudwatch_event_rule" "comment_ingestion_schedule" {
  name                = "${var.project_name}-ingestion-${var.environment}"
  description         = "Trigger comment ingestion every 5 minutes"
  schedule_expression = "rate(5 minutes)"

  tags = {
    Name        = "${var.project_name}-schedule"
    Environment = var.environment
  }
}

# API Gateway for dashboard
resource "aws_api_gateway_rest_api" "dashboard_api" {
  name        = "${var.project_name}-api-${var.environment}"
  description = "ORM Platform Dashboard API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name        = "${var.project_name}-api"
    Environment = var.environment
  }
}

# API Gateway deployment (will be added later when we have methods)
# resource "aws_api_gateway_deployment" "dashboard_api_deployment" {
#   depends_on = [aws_api_gateway_rest_api.dashboard_api]
# 
#   rest_api_id = aws_api_gateway_rest_api.dashboard_api.id
#   stage_name  = var.environment
# 
#   lifecycle {
#     create_before_destroy = true
#   }
# }

# CloudWatch Log Groups for Lambda functions
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each = toset([
    "ingestion",
    "classification",
    "reply-handler",
    "hide-handler", 
    "escalation-handler",
    "dashboard-api"
  ])

  name              = "/aws/lambda/${var.project_name}-${each.key}-${var.environment}"
  retention_in_days = 7  # Free tier friendly

  tags = {
    Name        = "${var.project_name}-${each.key}-logs"
    Environment = var.environment
  }
}

# CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset([
    "ingestion",
    "classification", 
    "reply-handler",
    "hide-handler",
    "escalation-handler"
  ])

  alarm_name          = "${var.project_name}-${each.key}-errors-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"
  statistic           = "Sum"
  threshold           = "5"
  alarm_description   = "This metric monitors lambda errors"
  alarm_actions       = []  # Add SNS topic ARN for notifications

  dimensions = {
    FunctionName = "${var.project_name}-${each.key}-${var.environment}"
  }

  tags = {
    Name        = "${var.project_name}-${each.key}-alarm"
    Environment = var.environment
  }
}

# Outputs
output "dynamodb_tables" {
  description = "DynamoDB table names"
  value = {
    comments   = aws_dynamodb_table.comments.name
    config     = aws_dynamodb_table.config.name
    audit_logs = aws_dynamodb_table.audit_logs.name
  }
}

output "sqs_queue_url" {
  description = "SQS queue URL for comment processing"
  value       = aws_sqs_queue.comment_processing.url
}

output "s3_bucket_name" {
  description = "S3 bucket name for assets"
  value       = aws_s3_bucket.assets.id
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL (will be available after methods are added)"
  value       = "https://${aws_api_gateway_rest_api.dashboard_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
}

output "secrets_manager_secret_name" {
  description = "Secrets Manager secret name"
  value       = aws_secretsmanager_secret.api_keys.name
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda_execution_role.arn
}