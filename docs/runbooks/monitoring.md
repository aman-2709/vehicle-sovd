# Monitoring Guide

This guide explains the monitoring infrastructure, metrics, dashboards, and alerting strategy for the SOVD Web Application.

## Table of Contents

- [Overview](#overview)
- [Monitoring Stack](#monitoring-stack)
- [Metrics Collection](#metrics-collection)
  - [Application Metrics](#application-metrics)
  - [Infrastructure Metrics](#infrastructure-metrics)
  - [Business Metrics](#business-metrics)
- [Grafana Dashboards](#grafana-dashboards)
- [Prometheus Queries](#prometheus-queries)
- [Alert Rules](#alert-rules)
- [Log Analysis](#log-analysis)
- [Health Monitoring](#health-monitoring)
- [Performance Baselines](#performance-baselines)

---

## Overview

The SOVD monitoring strategy provides:
- **Real-time visibility** into application and infrastructure health
- **Proactive alerting** for critical issues before they impact users
- **Historical analysis** for capacity planning and incident investigation
- **Business insights** for understanding system usage patterns

**Key Principles**:
1. **Monitor what matters**: Focus on user-impacting metrics
2. **Alert on symptoms, not causes**: Alert when users are affected
3. **Make data actionable**: Every alert should have a runbook
4. **Reduce noise**: Set appropriate thresholds to avoid alert fatigue

---

## Monitoring Stack

| Component | Purpose | Access |
|-----------|---------|--------|
| **Prometheus** | Time-series metrics database | http://localhost:9090 (local) |
| **Grafana** | Visualization dashboards | http://localhost:3001 (local) |
| **CloudWatch** | AWS infrastructure metrics | AWS Console (production) |
| **Application Logs** | Structured JSON logging | Docker logs (local), CloudWatch Logs (production) |
| **Health Endpoints** | Service health checks | `/health/live`, `/health/ready` |

### Access Credentials

**Local Development**:
- Prometheus: No authentication
- Grafana: admin / admin (change after first login)

**Production**:
- Grafana: SSO via corporate identity provider
- Prometheus: Accessed via Grafana (no direct access)
- CloudWatch: AWS IAM roles

---

## Metrics Collection

### Application Metrics

The SOVD application exposes custom metrics via Prometheus at `/metrics` endpoint.

#### Command Execution Metrics

**`commands_executed_total`** (Counter)
- **Description**: Total number of commands executed, labeled by vehicle and status
- **Labels**: `vehicle_id`, `command_type`, `status` (success/failed)
- **Use Case**: Track command success rate, identify problematic vehicles

**Example Query**:
```promql
# Total commands in last hour
sum(increase(commands_executed_total[1h]))

# Success rate
sum(rate(commands_executed_total{status="success"}[5m]))
/
sum(rate(commands_executed_total[5m]))
```

**Normal Values**:
- Success rate: >95%
- Total commands: Varies by usage (10-1000/hour)

**Warning Signs**:
- Success rate <90%: Check vehicle connectivity
- Sudden drop in volume: Possible authentication issues

---

**`command_execution_duration_seconds`** (Histogram)
- **Description**: Time taken to execute commands (end-to-end)
- **Labels**: `command_type`
- **Buckets**: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0 seconds
- **Use Case**: Monitor command latency, identify slow operations

**Example Query**:
```promql
# P95 latency by command type
histogram_quantile(0.95,
  sum(rate(command_execution_duration_seconds_bucket[5m])) by (command_type, le)
)

# Average latency
rate(command_execution_duration_seconds_sum[5m])
/
rate(command_execution_duration_seconds_count[5m])
```

**Normal Values**:
- P50 latency: 0.5-1.0 seconds
- P95 latency: 2-3 seconds
- P99 latency: <5 seconds

**Warning Signs**:
- P95 >5 seconds: Vehicle response slow, network issues
- P99 >10 seconds: Investigate backend performance

---

#### WebSocket Metrics

**`websocket_connections_active`** (Gauge)
- **Description**: Number of currently active WebSocket connections
- **Labels**: None
- **Use Case**: Monitor concurrent user activity

**Example Query**:
```promql
# Current active connections
websocket_connections_active

# Average over last hour
avg_over_time(websocket_connections_active[1h])
```

**Normal Values**:
- Development: 0-5 connections
- Production: 10-100 connections (depends on user count)

**Warning Signs**:
- Sudden drop to 0: WebSocket server crashed
- Unusually high (>500): Possible connection leak or DoS attack

---

**`websocket_messages_total`** (Counter)
- **Description**: Total WebSocket messages sent/received
- **Labels**: `direction` (sent/received), `message_type`
- **Use Case**: Track WebSocket traffic volume

**Example Query**:
```promql
# Messages per second
rate(websocket_messages_total[1m])

# Sent vs received ratio
rate(websocket_messages_total{direction="sent"}[5m])
/
rate(websocket_messages_total{direction="received"}[5m])
```

---

#### Vehicle Connection Metrics

**`vehicle_connections_active`** (Gauge)
- **Description**: Number of vehicles currently connected
- **Labels**: `vehicle_id`
- **Use Case**: Monitor vehicle availability

**Example Query**:
```promql
# Total connected vehicles
sum(vehicle_connections_active)

# Specific vehicle status
vehicle_connections_active{vehicle_id="WDD1234567890ABCD"}
```

**Normal Values**:
- Development: 2 vehicles (seed data)
- Production: Varies by fleet size

**Warning Signs**:
- No vehicles connected: Network issue or vehicle connector service down
- Specific vehicle offline: Check vehicle logs in `troubleshooting.md`

---

#### HTTP Metrics (from FastAPI)

**`http_requests_total`** (Counter)
- **Description**: Total HTTP requests
- **Labels**: `method`, `endpoint`, `status_code`
- **Use Case**: Track API usage and error rates

**Example Query**:
```promql
# Requests per second by endpoint
sum(rate(http_requests_total[1m])) by (endpoint)

# Error rate (5xx responses)
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
```

**Normal Values**:
- Total RPS: 10-100 (varies by load)
- Error rate: <1%

**Warning Signs**:
- Error rate >5%: Backend issues, check logs
- Sudden traffic spike: Possible attack or viral event

---

**`http_request_duration_seconds`** (Histogram)
- **Description**: HTTP request latency
- **Labels**: `method`, `endpoint`
- **Use Case**: Identify slow endpoints

**Example Query**:
```promql
# P95 latency by endpoint
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket[5m])) by (endpoint, le)
)
```

**Normal Values**:
- P50: 50-200ms
- P95: 200-500ms
- P99: <1s

**Warning Signs**:
- P95 >1s: Database query performance issue
- Specific endpoint slow: Investigate that handler in backend code

---

### Infrastructure Metrics

#### Database Metrics (PostgreSQL)

**CloudWatch RDS Metrics** (Production):
- `DatabaseConnections`: Active connections to database
- `CPUUtilization`: Database CPU usage
- `FreeableMemory`: Available memory
- `ReadLatency` / `WriteLatency`: Disk I/O latency
- `NetworkReceiveThroughput` / `NetworkTransmitThroughput`: Network traffic

**Normal Values**:
- CPU: <70%
- Connections: <50% of max_connections (typically <100)
- Read/Write Latency: <10ms

**Warning Signs**:
- CPU >80%: Consider vertical scaling or query optimization
- Connections near max: Connection pool exhausted, possible leak
- High latency: Storage performance issue

#### Redis Metrics (ElastiCache)

**CloudWatch ElastiCache Metrics** (Production):
- `CurrConnections`: Active connections
- `EngineCPUUtilization`: Redis CPU usage
- `DatabaseMemoryUsagePercentage`: Memory usage
- `NetworkBytesIn` / `NetworkBytesOut`: Network traffic
- `CacheHits` / `CacheMisses`: Cache efficiency

**Normal Values**:
- CPU: <60%
- Memory: <80%
- Cache hit rate: >80%

**Warning Signs**:
- Memory >90%: Risk of eviction, increase memory or reduce TTL
- Cache hit rate <50%: Poor cache strategy

#### Kubernetes Metrics (Production)

- `kube_pod_status_phase`: Pod status (Running, Pending, Failed)
- `kube_deployment_status_replicas_available`: Available replicas
- `container_cpu_usage_seconds_total`: Container CPU usage
- `container_memory_working_set_bytes`: Container memory usage

**Example Query**:
```promql
# Pods not in Running state
count(kube_pod_status_phase{phase!="Running", namespace="production"})

# CPU usage by pod
rate(container_cpu_usage_seconds_total{namespace="production"}[5m])
```

---

### Business Metrics

These metrics provide insights into application usage:

**`active_users`** (Gauge)
- Number of users logged in (based on valid JWT tokens in last 30 min)

**`commands_by_type_total`** (Counter)
- Commands grouped by type (ReadDTC, ClearDTC, etc.)

**`command_execution_errors_total`** (Counter)
- Failed commands grouped by error type
- **Labels**: `error_type` (timeout, vehicle_unreachable, invalid_command, etc.)

**Example Query**:
```promql
# Most common command types
topk(5, sum(increase(commands_by_type_total[1h])) by (command_type))

# Most common error types
topk(5, sum(increase(command_execution_errors_total[1h])) by (error_type))
```

---

## Grafana Dashboards

The SOVD application includes 3 pre-configured Grafana dashboards (auto-provisioned from `monitoring/grafana/dashboards/`).

### Dashboard 1: Operations Dashboard

**Purpose**: Overall system health and performance

**Panels**:
1. **Request Rate**: Requests per second (RPS) over time
2. **Error Rate**: Percentage of 5xx responses
3. **Latency (P50, P95, P99)**: HTTP request latency percentiles
4. **Active Connections**: WebSocket and database connections
5. **CPU Usage**: Backend container CPU usage
6. **Memory Usage**: Backend container memory usage
7. **Database Connections**: PostgreSQL active connections
8. **Redis Operations**: Redis commands per second

**Use Cases**:
- Daily health checks
- Incident investigation
- Capacity planning

**Key Metrics to Watch**:
- Error rate should be <1%
- P95 latency should be <1s
- Database connections should be stable (not growing)

**Access**: http://localhost:3001/d/operations (local)

---

### Dashboard 2: Commands Dashboard

**Purpose**: Monitor SOVD command execution

**Panels**:
1. **Command Execution Rate**: Commands per minute
2. **Command Success Rate**: Percentage of successful commands
3. **Command Latency**: P95 latency by command type
4. **Commands by Type**: Breakdown of command types
5. **Failed Commands**: Error count by error type
6. **Top Vehicles**: Most active vehicles by command count

**Use Cases**:
- Monitor command success rate
- Identify slow command types
- Debug vehicle-specific issues

**Key Metrics to Watch**:
- Success rate should be >95%
- Latency should be <3s for P95
- No single vehicle should dominate traffic (indicates issue)

**Access**: http://localhost:3001/d/commands (local)

---

### Dashboard 3: Vehicles Dashboard

**Purpose**: Monitor vehicle connectivity and status

**Panels**:
1. **Connected Vehicles**: Number of vehicles currently connected
2. **Vehicle Connection Status**: Status by vehicle (up/down)
3. **Vehicle Response Time**: Latency by vehicle
4. **Vehicle Command History**: Recent commands per vehicle
5. **Vehicle Errors**: Error count by vehicle

**Use Cases**:
- Monitor vehicle fleet health
- Identify problematic vehicles
- Track vehicle availability

**Key Metrics to Watch**:
- All registered vehicles should be connected
- Response time should be consistent across vehicles
- No vehicles should have persistent errors

**Access**: http://localhost:3001/d/vehicles (local)

---

## Prometheus Queries

Common PromQL queries for manual investigation.

### Availability Queries

```promql
# Service uptime (% of time with successful health checks)
avg_over_time(up{job="backend"}[1d]) * 100

# Number of restarts in last 24h
increase(kube_pod_container_status_restarts_total{namespace="production"}[24h])
```

### Performance Queries

```promql
# Request rate by status code
sum(rate(http_requests_total[5m])) by (status_code)

# Slowest endpoints (P95)
topk(10,
  histogram_quantile(0.95,
    sum(rate(http_request_duration_seconds_bucket[5m])) by (endpoint, le)
  )
)

# Database query latency
rate(pg_stat_statements_total_time[5m]) / rate(pg_stat_statements_calls[5m])
```

### Capacity Queries

```promql
# CPU usage trend (1-week average)
avg_over_time(container_cpu_usage_seconds_total{namespace="production"}[1w])

# Memory usage trend
avg_over_time(container_memory_working_set_bytes{namespace="production"}[1w])

# Disk I/O trend
rate(node_disk_io_time_seconds_total[5m])
```

### Business Queries

```promql
# Daily active users
count(count_over_time(http_requests_total{endpoint="/api/v1/auth/login"}[24h]))

# Most popular command types (last 24h)
topk(10, sum(increase(commands_executed_total[24h])) by (command_type))

# Busiest hour of the day
sum(increase(http_requests_total[1h])) by (hour)
```

---

## Alert Rules

Alert rules are defined in `monitoring/prometheus/alerts.yml` (for local) and Kubernetes AlertManager (for production).

### Critical Alerts (P1)

**Alert**: `ServiceDown`
- **Condition**: `up{job="backend"} == 0`
- **Duration**: 1 minute
- **Severity**: Critical
- **Action**: Page on-call engineer immediately
- **Runbook**: Check pod status, view logs, restart if necessary

**Alert**: `DatabaseDown`
- **Condition**: `up{job="postgres"} == 0`
- **Duration**: 1 minute
- **Severity**: Critical
- **Action**: Page on-call engineer immediately
- **Runbook**: Check RDS status, check connectivity from backend

**Alert**: `HighErrorRate`
- **Condition**: `(sum(rate(http_requests_total{status_code=~"5.."}[5m])) / sum(rate(http_requests_total[5m]))) > 0.05`
- **Duration**: 5 minutes
- **Severity**: Critical
- **Action**: Page on-call engineer
- **Runbook**: Check backend logs for errors, review recent deployments

---

### Warning Alerts (P2)

**Alert**: `HighLatency`
- **Condition**: `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 3`
- **Duration**: 10 minutes
- **Severity**: Warning
- **Action**: Notify via Slack
- **Runbook**: Check database query performance, check vehicle response time

**Alert**: `LowCommandSuccessRate`
- **Condition**: `(sum(rate(commands_executed_total{status="success"}[5m])) / sum(rate(commands_executed_total[5m]))) < 0.9`
- **Duration**: 10 minutes
- **Severity**: Warning
- **Action**: Notify via Slack
- **Runbook**: Check vehicle connectivity, review command logs

**Alert**: `HighCPUUsage`
- **Condition**: `rate(container_cpu_usage_seconds_total{namespace="production"}[5m]) > 0.8`
- **Duration**: 15 minutes
- **Severity**: Warning
- **Action**: Notify via Slack
- **Runbook**: Consider scaling up pods, investigate CPU-intensive operations

**Alert**: `HighMemoryUsage`
- **Condition**: `container_memory_working_set_bytes{namespace="production"} / container_spec_memory_limit_bytes > 0.9`
- **Duration**: 15 minutes
- **Severity**: Warning
- **Action**: Notify via Slack
- **Runbook**: Check for memory leaks, consider increasing memory limits

---

### Info Alerts (P3)

**Alert**: `DatabaseConnectionsHigh`
- **Condition**: `sum(pg_stat_activity_count) > 80`
- **Duration**: 30 minutes
- **Severity**: Info
- **Action**: Log to monitoring channel
- **Runbook**: Monitor for connection leaks, increase pool size if needed

**Alert**: `DiskSpaceLow`
- **Condition**: `(node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.2`
- **Duration**: 1 hour
- **Severity**: Info
- **Action**: Create ticket for disk cleanup
- **Runbook**: Clean up old logs, increase disk size

---

## Log Analysis

### Structured Logging Format

All logs are in JSON format with the following fields:

```json
{
  "timestamp": "2025-10-30T14:32:01.234Z",
  "level": "INFO",
  "logger": "sovd.api.commands",
  "message": "Command executed successfully",
  "correlation_id": "abc123-def456-ghi789",
  "user_id": "john_doe",
  "vehicle_id": "WDD1234567890ABCD",
  "command_type": "ReadDTC",
  "duration_ms": 1234
}
```

### Log Levels

| Level | Use Case | Example |
|-------|----------|---------|
| **DEBUG** | Development debugging | "Entering function foo with args..." |
| **INFO** | Normal operations | "Command executed successfully" |
| **WARNING** | Recoverable errors | "Vehicle response slow (3.5s)" |
| **ERROR** | Unexpected errors | "Database query failed: connection lost" |
| **CRITICAL** | Service failures | "Redis unreachable, service degraded" |

### Searching Logs

**Local (Docker)**:
```bash
# Show all logs
docker-compose logs backend

# Filter by level
docker-compose logs backend | grep ERROR

# Follow logs in real-time
docker-compose logs -f backend

# Search by correlation ID
docker-compose logs backend | grep "abc123-def456"
```

**Production (CloudWatch Logs)**:
```
# CloudWatch Insights query
fields @timestamp, message, level, correlation_id, user_id
| filter level = "ERROR"
| sort @timestamp desc
| limit 100
```

**Using `jq` for JSON parsing**:
```bash
# Pretty-print logs
docker-compose logs backend --no-log-prefix | jq '.'

# Filter by user
docker-compose logs backend --no-log-prefix | jq 'select(.user_id == "john_doe")'

# Extract command latency
docker-compose logs backend --no-log-prefix | jq 'select(.command_type) | .duration_ms'
```

---

## Health Monitoring

### Liveness Probe

**Endpoint**: `GET /health/live`

**Purpose**: Is the service running?

**Response**:
```json
{"status": "ok"}
```

**Use Case**: Kubernetes liveness probe (restart pod if fails)

**Check interval**: Every 10 seconds

---

### Readiness Probe

**Endpoint**: `GET /health/ready`

**Purpose**: Is the service ready to accept traffic?

**Response**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected"
}
```

**Unhealthy response** (503 status):
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "redis": "connected"
}
```

**Use Case**: Kubernetes readiness probe (remove from load balancer if fails)

**Check interval**: Every 5 seconds

**Implementation**: See `backend/app/services/health_service.py:7` for `check_database_health()` and `check_redis_health()` functions.

---

## Performance Baselines

Establishing performance baselines helps identify anomalies.

### Typical Load (Production)

| Metric | Normal Range | Peak | Degraded |
|--------|-------------|------|----------|
| **Request Rate** | 50-200 RPS | 500 RPS | <10 RPS |
| **Error Rate** | 0.1-1% | 2% | >5% |
| **P95 Latency** | 200-500ms | 1s | >3s |
| **P99 Latency** | 500ms-1s | 2s | >5s |
| **WebSocket Connections** | 50-200 | 500 | 0 |
| **Database Connections** | 20-50 | 100 | >150 |
| **CPU Usage** | 30-50% | 70% | >90% |
| **Memory Usage** | 40-60% | 80% | >90% |

### Daily Patterns

**Typical traffic pattern**:
- **Peak hours**: 9 AM - 5 PM (business hours)
- **Low hours**: 11 PM - 6 AM
- **Weekend**: 30% of weekday traffic

**Use for**:
- Capacity planning (scale up before peak hours)
- Anomaly detection (traffic spike at 2 AM is suspicious)
- Cost optimization (scale down during low hours)

---

## Monitoring Best Practices

### 1. Define SLIs and SLOs

**Service Level Indicators (SLIs)**:
- Availability: % of time service returns 200 OK
- Latency: P95 request duration
- Error rate: % of requests with 5xx response

**Service Level Objectives (SLOs)**:
- Availability: 99.9% uptime (8.76 hours downtime/year)
- Latency: P95 <1s
- Error rate: <1%

### 2. Set Up Alerting Hierarchy

1. **Critical**: Page on-call engineer (service down, data loss)
2. **Warning**: Notify team via Slack (high latency, elevated errors)
3. **Info**: Log for review (resource usage trends)

### 3. Correlation IDs

Every request gets a unique `correlation_id` that flows through:
- HTTP headers
- Log entries
- Database queries
- Metrics labels

**Use for**: Tracing a single request across all components.

### 4. Dashboard Organization

- **Executive Dashboard**: High-level KPIs (uptime, users, commands)
- **Operations Dashboard**: System health (errors, latency, resources)
- **Service-Specific Dashboards**: Deep dive per service (commands, vehicles)

### 5. Regular Review

- **Daily**: Check operations dashboard for anomalies
- **Weekly**: Review alert trends, adjust thresholds
- **Monthly**: Capacity planning, performance trends
- **Quarterly**: SLO review, monitoring strategy update

---

## Troubleshooting with Monitoring

### Scenario 1: High Latency

**Symptoms**: P95 latency >3s

**Investigation**:
1. Check Grafana Operations Dashboard for latency spike
2. Identify slow endpoints: `topk(10, histogram_quantile(0.95, ...))`
3. Check database query performance
4. Check vehicle response time
5. Review backend logs for slow operations

**Resolution**: See [troubleshooting.md](troubleshooting.md)

---

### Scenario 2: Elevated Error Rate

**Symptoms**: Error rate >5%

**Investigation**:
1. Check Grafana Operations Dashboard for error spike
2. Identify failing endpoints: `sum(rate(http_requests_total{status_code=~"5.."})) by (endpoint)`
3. Search logs for ERROR level messages
4. Use correlation IDs to trace failed requests
5. Check external dependencies (database, Redis, vehicles)

**Resolution**: See [troubleshooting.md](troubleshooting.md)

---

### Scenario 3: No Commands Being Executed

**Symptoms**: `commands_executed_total` flat (no increase)

**Investigation**:
1. Check Grafana Commands Dashboard
2. Verify users are connected: `websocket_connections_active`
3. Check vehicle connectivity: `vehicle_connections_active`
4. Review backend logs for command submission
5. Check authentication (users logged in?)

**Resolution**: See [troubleshooting.md](troubleshooting.md)

---

## Additional Resources

- **Prometheus Documentation**: https://prometheus.io/docs/
- **Grafana Documentation**: https://grafana.com/docs/
- **PromQL Basics**: https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Troubleshooting Guide**: [troubleshooting.md](troubleshooting.md)
- **Deployment Guide**: [deployment.md](deployment.md)
- **Architecture Docs**: `.codemachine/artifacts/architecture/05_Operational_Architecture.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-30
**Owner**: Platform Engineering Team
**Review Schedule**: Monthly
