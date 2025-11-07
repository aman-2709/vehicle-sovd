#!/bin/bash
# SOVD Quick Test Script
# Run this to verify everything is working

set -e

echo "🚀 SOVD Command WebApp - Quick Test"
echo "===================================="
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Start services
echo "📦 Starting services..."
docker compose up -d
echo ""

# Wait for services
echo "⏳ Waiting for services to be ready (30 seconds)..."
sleep 30
echo ""

# Check service status
echo "📊 Service Status:"
docker compose ps
echo ""

# Test backend health
echo "🏥 Testing backend health..."
HEALTH=$(curl -s http://localhost:8000/health/ready)
if echo "$HEALTH" | grep -q '"status":"ready"'; then
    echo "✅ Backend is healthy"
else
    echo "❌ Backend health check failed"
    echo "Response: $HEALTH"
fi
echo ""

# Test frontend
echo "🌐 Testing frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_STATUS" = "200" ]; then
    echo "✅ Frontend is accessible"
else
    echo "❌ Frontend returned status: $FRONTEND_STATUS"
fi
echo ""

# Test database
echo "🗄️  Testing database..."
if PGPASSWORD=sovd_pass psql -h localhost -p 5433 -U sovd_user -d sovd -c "SELECT COUNT(*) FROM users;" > /dev/null 2>&1; then
    USER_COUNT=$(PGPASSWORD=sovd_pass psql -h localhost -p 5433 -U sovd_user -d sovd -t -c "SELECT COUNT(*) FROM users;" | tr -d ' ')
    echo "✅ Database is accessible (${USER_COUNT} users found)"
else
    echo "❌ Database connection failed"
fi
echo ""

# Test authentication protection
echo "🔒 Testing authentication protection..."
AUTH_TEST=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/vehicles)
if [ "$AUTH_TEST" = "403" ]; then
    echo "✅ Authentication protection working"
else
    echo "⚠️  Unexpected status code: $AUTH_TEST"
fi
echo ""

# Summary
echo "=================================="
echo "📋 Test Summary"
echo "=================================="
echo ""
echo "Access URLs:"
echo "  Frontend:     http://localhost:3000"
echo "  API Docs:     http://localhost:8000/docs"
echo "  Health Check: http://localhost:8000/health/ready"
echo "  Prometheus:   http://localhost:9090"
echo ""
echo "Credentials:"
echo "  Username: admin"
echo "  Password: admin123"
echo "  (Note: Login currently has a known bcrypt issue)"
echo ""
echo "Database:"
echo "  Host: localhost:5433"
echo "  Database: sovd"
echo "  User: sovd_user"
echo "  Password: sovd_pass"
echo ""
echo "Next Steps:"
echo "  1. Open http://localhost:3000 in your browser"
echo "  2. Open http://localhost:8000/docs for API documentation"
echo "  3. Run 'docker compose logs -f' to view logs"
echo "  4. See TEST_USER_GUIDE.md for detailed testing instructions"
echo ""
echo "To stop services: docker compose down"
echo ""
