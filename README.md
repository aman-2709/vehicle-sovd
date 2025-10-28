# Cloud-to-Vehicle SOVD Command WebApp

## Project Overview

A secure, cloud-based web application that enables automotive engineers to remotely execute SOVD (Service-Oriented Vehicle Diagnostics) 2.0 commands on connected vehicles and view real-time responses through a modern, unified interface.

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
- React 18
- TypeScript
- Material-UI (MUI)
- React Query (state management)
- Vite (build tool)
- Vitest + React Testing Library (testing)
- ESLint + Prettier (code quality)

### Backend
- Python 3.11+
- FastAPI
- Uvicorn (ASGI server)
- SQLAlchemy 2.0 (ORM)
- Alembic (database migrations)
- pytest + pytest-asyncio + httpx (testing)
- Ruff + Black + mypy (code quality)

### Database & Caching
- PostgreSQL 15+ (with JSONB support)
- Redis 7 (session storage, Pub/Sub, caching)

### Communication
- gRPC (primary vehicle communication)
- WebSocket (fallback & real-time streaming)
- JWT authentication (python-jose, passlib)

### Infrastructure
- Docker & Docker Compose (local development)
- Kubernetes/Helm (production deployment)
- Nginx (API gateway, TLS termination, load balancing)
- AWS EKS (primary cloud target)

### Observability
- Prometheus + Grafana (monitoring)
- OpenTelemetry + Jaeger (tracing)
- structlog (structured logging)

### CI/CD
- GitHub Actions
- Playwright (E2E testing)

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- Make (optional, for convenience commands)

### Running the Application

```bash
# Start all services
make up

# View logs
make logs

# Run tests
make test

# Run linters
make lint

# Stop all services
make down
```

### Without Make

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down
```

## Project Structure

```
sovd-command-webapp/
├── frontend/           # React TypeScript frontend
├── backend/            # FastAPI Python backend
├── infrastructure/     # Docker, Kubernetes, Helm charts
├── docs/               # Documentation and diagrams
├── scripts/            # Development and utility scripts
└── tests/              # End-to-end tests
```

## Documentation

- Architecture documentation: `docs/architecture/`
- API specifications: `docs/api/`
- Operational runbooks: `docs/runbooks/`
- User guides: `docs/user-guides/`

## Development

This project follows a modular monolith architecture with clear service boundaries. For detailed development guidelines, see the documentation in the `docs/` directory.

## License

Proprietary - All rights reserved
