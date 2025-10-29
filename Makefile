.PHONY: up down test lint logs e2e help

# Default target - show help
help:
	@echo "Available targets:"
	@echo "  make up    - Start all services with docker-compose"
	@echo "  make down  - Stop all services"
	@echo "  make test  - Run all tests (backend, frontend, e2e)"
	@echo "  make e2e   - Run end-to-end tests with docker-compose (starts services, runs tests, stops services)"
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

# Run end-to-end tests with full service orchestration
e2e:
	@echo "Starting docker-compose services..."
	@docker-compose up -d
	@echo "Waiting for services to be ready..."
	@sleep 10
	@echo "Checking service health..."
	@docker-compose ps
	@echo "Waiting for frontend to be ready..."
	@timeout 60 sh -c 'until curl -s http://localhost:3000 > /dev/null; do sleep 2; done' || (echo "Frontend failed to start" && docker-compose down && exit 1)
	@echo "Waiting for backend to be ready..."
	@timeout 60 sh -c 'until curl -s http://localhost:8000/docs > /dev/null; do sleep 2; done' || (echo "Backend failed to start" && docker-compose down && exit 1)
	@echo "Services are ready, running E2E tests..."
	@cd tests/e2e && npx playwright test || (EXIT_CODE=$$?; cd ../.. && docker-compose down && exit $$EXIT_CODE)
	@echo "E2E tests completed, stopping services..."
	@docker-compose down
	@echo "E2E test suite finished successfully!"

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
