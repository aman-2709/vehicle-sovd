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

### Getting Started

```bash
# Start all services (frontend, backend, database, redis)
make up

# View logs from all services
make logs

# Run tests
make test

# Run linters
make lint

# Stop all services
make down
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

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
