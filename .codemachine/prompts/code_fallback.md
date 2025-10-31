# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

**Task I4.T10: Security Hardening**

Security hardening: add security headers middleware (CSP, X-Frame-Options, HSTS), run dependency audit (pip-audit, npm audit), configure CORS properly, ensure secrets from env, input sanitization, run Bandit/eslint-plugin-security, update CI for security scans, document in security_review.md.

**Acceptance Criteria:**
- All responses include security headers
- CSP restricts sources
- HSTS present
- pip-audit/npm audit pass or documented
- CORS configured (not *)
- JWT_SECRET from env
- Bandit/ESLint pass
- CI runs scans
- security_review.md documents threats

---

## Issues Detected

**NO CODE WAS GENERATED for Task I4.T10.** The only changes made were:
- Deletion of code_fallback.md from a previous task
- Updates to context.md (task briefing)
- Test fixes for previous tasks (unrelated to I4.T10)

**All required deliverables are missing:**

### Missing Deliverable #1: Security Headers Middleware
- **File:** `backend/app/middleware/security_headers_middleware.py` does NOT exist
- **Impact:** No security headers (CSP, X-Frame-Options, HSTS, etc.) are being added to HTTP responses

### Missing Deliverable #2: Security Middleware Integration
- **File:** `backend/app/main.py` has NOT been updated
- **Impact:** Security headers middleware is not registered in the application
- **Current State:** CORS is hardcoded to `["http://localhost:3000"]` (not environment-configurable)

### Missing Deliverable #3: CORS Configuration
- **File:** `backend/app/config.py` has NOT been updated
- **Impact:** No CORS_ORIGINS setting for environment-based CORS configuration
- **Current State:** JWT_SECRET is correctly loaded from env (this part is already done ✓)

### Missing Deliverable #4: Backend Security Tools
- **File:** `backend/requirements-dev.txt` has NOT been updated
- **Impact:** No bandit or pip-audit tools available for security scanning
- **Current State:** File only has pytest, ruff, black, mypy (no security tools)

### Missing Deliverable #5: Frontend Security Tools
- **File:** `frontend/package.json` has NOT been updated
- **Impact:** No eslint-plugin-security for frontend security scanning
- **Current State:** Standard dev dependencies only (no security scanning)

### Missing Deliverable #6: ESLint Security Configuration
- **File:** `frontend/.eslintrc.json` or `frontend/.eslintrc.cjs` has NOT been updated
- **Impact:** ESLint security plugin not enabled (even if installed)

### Missing Deliverable #7: CI/CD Security Jobs
- **File:** `.github/workflows/ci-cd.yml` has NOT been updated
- **Impact:** No automated security scanning in CI pipeline
- **Required:** New jobs for backend-security (Bandit + pip-audit) and frontend-security (npm audit + ESLint)

### Missing Deliverable #8: Security Review Documentation
- **File:** `docs/architecture/security_review.md` does NOT exist
- **Impact:** No security documentation, threat model, or compliance checklist

---

## Best Approach to Fix

You MUST implement ALL eight deliverables for Task I4.T10. Follow these steps in order:

### Step 1: Create Security Headers Middleware

Create file `backend/app/middleware/security_headers_middleware.py` with the following implementation:

```python
"""
Security Headers Middleware for SOVD Command WebApp.

Adds security-related HTTP headers to all responses to enhance application security.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to all HTTP responses.

    Headers added:
    - Content-Security-Policy (CSP): Restricts sources for scripts, styles, images
    - X-Frame-Options: Prevents clickjacking by restricting iframe embedding
    - X-Content-Type-Options: Prevents MIME type sniffing
    - Strict-Transport-Security (HSTS): Enforces HTTPS connections
    - Referrer-Policy: Controls referrer information leakage
    - Permissions-Policy: Restricts browser features
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add security headers to response."""
        response = await call_next(request)

        # Content Security Policy (CSP)
        # Allow same-origin resources and inline scripts/styles (required for React/MUI)
        # Note: 'unsafe-inline' is needed for React and MUI but documented as accepted risk
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' ws: wss:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Prevent clickjacking - allow same-origin iframes only
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Enforce HTTPS (HSTS) - 1 year max-age, include subdomains
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict browser features (Permissions Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=()"
        )

        return response
```

### Step 2: Update Backend Configuration

Modify `backend/app/config.py` to add CORS_ORIGINS setting. Add this field after LOG_LEVEL (around line 30):

```python
    # CORS configuration
    CORS_ORIGINS: str = "http://localhost:3000"
```

This allows environment override like: `CORS_ORIGINS=https://app.example.com,https://app-staging.example.com`

### Step 3: Integrate Security Middleware in Main App

Modify `backend/app/main.py`:

1. **Add import** at the top (after other middleware imports, around line 13):
```python
from app.middleware.security_headers_middleware import SecurityHeadersMiddleware
```

2. **Register SecurityHeadersMiddleware FIRST** (before SlowAPIMiddleware, around line 140):
```python
# Register middleware (order matters - LIFO execution)
# Execution order: SecurityHeadersMiddleware → LoggingMiddleware → CORSMiddleware → SlowAPIMiddleware → Endpoints
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(LoggingMiddleware)
```

3. **Update CORS configuration** to use environment variable (around line 146-152):
```python
# Configure CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),  # Environment-configurable origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Step 4: Add Backend Security Tools

Modify `backend/requirements-dev.txt` by adding these lines at the end (after line 23):

```
# Security scanning
bandit>=1.7.0
pip-audit>=2.6.0
```

### Step 5: Add Frontend Security Tools

Modify `frontend/package.json` by adding to the `devDependencies` section:

```json
"eslint-plugin-security": "^1.7.1"
```

### Step 6: Configure ESLint Security Plugin

Check if `frontend/.eslintrc.json` or `frontend/.eslintrc.cjs` exists. Update the configuration to add the security plugin:

If using `.eslintrc.json`:
```json
{
  "plugins": ["react", "react-hooks", "security"],
  "extends": [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:react-hooks/recommended",
    "plugin:security/recommended"
  ]
}
```

If using `.eslintrc.cjs`:
```javascript
module.exports = {
  plugins: ['react', 'react-hooks', 'security'],
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
    'plugin:security/recommended'
  ],
  // ... rest of config
}
```

### Step 7: Add Security Jobs to CI/CD

Modify `.github/workflows/ci-cd.yml` by adding two new jobs after the existing lint jobs but before `ci-success`:

```yaml
  backend-security:
    name: Backend Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install security tools
        run: |
          pip install bandit pip-audit

      - name: Run Bandit security scan
        run: |
          bandit -r backend/app/ -f json -o bandit-report.json || true
          bandit -r backend/app/

      - name: Run pip-audit
        run: |
          pip-audit -r backend/requirements.txt || echo "Vulnerabilities found - review required"

      - name: Upload Bandit report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: bandit-security-report
          path: bandit-report.json

  frontend-security:
    name: Frontend Security Scan
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ./frontend
    steps:
      - uses: actions/checkout@v3

      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: npm ci

      - name: Run npm audit
        run: |
          npm audit --audit-level=high || echo "Vulnerabilities found - review required"

      - name: Run ESLint with security rules
        run: npm run lint
```

Also update the `ci-success` job's `needs` array to include the new security jobs:

```yaml
  ci-success:
    name: CI Success
    runs-on: ubuntu-latest
    needs:
      - frontend-lint
      - frontend-test
      - frontend-lighthouse
      - backend-lint
      - backend-test
      - backend-security    # ADD THIS
      - frontend-security   # ADD THIS
```

### Step 8: Create Security Review Documentation

Create file `docs/architecture/security_review.md` with comprehensive security documentation:

```markdown
# Security Review - SOVD Command WebApp

## 1. Overview

The SOVD Command WebApp implements a defense-in-depth security strategy with multiple layers of protection:
- Authentication and authorization (JWT + RBAC)
- Network security (HTTPS, CORS, security headers)
- Input validation and output encoding
- Audit logging and monitoring
- Rate limiting
- Automated security scanning

This document provides a comprehensive review of the application's security posture, threat model, and compliance with industry standards.

## 2. Threat Model

### 2.1 Identified Threats

| Threat | Likelihood | Impact | Risk Level |
|--------|-----------|--------|-----------|
| Unauthorized Access to Vehicles/Commands | Medium | High | High |
| SQL Injection | Low | High | Medium |
| Cross-Site Scripting (XSS) | Low | High | Medium |
| Cross-Site Request Forgery (CSRF) | Low | Medium | Low |
| Man-in-the-Middle Attacks | Medium | High | High |
| Denial of Service | Medium | Medium | Medium |
| Information Disclosure | Low | Medium | Low |
| Dependency Vulnerabilities | Medium | Medium | Medium |

### 2.2 Threat Mitigations

**Unauthorized Access:**
- **Mitigation:** JWT-based authentication with bcrypt password hashing, RBAC with role enforcement
- **Implementation:** `auth_service.py`, `dependencies.py` (get_current_user, require_role)
- **Status:** ✅ Implemented

**SQL Injection:**
- **Mitigation:** Parameterized queries via SQLAlchemy ORM, Pydantic input validation
- **Implementation:** All database models use SQLAlchemy ORM (never raw SQL)
- **Status:** ✅ Implemented

**Cross-Site Scripting (XSS):**
- **Mitigation:** Content Security Policy headers, React JSX auto-escaping, Pydantic output validation
- **Implementation:** SecurityHeadersMiddleware (CSP), React framework default behavior
- **Status:** ✅ Implemented

**Cross-Site Request Forgery (CSRF):**
- **Mitigation:** JWT tokens in Authorization header (not cookies), CORS restrictions
- **Implementation:** JWT authentication requires explicit header (not susceptible to browser auto-send)
- **Status:** ✅ Implemented

**Man-in-the-Middle Attacks:**
- **Mitigation:** HTTPS/TLS in production, HSTS header, secure cookie flags
- **Implementation:** HSTS header in SecurityHeadersMiddleware, production deployment uses TLS
- **Status:** ✅ Implemented (HSTS), 🔄 Pending (TLS cert in production deployment)

**Denial of Service:**
- **Mitigation:** Rate limiting on API endpoints, connection pooling, resource limits
- **Implementation:** SlowAPI middleware (5/min auth, 10/min commands), asyncio concurrency limits
- **Status:** ✅ Implemented

**Information Disclosure:**
- **Mitigation:** Generic error messages, sensitive data redaction in logs, security headers
- **Implementation:** ErrorHandlingMiddleware (filter_sensitive_data), X-Content-Type-Options header
- **Status:** ✅ Implemented

**Dependency Vulnerabilities:**
- **Mitigation:** Automated dependency scanning in CI/CD, regular updates
- **Implementation:** pip-audit and npm audit in GitHub Actions workflow
- **Status:** ✅ Implemented

## 3. Security Controls Implemented

### 3.1 Authentication & Authorization

**JWT-based Authentication:**
- Tokens include user ID, username, role, and expiration
- Tokens signed with HS256 algorithm using JWT_SECRET from environment
- Token expiration: 15 minutes (configurable via JWT_EXPIRATION_MINUTES)
- Implementation: `backend/app/services/auth_service.py`

**Password Security:**
- Bcrypt hashing with automatic salt generation
- Password validation enforced at API level (Pydantic models)
- No password storage in logs (filtered by SENSITIVE_FIELDS)
- Implementation: `passlib` library with `bcrypt` scheme

**Role-Based Access Control (RBAC):**
- Roles: `user`, `admin`
- Protected endpoints use `require_role()` dependency
- Commands restricted by user ownership or admin role
- Implementation: `backend/app/dependencies.py`

### 3.2 Network Security

**HTTPS/TLS:**
- Production deployment enforces HTTPS
- HSTS header with 1-year max-age and includeSubDomains
- Status: Production deployment pending (I5 tasks)

**CORS (Cross-Origin Resource Sharing):**
- Environment-configurable allowed origins (no wildcard)
- Development: `http://localhost:3000`
- Production: Specific domain(s) from CORS_ORIGINS environment variable
- Credentials allowed only for whitelisted origins
- Implementation: `backend/app/main.py` (CORSMiddleware)

**Security Headers:**
- Content-Security-Policy (CSP): Restricts script/style/image sources
- X-Frame-Options: SAMEORIGIN (prevents clickjacking)
- X-Content-Type-Options: nosniff (prevents MIME sniffing)
- Strict-Transport-Security (HSTS): Enforces HTTPS
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: Restricts geolocation, microphone, camera
- Implementation: `backend/app/middleware/security_headers_middleware.py`

### 3.3 Input Validation & Output Encoding

**Input Validation:**
- All API inputs validated using Pydantic models
- Type checking, format validation, length limits
- Email validation using pydantic EmailStr
- Implementation: `backend/app/models/schemas.py`

**SQL Injection Prevention:**
- All queries use SQLAlchemy ORM (parameterized queries)
- No raw SQL or string concatenation
- Implementation: All `backend/app/models/*.py` and `backend/app/services/*.py`

**XSS Prevention:**
- React JSX auto-escapes all output by default
- Content-Security-Policy header restricts inline scripts
- No use of dangerouslySetInnerHTML in frontend
- Implementation: React framework + SecurityHeadersMiddleware

**Output Encoding:**
- JSON responses automatically encoded by FastAPI
- Structured logging prevents log injection
- Implementation: FastAPI framework, structlog library

### 3.4 Logging & Monitoring

**Audit Logging:**
- All authentication attempts logged (success and failure)
- All command executions logged with user, vehicle, timestamp
- Sensitive data automatically redacted from logs
- Structured JSON logs for easy parsing
- Implementation: `backend/app/middleware/logging_middleware.py`

**Sensitive Data Redaction:**
- Fields filtered: password, token, secret, api_key, authorization, cookie
- Recursive filtering for nested objects
- Implementation: `backend/app/middleware/error_handling_middleware.py` (SENSITIVE_FIELDS)

**Metrics & Monitoring:**
- Prometheus metrics for request latency, error rates, active requests
- Health check endpoint: `/health`
- Implementation: `prometheus-fastapi-instrumentator` library

**Correlation IDs:**
- Unique request ID for distributed tracing
- Included in all log entries and error responses
- Implementation: LoggingMiddleware adds `correlation_id` to context

### 3.5 Rate Limiting

**Endpoint Rate Limits:**
- Authentication endpoints: 5 requests/minute per IP
- Command endpoints: 10 requests/minute per IP
- Implementation: `slowapi` library with Redis backend

**Configuration:**
- Storage: Redis (shared across instances)
- Strategy: Fixed window per IP address
- Headers: X-RateLimit-Limit, X-RateLimit-Remaining

### 3.6 Secrets Management

**Environment Variables:**
- JWT_SECRET: Required, loaded from environment
- DATABASE_URL: Required, loaded from environment
- REDIS_URL: Required, loaded from environment
- Implementation: `backend/app/config.py` (Pydantic Settings)

**Production Secrets:**
- AWS Secrets Manager integration (planned for I5)
- No secrets in source code or version control
- .env file excluded via .gitignore

## 4. Dependency Audit Results

### 4.1 Backend Dependencies (Python)

**Audit Tool:** pip-audit

**Audit Date:** [TO BE FILLED BY CODER - Run `pip-audit -r backend/requirements.txt`]

**Results:** [TO BE FILLED BY CODER]

**Known Issues:**
- [List any vulnerabilities found with CVE IDs, severity, and mitigation plan]
- Example: CVE-2024-XXXXX in package Y (Medium severity) - Upgrade pending, mitigated by network isolation

**Mitigation Actions:**
- [Document any vulnerabilities that can't be immediately fixed]

### 4.2 Frontend Dependencies (Node.js)

**Audit Tool:** npm audit

**Audit Date:** [TO BE FILLED BY CODER - Run `npm audit` in frontend/]

**Results:** [TO BE FILLED BY CODER]

**Known Issues:**
- [List any vulnerabilities found with CVE IDs, severity, and mitigation plan]

**Mitigation Actions:**
- [Document any vulnerabilities that can't be immediately fixed]

## 5. Static Analysis Results

### 5.1 Backend (Bandit)

**Tool:** Bandit (Python security linter)

**Scan Date:** [TO BE FILLED BY CODER - Run `bandit -r backend/app/`]

**Results:** [TO BE FILLED BY CODER]

**Findings:**
- [List any high/medium severity findings]
- [Note: SQL queries using SQLAlchemy ORM are safe - suppress false positives if needed]

**Suppressions:**
- Test files: Bandit skips `backend/tests/` directory
- Hardcoded test secrets: Use `# nosec` comment for test fixtures

### 5.2 Frontend (ESLint Security Plugin)

**Tool:** eslint-plugin-security

**Scan Date:** [TO BE FILLED BY CODER - Run `npm run lint` in frontend/]

**Results:** [TO BE FILLED BY CODER]

**Findings:**
- [List any security-related ESLint warnings]
- [Note: No use of eval(), dangerouslySetInnerHTML, or insecure randomness expected]

## 6. Security Best Practices for Developers

### 6.1 Code Guidelines

**Authentication & Authorization:**
- Always use `get_current_user` dependency for protected endpoints
- Use `require_role("admin")` for admin-only operations
- Never bypass authentication checks

**Input Validation:**
- Always define Pydantic models for request bodies
- Use appropriate field types (EmailStr, constr, conint, etc.)
- Validate all user inputs before processing

**Secrets & Configuration:**
- Never hardcode secrets or credentials
- Use environment variables for all configuration
- Add new secrets to `config.py` with Pydantic validation

**Logging:**
- Use structured logging (logger.info, logger.error)
- Never log passwords, tokens, or sensitive user data
- Include correlation IDs for traceability

**Error Handling:**
- Use HTTPException with appropriate status codes
- Return generic error messages to clients (no stack traces)
- Log detailed errors internally with correlation IDs

**Dependencies:**
- Run `pip-audit` and `npm audit` before adding new dependencies
- Keep dependencies up to date
- Review security advisories for critical packages

### 6.2 Testing Security

**Test Authentication:**
- Test with valid and invalid tokens
- Test with expired tokens
- Test with missing Authorization header

**Test Authorization:**
- Test user accessing their own resources (should succeed)
- Test user accessing others' resources (should fail)
- Test admin accessing any resources (should succeed)

**Test Input Validation:**
- Test with missing required fields
- Test with invalid data types
- Test with SQL injection payloads (should be rejected)
- Test with XSS payloads (should be escaped)

## 7. Known Risks and Mitigations

### 7.1 Accepted Risks

**Risk:** Content-Security-Policy allows 'unsafe-inline' for scripts and styles

**Justification:**
- Required by React (inline event handlers) and MUI (inline styles)
- React's JSX auto-escaping provides XSS protection
- Alternative (strict CSP with nonces) requires significant refactoring

**Mitigation:**
- React framework prevents XSS through auto-escaping
- No use of dangerouslySetInnerHTML
- Regular security audits of frontend code

**Residual Risk:** Low

---

**Risk:** JWT tokens stored in browser localStorage

**Justification:**
- Alternative (httpOnly cookies) complicates SPA architecture
- CORS restrictions limit cross-origin attacks

**Mitigation:**
- Short token expiration (15 minutes)
- Refresh token rotation (to be implemented in I5)
- XSS prevention via CSP and React escaping

**Residual Risk:** Medium

### 7.2 Residual Risks

**Risk:** Dependency vulnerabilities in transitive dependencies

**Mitigation:**
- Automated scanning in CI/CD pipeline
- Regular dependency updates
- Security advisories monitoring

**Current Status:** Monitored via pip-audit and npm audit

---

**Risk:** Insider threats (malicious admin users)

**Mitigation:**
- Comprehensive audit logging
- Role-based access control
- Monitoring and alerting (Prometheus metrics)

**Current Status:** Logging implemented, alerting pending (I5)

## 8. OWASP Top 10 (2021) Compliance

| # | Vulnerability | Status | Mitigation |
|---|--------------|--------|-----------|
| A01:2021 | Broken Access Control | ✅ Mitigated | JWT authentication + RBAC with role enforcement |
| A02:2021 | Cryptographic Failures | ✅ Mitigated | TLS/HTTPS, bcrypt password hashing, secure JWT signing |
| A03:2021 | Injection | ✅ Mitigated | Pydantic validation, SQLAlchemy ORM parameterized queries |
| A04:2021 | Insecure Design | ✅ Mitigated | Security-first architecture, defense-in-depth |
| A05:2021 | Security Misconfiguration | ✅ Mitigated | Security headers, proper CORS, no default credentials |
| A06:2021 | Vulnerable Components | ✅ Mitigated | Automated dependency scanning (pip-audit, npm audit) |
| A07:2021 | Identification and Authentication Failures | ✅ Mitigated | JWT tokens, bcrypt hashing, session management |
| A08:2021 | Software and Data Integrity Failures | ✅ Mitigated | CI/CD pipeline, code review, dependency verification |
| A09:2021 | Security Logging Failures | ✅ Mitigated | Comprehensive audit logging, structured logs, metrics |
| A10:2021 | Server-Side Request Forgery (SSRF) | ⚠️ Not Applicable | Application does not make outbound HTTP requests |

**Overall OWASP Compliance:** 9/10 applicable categories mitigated

## 9. Future Security Enhancements

### 9.1 Short-term Improvements (Next Iteration - I5)

1. **Refresh Token Rotation**
   - Implement refresh tokens with rotation
   - Reduce access token lifetime to 5 minutes
   - Detect token reuse attacks

2. **Multi-Factor Authentication (MFA)**
   - TOTP-based 2FA using authenticator apps
   - SMS-based 2FA as fallback
   - Recovery codes for account recovery

3. **Web Application Firewall (WAF)**
   - Deploy AWS WAF in production
   - Block common attack patterns
   - Rate limiting at edge

4. **Enhanced Monitoring**
   - Real-time security alerts
   - Anomaly detection (unusual login patterns)
   - Integration with SIEM system

### 9.2 Long-term Improvements

1. **Penetration Testing**
   - Annual third-party penetration tests
   - Bug bounty program

2. **Content Security Policy Hardening**
   - Remove 'unsafe-inline' using CSP nonces
   - Implement CSP reporting endpoint

3. **Zero-Trust Architecture**
   - Mutual TLS for service-to-service communication
   - Network segmentation
   - Principle of least privilege

4. **Advanced Threat Protection**
   - Behavioral analysis for fraud detection
   - Machine learning for anomaly detection

## 10. Security Incident Response

### 10.1 Incident Classification

**Critical:** Data breach, unauthorized admin access, service compromise
**High:** Successful XSS/injection attack, authentication bypass
**Medium:** DoS attack, brute force attempt, known vulnerability exploit
**Low:** Failed login attempts, suspicious activity

### 10.2 Response Procedure

1. **Detection:** Monitoring alerts, user reports, audit log analysis
2. **Containment:** Isolate affected systems, revoke compromised credentials
3. **Investigation:** Analyze logs, identify attack vector, assess impact
4. **Remediation:** Patch vulnerabilities, update security controls
5. **Recovery:** Restore services, validate security posture
6. **Post-Mortem:** Document incident, update security controls, train team

### 10.3 Contact Information

**Security Team:** [TO BE FILLED - security@example.com]
**On-Call Engineer:** [TO BE FILLED - Pager Duty rotation]
**Incident Commander:** [TO BE FILLED - Engineering Manager]

## 11. Compliance & Regulatory Considerations

**GDPR (if applicable):**
- User data encryption at rest and in transit
- Right to erasure (delete user data)
- Data breach notification within 72 hours

**SOC 2 (if pursuing certification):**
- Access controls and logging
- Change management process
- Incident response plan

**ISO 27001 (if pursuing certification):**
- Information security management system
- Risk assessment and treatment
- Continuous improvement

## 12. Security Review Sign-off

**Reviewed By:** [TO BE FILLED - Lead Engineer]
**Review Date:** [TO BE FILLED]
**Next Review Date:** [TO BE FILLED - Quarterly reviews recommended]

**Approval:**
- [ ] All OWASP Top 10 vulnerabilities addressed or documented
- [ ] Dependency audits completed with no critical vulnerabilities
- [ ] Static analysis scans passed
- [ ] Security headers implemented and verified
- [ ] CORS properly configured
- [ ] Secrets managed via environment variables
- [ ] CI/CD security scans enabled

---

**Document Version:** 1.0
**Last Updated:** [TO BE FILLED BY CODER]
**Status:** Draft
```

### Step 9: Run Security Scans and Update Documentation

After implementing all code changes, you MUST:

1. Install the new dependencies:
```bash
cd backend && pip install -r requirements-dev.txt
cd ../frontend && npm install
```

2. Run security scans locally:
```bash
# Backend scans
cd backend
bandit -r app/
pip-audit -r requirements.txt

# Frontend scans
cd ../frontend
npm audit
npm run lint
```

3. Update the security_review.md file with actual scan results:
   - Fill in the audit dates
   - Copy the scan results into sections 4.1, 4.2, 5.1, 5.2
   - Document any vulnerabilities found
   - Add mitigation plans for any issues that can't be immediately fixed

4. Test the security headers:
```bash
# Start the backend server
cd backend
uvicorn app.main:app --reload

# In another terminal, check headers
curl -I http://localhost:8000/health
```

Verify that the response includes:
- Content-Security-Policy
- X-Frame-Options
- X-Content-Type-Options
- Strict-Transport-Security
- Referrer-Policy
- Permissions-Policy

### Step 10: Verify All Acceptance Criteria

Before submitting, verify ALL acceptance criteria are met:

- [ ] All responses include security headers (verify with curl -I)
- [ ] CSP restricts sources (check CSP header value)
- [ ] HSTS present (check Strict-Transport-Security header)
- [ ] pip-audit/npm audit pass or documented (run scans, document results)
- [ ] CORS configured (not *) (verify allow_origins in main.py uses environment variable)
- [ ] JWT_SECRET from env (already done - config.py line 25)
- [ ] Bandit/ESLint pass (run scans locally)
- [ ] CI runs scans (verify backend-security and frontend-security jobs added)
- [ ] security_review.md documents threats (verify file created with all 12 sections)

---

## Summary

You must implement a complete security hardening solution with 8 deliverables:

1. **SecurityHeadersMiddleware** - New middleware class
2. **CORS configuration** - Environment-based CORS_ORIGINS setting
3. **Main app integration** - Register middleware and update CORS
4. **Backend security tools** - Add bandit and pip-audit
5. **Frontend security tools** - Add eslint-plugin-security
6. **ESLint configuration** - Enable security plugin
7. **CI/CD security jobs** - Add backend-security and frontend-security jobs
8. **Security documentation** - Comprehensive security_review.md

All code must be functional, properly formatted, and pass linting. All security scans must run successfully (or have documented exceptions). The security_review.md must be complete with actual scan results.

DO NOT submit partial work. ALL eight deliverables must be complete before marking this task as done.
