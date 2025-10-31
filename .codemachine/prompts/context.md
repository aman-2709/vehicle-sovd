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

The following are the relevant sections from the architecture and plan documents. Since the architecture blueprint files don't exist in the current codebase, I've extracted the relevant requirements from the task description and related documentation.

### Security Requirements Overview

The task requires implementing comprehensive security hardening across the following areas:

1. **Security Headers** - Add middleware to set HTTP security headers on all responses
2. **Dependency Auditing** - Scan Python and Node.js dependencies for known vulnerabilities
3. **CORS Configuration** - Ensure CORS is properly configured (not wildcard)
4. **Secrets Management** - Verify all secrets are loaded from environment variables
5. **Input Sanitization** - Ensure input validation and sanitization is in place
6. **Static Security Analysis** - Run Bandit (Python) and ESLint security plugin (JavaScript)
7. **CI Integration** - Add security scans to the CI/CD pipeline
8. **Security Documentation** - Create a comprehensive security review document

### Security Best Practices Reference

Based on OWASP Top 10 and industry standards, the application should implement:

**Security Headers (Required):**
- `Content-Security-Policy` (CSP) - Restrict script/style/image sources to prevent XSS
- `X-Frame-Options` - Prevent clickjacking by restricting iframe embedding
- `X-Content-Type-Options` - Prevent MIME type sniffing
- `Strict-Transport-Security` (HSTS) - Enforce HTTPS connections
- `Referrer-Policy` - Control referrer information leakage
- `Permissions-Policy` - Restrict browser features

**Dependency Security:**
- Regular vulnerability scanning of npm and pip packages
- Documented exceptions for any known vulnerabilities that can't be fixed
- Automated scanning in CI/CD pipeline

**CORS Security:**
- Explicit origin whitelist (development: localhost:3000, production: actual domain)
- No wildcard (*) origins in production
- Credentials allowed only for trusted origins

**Secrets Management:**
- All sensitive values (JWT_SECRET, DATABASE_URL, etc.) from environment variables
- No hardcoded secrets in source code
- .env file excluded from version control

**Input Sanitization:**
- Pydantic validation for all API inputs (already implemented)
- SQL injection prevention via parameterized queries (SQLAlchemy ORM handles this)
- XSS prevention via CSP headers and React's built-in escaping

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `backend/app/main.py`
    *   **Summary:** This is the FastAPI application entry point. It currently has CORS middleware configured with `allow_origins=["http://localhost:3000"]`, which is correct for development but will need to be environment-based for production. It already includes LoggingMiddleware, SlowAPIMiddleware, and exception handlers.
    *   **Current CORS Configuration (lines 145-152):**
        ```python
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],  # Frontend URL
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        ```
    *   **Recommendation:** You MUST:
        1. Create a new `CORS_ORIGINS` setting in `backend/app/config.py` that reads from environment variable
        2. Update the CORS middleware to use `settings.CORS_ORIGINS.split(",")` to support multiple origins
        3. Add the new security headers middleware BEFORE the existing middleware (middleware execution is LIFO - Last In First Out)
        4. The order should be: SecurityHeadersMiddleware → SlowAPIMiddleware → LoggingMiddleware → CORSMiddleware
    *   **Important Note:** The middleware stack on lines 140-152 shows the current order. Your SecurityHeadersMiddleware should be added at line 140 (before SlowAPIMiddleware).

*   **File:** `backend/app/config.py`
    *   **Summary:** Uses pydantic-settings to load configuration from environment variables. Currently has DATABASE_URL, REDIS_URL, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION_MINUTES, and LOG_LEVEL.
    *   **Current State:** JWT_SECRET is correctly loaded from environment (line 25), which satisfies one of the acceptance criteria.
    *   **Recommendation:** You MUST add a new `CORS_ORIGINS` field:
        ```python
        CORS_ORIGINS: str = "http://localhost:3000"
        ```
        This allows production deployments to override with their actual domain (e.g., `CORS_ORIGINS=https://app.example.com,https://app-staging.example.com`).
    *   **Validation:** The existing config already ensures JWT_SECRET must be provided or the app won't start, which is good.

*   **File:** `backend/app/middleware/error_handling_middleware.py`
    *   **Summary:** Provides global error handling with sensitive data filtering. There's a `SENSITIVE_FIELDS` set (lines 26-35) that includes password, token, secret, etc. The `filter_sensitive_data()` function (lines 258-276) can redact sensitive fields from logs.
    *   **Recommendation:** This existing sensitive data filtering demonstrates that input sanitization awareness is already present. You should reference this pattern in your security review document as a positive security control.
    *   **Note:** The error handlers already avoid exposing internal details (see `handle_unexpected_exception` which returns a generic message on line 234).

*   **File:** `backend/requirements-dev.txt`
    *   **Summary:** Contains development dependencies including pytest, ruff, black, mypy. Does NOT currently include security scanning tools.
    *   **Recommendation:** You MUST add these security tools:
        ```
        # Security scanning
        bandit>=1.7.0
        pip-audit>=2.6.0
        ```
    *   **Line Position:** Add the new "Security scanning" section after the "Type checking" section (after line 23).

*   **File:** `frontend/package.json`
    *   **Summary:** Contains all frontend dependencies. Currently includes standard dev dependencies (ESLint, Prettier, Vitest). Does NOT have security scanning plugins.
    *   **Recommendation:** You MUST add to devDependencies:
        ```json
        "eslint-plugin-security": "^1.7.1"
        ```
    *   **Additional Change:** You must also create or update `frontend/.eslintrc.json` to enable the security plugin:
        ```json
        "plugins": ["react", "react-hooks", "security"],
        "extends": [...existing..., "plugin:security/recommended"]
        ```

*   **File:** `.github/workflows/ci-cd.yml`
    *   **Summary:** Current CI/CD pipeline has separate jobs for frontend-lint, frontend-test, frontend-lighthouse, backend-lint, and backend-test. The workflow runs on push/PR to main, master, and develop branches.
    *   **Current Backend Lint Job (lines 116-146):** Runs ruff, black, and mypy. Does NOT run security scans.
    *   **Current Frontend Lint Job (lines 14-39):** Runs ESLint and Prettier. Does NOT run npm audit or security plugin checks.
    *   **Recommendation:** You MUST:
        1. Add a new job `backend-security` that runs Bandit and pip-audit
        2. Add a new job `frontend-security` that runs npm audit and ESLint with security rules
        3. Update the `ci-success` job's `needs` array to include these new security jobs
        4. The security jobs can run in parallel with the existing lint jobs (no dependencies between them)
    *   **Job Structure Template:**
        ```yaml
        backend-security:
          name: Backend Security Scan
          runs-on: ubuntu-latest
          steps:
            - uses: actions/checkout@v3
            - uses: actions/setup-python@v4
              with:
                python-version: '3.11'
                cache: 'pip'
            - name: Install security tools
              run: pip install bandit pip-audit
            - name: Run Bandit
              run: bandit -r backend/app/ -f json -o bandit-report.json
            - name: Run pip-audit
              run: pip-audit -r backend/requirements.txt
        ```

*   **File:** `docs/architecture/security_review.md` (does not exist yet)
    *   **Summary:** This file needs to be CREATED from scratch.
    *   **Recommendation:** You MUST create this file with the following sections:
        1. **Overview** - Summary of security posture
        2. **Threat Model** - Identify key threats (unauthorized access, data breaches, XSS, CSRF, injection attacks)
        3. **Security Controls Implemented** - List all security measures (headers, CORS, input validation, password hashing, JWT, rate limiting, audit logging)
        4. **Dependency Audit Results** - Document results of pip-audit and npm audit (include any known vulnerabilities and justifications if not immediately fixable)
        5. **Static Analysis Results** - Bandit and ESLint security findings
        6. **Security Best Practices** - Coding guidelines for developers
        7. **Known Risks and Mitigations** - Any residual risks
        8. **Compliance Checklist** - OWASP Top 10 coverage
    *   **Location:** Create at `docs/architecture/security_review.md` (you may need to create the `docs/architecture/` directory first).

*   **File:** `backend/app/services/auth_service.py`
    *   **Summary:** Implements JWT token generation/validation and password hashing using passlib with bcrypt (line 24). JWT uses python-jose library.
    *   **Security Analysis:**
        - ✅ Password hashing uses bcrypt (industry standard)
        - ✅ JWT tokens include expiration (line 74)
        - ✅ Tokens include role for RBAC (line 73)
        - ⚠️  Uses `datetime.utcnow()` (line 66) which is deprecated in Python 3.12+ (should use `datetime.now(timezone.utc)`)
    *   **Recommendation:** You SHOULD mention in the security review that password hashing and JWT handling follow best practices. The deprecated datetime usage is not a security issue but could be noted as a code quality improvement.

*   **File:** `backend/app/dependencies.py` (not read, but referenced in task dependencies)
    *   **Assumption:** This file likely contains the `get_current_user` and `require_role` dependencies for RBAC.
    *   **Recommendation:** In your security review, verify that all protected endpoints use these dependencies correctly. You don't need to modify this file for I4.T10.

### Implementation Tips & Notes

*   **Tip:** When creating the SecurityHeadersMiddleware, use Starlette's `BaseHTTPMiddleware` class pattern. The middleware should add headers to EVERY response, including error responses. Example structure:
    ```python
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request

    class SecurityHeadersMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            response = await call_next(request)
            # Add security headers here
            response.headers["X-Frame-Options"] = "SAMEORIGIN"
            # ... more headers
            return response
    ```

*   **Tip:** For Content-Security-Policy (CSP), use a strict policy that allows:
    - `default-src 'self'` - Only allow resources from same origin
    - `script-src 'self' 'unsafe-inline'` - Allow inline scripts (React requires this) and same-origin scripts
    - `style-src 'self' 'unsafe-inline'` - Allow inline styles (MUI uses inline styles) and same-origin stylesheets
    - `img-src 'self' data: https:` - Allow images from same origin, data URIs, and HTTPS sources
    - `connect-src 'self' ws: wss:` - Allow API calls to same origin and WebSocket connections
    - `font-src 'self'` - Only same-origin fonts
    - Note: 'unsafe-inline' is not ideal but necessary for React/MUI. Document this in security_review.md as an accepted risk.

*   **Tip:** For HSTS header, use: `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
    - max-age=31536000 is 1 year
    - includeSubDomains applies to all subdomains
    - preload allows the domain to be included in browser HSTS preload lists

*   **Note:** When running `pip-audit` in CI, you may encounter known vulnerabilities in transitive dependencies. If vulnerabilities are found:
    1. Try upgrading the affected package
    2. If upgrade breaks compatibility, document the vulnerability in security_review.md with:
       - CVE ID and severity
       - Why it can't be fixed immediately
       - Mitigation measures in place
       - Plan to fix (e.g., "waiting for library X to release compatible version")
    3. Use `pip-audit --ignore-vuln <CVE-ID>` to allow CI to pass, but ONLY after documenting

*   **Note:** Similarly for `npm audit`, you may need to use `npm audit --audit-level=high` to ignore low/moderate severity issues temporarily, but all findings must be documented in security_review.md.

*   **Warning:** The Bandit security scanner may flag some false positives:
    - SQL queries using SQLAlchemy ORM are safe (parameterized by default)
    - Assert statements in tests are acceptable (Bandit may flag these)
    - Hardcoded JWT test secrets in tests are acceptable (use `# nosec` comment to suppress)
    - Configure Bandit to skip the `tests/` directory: `bandit -r backend/app/ --exclude backend/tests/`

*   **Tip:** For the ESLint security plugin, common issues it catches:
    - Use of `eval()` or `Function()` constructor
    - Dangerous use of `dangerouslySetInnerHTML` in React
    - Insecure randomness (e.g., Math.random() for security purposes)
    - The frontend doesn't currently use any of these, so it should pass cleanly

*   **Testing Your Changes:**
    1. Run `bandit -r backend/app/` locally - should pass with 0 high/medium severity issues
    2. Run `pip-audit -r backend/requirements.txt` - document any findings
    3. Run `npm audit` in frontend directory - document any findings
    4. Test security headers by running the backend and checking response headers:
       ```bash
       curl -I http://localhost:8000/api/v1/vehicles
       ```
       You should see all security headers in the response
    5. Verify CORS by making a cross-origin request from the frontend - should still work
    6. Run the full CI/CD pipeline locally or in a PR to ensure security jobs pass

*   **Performance Note:** Adding security headers middleware has negligible performance impact (< 1ms per request). The headers are small and added in-memory.

### Project Conventions

*   **Code Style:** All Python code must pass ruff, black, and mypy checks. All TypeScript must pass ESLint and Prettier.

*   **Middleware Naming:** Middleware files should be named `*_middleware.py` and placed in `backend/app/middleware/`.

*   **Documentation Style:** All markdown documentation should use clear headers, code blocks with language identifiers, and bullet lists for readability.

*   **Configuration Pattern:** All environment-specific settings go in `backend/app/config.py` using Pydantic Settings. Never hardcode environment-specific values in source code.

*   **Error Handling:** All errors should use the standardized error response format from `error_handling_middleware.py`. The security review should note this as a security control (prevents information leakage).

*   **Git Workflow:** Create a feature branch `feature/I4.T10-security-hardening` for this work. The branch should be based on `develop`.

### Additional Context from Codebase Survey

*   **Existing Security Controls:** The codebase already has several security measures in place:
    - JWT-based authentication with bcrypt password hashing
    - RBAC (role-based access control) via `require_role` dependency
    - Rate limiting via slowapi (5/min for auth, 10/min for commands)
    - Input validation via Pydantic models
    - Audit logging for all security events
    - Sensitive data redaction in logs
    - CORS (though it needs to be environment-configurable)

*   **Input Sanitization:** Pydantic handles input validation on all API endpoints. SQLAlchemy ORM uses parameterized queries, preventing SQL injection. React's JSX automatically escapes output, preventing XSS. These are all sufficient and should be documented in security_review.md.

*   **Secrets Management:** Currently uses .env file for local development. The config.py correctly loads JWT_SECRET from environment (line 25). Production deployment (I5 tasks) will use AWS Secrets Manager. Document this in security_review.md.

*   **Known Dependencies:**
    - Backend: FastAPI, SQLAlchemy, Pydantic, passlib, python-jose, redis, asyncpg, structlog, prometheus-fastapi-instrumentator, slowapi
    - Frontend: React, MUI, React Router, React Query, Axios
    - All major dependencies are industry-standard and actively maintained

*   **Missing Security Measures (to be implemented in this task):**
    1. ✗ Security headers middleware
    2. ✗ Automated dependency vulnerability scanning
    3. ✗ Static security analysis in CI
    4. ✗ Environment-based CORS configuration
    5. ✗ Security documentation

### Security Review Document Structure

Your `security_review.md` should follow this structure:

```markdown
# Security Review - SOVD Command WebApp

## 1. Overview
[Brief summary of security posture - e.g., "The application implements defense-in-depth..."]

## 2. Threat Model
### Identified Threats
- Unauthorized Access to Vehicles/Commands
- SQL Injection
- Cross-Site Scripting (XSS)
- Cross-Site Request Forgery (CSRF)
- Man-in-the-Middle Attacks
- Denial of Service
- Information Disclosure

### Threat Mitigations
[Map each threat to the controls that mitigate it]

## 3. Security Controls Implemented
### Authentication & Authorization
- JWT-based authentication
- Bcrypt password hashing
- RBAC with role enforcement

### Network Security
- HTTPS/TLS (production)
- CORS with explicit origin whitelist
- Security headers (CSP, HSTS, etc.)

### Input Validation & Output Encoding
- Pydantic input validation
- SQLAlchemy parameterized queries
- React JSX auto-escaping

### Logging & Monitoring
- Structured audit logging
- Sensitive data redaction
- Prometheus metrics

### Rate Limiting
- Auth endpoints: 5 requests/minute
- Command endpoints: 10 requests/minute

## 4. Dependency Audit Results
### Backend (Python)
[Include pip-audit results - clean or documented exceptions]

### Frontend (Node.js)
[Include npm audit results - clean or documented exceptions]

## 5. Static Analysis Results
### Backend (Bandit)
[Include Bandit findings and resolutions]

### Frontend (ESLint Security)
[Include ESLint security findings]

## 6. Security Best Practices for Developers
- Always use Pydantic models for API inputs
- Never log sensitive data (passwords, tokens, etc.)
- Use `get_current_user` and `require_role` dependencies for protected endpoints
- Keep dependencies up to date
- Run security scans before committing

## 7. Known Risks and Mitigations
### Accepted Risks
- CSP allows 'unsafe-inline' for scripts/styles (required by React/MUI)
  - Mitigation: React's JSX escaping prevents XSS despite inline scripts

### Residual Risks
- [List any vulnerabilities that can't be fixed immediately with mitigation plans]

## 8. OWASP Top 10 (2021) Compliance
- [x] A01:2021 – Broken Access Control: Mitigated by JWT + RBAC
- [x] A02:2021 – Cryptographic Failures: Mitigated by TLS, bcrypt, secure JWT
- [x] A03:2021 – Injection: Mitigated by Pydantic validation, ORM parameterized queries
- [x] A04:2021 – Insecure Design: Mitigated by secure architecture, defense-in-depth
- [x] A05:2021 – Security Misconfiguration: Mitigated by security headers, proper CORS
- [x] A06:2021 – Vulnerable Components: Mitigated by automated dependency scanning
- [x] A07:2021 – Identification and Authentication Failures: Mitigated by JWT, bcrypt
- [x] A08:2021 – Software and Data Integrity Failures: Mitigated by CI/CD, code review
- [x] A09:2021 – Security Logging Failures: Mitigated by audit logging, metrics
- [x] A10:2021 – Server-Side Request Forgery: Not applicable (no SSRF functionality)

## 9. Future Security Enhancements
- Implement refresh token rotation
- Add MFA (multi-factor authentication)
- Implement Content Security Policy reporting
- Add Web Application Firewall (WAF) in production
- Implement automated penetration testing
```

### Critical Acceptance Criteria Checklist

Before marking this task complete, verify ALL of these:

1. **Security Headers Middleware:**
   - [ ] SecurityHeadersMiddleware class created in `backend/app/middleware/security_headers_middleware.py`
   - [ ] Middleware added to main.py (before other middleware)
   - [ ] All required headers present: CSP, X-Frame-Options, X-Content-Type-Options, HSTS, Referrer-Policy
   - [ ] Headers verified in HTTP response (use curl -I)

2. **CORS Configuration:**
   - [ ] CORS_ORIGINS setting added to config.py
   - [ ] main.py updated to use settings.CORS_ORIGINS.split(",")
   - [ ] No wildcard (*) origins in configuration
   - [ ] Frontend can still connect (test manually)

3. **Dependency Auditing:**
   - [ ] pip-audit added to requirements-dev.txt
   - [ ] bandit added to requirements-dev.txt
   - [ ] eslint-plugin-security added to frontend package.json
   - [ ] All audits run successfully (or exceptions documented)

4. **CI/CD Integration:**
   - [ ] backend-security job added to workflow
   - [ ] frontend-security job added to workflow
   - [ ] Both jobs run Bandit/pip-audit and npm audit/ESLint security
   - [ ] ci-success job updated to depend on security jobs
   - [ ] Workflow file is valid YAML (no syntax errors)

5. **Security Review Document:**
   - [ ] docs/architecture/security_review.md created
   - [ ] All 9 sections present (Overview, Threat Model, Controls, Audits, etc.)
   - [ ] Dependency audit results documented
   - [ ] Static analysis results documented
   - [ ] OWASP Top 10 compliance checklist complete

6. **Secrets Management:**
   - [ ] Verified JWT_SECRET loaded from environment (already done - config.py line 25)
   - [ ] Verified no secrets hardcoded in source (grep for common patterns)
   - [ ] .env file in .gitignore (already done - .gitignore includes .env)

7. **Testing:**
   - [ ] Run `bandit -r backend/app/` - passes
   - [ ] Run `pip-audit -r backend/requirements.txt` - clean or documented
   - [ ] Run `npm audit` in frontend - clean or documented
   - [ ] Verify security headers with curl
   - [ ] All existing tests still pass
   - [ ] CI/CD pipeline passes

### Summary

This task focuses on adding the final security hardening layer to make the application production-ready. The key deliverables are:

1. **New middleware** to add security headers to all HTTP responses
2. **Enhanced CORS** configuration that's environment-aware
3. **Automated security scanning** integrated into CI/CD
4. **Comprehensive security documentation** for the security review

The implementation should take approximately 3-4 hours for an experienced developer. Most of the security controls are already in place (authentication, input validation, rate limiting), so this task is primarily about adding the missing infrastructure security layer (headers, auditing, scanning) and documenting the overall security posture.
