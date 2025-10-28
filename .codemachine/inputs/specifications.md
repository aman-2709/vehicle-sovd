# Project: Cloud-to-Vehicle SOVD Command WebApp

## Problem / Goal
Automotive engineers need a secure and modern web application to send standardized SOVD (Service-Oriented Vehicle Diagnostics) commands from the cloud to vehicles, and view responses in real time. This should simplify remote diagnostics and testing by replacing manual tooling with a unified web interface.

## Success Criteria
- User can log in, select a connected vehicle, and send SOVD request commands.
- Responses are displayed clearly on the same web app within <2s round-trip.
- Support for both single-shot requests and streaming responses.
- Secure communication (TLS, JWT, role-based access).
- Runs in Docker, deployable to cloud (AWS/GCP/Azure).
- 80%+ test coverage; CI pipeline green.

## Scope
**In**:  
- Cloud web app (frontend + backend APIs).  
- Command execution over secure channel to vehicle (mock + real endpoints).  
- Logging and response viewer.  

**Out**:  
- Mobile native apps.  
- Deep vehicle ECU firmware update flows (only diagnostic commands).  

## Constraints
- Must comply with automotive SOVD 2.0 specification.  
- Backend: Node.js/Express or FastAPI.  
- Frontend: React + TypeScript.  
- Database: Postgres (for sessions, logs).  
- Secure comms via HTTPS + WebSocket.  

## Deliverables
- Source code (frontend, backend, DB migrations).  
- Dockerfiles and docker-compose.  
- OpenAPI/Swagger docs for backend.  
- Unit + integration tests.  
- CI/CD pipeline config.  

---

## Architecture (Advanced)
- **Frontend**: React webapp with auth, command input, response panel.  
- **Backend**: API gateway + SOVD command executor.  
- **Database**: Postgres for storing sessions, command history.  
- **Vehicle Connector**: service module to forward commands to vehicle endpoint (via gRPC/WebSocket).  

## APIs & Data Models (Advanced)
- `POST /api/sovd/command` → `{ vehicleId, command, params }`  
- `GET /api/sovd/response/{sessionId}` → streaming JSON response.  
- `GET /api/vehicles` → list of available vehicles.  
Tables:  
- `vehicles(id, vin, status)`  
- `commands(id, vehicleId, command, timestamp, status)`  
- `responses(id, commandId, payload, receivedAt)`  

## Non-Functionals (Advanced)
- Handle 100 concurrent users.  
- Round-trip < 2s for 95% of commands.  
- Audit logs for all requests.  
- Encryption in transit & rest.  

## Tooling & Deployment (Advanced)
- `make up`, `make test`.  
- GitHub Actions CI (lint, build, test, docker build).  
- Docker Compose (dev), Helm chart (prod).  

## Coding Standards (Advanced)
- ESLint + Prettier (frontend), Black + Ruff (if Python backend).  
- 80%+ coverage.  
- Conventional commits + CODEOWNERS reviews.  

