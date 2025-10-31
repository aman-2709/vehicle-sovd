# ElastiCache Redis Module
# Creates Redis cluster for caching and pub/sub messaging

# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  name       = "sovd-${var.environment}-redis-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name        = "sovd-${var.environment}-redis-subnet-group"
    Environment = var.environment
  }
}

# Security Group for ElastiCache
resource "aws_security_group" "redis" {
  name        = "sovd-${var.environment}-redis-sg"
  description = "Security group for SOVD ElastiCache Redis"
  vpc_id      = var.vpc_id

  # Allow Redis access from EKS worker nodes
  ingress {
    description     = "Redis from EKS workers"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.eks_security_group_id]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "sovd-${var.environment}-redis-sg"
    Environment = var.environment
  }
}

# ElastiCache Parameter Group
resource "aws_elasticache_parameter_group" "main" {
  name   = "sovd-${var.environment}-redis7"
  family = "redis7"

  # Optimize for SOVD workload (caching + pub/sub)
  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru" # Evict least recently used keys when memory is full
  }

  parameter {
    name  = "timeout"
    value = "300" # Close idle connections after 5 minutes
  }

  tags = {
    Name        = "sovd-${var.environment}-redis7-params"
    Environment = var.environment
  }
}

# ElastiCache Replication Group (Redis Cluster)
resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "sovd-${var.environment}"
  description          = "SOVD ${var.environment} Redis cluster for caching and pub/sub"

  # Engine configuration
  engine         = "redis"
  engine_version = "7.1"
  port           = 6379

  # Node configuration
  node_type            = var.node_type
  num_cache_clusters   = var.num_cache_nodes
  parameter_group_name = aws_elasticache_parameter_group.main.name

  # Network configuration
  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  # High availability
  automatic_failover_enabled = var.automatic_failover && var.num_cache_nodes >= 2
  multi_az_enabled           = var.automatic_failover && var.num_cache_nodes >= 2

  # Backup configuration
  snapshot_retention_limit = var.environment == "production" ? 7 : 1
  snapshot_window          = "03:00-05:00" # UTC
  maintenance_window       = "mon:05:00-mon:07:00"

  # Security
  at_rest_encryption_enabled = true
  transit_encryption_enabled = false # Set to true if you want TLS (requires client configuration)
  auth_token_enabled         = false # Set to true to require password authentication

  # Notifications
  notification_topic_arn = "" # Add SNS topic ARN for notifications

  # Auto minor version upgrade
  auto_minor_version_upgrade = true

  tags = {
    Name        = "sovd-${var.environment}-redis"
    Environment = var.environment
  }

  lifecycle {
    ignore_changes = [num_cache_clusters]
  }
}

# CloudWatch Alarms for ElastiCache monitoring
resource "aws_cloudwatch_metric_alarm" "redis_cpu" {
  alarm_name          = "sovd-${var.environment}-redis-high-cpu"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "75"
  alarm_description   = "This metric monitors ElastiCache CPU utilization"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = {
    Name        = "sovd-${var.environment}-redis-cpu-alarm"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_memory" {
  alarm_name          = "sovd-${var.environment}-redis-low-memory"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeableMemory"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "536870912" # 512 MB in bytes
  alarm_description   = "This metric monitors ElastiCache freeable memory"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = {
    Name        = "sovd-${var.environment}-redis-memory-alarm"
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "redis_evictions" {
  alarm_name          = "sovd-${var.environment}-redis-high-evictions"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "Evictions"
  namespace           = "AWS/ElastiCache"
  period              = "300"
  statistic           = "Average"
  threshold           = "1000"
  alarm_description   = "This metric monitors ElastiCache evictions"
  alarm_actions       = [] # Add SNS topic ARN for notifications

  dimensions = {
    ReplicationGroupId = aws_elasticache_replication_group.main.id
  }

  tags = {
    Name        = "sovd-${var.environment}-redis-evictions-alarm"
    Environment = var.environment
  }
}
