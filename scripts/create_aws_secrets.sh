#!/bin/bash

# create_aws_secrets.sh
# Creates AWS Secrets Manager secrets for SOVD WebApp
# Requires: AWS CLI configured with appropriate credentials
# Usage: ./create_aws_secrets.sh <environment> [region]
# Example: ./create_aws_secrets.sh production us-east-1

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="${1:-production}"
AWS_REGION="${2:-us-east-1}"
TERRAFORM_DIR="../infrastructure/terraform"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(production|staging)$ ]]; then
    echo -e "${RED}Error: Environment must be 'production' or 'staging'${NC}"
    echo "Usage: $0 <environment> [region]"
    exit 1
fi

echo -e "${GREEN}Creating AWS Secrets Manager secrets for SOVD WebApp${NC}"
echo "Environment: $ENVIRONMENT"
echo "AWS Region: $AWS_REGION"
echo ""

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2
    local description=$3

    echo -n "Creating/updating secret: $secret_name... "

    # Check if secret exists
    if aws secretsmanager describe-secret --secret-id "$secret_name" --region "$AWS_REGION" &>/dev/null; then
        # Update existing secret
        aws secretsmanager put-secret-value \
            --secret-id "$secret_name" \
            --secret-string "$secret_value" \
            --region "$AWS_REGION" \
            --force-overwrite-replica-secret &>/dev/null
        echo -e "${YELLOW}Updated${NC}"
    else
        # Create new secret
        aws secretsmanager create-secret \
            --name "$secret_name" \
            --description "$description" \
            --secret-string "$secret_value" \
            --region "$AWS_REGION" &>/dev/null
        echo -e "${GREEN}Created${NC}"
    fi
}

# Function to read Terraform outputs
get_terraform_output() {
    local output_name=$1
    local default_value=$2

    if [ -d "$TERRAFORM_DIR/environments/$ENVIRONMENT" ]; then
        local value=$(cd "$TERRAFORM_DIR/environments/$ENVIRONMENT" && terraform output -raw "$output_name" 2>/dev/null || echo "")
        if [ -n "$value" ]; then
            echo "$value"
        else
            echo "$default_value"
        fi
    else
        echo "$default_value"
    fi
}

# Extract connection details from Terraform outputs or use defaults
echo "Reading Terraform outputs..."

# Database configuration
DB_ENDPOINT=$(get_terraform_output "rds_endpoint" "")
DB_USERNAME=$(get_terraform_output "rds_username" "sovd_admin")
DB_NAME=$(get_terraform_output "rds_database_name" "sovd_${ENVIRONMENT}")

if [ -z "$DB_ENDPOINT" ]; then
    echo -e "${YELLOW}Warning: RDS endpoint not found in Terraform outputs${NC}"
    echo "Please provide database details manually:"
    read -p "Database endpoint (host:port): " DB_ENDPOINT
    read -p "Database username [$DB_USERNAME]: " input_username
    DB_USERNAME="${input_username:-$DB_USERNAME}"
    read -p "Database name [$DB_NAME]: " input_dbname
    DB_NAME="${input_dbname:-$DB_NAME}"
fi

# Generate secure database password
echo "Generating secure database password..."
DB_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-32)

# Construct DATABASE_URL
DATABASE_URL="postgresql+asyncpg://${DB_USERNAME}:${DB_PASSWORD}@${DB_ENDPOINT}/${DB_NAME}"

# Redis configuration
REDIS_ENDPOINT=$(get_terraform_output "redis_endpoint" "")

if [ -z "$REDIS_ENDPOINT" ]; then
    echo -e "${YELLOW}Warning: Redis endpoint not found in Terraform outputs${NC}"
    read -p "Redis endpoint (host:port): " REDIS_ENDPOINT
fi

# Redis URLs for ElastiCache don't typically use passwords (encryption in-transit via TLS)
# But we'll create a simple URL structure
REDIS_URL="redis://${REDIS_ENDPOINT}/0"

# Generate secure JWT secret
echo "Generating secure JWT secret..."
JWT_SECRET=$(openssl rand -base64 64 | tr -d "=+/" | cut -c1-64)

echo ""
echo -e "${GREEN}Creating secrets in AWS Secrets Manager...${NC}"

# Create database secret
create_or_update_secret \
    "sovd/${ENVIRONMENT}/database" \
    "{\"DATABASE_URL\":\"${DATABASE_URL}\",\"DB_HOST\":\"${DB_ENDPOINT%:*}\",\"DB_PORT\":\"${DB_ENDPOINT#*:}\",\"DB_NAME\":\"${DB_NAME}\",\"DB_USERNAME\":\"${DB_USERNAME}\",\"DB_PASSWORD\":\"${DB_PASSWORD}\"}" \
    "SOVD ${ENVIRONMENT} database credentials and connection string"

# Create JWT secret
create_or_update_secret \
    "sovd/${ENVIRONMENT}/jwt" \
    "{\"JWT_SECRET\":\"${JWT_SECRET}\"}" \
    "SOVD ${ENVIRONMENT} JWT signing secret"

# Create Redis secret
create_or_update_secret \
    "sovd/${ENVIRONMENT}/redis" \
    "{\"REDIS_URL\":\"${REDIS_URL}\",\"REDIS_HOST\":\"${REDIS_ENDPOINT%:*}\",\"REDIS_PORT\":\"${REDIS_ENDPOINT#*:}\"}" \
    "SOVD ${ENVIRONMENT} Redis connection string"

echo ""
echo -e "${GREEN}✓ All secrets created successfully!${NC}"
echo ""
echo "Secret ARNs:"
echo "  sovd/${ENVIRONMENT}/database"
echo "  sovd/${ENVIRONMENT}/jwt"
echo "  sovd/${ENVIRONMENT}/redis"
echo ""
echo -e "${YELLOW}IMPORTANT: Store the database password securely!${NC}"
echo "Database Password: ${DB_PASSWORD}"
echo ""
echo -e "${YELLOW}Note: If you need to update RDS master password, run:${NC}"
echo "aws rds modify-db-instance \\"
echo "  --db-instance-identifier sovd-${ENVIRONMENT}-db \\"
echo "  --master-user-password '${DB_PASSWORD}' \\"
echo "  --apply-immediately \\"
echo "  --region ${AWS_REGION}"
echo ""
echo "Next steps:"
echo "1. Update RDS master password using the command above"
echo "2. Verify External Secrets Operator is installed: helm list -n external-secrets-system"
echo "3. Deploy SOVD WebApp with External Secrets enabled"
echo "4. Verify secrets are synced: kubectl get externalsecrets -n ${ENVIRONMENT}"
