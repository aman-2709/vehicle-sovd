# SOVD WebApp Helm Chart

A comprehensive Helm chart for deploying the SOVD Command WebApp on Kubernetes (AWS EKS).

## Overview

This Helm chart deploys a complete SOVD (Service-Oriented Vehicle Diagnostics) web application consisting of:

- **Backend**: FastAPI application (3 replicas by default)
- **Frontend**: React SPA served by Nginx (3 replicas by default)
- **Vehicle Connector**: gRPC service for vehicle communication (optional, 2 replicas)
- **Ingress**: AWS Application Load Balancer with TLS termination
- **Autoscaling**: Horizontal Pod Autoscaler for both backend and frontend
- **Configuration**: ConfigMaps for non-sensitive config and Secrets for sensitive data

## Prerequisites

Before installing this chart, ensure you have:

1. **Kubernetes Cluster**: AWS EKS cluster (v1.24+) with 3+ worker nodes
2. **kubectl**: Configured to access your cluster
   ```bash
   aws eks update-kubeconfig --region us-east-1 --name your-cluster-name
   ```
3. **Helm**: Version 3.8+ installed
   ```bash
   helm version
   ```
4. **AWS ALB Ingress Controller**: Installed in your cluster
   ```bash
   kubectl get deployment -n kube-system aws-load-balancer-controller
   ```
5. **Container Images**: Backend and frontend images pushed to ECR
6. **ECR Access**: ImagePullSecrets configured for private ECR repositories
7. **Database**: PostgreSQL database (RDS) accessible from the cluster
8. **Cache**: Redis cache (ElastiCache) accessible from the cluster

## Installation

### Quick Start (Development)

```bash
# Install with default values
helm install sovd-webapp ./infrastructure/helm/sovd-webapp \
  --namespace default \
  --create-namespace
```

### Production Installation

```bash
# Install with production values
helm install sovd-webapp ./infrastructure/helm/sovd-webapp \
  -f infrastructure/helm/sovd-webapp/values-production.yaml \
  --namespace production \
  --create-namespace \
  --set backend.image.tag=v1.0.0 \
  --set frontend.image.tag=v1.0.0
```

### Installation with Custom Values

```bash
helm install sovd-webapp ./infrastructure/helm/sovd-webapp \
  --namespace production \
  --set global.domain=sovd.mycompany.com \
  --set backend.image.repository=123456789012.dkr.ecr.us-east-1.amazonaws.com/sovd-backend \
  --set backend.image.tag=abc1234 \
  --set frontend.image.repository=123456789012.dkr.ecr.us-east-1.amazonaws.com/sovd-frontend \
  --set frontend.image.tag=abc1234 \
  --set config.database.host=my-rds-instance.us-east-1.rds.amazonaws.com \
  --set config.redis.host=my-elasticache.abc123.use1.cache.amazonaws.com
```

## Upgrading

### Standard Upgrade

```bash
helm upgrade sovd-webapp ./infrastructure/helm/sovd-webapp \
  -f infrastructure/helm/sovd-webapp/values-production.yaml \
  --namespace production \
  --set backend.image.tag=v1.1.0 \
  --set frontend.image.tag=v1.1.0
```

### Upgrade with Rollback on Failure

```bash
helm upgrade sovd-webapp ./infrastructure/helm/sovd-webapp \
  -f infrastructure/helm/sovd-webapp/values-production.yaml \
  --namespace production \
  --atomic \
  --timeout 10m
```

### Dry Run (Preview Changes)

```bash
helm upgrade sovd-webapp ./infrastructure/helm/sovd-webapp \
  -f infrastructure/helm/sovd-webapp/values-production.yaml \
  --namespace production \
  --dry-run \
  --debug
```

## Rollback

### Rollback to Previous Version

```bash
helm rollback sovd-webapp --namespace production
```

### Rollback to Specific Revision

```bash
# List revisions
helm history sovd-webapp --namespace production

# Rollback to specific revision
helm rollback sovd-webapp 3 --namespace production
```

## Uninstallation

```bash
helm uninstall sovd-webapp --namespace production
```

## Configuration

### Key Configuration Parameters

#### Global Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.namespace` | Kubernetes namespace | `default` |
| `global.domain` | Base domain for the application | `sovd.example.com` |

#### Backend Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `backend.enabled` | Enable backend deployment | `true` |
| `backend.replicaCount` | Number of backend replicas | `3` |
| `backend.image.repository` | Backend image repository | `YOUR_ECR_REGISTRY/sovd-backend` |
| `backend.image.tag` | Backend image tag | `latest` |
| `backend.resources.requests.memory` | Memory request | `256Mi` |
| `backend.resources.requests.cpu` | CPU request | `250m` |
| `backend.resources.limits.memory` | Memory limit | `512Mi` |
| `backend.resources.limits.cpu` | CPU limit | `500m` |

#### Frontend Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `frontend.enabled` | Enable frontend deployment | `true` |
| `frontend.replicaCount` | Number of frontend replicas | `3` |
| `frontend.image.repository` | Frontend image repository | `YOUR_ECR_REGISTRY/sovd-frontend` |
| `frontend.image.tag` | Frontend image tag | `latest` |
| `frontend.resources.requests.memory` | Memory request | `64Mi` |
| `frontend.resources.requests.cpu` | CPU request | `100m` |

#### HPA (Horizontal Pod Autoscaler)

| Parameter | Description | Default |
|-----------|-------------|---------|
| `hpa.enabled` | Enable HPA | `true` |
| `hpa.backend.minReplicas` | Minimum backend replicas | `3` |
| `hpa.backend.maxReplicas` | Maximum backend replicas | `10` |
| `hpa.backend.targetCPUUtilizationPercentage` | Target CPU utilization | `70` |

#### Ingress Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `true` |
| `ingress.className` | Ingress class | `alb` |
| `ingress.hosts[0].host` | Primary hostname | `sovd.example.com` |

#### Database Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `config.database.host` | Database hostname | `postgres.default.svc.cluster.local` |
| `config.database.port` | Database port | `5432` |
| `config.database.name` | Database name | `sovd` |
| `config.database.user` | Database user | `sovd_user` |
| `secrets.databasePassword` | Database password (base64) | `cGxhY2Vob2xkZXI=` |

#### Redis Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `config.redis.host` | Redis hostname | `redis.default.svc.cluster.local` |
| `config.redis.port` | Redis port | `6379` |
| `config.redis.db` | Redis database number | `0` |

### Production Configuration Checklist

Before deploying to production, update the following values:

- [ ] **Backend Image**: Set `backend.image.repository` and `backend.image.tag` to your ECR registry and specific version
- [ ] **Frontend Image**: Set `frontend.image.repository` and `frontend.image.tag`
- [ ] **Domain**: Set `global.domain` to your production domain
- [ ] **Database**: Set `config.database.host` to your RDS endpoint
- [ ] **Redis**: Set `config.redis.host` to your ElastiCache endpoint
- [ ] **Secrets**: Configure External Secrets Operator or manually update secrets
- [ ] **TLS Certificate**: Set `ingress.annotations.alb.ingress.kubernetes.io/certificate-arn` to your ACM certificate ARN
- [ ] **Resource Limits**: Adjust `backend.resources` and `frontend.resources` based on load testing
- [ ] **HPA Settings**: Tune `hpa.backend.minReplicas` and `hpa.backend.maxReplicas` based on expected traffic
- [ ] **ImagePullSecrets**: Configure `backend.imagePullSecrets` and `frontend.imagePullSecrets` for private ECR

## Secrets Management

### Development (Placeholder Secrets)

The chart includes base64-encoded placeholder secrets for development:

```bash
# Default placeholders (DO NOT use in production)
database-password: "placeholder" (base64: cGxhY2Vob2xkZXI=)
jwt-secret: "placeholder-jwt-secret-change-in-production"
```

### Production (External Secrets Operator)

For production, use [External Secrets Operator](https://external-secrets.io/) to sync secrets from AWS Secrets Manager:

1. **Install External Secrets Operator**:
   ```bash
   helm repo add external-secrets https://charts.external-secrets.io
   helm install external-secrets external-secrets/external-secrets -n external-secrets-system --create-namespace
   ```

2. **Create SecretStore**:
   ```yaml
   apiVersion: external-secrets.io/v1beta1
   kind: SecretStore
   metadata:
     name: aws-secrets-manager
     namespace: production
   spec:
     provider:
       aws:
         service: SecretsManager
         region: us-east-1
         auth:
           jwt:
             serviceAccountRef:
               name: sovd-webapp-production-sa
   ```

3. **Update secrets.yaml**: Uncomment the ExternalSecret configuration in `templates/secrets.yaml`

4. **Create secrets in AWS Secrets Manager**:
   ```bash
   aws secretsmanager create-secret --name sovd/production/database --secret-string '{"password":"YOUR_DB_PASSWORD"}'
   aws secretsmanager create-secret --name sovd/production/jwt --secret-string '{"secret":"YOUR_JWT_SECRET"}'
   aws secretsmanager create-secret --name sovd/production/redis --secret-string '{"password":"YOUR_REDIS_PASSWORD"}'
   ```

## Monitoring Deployment

### Check Deployment Status

```bash
# Watch rollout status
kubectl rollout status deployment/sovd-webapp-backend -n production
kubectl rollout status deployment/sovd-webapp-frontend -n production

# Check all resources
kubectl get all -n production -l app.kubernetes.io/instance=sovd-webapp

# Check HPA status
kubectl get hpa -n production
```

### View Logs

```bash
# Backend logs
kubectl logs -n production -l app=backend --tail=100 -f

# Frontend logs
kubectl logs -n production -l app=frontend --tail=100 -f
```

### Check Ingress

```bash
# Get Ingress details
kubectl get ingress -n production

# Get ALB details
kubectl describe ingress sovd-webapp-ingress -n production
```

## Troubleshooting

### Common Issues

#### 1. Pods Not Starting

```bash
# Check pod status
kubectl get pods -n production

# Describe pod for events
kubectl describe pod <pod-name> -n production

# Check logs
kubectl logs <pod-name> -n production
```

**Common causes**:
- ImagePullBackOff: Check `imagePullSecrets` and ECR permissions
- CrashLoopBackOff: Check application logs and environment variables
- Pending: Check resource requests vs cluster capacity

#### 2. Database Connection Errors

```bash
# Verify database configuration
kubectl get configmap sovd-webapp-config -n production -o yaml

# Test database connectivity from a pod
kubectl run -it --rm debug --image=postgres:15 --restart=Never -- psql -h YOUR_DB_HOST -U sovd_user -d sovd
```

**Checklist**:
- [ ] Database host is correct (RDS endpoint)
- [ ] Database credentials are correct in secrets
- [ ] Security groups allow traffic from EKS worker nodes
- [ ] Database is accessible from VPC

#### 3. Ingress Not Creating ALB

```bash
# Check ALB controller logs
kubectl logs -n kube-system -l app.kubernetes.io/name=aws-load-balancer-controller

# Verify ingress events
kubectl describe ingress sovd-webapp-ingress -n production
```

**Common causes**:
- ALB controller not installed
- Incorrect annotations
- IAM permissions missing for ALB controller

#### 4. HPA Not Scaling

```bash
# Check HPA status
kubectl get hpa -n production
kubectl describe hpa sovd-webapp-backend-hpa -n production

# Check metrics server
kubectl top nodes
kubectl top pods -n production
```

**Common causes**:
- Metrics server not installed
- Resource requests not set
- CPU utilization below threshold

### Health Checks

```bash
# Port-forward to backend and test health endpoints
kubectl port-forward -n production svc/backend 8000:8000

# In another terminal
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

## Testing the Chart

### Lint the Chart

```bash
# Lint for syntax errors and best practices
helm lint ./infrastructure/helm/sovd-webapp
```

### Template and Verify

```bash
# Generate templates without installing
helm template sovd-webapp ./infrastructure/helm/sovd-webapp \
  -f ./infrastructure/helm/sovd-webapp/values-production.yaml \
  --namespace production

# Save output to file for inspection
helm template sovd-webapp ./infrastructure/helm/sovd-webapp > output.yaml
```

### Dry Run Installation

```bash
# Test installation without actually deploying
helm install sovd-webapp ./infrastructure/helm/sovd-webapp \
  --namespace production \
  --dry-run \
  --debug
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     AWS ALB Ingress                      │
│                   (TLS Termination)                      │
└────────────┬────────────────────────────────┬───────────┘
             │                                │
             │ /api, /ws                      │ /
             │                                │
┌────────────▼────────────┐      ┌───────────▼───────────┐
│   Backend Service        │      │  Frontend Service      │
│   (ClusterIP:8000)       │      │  (ClusterIP:80)        │
└────────────┬────────────┘      └───────────┬───────────┘
             │                                │
   ┌─────────▼─────────┐          ┌──────────▼──────────┐
   │  Backend Pods     │          │  Frontend Pods      │
   │  (FastAPI)        │          │  (Nginx + React)    │
   │  Min: 3 Max: 10   │          │  Replicas: 3        │
   │  HPA: CPU 70%     │          │                     │
   └─────────┬─────────┘          └─────────────────────┘
             │
    ┌────────┴─────────┐
    │                  │
┌───▼────┐      ┌─────▼──────┐
│ RDS    │      │ ElastiCache│
│ (PG)   │      │ (Redis)    │
└────────┘      └────────────┘
```

## Best Practices

1. **Use Specific Image Tags**: Never use `latest` in production. Use commit SHAs or semantic versions.
   ```bash
   --set backend.image.tag=v1.0.0
   ```

2. **Resource Requests and Limits**: Always set both to ensure proper scheduling and prevent resource exhaustion.

3. **Health Checks**: The chart includes both liveness and readiness probes. Ensure your application implements these endpoints.

4. **Secrets Management**: Use External Secrets Operator in production. Never commit secrets to version control.

5. **Zero Downtime Deployments**: The chart uses rolling updates with `maxUnavailable: 0` to ensure zero downtime.

6. **Pod Anti-Affinity**: Backend pods have soft anti-affinity to spread across nodes for high availability.

7. **Monitoring**: Integrate with Prometheus and Grafana for observability (see deployment runbook).

## Related Documentation

- [Architecture Blueprint](../../../docs/architecture/architecture_blueprint.md)
- [Deployment Runbook](../../../docs/runbooks/deployment.md)
- [Operations Guide](../../../docs/runbooks/operations.md)
- [Iteration I5 Plan](../../../docs/planning/02_Iteration_I5.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review application logs: `kubectl logs -n production -l app=backend`
3. Check Kubernetes events: `kubectl get events -n production --sort-by='.lastTimestamp'`
4. Consult the operations runbook

## License

Copyright © 2025 SOVD Team
