output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "nat_gateway_ips" {
  description = "NAT Gateway public IPs"
  value       = module.vpc.nat_gateway_ips
}

# RDS Outputs
output "rds_endpoint" {
  description = "RDS instance endpoint (use this in Helm values for config.database.host)"
  value       = module.rds.db_instance_endpoint
}

output "rds_address" {
  description = "RDS instance address (hostname only)"
  value       = module.rds.db_instance_address
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.db_instance_port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.db_name
}

output "rds_master_username" {
  description = "RDS master username"
  value       = module.rds.db_master_username
  sensitive   = true
}

output "rds_connection_string" {
  description = "PostgreSQL connection string for DATABASE_URL"
  value       = "postgresql://${module.rds.db_master_username}:<PASSWORD>@${module.rds.db_instance_address}:${module.rds.db_instance_port}/${module.rds.db_name}"
  sensitive   = true
}

output "rds_secret_arn" {
  description = "ARN of AWS Secrets Manager secret containing RDS password"
  value       = module.rds.db_password_secret_arn
}

# ElastiCache Outputs
output "elasticache_endpoint" {
  description = "ElastiCache primary endpoint (use this in Helm values for config.redis.host)"
  value       = module.elasticache.primary_endpoint_address
}

output "elasticache_port" {
  description = "ElastiCache port"
  value       = module.elasticache.port
}

output "elasticache_redis_url" {
  description = "Redis connection URL for REDIS_URL"
  value       = "redis://${module.elasticache.primary_endpoint_address}:${module.elasticache.port}"
}

# EKS Outputs
output "eks_cluster_name" {
  description = "EKS cluster name (use with: aws eks update-kubeconfig --name <this>)"
  value       = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  description = "EKS cluster API endpoint"
  value       = module.eks.cluster_endpoint
}

output "eks_cluster_version" {
  description = "EKS cluster Kubernetes version"
  value       = module.eks.cluster_version
}

output "eks_cluster_security_group_id" {
  description = "EKS cluster security group ID"
  value       = module.eks.cluster_security_group_id
}

output "eks_worker_security_group_id" {
  description = "EKS worker node security group ID"
  value       = module.eks.worker_security_group_id
}

output "eks_oidc_provider_arn" {
  description = "ARN of EKS OIDC provider (for IRSA)"
  value       = module.eks.oidc_provider_arn
}

output "eks_cluster_certificate_authority" {
  description = "EKS cluster certificate authority data"
  value       = module.eks.cluster_certificate_authority
  sensitive   = true
}

output "eks_update_kubeconfig_command" {
  description = "Command to configure kubectl for this cluster"
  value       = "aws eks update-kubeconfig --region ${var.aws_region} --name ${module.eks.cluster_name}"
}

# IAM Outputs
output "service_account_role_arn" {
  description = "ARN of IAM role for Kubernetes service account (use in serviceAccount.annotations.eks.amazonaws.com/role-arn)"
  value       = module.iam.service_account_role_arn
}

output "service_account_role_name" {
  description = "Name of IAM role for service account"
  value       = module.iam.service_account_role_name
}

# ECR Outputs
output "ecr_backend_repository_url" {
  description = "ECR repository URL for backend (use in Helm values for backend.image.repository)"
  value       = module.ecr.backend_repository_url
}

output "ecr_frontend_repository_url" {
  description = "ECR repository URL for frontend (use in Helm values for frontend.image.repository)"
  value       = module.ecr.frontend_repository_url
}

output "ecr_login_command" {
  description = "Command to authenticate Docker with ECR"
  value       = "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${module.ecr.registry_url}"
}

# S3 Outputs
output "s3_logs_bucket" {
  description = "S3 bucket for application logs"
  value       = module.s3.logs_bucket_name
}

output "s3_backups_bucket" {
  description = "S3 bucket for database backups"
  value       = module.s3.backups_bucket_name
}

# Combined Output for Easy Helm Values Update
output "helm_values_snippet" {
  description = "Copy-paste this into values-production.yaml"
  value = <<-EOT
    # Update infrastructure/helm/sovd-webapp/values-production.yaml with these values:

    backend:
      image:
        repository: ${module.ecr.backend_repository_url}

    frontend:
      image:
        repository: ${module.ecr.frontend_repository_url}

    config:
      database:
        host: "${module.rds.db_instance_address}"
        port: "${module.rds.db_instance_port}"
        name: "${module.rds.db_name}"
        user: "${module.rds.db_master_username}"

      redis:
        host: "${module.elasticache.primary_endpoint_address}"
        port: "${module.elasticache.port}"

    serviceAccount:
      annotations:
        eks.amazonaws.com/role-arn: "${module.iam.service_account_role_arn}"
      name: "sovd-webapp-${var.environment}-sa"
  EOT
}

# AWS Secrets Manager Secret Names
output "secrets_manager_secret_names" {
  description = "AWS Secrets Manager secret names to create manually"
  value = {
    database = "sovd/${var.environment}/database"
    jwt      = "sovd/${var.environment}/jwt"
    redis    = "sovd/${var.environment}/redis"
  }
}

# Cost Estimate Summary
output "estimated_monthly_cost_usd" {
  description = "Estimated monthly cost breakdown (approximate)"
  value = var.environment == "production" ? {
    eks_control_plane = "~$73"
    eks_worker_nodes  = "~$270 (3x t3.large)"
    rds_multi_az      = "~$220 (db.t3.large Multi-AZ)"
    elasticache       = "~$85 (cache.t3.medium)"
    nat_gateways      = "~$100 (3x NAT @ $0.045/hr + data)"
    alb               = "~$25 (ALB + data transfer)"
    s3_ecr_misc       = "~$20 (storage, data transfer)"
    total             = "~$793/month"
  } : {
    eks_control_plane = "~$73"
    eks_worker_nodes  = "~$90 (3x t3.medium)"
    rds_single_az     = "~$70 (db.t3.medium Single-AZ)"
    elasticache       = "~$40 (cache.t3.small)"
    nat_gateway       = "~$35 (1x NAT)"
    alb               = "~$25"
    s3_ecr_misc       = "~$15"
    total             = "~$348/month"
  }
}
