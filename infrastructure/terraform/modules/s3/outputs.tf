output "logs_bucket_name" {
  description = "Name of the S3 bucket for application logs"
  value       = aws_s3_bucket.logs.id
}

output "logs_bucket_arn" {
  description = "ARN of the S3 bucket for application logs"
  value       = aws_s3_bucket.logs.arn
}

output "backups_bucket_name" {
  description = "Name of the S3 bucket for database backups"
  value       = aws_s3_bucket.backups.id
}

output "backups_bucket_arn" {
  description = "ARN of the S3 bucket for database backups"
  value       = aws_s3_bucket.backups.arn
}
