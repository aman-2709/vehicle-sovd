# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I1.T10",
  "iteration_id": "I1",
  "iteration_goal": "Foundation, Architecture Artifacts & Database Schema",
  "description": "Implement `backend/app/database.py` module for database connection and session management. Use SQLAlchemy async engine (`create_async_engine`) with asyncpg driver. Create `async_session_maker` using `async_sessionmaker`. Implement `get_db()` async generator function for dependency injection (yields session, closes after use). Read database URL from `backend/app/config.py` (create config module using Pydantic Settings to load DATABASE_URL, REDIS_URL, JWT_SECRET from environment variables or `.env` file). Configure connection pooling (pool_size=20, max_overflow=10). Add logging for database connections.",
  "agent_type_hint": "BackendAgent",
  "inputs": "SQLAlchemy async best practices; FastAPI dependency injection patterns.",
  "target_files": [
    "backend/app/database.py",
    "backend/app/config.py"
  ],
  "input_files": [],
  "deliverables": "Database session management module with async support; configuration module with environment variable loading.",
  "acceptance_criteria": "`database.py` exports `get_db()` function; `get_db()` is an async generator function yielding AsyncSession; Async engine created with DATABASE_URL from config; Connection pool configured (pool_size=20, max_overflow=10); `config.py` uses Pydantic `BaseSettings` (or `pydantic-settings` in Pydantic v2); Config loads DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_ALGORITHM (default HS256), JWT_EXPIRATION_MINUTES (default 15); `.env.example` file created with sample values for environment variables; No errors when importing `from app.database import get_db`; Logging configured to log database connections (use structlog)",
  "dependencies": [
    "I1.T6",
    "I1.T9"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: SQLAlchemy 2.0 Best Practices

**SQLAlchemy 2.0 Async Engine Pattern:**
- Use `create_async_engine()` from `sqlalchemy.ext.asyncio` for async database operations
- AsyncEngine is the entry point for all async database operations
- Use `async_sessionmaker()` to create a factory for async sessions
- Sessions should be managed using async context managers or dependency injection
- Always use `await` for database operations

**Connection Pooling:**
- Default pool is QueuePool (recommended for most applications)
- Configure `pool_size` for number of connections to maintain
- Configure `max_overflow` for additional connections beyond pool_size during peak load
- For production: pool_size=20, max_overflow=10 is a good starting point
- Connection pools are automatically managed by the engine

**Best Practice for FastAPI:**
```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(
    database_url,
    pool_size=20,
    max_overflow=10,
    echo=False  # Set to True for SQL logging in development
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False  # Prevent lazy loading errors
)

async def get_db():
    async with async_session_maker() as session:
        yield session
```

### Context: FastAPI Dependency Injection Pattern

**Dependency Injection for Database Sessions:**
- Use async generator functions that yield the session
- FastAPI automatically handles cleanup after request
- Pattern:
```python
from typing import AsyncGenerator
from fastapi import Depends

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
        # Cleanup happens automatically after yield

# Usage in route
@app.get("/users")
async def get_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()
```

### Context: Pydantic Settings (v2)

**Environment Variable Configuration:**
- Pydantic v2 uses `pydantic-settings` package (separate from pydantic)
- Import `BaseSettings` from `pydantic_settings` (not `pydantic`)
- Field defaults and validation work the same as Pydantic models
- Automatically reads from environment variables or `.env` file

**Pattern:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Database configuration
    DATABASE_URL: str

    # Redis configuration
    REDIS_URL: str

    # JWT configuration
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 15

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )

settings = Settings()
```

### Context: structlog Configuration

**Structured Logging Pattern:**
- structlog provides structured, context-aware logging
- Integrates with Python's standard logging
- Outputs JSON for easy parsing by log aggregation tools
- Add context to logs (correlation IDs, user IDs, etc.)

**Basic Configuration:**
```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()
logger.info("database_connection_created", pool_size=20, max_overflow=10)
```

### Context: Docker Compose Environment Variables

**Environment Variables from docker-compose.yml:**
```yaml
backend:
  environment:
    DATABASE_URL: postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd
    REDIS_URL: redis://redis:6379/0
```

**Important Notes:**
- DATABASE_URL uses `postgresql+asyncpg://` scheme (not just `postgresql://`)
- The `asyncpg` driver is required for async operations
- Service names (`db`, `redis`) are used as hostnames in Docker network
- These environment variables are automatically available to the backend container

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/app/models/__init__.py`
    *   **Summary:** This file exports all SQLAlchemy ORM models and the Base class. All models (User, Vehicle, Command, Response, Session, AuditLog) are properly defined and use SQLAlchemy 2.0 syntax with type hints.
    *   **Recommendation:** You MUST import `Base` from `app.models` in your `database.py` file. The Base class contains the metadata for all models and is required for Alembic migrations.

*   **File:** `backend/app/models/base.py`
    *   **Summary:** Defines the DeclarativeBase class that all ORM models inherit from.
    *   **Recommendation:** This Base class is already configured and working. DO NOT modify it. Import it via `app.models` as shown in the Alembic env.py file.

*   **File:** `backend/app/models/user.py`
    *   **Summary:** Example of a properly configured SQLAlchemy 2.0 model with Mapped type hints, relationships, and PostgreSQL-specific types (UUID, DateTime with timezone).
    *   **Recommendation:** Your database session configuration should work seamlessly with these models. All models follow the same pattern with proper async support.

*   **File:** `backend/requirements.txt`
    *   **Summary:** Contains all required dependencies including `sqlalchemy>=2.0.0`, `asyncpg>=0.29.0`, `pydantic>=2.4.0`, `pydantic-settings>=2.0.0`, and `structlog>=23.2.0`.
    *   **Recommendation:** All dependencies you need are already installed. You MUST use `pydantic-settings` for the Settings class (not the deprecated `pydantic.BaseSettings`).

*   **File:** `backend/pyproject.toml`
    *   **Summary:** Contains linter and type checker configuration (black, ruff, mypy). Mypy is configured in strict mode with `disallow_untyped_defs = true`.
    *   **Recommendation:** You MUST add type hints to all functions and parameters. Use `AsyncSession` from `sqlalchemy.ext.asyncio` for type hints. Use `AsyncGenerator[AsyncSession, None]` for the `get_db()` return type.

*   **File:** `backend/alembic/env.py`
    *   **Summary:** Already configured to use async SQLAlchemy engine and imports models from `app.models`. Shows the correct pattern for reading DATABASE_URL from environment variables.
    *   **Recommendation:** Your `config.py` should follow the same pattern for reading DATABASE_URL. The Alembic configuration demonstrates proper async engine setup with environment variables.

*   **File:** `backend/app/main.py`
    *   **Summary:** Basic FastAPI app with CORS middleware and health check endpoint. Uses startup/shutdown events.
    *   **Recommendation:** You may want to import and initialize the database engine in the startup event (optional for now, but good practice). Ensure your config module can be imported without errors from this file.

*   **File:** `docker-compose.yml`
    *   **Summary:** Defines environment variables for the backend service including DATABASE_URL and REDIS_URL. Uses PostgreSQL service name `db` and Redis service name `redis` as hostnames.
    *   **Recommendation:** Your `config.py` MUST read these environment variables. The DATABASE_URL is already in the correct format: `postgresql+asyncpg://sovd_user:sovd_pass@db:5432/sovd`.

### Implementation Tips & Notes

*   **Tip:** The project uses Pydantic v2, which requires `pydantic-settings` as a separate package. Import `BaseSettings` from `pydantic_settings` (note the underscore, not hyphen).

*   **Tip:** For the `get_db()` function, use the async generator pattern with `yield` to ensure proper session cleanup. FastAPI's dependency injection system will automatically call cleanup code after the yield statement.

*   **Tip:** Set `expire_on_commit=False` in `async_sessionmaker` to prevent lazy loading errors. This is especially important for async sessions where you can't lazily load relationships outside the session context.

*   **Tip:** Configure the async engine with `echo=False` in production but you may want to make this configurable (e.g., `echo=settings.DEBUG` if you add a DEBUG setting).

*   **Note:** The task requires logging database connections using structlog. Configure structlog at the module level and log when the engine is created. Include relevant context like pool_size and max_overflow in your log messages.

*   **Note:** For the `.env.example` file, include all required environment variables with placeholder values. This file should be committed to git (unlike `.env` which should be in `.gitignore`).

*   **Warning:** DO NOT hardcode any database credentials or secrets in your code. All sensitive values MUST come from environment variables loaded via Pydantic Settings.

*   **Warning:** The `JWT_SECRET` environment variable is critical for security. In the `.env.example` file, use a placeholder value and add a comment explaining that users should generate a secure random string.

*   **Best Practice:** Create a single `settings` instance at the module level in `config.py` and export it. This ensures the configuration is loaded once and reused throughout the application.

*   **Best Practice:** Use context managers (`async with`) for session management. The `get_db()` function should use the async session maker's context manager to ensure proper cleanup.

*   **Testing:** After implementation, you should be able to run `from app.database import get_db` without errors. You can test the database connection by running Alembic migrations: `alembic upgrade head`.

### File Structure Expectations

Based on the task requirements, you should create:

1. **`backend/app/config.py`** - Configuration module with:
   - `Settings` class using `BaseSettings` from `pydantic_settings`
   - Fields for DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES
   - `model_config` with `.env` file support
   - Singleton `settings` instance exported

2. **`backend/app/database.py`** - Database session module with:
   - Import of `create_async_engine`, `async_sessionmaker`, `AsyncSession` from `sqlalchemy.ext.asyncio`
   - Engine creation with connection pool configuration
   - `async_session_maker` factory
   - `get_db()` async generator function for FastAPI dependency injection
   - structlog configuration and connection logging

3. **`backend/.env.example`** - Example environment file with:
   - DATABASE_URL (with placeholder values)
   - REDIS_URL (with placeholder values)
   - JWT_SECRET (with security comment)
   - JWT_ALGORITHM (optional, defaults to HS256)
   - JWT_EXPIRATION_MINUTES (optional, defaults to 15)

### Acceptance Criteria Checklist

Ensure your implementation satisfies all acceptance criteria:

- [ ] `database.py` exports `get_db()` function
- [ ] `get_db()` is an async generator function yielding AsyncSession
- [ ] Async engine created with DATABASE_URL from config
- [ ] Connection pool configured (pool_size=20, max_overflow=10)
- [ ] `config.py` uses Pydantic BaseSettings from `pydantic_settings`
- [ ] Config loads DATABASE_URL, REDIS_URL, JWT_SECRET
- [ ] JWT_ALGORITHM defaults to "HS256"
- [ ] JWT_EXPIRATION_MINUTES defaults to 15
- [ ] `.env.example` file created with sample values
- [ ] No errors when importing `from app.database import get_db`
- [ ] Logging configured to log database connections using structlog
- [ ] Code passes type checking (`mypy backend/app/config.py backend/app/database.py`)
- [ ] Code passes linting (`ruff check backend/app/config.py backend/app/database.py`)

### Additional Context

**Why this task matters:**
This task establishes the foundational database connection layer that all subsequent backend tasks will depend on. Without this, you cannot implement API endpoints, authentication, or any database operations. The configuration module also establishes the pattern for managing environment variables across the application.

**Common pitfalls to avoid:**
1. Using `pydantic.BaseSettings` instead of `pydantic_settings.BaseSettings` (Pydantic v2 change)
2. Forgetting to set `expire_on_commit=False` in async_sessionmaker (causes lazy loading errors)
3. Not using `async with` for session management in `get_db()` (causes resource leaks)
4. Hardcoding database credentials instead of using environment variables
5. Using `postgresql://` instead of `postgresql+asyncpg://` for the async driver

**Success validation:**
After implementing, test with:
```bash
# From backend directory
python -c "from app.database import get_db; print('Import successful')"
python -c "from app.config import settings; print(f'Config loaded: {settings.JWT_ALGORITHM}')"
```
