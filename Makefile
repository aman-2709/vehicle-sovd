.PHONY: up down test lint logs help

# Default target
help:
	@echo "Available targets:"
	@echo "  make up    - Start all services with docker-compose"
	@echo "  make down  - Stop all services"
	@echo "  make test  - Run all tests (frontend + backend + e2e)"
	@echo "  make lint  - Run all linters (frontend + backend)"
	@echo "  make logs  - View logs from all services"

# Start all services with docker-compose
up:
	@echo "Starting all services..."
	@if [ -f docker-compose.yml ]; then \
		docker-compose up -d; \
	else \
		echo "docker-compose.yml not yet configured"; \
	fi

# Stop all services
down:
	@echo "Stopping all services..."
	@if [ -f docker-compose.yml ]; then \
		docker-compose down; \
	else \
		echo "docker-compose.yml not yet configured"; \
	fi

# Run all tests
test:
	@echo "Running all tests..."
	@echo "Frontend tests:"
	@if [ -d frontend ] && [ -f frontend/package.json ]; then \
		cd frontend && npm test; \
	else \
		echo "  Frontend tests not yet implemented"; \
	fi
	@echo ""
	@echo "Backend tests:"
	@if [ -d backend ] && [ -f backend/requirements.txt ]; then \
		cd backend && pytest; \
	else \
		echo "  Backend tests not yet implemented"; \
	fi
	@echo ""
	@echo "E2E tests:"
	@if [ -d tests/e2e ]; then \
		cd tests/e2e && npx playwright test; \
	else \
		echo "  E2E tests not yet implemented"; \
	fi

# Run all linters
lint:
	@echo "Running all linters..."
	@echo "Frontend linting:"
	@if [ -d frontend ] && [ -f frontend/package.json ]; then \
		cd frontend && npm run lint; \
	else \
		echo "  Frontend linters not yet configured"; \
	fi
	@echo ""
	@echo "Backend linting:"
	@if [ -d backend ] && [ -f backend/requirements.txt ]; then \
		cd backend && ruff check . && black --check . && mypy .; \
	else \
		echo "  Backend linters not yet configured"; \
	fi

# View logs from all services
logs:
	@echo "Viewing logs from all services..."
	@if [ -f docker-compose.yml ]; then \
		docker-compose logs -f; \
	else \
		echo "docker-compose.yml not yet configured"; \
	fi
