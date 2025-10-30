# Cloud-to-Vehicle SOVD Command WebApp

## Project Overview

This project develops a secure, cloud-based web application that enables automotive engineers to remotely execute SOVD (Service-Oriented Vehicle Diagnostics) 2.0 commands on connected vehicles and view real-time responses through a modern, unified interface.

## Goals

- User authentication and role-based access control (Engineer, Admin roles)
- Vehicle registry with connection status monitoring
- SOVD command submission with parameter validation
- Real-time response streaming via WebSocket
- Command history and audit logging
- <2 second round-trip time for 95% of commands
- Support for 100+ concurrent users
- Secure communication (TLS, JWT, RBAC)
- Docker-based deployment ready for cloud platforms (AWS/GCP/Azure)
- 80%+ test coverage with CI/CD pipeline
- OpenAPI/Swagger documentation for all backend APIs

## Technology Stack

### Frontend
- **Framework:** React 18 with TypeScript
- **UI Library:** Material-UI (MUI)
- **State Management:** React Query
- **Build Tool:** Vite
- **Code Quality:** ESLint, Prettier, TypeScript

### Backend
- **Framework:** Python 3.11+ with FastAPI
- **Server:** Uvicorn (ASGI)
- **ORM:** SQLAlchemy 2.0
- **Migrations:** Alembic
- **Authentication:** JWT (python-jose, passlib)
- **Code Quality:** Ruff, Black, mypy

### Infrastructure
- **Database:** PostgreSQL 15+
- **Cache/Messaging:** Redis 7
- **Vehicle Communication:** gRPC (primary), WebSocket (fallback)
- **API Gateway:** Nginx (production)
- **Containerization:** Docker, Docker Compose (local), Kubernetes/Helm (production)
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana, structlog
- **Tracing:** OpenTelemetry + Jaeger

### Testing
- **Backend:** pytest, pytest-asyncio, httpx
- **Frontend:** Vitest, React Testing Library
- **E2E:** Playwright

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Make utility installed
- Ports 3000, 8000, 5432, and 6379 available on localhost

### Getting Started

```bash
# Start all services (frontend, backend, database, redis)
make up

# Initialize the database with schema and seed data
POSTGRES_PASSWORD=sovd_pass ./scripts/init_db.sh

# View logs from all services
make logs

# Stop all services
make down
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Prometheus Metrics: http://localhost:8000/metrics
- Prometheus UI: http://localhost:9090
- PostgreSQL: localhost:5432 (credentials: sovd_user/sovd_pass)
- Redis: localhost:6379

### Docker Services

The development environment includes five services:

1. **PostgreSQL Database (`db`)**
   - Image: `postgres:15`
   - Port: 5432
   - Database: `sovd`
   - Credentials: `sovd_user` / `sovd_pass`
   - Persistent volume: `sovd-db-data`

2. **Redis Cache (`redis`)**
   - Image: `redis:7`
   - Port: 6379
   - AOF persistence enabled
   - Persistent volume: `sovd-redis-data`

3. **Backend API Server (`backend`)**
   - Port: 8000
   - Hot reload enabled
   - Depends on: db, redis
   - Environment variables configured in `docker-compose.yml`

4. **Frontend Development Server (`frontend`)**
   - Port: 3000
   - Vite HMR enabled
   - Depends on: backend
   - Environment variables configured in `docker-compose.yml`

5. **Prometheus Monitoring (`prometheus`)**
   - Image: `prom/prometheus:latest`
   - Port: 9090
   - Scrapes backend metrics every 10 seconds
   - Persistent volume: `prometheus-data`

### Database Initialization

After starting the services for the first time, initialize the database:

```bash
# Wait for PostgreSQL to be healthy (check with docker-compose ps)
docker-compose ps

# Run the initialization script
POSTGRES_PASSWORD=sovd_pass ./scripts/init_db.sh
```

This script will:
- Create all database tables (users, vehicles, commands, responses, sessions, audit_logs)
- Create 21+ indexes for performance optimization
- Insert seed data (2 test users and 2 test vehicles)
- Verify the schema was created successfully

**Seed Data Credentials:**
- Admin: `admin` / `admin123`
- Engineer: `engineer` / `engineer123`

### Development Workflow

**Hot Reload:**
Both backend and frontend support hot reload:
- Backend: Edit files in `backend/app/` - uvicorn auto-reloads
- Frontend: Edit files in `frontend/src/` - Vite HMR updates instantly

**Viewing Logs:**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f db
docker-compose logs -f redis
```

**Database Access:**
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U sovd_user -d sovd

# Run SQL queries
docker-compose exec db psql -U sovd_user -d sovd -c "SELECT * FROM users;"
```

**Redis Access:**
```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# Test connection
docker-compose exec redis redis-cli ping
```

**Rebuilding Services:**
```bash
# Rebuild all services
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build backend
```

### Troubleshooting

**Port Conflicts:**
If ports are already in use, you'll see errors like "port is already allocated". Solutions:
- Stop conflicting services: `sudo lsof -ti:8000 | xargs kill -9`
- Change ports in `docker-compose.yml`

**Database Connection Issues:**
- Verify PostgreSQL is healthy: `docker-compose ps` (should show "healthy")
- Check logs: `docker-compose logs db`
- Ensure `init_db.sh` was run successfully

**Backend Won't Start:**
- Check if database is healthy and initialized
- Verify environment variables in `docker-compose.yml`
- Check logs: `docker-compose logs backend`

**Frontend Won't Start:**
- Check if backend is running
- Verify port 3000 is not in use
- Check logs: `docker-compose logs frontend`

**Volume Permission Issues:**
- On Linux, you may need to adjust volume permissions
- Run: `sudo chown -R $USER:$USER backend/ frontend/`

**Clean Slate Restart:**
```bash
# Stop all services and remove volumes
docker-compose down -v

# Remove all containers and images
docker-compose down --rmi all -v

# Start fresh
make up
POSTGRES_PASSWORD=sovd_pass ./scripts/init_db.sh
```

### Additional Commands

```bash
# Run tests
make test

# Run end-to-end tests (starts services, runs tests, stops services)
make e2e

# Run linters
make lint

# Stop services without removing volumes
make down

# Stop services and remove volumes (data loss!)
docker-compose down -v

# View service status
docker-compose ps

# Execute command in service
docker-compose exec backend bash
docker-compose exec frontend sh
```

## Monitoring

The application includes Prometheus metrics for monitoring system health and performance.

### Accessing Metrics

- **Metrics Endpoint**: http://localhost:8000/metrics (Prometheus exposition format)
- **Prometheus UI**: http://localhost:9090 (query and visualize metrics)

### Available Metrics

**HTTP Metrics** (automatic via prometheus-fastapi-instrumentator):
- `http_requests_total`: Total HTTP request count by method, endpoint, and status
- `http_request_duration_seconds`: Request latency histogram
- `http_requests_in_progress`: Number of HTTP requests currently being processed

**Custom Application Metrics**:
- `commands_executed_total`: Total SOVD commands executed (labeled by status: completed, failed, timeout)
- `command_execution_duration_seconds`: Command round-trip time histogram from submission to completion
- `websocket_connections_active`: Current number of active WebSocket connections for real-time updates
- `vehicle_connections_active`: Number of vehicles currently connected to the system

### Example Queries

In the Prometheus UI (http://localhost:9090), navigate to **Graph** and try these queries:

**Request Rate:**
```promql
# Total requests per second in the last 5 minutes
rate(http_requests_total[5m])

# Requests per second by endpoint
sum by (handler) (rate(http_requests_total[5m]))
```

**Command Success Rate:**
```promql
# Command success rate over 5 minutes
rate(commands_executed_total{status="completed"}[5m]) / rate(commands_executed_total[5m])

# Total completed vs failed commands
sum(commands_executed_total{status="completed"})
sum(commands_executed_total{status="failed"})
```

**Latency Metrics:**
```promql
# 95th percentile command execution time
histogram_quantile(0.95, rate(command_execution_duration_seconds_bucket[5m]))

# 50th percentile (median) HTTP request duration
histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))
```

**Connection Metrics:**
```promql
# Current active WebSocket connections
websocket_connections_active

# Current connected vehicles
vehicle_connections_active
```

### Viewing Metrics in Terminal

You can also view raw metrics in Prometheus exposition format using curl:

```bash
# View all metrics
curl http://localhost:8000/metrics

# Filter for specific metrics
curl http://localhost:8000/metrics | grep commands_executed
curl http://localhost:8000/metrics | grep websocket_connections
```

### Prometheus Targets Health

To verify that Prometheus is successfully scraping the backend:

1. Open Prometheus UI: http://localhost:9090
2. Navigate to **Status** → **Targets**
3. Verify the `sovd-backend` target shows as **UP** (green)
4. Check **Last Scrape** timestamp is recent (within 10-15 seconds)

### Troubleshooting Metrics

**Metrics endpoint returns 404:**
- Verify backend is running: `docker-compose ps backend`
- Check backend logs: `docker-compose logs backend`
- Ensure prometheus-fastapi-instrumentator is installed

**Prometheus UI not accessible:**
- Verify Prometheus container is running: `docker-compose ps prometheus`
- Check Prometheus logs: `docker-compose logs prometheus`
- Ensure port 9090 is not in use: `sudo lsof -ti:9090`

**Prometheus shows backend target as DOWN:**
- Verify backend is healthy: `curl http://localhost:8000/health`
- Check Prometheus configuration: `cat infrastructure/docker/prometheus.yml`
- Review Prometheus logs for scrape errors: `docker-compose logs prometheus | grep error`

**Custom metrics not appearing:**
- Submit a command to generate metric data
- Wait 10-15 seconds for next scrape
- Refresh the /metrics endpoint
- Verify metrics are initialized in backend startup logs

## End-to-End Testing

The project includes comprehensive end-to-end tests using Playwright that validate complete user workflows across the entire application stack.

### Prerequisites

- Node.js 18+ installed (for running Playwright tests)
- Docker and Docker Compose installed
- Playwright browsers installed (chromium, firefox)

### Running E2E Tests

**Automated Full Stack Testing:**

The simplest way to run E2E tests is using the `make e2e` command, which handles all service orchestration automatically:

```bash
make e2e
```

This command will:
1. Start all docker-compose services (frontend, backend, database, redis)
2. Wait for services to be healthy and ready
3. Run the complete Playwright test suite
4. Stop all services and clean up
5. Exit with proper status code (0 = success, non-zero = failure)

**Manual E2E Test Execution:**

If you want more control over the test execution:

```bash
# Start services manually
make up

# Wait for services to be ready (check health)
docker-compose ps

# Navigate to E2E test directory
cd tests/e2e

# Run all tests in headless mode (default)
npx playwright test

# Run tests in headed mode (see browser)
npx playwright test --headed

# Run tests with UI mode (interactive debugging)
npx playwright test --ui

# Run specific test file
npx playwright test specs/auth.spec.ts

# Run tests for specific browser only
npx playwright test --project=chromium
npx playwright test --project=firefox

# Run tests in debug mode (step-by-step)
npx playwright test --debug

# Stop services when done
make down
```

### Test Suites

The E2E test suite covers three critical user flows:

**1. Authentication Flow (`tests/e2e/specs/auth.spec.ts`)**
- Complete login flow with valid credentials
- Redirect to dashboard after successful login
- Username display in header after authentication
- Logout functionality and redirect to login
- Session persistence across page refreshes
- Protected route access control
- Invalid credentials handling

**2. Vehicle Management (`tests/e2e/specs/vehicle_management.spec.ts`)**
- Vehicle list rendering and display
- Search filtering by VIN
- Status filter dropdown (All, Connected, Disconnected)
- Vehicle details visibility
- Auto-refresh behavior
- Empty search results handling

**3. Command Execution (`tests/e2e/specs/command_execution.spec.ts`)**
- Complete command execution flow (vehicle selection → command selection → parameter input → submission)
- Real-time response viewing via WebSocket
- Command ID display after submission
- Parameter validation
- Multiple sequential command execution
- Error handling for disconnected vehicles
- Response viewer real-time updates

### Test Results and Artifacts

Playwright automatically captures artifacts for debugging:

- **Screenshots:** `tests/e2e/test-results/screenshots/` (captured on failure only)
- **Videos:** `tests/e2e/test-results/artifacts/` (retained on failure only)
- **Test Report:** `tests/e2e/test-results/html-report/` (HTML report with detailed results)
- **JSON Results:** `tests/e2e/test-results/results.json` (machine-readable results)

To view the HTML test report:

```bash
cd tests/e2e
npx playwright show-report
```

### Browser Coverage

E2E tests run across multiple browsers to ensure cross-browser compatibility:
- **Chromium** (Chrome, Edge)
- **Firefox**

### Configuration

Playwright configuration is located at `tests/e2e/playwright.config.ts`:
- Base URL: `http://localhost:3000`
- Headless mode: Enabled by default (can be overridden with `--headed`)
- Timeouts: 60s per test, 10s per assertion, 15s per action
- Retries: 2 retries on CI, 0 retries locally
- Parallel execution: Fully parallel (limited to 1 worker on CI)
- Screenshot on failure: Enabled
- Video on failure: Enabled

### Troubleshooting E2E Tests

**Tests fail immediately:**
- Verify services are running: `docker-compose ps`
- Check frontend is accessible: `curl http://localhost:3000`
- Check backend is accessible: `curl http://localhost:8000/docs`
- Verify database was initialized: `docker-compose exec db psql -U sovd_user -d sovd -c "SELECT * FROM users;"`

**Timeout errors:**
- Increase timeout in `playwright.config.ts` if services are slow to start
- Check service logs: `docker-compose logs backend` or `docker-compose logs frontend`
- Ensure adequate system resources (CPU, memory)

**Flaky tests (intermittent failures):**
- Check for race conditions in test code (use proper `waitFor` methods)
- Verify WebSocket connections are stable: `docker-compose logs backend | grep websocket`
- Increase wait timeouts for slower systems

**WebSocket response tests fail:**
- Verify Redis is running and healthy: `docker-compose ps redis`
- Check backend WebSocket endpoint: `docker-compose logs backend | grep ws`
- Ensure response broadcasting is working: check backend logs for pub/sub activity

**"Browser not found" error:**
- Install Playwright browsers: `npx playwright install chromium firefox`
- Or install all browsers: `npx playwright install`

**Port conflicts:**
- Ensure ports 3000, 8000, 5432, and 6379 are available
- Stop conflicting services: `sudo lsof -ti:3000 | xargs kill -9`

**Clean slate for E2E tests:**
```bash
# Stop all services and remove volumes
docker-compose down -v

# Start fresh and run E2E tests
make e2e
```

### CI/CD Integration

E2E tests are integrated into the GitHub Actions CI/CD pipeline:
- Tests run automatically on every pull request and merge to main
- Tests run in headless mode across multiple browsers
- Screenshots and videos are uploaded as artifacts on failure
- Pipeline fails if any E2E test fails
- Expected duration: <5 minutes for complete E2E suite

## Project Structure

```
sovd-command-webapp/
├── frontend/          # React TypeScript frontend
├── backend/           # FastAPI Python backend
├── infrastructure/    # IaC and deployment configs
├── docs/             # Documentation and diagrams
├── scripts/          # Development and utility scripts
└── tests/
    └── e2e/          # End-to-end tests (Playwright)
        ├── specs/    # Test specifications
        ├── test-results/ # Test artifacts (screenshots, videos, reports)
        ├── package.json
        └── playwright.config.ts
```

## Documentation

Detailed documentation is available in the `docs/` directory:
- Architecture: `docs/architecture/`
- API Specifications: `docs/api/`
- Operational Runbooks: `docs/runbooks/`
- User Guides: `docs/user-guides/`

## Development

See individual component READMEs for detailed development instructions:
- [Frontend Development](frontend/README.md)
- [Backend Development](backend/README.md)

## License

[To be determined]
