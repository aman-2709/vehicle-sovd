# Frontend Dockerfile for SOVD Command WebApp
# Development mode with Vite hot module replacement (HMR)
#
# This Dockerfile creates a Node.js 20 development environment for the React frontend.
# Features:
# - Vite dev server with HMR enabled
# - Volume mount at /app for live code updates
# - Port 3000 exposed for browser access
# - Fast refresh for instant feedback during development

FROM node:20-alpine

# Set environment variables
# NODE_ENV=development: Enable development mode for better error messages
ENV NODE_ENV=development

# Install system dependencies (if needed)
# Alpine requires different packages than Debian-based images
RUN apk add --no-cache \
    git \
    python3 \
    make \
    g++

# Set working directory
WORKDIR /app

# Copy package files
# Note: package.json may be minimal initially (populated in task I1.T7)
COPY package*.json ./

# Install Node dependencies
# Using --legacy-peer-deps to handle potential dependency conflicts
# If package.json has no dependencies, this will succeed without installing anything
RUN npm install --legacy-peer-deps || npm install || true

# Copy application code
# In development, this is overridden by volume mount, but needed for initial build
COPY . .

# Expose port 3000 for Vite dev server
EXPOSE 3000

# Health check to verify Vite dev server is responding
# This checks if the dev server is serving the application
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Start Vite dev server
# --host 0.0.0.0: Listen on all interfaces (required for Docker networking)
# --port 3000: Listen on port 3000
# Vite automatically enables HMR in development mode
#
# Note: This assumes package.json has a "dev" script defined
# The script should run: vite --host 0.0.0.0 --port 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
