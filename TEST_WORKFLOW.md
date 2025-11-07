# SOVD Test Workflow Diagram

## 🔄 Complete Testing Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    START TESTING                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Start Services                                         │
│  $ docker compose up -d                                         │
│  ⏱️  Wait: 30 seconds for all services to initialize            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: Verify Services                                        │
│  $ docker compose ps                                            │
│                                                                 │
│  Expected Status:                                               │
│  ✅ sovd-backend:    healthy                                    │
│  ✅ sovd-frontend:   up (healthy/unhealthy ok)                  │
│  ✅ sovd-db:         healthy                                    │
│  ✅ sovd-redis:      healthy                                    │
│  ✅ sovd-prometheus: up                                         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    ┌─────────┴─────────┐
                    │                   │
          ┌─────────▼────────┐  ┌──────▼─────────┐
          │  Test Backend    │  │  Test Frontend │
          │  (API)           │  │  (UI)          │
          └─────────┬────────┘  └──────┬─────────┘
                    │                   │
                    └─────────┬─────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3A: Test Backend API                                      │
│                                                                 │
│  🏥 Health Check:                                               │
│  $ curl http://localhost:8000/health/ready                     │
│  Expected: {"status":"ready","checks":{...}}                   │
│                                                                 │
│  📊 Metrics:                                                    │
│  $ curl http://localhost:8000/metrics                          │
│  Expected: Prometheus metrics output                           │
│                                                                 │
│  🔒 Auth Protection:                                            │
│  $ curl http://localhost:8000/api/v1/vehicles                  │
│  Expected: 403 Forbidden                                       │
│                                                                 │
│  📚 API Docs:                                                   │
│  Open: http://localhost:8000/docs                              │
│  Expected: Swagger UI interface                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3B: Test Frontend                                         │
│                                                                 │
│  🌐 Accessibility:                                              │
│  $ curl -I http://localhost:3000                               │
│  Expected: HTTP 200 OK                                         │
│                                                                 │
│  🖥️  Browser Test:                                              │
│  Open: http://localhost:3000                                   │
│  Expected: React app loads, shows login page                   │
│                                                                 │
│  ⚠️  Login Test:                                                │
│  Username: admin                                               │
│  Password: admin123                                            │
│  Expected: Currently fails (known bcrypt issue)                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Test Database                                          │
│                                                                 │
│  🗄️  Connect:                                                   │
│  $ PGPASSWORD=sovd_pass psql -h localhost -p 5433 \            │
│    -U sovd_user -d sovd                                        │
│                                                                 │
│  📋 Verify Data:                                                │
│  sovd=# SELECT username, role FROM users;                      │
│  Expected: admin (admin), engineer (engineer)                  │
│                                                                 │
│  sovd=# SELECT vin, make FROM vehicles;                        │
│  Expected: TESTVIN0000000001 (Tesla), TESTVIN0000000002 (BMW) │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Run Test Suites                                        │
│                                                                 │
│  🐍 Backend Tests:                                              │
│  $ cd backend && pytest -v                                     │
│  Expected: 143/160 pass (89%)                                  │
│                                                                 │
│  ⚛️  Frontend Tests:                                            │
│  $ cd frontend && npm run test                                 │
│  Expected: 303/318 pass (95%)                                  │
│                                                                 │
│  🎭 E2E Tests:                                                  │
│  $ make e2e                                                    │
│  Expected: Full workflow tests                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  STEP 6: Advanced Testing (When Auth Fixed)                    │
│                                                                 │
│  1️⃣  Login & Get Token:                                         │
│  POST /api/v1/auth/login                                       │
│  → access_token                                                │
│                                                                 │
│  2️⃣  List Vehicles:                                             │
│  GET /api/v1/vehicles                                          │
│  Authorization: Bearer {token}                                 │
│                                                                 │
│  3️⃣  Submit SOVD Command:                                       │
│  POST /api/v1/commands                                         │
│  {                                                             │
│    "vehicle_id": "...",                                        │
│    "command_type": "read_dtc",                                 │
│    "params": {"ecu_address": "0x10"}                           │
│  }                                                             │
│                                                                 │
│  4️⃣  Monitor via WebSocket:                                     │
│  ws://localhost:8000/ws/responses/{command_id}?token={token}   │
│  → Real-time command responses                                │
│                                                                 │
│  5️⃣  Check Command History:                                     │
│  GET /api/v1/commands?vehicle_id={id}&status=completed         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│  CLEANUP                                                        │
│                                                                 │
│  Stop services:                                                │
│  $ docker compose down                                         │
│                                                                 │
│  Remove all data (fresh start):                                │
│  $ docker compose down -v                                      │
└─────────────────────────────────────────────────────────────────┘
```

## 🎯 Quick Test Paths

### Path 1: Basic Verification (2 minutes)
```bash
docker compose up -d
sleep 30
curl http://localhost:8000/health/ready
curl http://localhost:3000
```
**Pass**: Services respond with 200 OK

---

### Path 2: API Testing (5 minutes)
```bash
# Health & Metrics
curl http://localhost:8000/health/ready
curl http://localhost:8000/metrics

# Auth protection
curl http://localhost:8000/api/v1/vehicles  # Should be 403

# API docs
xdg-open http://localhost:8000/docs
```
**Pass**: Health ok, metrics available, auth blocking works, docs accessible

---

### Path 3: Database Testing (3 minutes)
```bash
PGPASSWORD=sovd_pass psql -h localhost -p 5433 -U sovd_user -d sovd

-- Inside psql
SELECT COUNT(*) FROM users;     -- Should be 2
SELECT COUNT(*) FROM vehicles;  -- Should be 2
\q
```
**Pass**: Database accessible, seed data present

---

### Path 4: Full Test Suite (15 minutes)
```bash
# Backend tests
cd backend && pytest -v

# Frontend tests
cd ../frontend && npm run test

# E2E tests
cd .. && make e2e
```
**Pass**: >85% tests passing

---

### Path 5: SOVD Workflow (When Auth Fixed)
```bash
# 1. Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' | jq -r '.access_token')

# 2. List vehicles
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/vehicles

# 3. Submit command
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://localhost:8000/api/v1/commands \
  -d '{"vehicle_id":"...","command_type":"read_dtc","params":{"ecu_address":"0x10"}}'

# 4. Check results
curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/api/v1/commands/{id}
```
**Pass**: Full SOVD command workflow

---

## 🔍 What Each Test Validates

| Test | Validates | Critical? |
|------|-----------|-----------|
| **Health Check** | Backend alive, DB & Redis connected | ✅ Critical |
| **Frontend Load** | React app builds and serves | ✅ Critical |
| **Database Access** | Schema created, seed data loaded | ✅ Critical |
| **Auth Protection** | Endpoints require authentication | ✅ Critical |
| **Metrics Endpoint** | Prometheus monitoring works | ⚠️ Important |
| **Login Flow** | JWT generation & validation | ❌ Currently Failing |
| **WebSocket** | Real-time updates working | ⚠️ Important |
| **SOVD Commands** | Vehicle communication protocol | ⚠️ Important |

## 📊 Test Coverage Map

```
┌──────────────────────────────────────────────────────────┐
│                   Test Coverage                          │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Backend (89% passing)                                   │
│  ████████████████████████████████████░░░░░               │
│                                                          │
│  Frontend (95% passing)                                  │
│  ██████████████████████████████████████████░             │
│                                                          │
│  Integration (Core services working)                     │
│  ██████████████████████████████████████████████          │
│                                                          │
│  E2E (Partial - auth issue blocks full flow)            │
│  ████████████████████░░░░░░░░░░░░░░░░░░░░░░░             │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## 🐛 Known Issues & Workarounds

### Issue: Login Endpoint Fails
**Symptom**: 500 error when POST to /api/v1/auth/login
**Cause**: bcrypt library compatibility
**Workaround**:
- Use mocked auth in tests (working)
- Database queries work directly
- All other endpoints functional

### Issue: Grafana Restarting
**Symptom**: Grafana container keeps restarting
**Impact**: Dashboards unavailable
**Workaround**: Prometheus still collecting metrics

### Issue: Frontend Health Check
**Symptom**: Shows as "unhealthy"
**Impact**: None - app still works
**Cause**: Health check script not configured

## 📖 Documentation Reference

- **TEST_USER_GUIDE.md**: Complete testing guide with all commands
- **QUICK_TEST_REFERENCE.md**: One-page quick reference
- **test-quick-start.sh**: Automated test script
- **README.md**: Project overview and architecture
- **CLAUDE.md**: AI assistant context and patterns

## 🚀 Next Steps After Testing

1. ✅ Verify all services running
2. ✅ Confirm database schema correct
3. ✅ Test API endpoints accessible
4. ⏳ Fix authentication bcrypt issue
5. ⏳ Implement real vehicle connector
6. ⏳ Add WebSocket real-time updates
7. ⏳ Deploy to staging environment
