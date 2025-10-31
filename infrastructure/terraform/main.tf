terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration for remote state storage
  # Initialize S3 bucket and DynamoDB table manually before first run:
  # aws s3 mb s3://sovd-terraform-state-<AWS_ACCOUNT_ID>
  # aws dynamodb create-table --table-name sovd-terraform-locks \
  #   --attribute-definitions AttributeName=LockID,AttributeType=S \
  #   --key-schema AttributeName=LockID,KeyType=HASH \
  #   --billing-mode PAY_PER_REQUEST
  backend "s3" {
    bucket         = "sovd-terraform-state-${AWS_ACCOUNT_ID}" # Replace with your bucket name
    key            = "sovd-webapp/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "sovd-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Application = "sovd-webapp"
      ManagedBy   = "Terraform"
      Environment = var.environment
      Project     = "SOVD"
    }
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"

  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  public_subnet_cidrs = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  enable_nat_gateway  = var.enable_nat_gateway
  single_nat_gateway  = var.single_nat_gateway
}

# S3 Module (for application logs, backups)
module "s3" {
  source = "./modules/s3"

  environment    = var.environment
  aws_account_id = data.aws_caller_identity.current.account_id
}

# RDS Module
module "rds" {
  source = "./modules/rds"

  environment               = var.environment
  vpc_id                    = module.vpc.vpc_id
  private_subnet_ids        = module.vpc.private_subnet_ids
  eks_security_group_id     = module.eks.worker_security_group_id
  instance_class            = var.rds_instance_class
  allocated_storage         = var.rds_allocated_storage
  max_allocated_storage     = var.rds_max_allocated_storage
  database_name             = var.rds_database_name
  master_username           = var.rds_master_username
  backup_retention_period   = var.rds_backup_retention_period
  multi_az                  = var.rds_multi_az
  deletion_protection       = var.rds_deletion_protection
  skip_final_snapshot       = var.environment != "production"
}

# ElastiCache Module
module "elasticache" {
  source = "./modules/elasticache"

  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  eks_security_group_id  = module.eks.worker_security_group_id
  node_type              = var.elasticache_node_type
  num_cache_nodes        = var.elasticache_num_cache_nodes
  automatic_failover     = var.elasticache_automatic_failover
}

# EKS Module
module "eks" {
  source = "./modules/eks"

  environment        = var.environment
  vpc_id             = module.vpc.vpc_id
  private_subnet_ids = module.vpc.private_subnet_ids
  public_subnet_ids  = module.vpc.public_subnet_ids
  cluster_version    = var.eks_cluster_version
  node_instance_type = var.eks_node_instance_type
  node_desired_size  = var.eks_node_desired_size
  node_min_size      = var.eks_node_min_size
  node_max_size      = var.eks_node_max_size
}

# IAM Module (for service accounts, policies)
module "iam" {
  source = "./modules/iam"

  environment       = var.environment
  aws_account_id    = data.aws_caller_identity.current.account_id
  eks_cluster_name  = module.eks.cluster_name
  oidc_provider_arn = module.eks.oidc_provider_arn
  oidc_provider_url = module.eks.oidc_provider_url
}

# ECR Module
module "ecr" {
  source = "./modules/ecr"

  environment = var.environment
}
