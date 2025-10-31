# IAM Module
# Creates IAM roles and policies for service accounts (IRSA) and application access

# IAM Role for Kubernetes Service Account (IRSA)
# This role allows the SOVD application pods to access AWS services (Secrets Manager, ECR, S3)
resource "aws_iam_role" "service_account" {
  name = "sovd-${var.environment}-service-account-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Federated = var.oidc_provider_arn
        }
        Action = "sts:AssumeRoleWithWebIdentity"
        Condition = {
          StringEquals = {
            "${replace(var.oidc_provider_url, "https://", "")}:sub" = "system:serviceaccount:${var.environment}:sovd-webapp-${var.environment}-sa"
            "${replace(var.oidc_provider_url, "https://", "")}:aud" = "sts.amazonaws.com"
          }
        }
      }
    ]
  })

  tags = {
    Name        = "sovd-${var.environment}-service-account-role"
    Environment = var.environment
  }
}

# Policy for AWS Secrets Manager access
resource "aws_iam_policy" "secrets_manager_access" {
  name        = "sovd-${var.environment}-secrets-manager-access"
  description = "Allow SOVD application to read secrets from AWS Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          "arn:aws:secretsmanager:*:${var.aws_account_id}:secret:sovd/${var.environment}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "sovd-${var.environment}-secrets-manager-policy"
    Environment = var.environment
  }
}

# Policy for S3 access (logs, backups)
resource "aws_iam_policy" "s3_access" {
  name        = "sovd-${var.environment}-s3-access"
  description = "Allow SOVD application to access S3 buckets for logs and backups"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::sovd-${var.environment}-logs/*",
          "arn:aws:s3:::sovd-${var.environment}-logs",
          "arn:aws:s3:::sovd-${var.environment}-backups/*",
          "arn:aws:s3:::sovd-${var.environment}-backups"
        ]
      }
    ]
  })

  tags = {
    Name        = "sovd-${var.environment}-s3-policy"
    Environment = var.environment
  }
}

# Attach policies to service account role
resource "aws_iam_role_policy_attachment" "service_account_secrets_manager" {
  role       = aws_iam_role.service_account.name
  policy_arn = aws_iam_policy.secrets_manager_access.arn
}

resource "aws_iam_role_policy_attachment" "service_account_s3" {
  role       = aws_iam_role.service_account.name
  policy_arn = aws_iam_policy.s3_access.arn
}

# CloudWatch Logs policy for application logging
resource "aws_iam_policy" "cloudwatch_logs" {
  name        = "sovd-${var.environment}-cloudwatch-logs"
  description = "Allow SOVD application to write logs to CloudWatch"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "arn:aws:logs:*:${var.aws_account_id}:log-group:/aws/sovd/${var.environment}/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "sovd-${var.environment}-cloudwatch-logs-policy"
    Environment = var.environment
  }
}

resource "aws_iam_role_policy_attachment" "service_account_cloudwatch" {
  role       = aws_iam_role.service_account.name
  policy_arn = aws_iam_policy.cloudwatch_logs.arn
}
