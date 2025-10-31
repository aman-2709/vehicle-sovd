# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T10",
  "iteration_id": "I4",
  "iteration_goal": "Production Readiness - Command History, Monitoring & Refinements",
  "description": "Security hardening: add security headers middleware (CSP, X-Frame-Options, HSTS), run dependency audit (pip-audit, npm audit), configure CORS properly, ensure secrets from env, input sanitization, run Bandit/eslint-plugin-security, update CI for security scans, document in security_review.md.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.8 (Security); Section 2.2 (NFRs).",
  "target_files": [
    "backend/app/middleware/security_headers_middleware.py",
    "backend/app/main.py",
    "backend/requirements-dev.txt",
    "frontend/package.json",
    ".github/workflows/ci-cd.yml",
    "docs/architecture/security_review.md"
  ],
  "input_files": [
    "backend/app/main.py"
  ],
  "deliverables": "Security headers; dependency audit results; CORS config; security scans in CI; security review doc.",
  "acceptance_criteria": "All responses include security headers; CSP restricts sources; HSTS present; pip-audit/npm audit pass or documented; CORS configured (not *); JWT_SECRET from env; Bandit/ESLint pass; CI runs scans; security_review.md documents threats",
  "dependencies": [
    "I4.T1",
    "I4.T2",
    "I4.T3",
    "I4.T4",
    "I4.T5",
    "I4.T6",
    "I4.T7",
    "I4.T8",
    "I4.T9"
  ],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: Security Non-Functional Requirements (from 01_Context_and_Drivers.md)

```markdown
<!-- anchor: nfr-security -->
#### Security
- **Encryption in Transit**: TLS 1.3 for all communication (web client ↔ backend, backend ↔ vehicle)
- **Encryption at Rest**: Sensitive data encrypted in database
- **Authentication**: JWT-based authentication with short-lived tokens (15 min) and refresh tokens
- **Authorization**: Role-based access control enforced at API gateway
- **Audit Logging**: All command executions logged with user identity, timestamp, and outcome
- **Input Validation**: Strict validation of all user inputs to prevent injection attacks
- **Secrets Management**: Secure storage and rotation of API keys, database credentials

**Architectural Impact**: API gateway for centralized auth, dedicated auth service, secure secrets management (e.g., AWS Secrets Manager), audit log service.
```

### Context: Security Considerations and Threat Model (from 05_Operational_Architecture.md)

```markdown
<!-- anchor: security-considerations -->
#### Security Considerations

<!-- anchor: security-threat-model -->
**Threat Model & Mitigations**

**Threat: Unauthorized Command Execution**
- **Mitigation**: JWT-based authentication on every request; RBAC enforcement; audit logging

**Threat: Man-in-the-Middle (MITM) Attacks**
- **Mitigation**: TLS 1.3 for all communication; HSTS headers; certificate pinning for vehicle communication

**Threat: SQL Injection**
- **Mitigation**: Parameterized queries via SQLAlchemy ORM; input validation with Pydantic

**Threat: Cross-Site Scripting (XSS)**
- **Mitigation**: React automatic escaping; Content-Security-Policy headers; sanitized user inputs

**Threat: Credential Stuffing / Brute Force**
- **Mitigation**: Rate limiting (Nginx); account lockout after 5 failed attempts; CAPTCHA for login (future)

**Threat: Token Theft**
- **Mitigation**: Short-lived access tokens (15 min); httpOnly cookies for refresh tokens; token binding (future)

**Threat: Insider Threat / Privilege Escalation**
- **Mitigation**: RBAC; audit logs for all actions; least-privilege principle; database row-level security (future)

**Threat: Denial of Service (DoS)**
- **Mitigation**: Rate limiting; API Gateway throttling; AWS WAF for DDoS; auto-scaling

**Threat: Data Breach / Database Compromise**
- **Mitigation**: Encryption at rest (AWS RDS); encryption in transit (TLS); secrets in AWS Secrets Manager; regular security audits

<!-- anchor: security-practices -->
**Security Practices**

**Secrets Management:**
- **Development**: `.env` file (gitignored), Docker secrets
- **Production**: AWS Secrets Manager
  - Database credentials, JWT signing key, API keys
  - Automatic rotation for database passwords (90 days)
  - IAM roles for service access (no hardcoded credentials)

**Input Validation:**
- All API inputs validated with Pydantic models (type, format, range)
- SOVD command validation against SOVD 2.0 schema
- Vehicle ID validation (UUID format, exists in database)
- File upload validation (if future feature): MIME type, size limit, virus scanning

**Dependency Security:**
- **Frontend**: `npm audit` in CI pipeline; Dependabot alerts
- **Backend**: `pip-audit` / `safety` in CI pipeline
- Automated dependency updates for critical vulnerabilities

**Secure Development Lifecycle:**
- Code review required (CODEOWNERS)
- Static analysis: Bandit (Python security linter), ESLint security plugin
- Secrets scanning: git-secrets, TruffleHog
- Penetration testing: Annual third-party audit (production)
```

### Context: Authentication & Authorization Strategy (from 05_Operational_Architecture.md)

```markdown
<!-- anchor: authentication-authorization -->
#### Authentication & Authorization

<!-- anchor: auth-strategy -->
**Authentication Strategy: JWT-Based with Refresh Tokens**

**Implementation:**
- **Access Tokens**: Short-lived (15 minutes), stateless JWT tokens
  - Contains: `user_id`, `username`, `role`, `exp` (expiration), `iat` (issued at)
  - Signed with HS256 algorithm (HMAC with SHA-256)
  - Validated on every API request via middleware
- **Refresh Tokens**: Long-lived (7 days), stored in database
  - Used to obtain new access tokens without re-authentication
  - Supports token revocation (logout invalidates refresh token)
  - Rotated on each refresh for security

**Authentication Flow:**
1. User submits credentials to `/api/v1/auth/login`
2. Backend validates against database (password hashed with bcrypt)
3. On success, generates access + refresh tokens
4. Client stores access token in memory, refresh token in httpOnly cookie (or local storage with XSS mitigations)
5. Client includes access token in `Authorization: Bearer {token}` header
6. On access token expiration, client calls `/api/v1/auth/refresh` with refresh token
7. Backend validates refresh token, issues new access token

**Integration with External IdP (Future):**
- Architecture supports OAuth2/OIDC integration
- FastAPI middleware can validate external IdP tokens (e.g., Auth0, Okapi, Azure AD)
- User profile synced to local database on first login
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/app/middleware/security_headers_middleware.py`
    *   **Summary:** This middleware is ALREADY IMPLEMENTED and adds comprehensive security headers to all HTTP responses including Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, HSTS, Referrer-Policy, and Permissions-Policy.
    *   **Status:** ✅ COMPLETE - Security headers middleware is already fully implemented with all required headers.
    *   **Recommendation:** You DO NOT need to implement this middleware. It already exists and is properly registered in `main.py`. However, you MUST verify that it is working correctly and that all headers are present in responses.

*   **File:** `backend/app/main.py`
    *   **Summary:** This is the main FastAPI application entry point. It already imports and registers the SecurityHeadersMiddleware (line 34, 143). CORS is configured with environment-variable-based origins (lines 148-154).
    *   **Current CORS Configuration:**
        ```python
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS.split(","),  # Environment-configurable origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        ```
    *   **Status:** ✅ CORS is already properly configured to use environment variable `CORS_ORIGINS` and NOT using wildcard (*). Default value in config.py is "http://localhost:3000".
    *   **Recommendation:** CORS configuration is CORRECT. You SHOULD verify that no wildcard is used and that the configuration is properly documented.

*   **File:** `backend/app/config.py`
    *   **Summary:** Application configuration using Pydantic Settings. All sensitive values are loaded from environment variables: DATABASE_URL, REDIS_URL, JWT_SECRET, CORS_ORIGINS.
    *   **Status:** ✅ Secrets management is correctly implemented using environment variables.
    *   **Issue:** There is NO `.env.example` file in the repository root to document required environment variables.
    *   **Recommendation:** You MUST create a `.env.example` file documenting all required environment variables with example (non-secret) values.

*   **File:** `backend/requirements-dev.txt`
    *   **Summary:** Development dependencies file. Already includes `bandit>=1.7.0` and `pip-audit>=2.6.0` for security scanning.
    *   **Status:** ✅ Security scanning tools are already in development dependencies.
    *   **Recommendation:** These tools are already available. You just need to ensure they are used correctly in the CI/CD pipeline.

*   **File:** `frontend/package.json`
    *   **Summary:** Frontend dependencies. Already includes `eslint-plugin-security: ^1.7.1` in devDependencies.
    *   **Status:** ✅ ESLint security plugin is already installed.
    *   **Recommendation:** The security plugin is already installed and configured in `.eslintrc.json`.

*   **File:** `frontend/.eslintrc.json`
    *   **Summary:** ESLint configuration with security plugin already enabled. Extends "plugin:security/recommended" (line 14) and includes "security" in plugins (line 29).
    *   **Status:** ✅ ESLint security plugin is properly configured.
    *   **Recommendation:** Configuration is correct. You just need to verify it works.

*   **File:** `.github/workflows/ci-cd.yml`
    *   **Summary:** CI/CD pipeline with comprehensive security scanning ALREADY IMPLEMENTED. Includes dedicated jobs for:
        - `backend-security` (lines 210-244): Runs Bandit and pip-audit
        - `frontend-security` (lines 247-272): Runs npm audit and ESLint with security rules
    *   **Status:** ✅ Security scans are ALREADY in the CI/CD pipeline.
    *   **Current Implementation:**
        - Bandit runs on `backend/app/` directory with JSON output
        - pip-audit runs on requirements.txt (allows failures with warning)
        - npm audit runs with `--audit-level=high` (allows failures with warning)
        - ESLint runs with security plugin enabled
    *   **Recommendation:** The security scans are already implemented. You SHOULD verify they run correctly and update the security_review.md with the actual results.

*   **File:** `docs/architecture/security_review.md`
    *   **Summary:** Comprehensive security review document ALREADY EXISTS with detailed threat model, OWASP Top 10 compliance mapping, dependency audit results (dated 2025-10-30), static analysis results, and security best practices.
    *   **Status:** ✅ Document is substantially complete with actual audit results.
    *   **Current Audit Results:**
        - Backend: 1 medium vulnerability in ecdsa (python-jose dependency) - DOCUMENTED as low risk
        - Frontend: 13 vulnerabilities (8 low, 5 moderate) in dev dependencies - DOCUMENTED as low risk
        - Bandit: 7 low-severity findings (all false positives or acceptable) - DOCUMENTED
        - ESLint: 5 security warnings (all false positives) - DOCUMENTED
    *   **Recommendation:** The document is already comprehensive and up-to-date. You SHOULD verify the information is current and make any minor updates if audit results have changed.

*   **File:** `backend/pyproject.toml`
    *   **Summary:** Python project configuration with tool configurations for Black, Ruff, mypy, pytest, and coverage. Does NOT include Bandit configuration.
    *   **Recommendation:** You MAY add a `[tool.bandit]` section to configure Bandit exclude paths or suppress known false positives, but this is OPTIONAL.

### Implementation Tips & Notes

*   **Tip:** The security hardening task is MOSTLY COMPLETE. Almost all required components are already implemented:
    - ✅ Security headers middleware exists and is registered
    - ✅ CORS is properly configured (not using wildcard)
    - ✅ Secrets are loaded from environment variables
    - ✅ Dependency scanning tools (Bandit, pip-audit, ESLint security, npm audit) are installed
    - ✅ CI/CD pipeline runs all security scans
    - ✅ security_review.md document exists with comprehensive threat analysis and audit results

*   **Note:** Your PRIMARY task is VERIFICATION and DOCUMENTATION:
    1. **Verify** that security headers are present in HTTP responses (test the running app)
    2. **Verify** that CORS is not using wildcard (code review confirms this)
    3. **Verify** that secrets are from environment (code review confirms this)
    4. **Run** security scans locally and verify they pass (or document failures)
    5. **Update** security_review.md if audit results have changed
    6. **Create** `.env.example` file (THIS IS MISSING and REQUIRED)
    7. **Document** any findings in security_review.md

*   **Warning:** The acceptance criteria states "pip-audit/npm audit pass or documented". The current security_review.md shows that vulnerabilities exist but are documented as low-risk (dev dependencies only). This is ACCEPTABLE per the criteria - they don't need to pass, they need to be DOCUMENTED, which they are.

*   **Tip:** When running Bandit, use the same command as the CI/CD pipeline:
    ```bash
    bandit -r backend/app/
    ```
    Expected result: 7 low-severity findings (all documented as false positives in security_review.md)

*   **Tip:** When running pip-audit:
    ```bash
    pip-audit -r backend/requirements.txt
    ```
    Expected result: 1 vulnerability in ecdsa (documented as low risk because we use HS256, not ECDSA)

*   **Tip:** The CSP header currently uses 'unsafe-inline' for scripts and styles. This is DOCUMENTED as an accepted risk in security_review.md section 7.1 because it's required by React and MUI. This is ACCEPTABLE and should not be changed.

*   **Critical:** You MUST create a `.env.example` file in the project root with all required environment variables. Based on `config.py`, the required variables are:
    - DATABASE_URL (example: "postgresql://user:password@localhost:5432/sovd")
    - REDIS_URL (example: "redis://localhost:6379")
    - JWT_SECRET (example: "your-secret-key-change-in-production")
    - JWT_ALGORITHM (optional, default: "HS256")
    - JWT_EXPIRATION_MINUTES (optional, default: 15)
    - LOG_LEVEL (optional, default: "INFO")
    - CORS_ORIGINS (optional, default: "http://localhost:3000")

*   **Testing Strategy:** To verify security headers, you can:
    1. Start the backend: `cd backend && uvicorn app.main:app --reload`
    2. Make a request: `curl -I http://localhost:8000/health`
    3. Verify headers include: Content-Security-Policy, X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security, Referrer-Policy, Permissions-Policy

*   **Final Acceptance Criteria Checklist:**
    - ✅ All responses include security headers (verify by testing)
    - ✅ CSP restricts sources (already implemented in middleware)
    - ✅ HSTS present (already implemented in middleware)
    - ✅ pip-audit/npm audit pass or documented (already documented in security_review.md)
    - ✅ CORS configured (not *) (already correct in main.py)
    - ✅ JWT_SECRET from env (already correct in config.py)
    - ✅ Bandit/ESLint pass (already documented in security_review.md)
    - ✅ CI runs scans (already implemented in ci-cd.yml)
    - ⏳ security_review.md documents threats (already exists, verify it's current)

---

## 4. Task Execution Recommendations

Based on my analysis, this task is **95% complete**. Here's what you need to do:

### 4.1 Required Actions (Missing Pieces)

1. **Create `.env.example` file** in project root with documented environment variables
2. **Verify security headers** by running the app and testing with curl or browser
3. **Run security scans locally** to confirm they work:
   - `bandit -r backend/app/`
   - `pip-audit -r backend/requirements.txt`
   - `npm audit --audit-level=high` (in frontend directory)
4. **Update security_review.md** if audit results have changed since 2025-10-30

### 4.2 Optional Enhancements

1. Add Bandit configuration to `pyproject.toml` to suppress known false positives
2. Add security testing to integration tests (verify headers are present)
3. Update README.md with security best practices section

### 4.3 What NOT to Do

- Do NOT reimplement security_headers_middleware.py (it already exists and works)
- Do NOT change CORS configuration (it's already correct)
- Do NOT change secrets management (it's already using environment variables)
- Do NOT remove 'unsafe-inline' from CSP (it's a documented accepted risk)

### 4.4 Success Criteria

The task is complete when:
- `.env.example` file exists and documents all required variables
- Security headers are verified to be present in responses
- Security scans run successfully (or failures are documented)
- security_review.md is verified to be current and accurate
- All acceptance criteria from the task specification are met
