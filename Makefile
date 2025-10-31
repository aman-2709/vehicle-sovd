.PHONY: up down test lint logs e2e help frontend-test frontend-coverage frontend-lint frontend-format proto

# Default target - show help
help:
	@echo "Available targets:"
	@echo "  make up                 - Start all services with docker-compose"
	@echo "  make down               - Stop all services"
	@echo "  make test               - Run all tests (backend, frontend, e2e)"
	@echo "  make frontend-test      - Run frontend tests"
	@echo "  make frontend-coverage  - Run frontend tests with coverage report"
	@echo "  make frontend-lint      - Run frontend linter (ESLint)"
	@echo "  make frontend-format    - Format frontend code (Prettier)"
	@echo "  make proto              - Compile protobuf definitions to Python code"
	@echo "  make e2e                - Run end-to-end tests with docker-compose (starts services, runs tests, stops services)"
	@echo "  make lint               - Run all linters (backend and frontend)"
	@echo "  make logs               - View logs from all services"

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
	@$(MAKE) frontend-test
	@echo "Running e2e tests..."
	@cd tests/e2e && npx playwright test || true

# Run frontend tests
frontend-test:
	@echo "Running frontend tests..."
	@cd frontend && npm run test

# Run frontend tests with coverage
frontend-coverage:
	@echo "Running frontend tests with coverage..."
	@cd frontend && npm run test:coverage
	@echo "Coverage report generated in frontend/coverage/"

# Run frontend linter
frontend-lint:
	@echo "Running ESLint on frontend..."
	@cd frontend && npm run lint

# Format frontend code
frontend-format:
	@echo "Formatting frontend code with Prettier..."
	@cd frontend && npm run format

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

# Compile protobuf definitions to Python code
proto:
	@echo "Creating generated code directory..."
	@mkdir -p backend/app/generated
	@echo "Compiling protobuf definitions..."
	@python -m grpc_tools.protoc \
		-I backend/protos \
		--python_out=backend/app/generated \
		--grpc_python_out=backend/app/generated \
		--pyi_out=backend/app/generated \
		backend/protos/sovd_vehicle_service.proto
	@echo "Creating Python package marker..."
	@touch backend/app/generated/__init__.py
	@echo "Fixing relative imports in generated code..."
	@sed -i 's/^import sovd_vehicle_service_pb2/from . import sovd_vehicle_service_pb2/' backend/app/generated/sovd_vehicle_service_pb2_grpc.py
	@echo "Protobuf compilation completed successfully!"
	@echo "Generated files:"
	@ls -la backend/app/generated/
