output "service_account_role_arn" {
  description = "ARN of the IAM role for Kubernetes service account"
  value       = aws_iam_role.service_account.arn
}

output "service_account_role_name" {
  description = "Name of the IAM role for service account"
  value       = aws_iam_role.service_account.name
}

output "secrets_manager_policy_arn" {
  description = "ARN of the Secrets Manager access policy"
  value       = aws_iam_policy.secrets_manager_access.arn
}

output "s3_access_policy_arn" {
  description = "ARN of the S3 access policy"
  value       = aws_iam_policy.s3_access.arn
}

output "cloudwatch_logs_policy_arn" {
  description = "ARN of the CloudWatch Logs policy"
  value       = aws_iam_policy.cloudwatch_logs.arn
}
