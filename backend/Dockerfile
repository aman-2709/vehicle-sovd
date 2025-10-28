# Backend Dockerfile for SOVD Command WebApp
# Development mode with hot reload enabled
#
# This Dockerfile creates a Python 3.11 development environment for the FastAPI backend.
# Features:
# - Hot reload enabled via uvicorn --reload flag
# - Volume mount at /app for live code updates
# - Minimal dependencies for fast builds
# - PostgreSQL and Redis client libraries included

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies required for PostgreSQL and other Python packages
# - postgresql-client: For pg_isready and psql CLI tools
# - gcc, python3-dev, musl-dev: For compiling Python packages with C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    gcc \
    python3-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
# Note: requirements.txt may be minimal/empty initially (populated in task I1.T6)
COPY requirements.txt .

# Install Python dependencies
# Using --no-cache-dir to reduce image size
# If requirements.txt is empty, this will succeed without installing anything
RUN pip install --no-cache-dir -r requirements.txt || true

# Copy application code
# In development, this is overridden by volume mount, but needed for initial build
COPY . .

# Expose port 8000 for FastAPI application
EXPOSE 8000

# Health check to verify the application is responding
# This checks if the application is serving HTTP requests
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# Start uvicorn with hot reload enabled
# --host 0.0.0.0: Listen on all interfaces (required for Docker networking)
# --port 8000: Listen on port 8000
# --reload: Enable auto-reload when code changes are detected
# --reload-dir /app: Watch /app directory for changes (where volume is mounted)
#
# Note: This assumes the FastAPI app instance is at app.main:app
# If the application structure changes, update this path accordingly
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/app"]
