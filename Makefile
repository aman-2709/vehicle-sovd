.PHONY: up down test lint logs help

# Default target - show help
help:
	@echo "Available targets:"
	@echo "  make up    - Start all services with docker-compose"
	@echo "  make down  - Stop all services"
	@echo "  make test  - Run all tests (backend, frontend, e2e)"
	@echo "  make lint  - Run all linters (backend and frontend)"
	@echo "  make logs  - View logs from all services"

# Start all services with docker-compose
up:
	@docker-compose up -d

# Stop all services
down:
	@docker-compose down

# Run all tests (backend unit, integration, frontend, e2e)
test:
	@echo "Running backend tests with coverage..."
	@cd backend && pytest --cov=app --cov-report=html --cov-report=term
	@echo "Running frontend tests..."
	@cd frontend && npm test || true
	@echo "Running e2e tests..."
	@cd tests/e2e && npx playwright test || true

# Run all linters (backend: ruff, black, mypy; frontend: eslint, prettier)
lint:
	@echo "Running backend linters..."
	@cd backend && ruff check app/ || true
	@cd backend && black --check app/ || true
	@cd backend && mypy app/ || true
	@echo "Running frontend linters..."
	@cd frontend && npm run lint || true

# View logs from all services
logs:
	@docker-compose logs -f
