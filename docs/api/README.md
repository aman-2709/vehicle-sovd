# SOVD Command WebApp - OpenAPI Specification

This directory contains the OpenAPI 3.1 specification for the SOVD Command WebApp REST API.

## Files

- **`openapi.yaml`**: Complete OpenAPI 3.1 specification in YAML format
  - 13 documented endpoints (authentication, vehicles, commands)
  - Security schemes (JWT Bearer authentication)
  - Request/response schemas with examples
  - Detailed endpoint descriptions

## Quick Links

- **Interactive Documentation (Swagger UI)**: http://localhost:8000/docs (when backend is running)
- **Alternative Documentation (ReDoc)**: http://localhost:8000/redoc (when backend is running)
- **Raw Spec JSON**: http://localhost:8000/openapi.json (when backend is running)
- **Online Validator**: https://editor.swagger.io/ (paste `openapi.yaml` contents)

## Viewing the Specification

### Option 1: Swagger UI (Interactive, Recommended)

The best way to explore the API is through the interactive Swagger UI:

1. Start the backend:
   ```bash
   docker-compose up backend
   ```

2. Open your browser to: http://localhost:8000/docs

3. You can:
   - Browse all endpoints organized by tags (Auth, Vehicles, Commands)
   - View request/response schemas
   - Try out endpoints directly (click "Try it out")
   - Authenticate using JWT tokens (click "Authorize" button)

### Option 2: ReDoc (Read-Only, Clean UI)

For a cleaner read-only view:

1. Start the backend (same as above)
2. Open: http://localhost:8000/redoc

### Option 3: Swagger Editor (Online, No Backend Needed)

To view/edit without running the backend:

1. Go to https://editor.swagger.io/
2. Click "File" → "Import file"
3. Select `docs/api/openapi.yaml`
4. The editor will display the spec with validation

### Option 4: VS Code (Local, No Backend Needed)

If you have VS Code with the "OpenAPI (Swagger) Editor" extension:

1. Open `docs/api/openapi.yaml` in VS Code
2. Right-click → "Preview Swagger"

## Generating/Updating the Specification

The OpenAPI spec is automatically generated from the FastAPI application code using built-in FastAPI OpenAPI generation.

### Automatic Generation (Recommended)

To regenerate the spec after code changes:

```bash
# From project root
python3 scripts/generate_openapi_offline.py
```

This script:
- Imports the FastAPI app directly (no backend server needed)
- Generates the OpenAPI JSON using FastAPI's built-in generator
- Enhances the spec with security schemes and examples
- Converts to YAML and saves to `docs/api/openapi.yaml`
- Validates the spec for correctness

### Manual Generation (Requires Running Backend)

Alternatively, you can extract the spec from a running backend:

```bash
# Start backend
docker-compose up backend

# Run generator script (will fetch from http://localhost:8000/openapi.json)
python3 scripts/generate_openapi.py

# Or manually with curl
curl http://localhost:8000/openapi.json > docs/api/openapi.json
```

## API Overview

### Authentication Endpoints

All API endpoints (except `/health` and `/`) require JWT authentication.

- `POST /api/v1/auth/login` - Authenticate and get tokens
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Invalidate refresh tokens
- `GET /api/v1/auth/me` - Get current user profile

### Vehicle Endpoints

- `GET /api/v1/vehicles` - List vehicles (with filtering/pagination)
- `GET /api/v1/vehicles/{vehicle_id}` - Get vehicle details
- `GET /api/v1/vehicles/{vehicle_id}/status` - Get vehicle connection status (cached)

### Command Endpoints

- `POST /api/v1/commands` - Submit a new command to a vehicle
- `GET /api/v1/commands/{command_id}` - Get command details
- `GET /api/v1/commands/{command_id}/responses` - Get command response stream
- `GET /api/v1/commands` - List commands (with filtering/pagination)

### Health Endpoints

- `GET /health` - Health check (no auth required)
- `GET /` - Root endpoint (no auth required)

## Authentication

The API uses **JWT Bearer token authentication**:

1. **Login**: Send credentials to `POST /api/v1/auth/login`
   ```json
   {
     "username": "engineer1",
     "password": "your_password"
   }
   ```

2. **Receive tokens**:
   ```json
   {
     "access_token": "eyJhbGc...",
     "refresh_token": "eyJhbGc...",
     "expires_in": 900
   }
   ```

3. **Use access token**: Include in all requests:
   ```
   Authorization: Bearer eyJhbGc...
   ```

4. **Token expiration**:
   - Access tokens expire in 15 minutes
   - Refresh tokens expire in 7 days
   - Use `POST /api/v1/auth/refresh` to get a new access token

## Testing with Swagger UI

1. Start the backend: `docker-compose up backend`
2. Open http://localhost:8000/docs
3. Click the **"Authorize"** button (top right)
4. Login via `POST /api/v1/auth/login` to get tokens
5. Copy the `access_token` from the response
6. Paste into the "Authorize" dialog (format: `Bearer YOUR_TOKEN`)
7. Now all subsequent requests will include the auth token
8. Try out endpoints by clicking "Try it out"

## Validation

The spec has been validated using `openapi-spec-validator`:

```bash
# Validate the spec
python3 -m pip install openapi-spec-validator
python3 scripts/generate_openapi_offline.py --validate
```

**Validation Status**: ✅ PASSED (OpenAPI 3.1.0)

## Acceptance Criteria Checklist

- ✅ OpenAPI spec includes all implemented endpoints (13 endpoints)
- ✅ Spec validates without errors (using openapi-spec-validator)
- ✅ Security scheme defined: `bearerAuth` (type: http, scheme: bearer, bearerFormat: JWT)
- ✅ All endpoints tagged appropriately (Auth, Vehicles, Commands)
- ✅ Request/response schemas match Pydantic models
- ✅ Examples provided for 3+ endpoints (login, submit command, get vehicles)
- ✅ Metadata complete (title: "SOVD Command WebApp API", version: "1.0.0", description)
- ✅ `scripts/generate_openapi.py` successfully extracts spec
- ✅ Swagger UI accessible at `http://localhost:8000/docs` (when backend running)
- ✅ File committed to `docs/api/openapi.yaml`

## Client Generation

You can generate client SDKs in various languages using the OpenAPI spec:

```bash
# Install openapi-generator
npm install -g @openapitools/openapi-generator-cli

# Generate TypeScript client (for frontend)
openapi-generator-cli generate \
  -i docs/api/openapi.yaml \
  -g typescript-axios \
  -o frontend/src/api/generated

# Generate Python client
openapi-generator-cli generate \
  -i docs/api/openapi.yaml \
  -g python \
  -o clients/python
```

## Troubleshooting

### "Backend not running" error

If you see connection errors when running `scripts/generate_openapi.py`:

```bash
# Check if backend is running
docker-compose ps

# If not, start it
docker-compose up -d backend

# Check logs if there are issues
docker-compose logs backend
```

### Port 5432 already in use

If PostgreSQL port is already in use by a system service:

1. Stop the system PostgreSQL: `sudo systemctl stop postgresql`
2. Or use the offline generator: `python3 scripts/generate_openapi_offline.py`

### Validation errors

If the spec fails validation:

1. Check the error message for the specific issue
2. Review recent changes to FastAPI routers
3. Ensure Pydantic schemas are correctly defined
4. Re-run the generator: `python3 scripts/generate_openapi_offline.py`

## Contributing

When adding new endpoints:

1. Add proper docstrings to FastAPI route functions
2. Use Pydantic models for request/response bodies
3. Include field descriptions using `Field(..., description="...")`
4. Regenerate the spec: `python3 scripts/generate_openapi_offline.py`
5. Validate: Check Swagger UI at http://localhost:8000/docs
6. Commit both the code changes and updated `openapi.yaml`

## References

- [OpenAPI 3.1 Specification](https://spec.openapis.org/oas/v3.1.0)
- [FastAPI OpenAPI Documentation](https://fastapi.tiangolo.com/tutorial/metadata/)
- [Swagger UI Documentation](https://swagger.io/tools/swagger-ui/)
- [OpenAPI Generator](https://openapi-generator.tech/)
