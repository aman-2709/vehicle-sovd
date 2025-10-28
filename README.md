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
- PostgreSQL: localhost:5432 (credentials: sovd_user/sovd_pass)
- Redis: localhost:6379

### Docker Services

The development environment includes four services:

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

## Project Structure

```
sovd-command-webapp/
├── frontend/          # React TypeScript frontend
├── backend/           # FastAPI Python backend
├── infrastructure/    # IaC and deployment configs
├── docs/             # Documentation and diagrams
├── scripts/          # Development and utility scripts
└── tests/            # End-to-end tests
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
