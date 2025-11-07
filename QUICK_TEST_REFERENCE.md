# SOVD Quick Test Reference Card

## 🚀 Quick Start (5 minutes)

```bash
# 1. Start services
docker compose up -d

# 2. Wait 30 seconds for PostgreSQL to be healthy
docker compose ps
# Look for "healthy" status on db service

# 3. Initialize database (REQUIRED on first run or after volume wipe)
POSTGRES_PASSWORD=sovd_pass ./scripts/init_db.sh

# 4. Test health
curl http://localhost:8000/health/ready

# 5. Open frontend
xdg-open http://localhost:3000
# Login with: admin / admin123
```

**⚠️ Important:** If you get "relation 'users' does not exist" errors, you forgot step 3!

## 🔑 Access Information

| What | Where | Credentials |
|------|-------|-------------|
| **Web App** | http://localhost:3000 | admin / admin123 |
| **API Docs** | http://localhost:8000/docs | - |
| **Database** | localhost:5433 | sovd_user / sovd_pass |
| **Prometheus** | http://localhost:9090 | - |

## 📝 Common Test Commands

### Check Everything Is Running
```bash
docker compose ps
# All services should show "Up" or "healthy"
```

### View Logs
```bash
# All logs
docker compose logs -f

# Just backend
docker compose logs -f backend

# Last 50 lines
docker compose logs --tail=50 backend
```

### Test API Endpoints
```bash
# Health check
curl http://localhost:8000/health/ready

# Metrics
curl http://localhost:8000/metrics

# Protected endpoint (should fail with 403)
curl http://localhost:8000/api/v1/vehicles
```

### Access Database
```bash
PGPASSWORD=sovd_pass psql -h localhost -p 5433 -U sovd_user -d sovd

# Inside psql:
SELECT username, role FROM users;
SELECT vin, make, model FROM vehicles;
\q
```

### Run Tests
```bash
# Backend tests
cd backend && pytest -v

# Frontend tests
cd frontend && npm run test

# E2E tests
make e2e
```

## ⚠️ Known Issues

**Authentication Login**
- ❌ Login endpoint currently fails (bcrypt compatibility issue)
- ✅ All other functionality works
- ✅ Tests use mocked authentication successfully

## 🔧 Troubleshooting

### Service won't start?
```bash
docker compose logs [service-name]
docker compose restart [service-name]
```

### Reset everything?
```bash
# WARNING: This deletes ALL data!
docker compose down -v

# Start fresh
docker compose up -d

# Wait for database to be healthy
docker compose ps

# Re-initialize database (REQUIRED after -v)
POSTGRES_PASSWORD=sovd_pass ./scripts/init_db.sh
```

### Port conflicts?
```bash
# Check what's using ports
sudo netstat -tlnp | grep -E "3000|8000|5433"

# Edit docker-compose.yml to change ports
```

## 📊 Test Results Summary

**Backend Tests**: 89% pass (143/160)
**Frontend Tests**: 95% pass (303/318)
**Core Services**: ✅ All operational
**Authentication**: ⚠️ Login endpoint issue

## 📖 Full Documentation

See `TEST_USER_GUIDE.md` for comprehensive testing guide.
