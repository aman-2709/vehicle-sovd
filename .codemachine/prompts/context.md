# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I5.T3",
  "iteration_id": "I5",
  "iteration_goal": "Production Deployment Infrastructure - Kubernetes, CI/CD & gRPC Foundation",
  "description": "Implement CI/CD pipeline in .github/workflows/ci-cd.yml. Stages: 1) Lint (parallel: backend+frontend), 2) Unit tests (parallel, fail <80%), 3) Integration tests (docker-compose), 4) E2E tests, 5) Security scans (parallel: pip-audit, npm audit, Bandit, Trivy), 6) Build images (tag SHA+latest), 7) Push to registry, 8) Deploy staging (on develop), 9) Deploy production (on main, manual approval, smoke tests, rollback). Cache dependencies. Add smoke test script. Add README badges.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.9; GitHub Actions docs.",
  "target_files": [
    ".github/workflows/ci-cd.yml",
    "scripts/smoke_tests.sh",
    "README.md"
  ],
  "input_files": [],
  "deliverables": "Complete CI/CD workflow; smoke tests; README badges; deployment automation.",
  "acceptance_criteria": "Pipeline triggers on push/PR; Lint/unit tests parallel; Integration/E2E run with docker-compose; Security scans fail on critical; Images built+pushed; Staging auto-deploys on develop; Production manual approval on main; Smoke tests verify endpoints; Caching works; Badges in README; Pipeline <15min",
  "dependencies": ["I5.T1", "I5.T2", "I3.T9"],
  "parallelizable": false,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: cicd-pipeline (from 05_Operational_Architecture.md)

```markdown
**CI/CD Pipeline (GitHub Actions)**

**Workflow Stages:**

1. **Lint & Format Check**
   - Frontend: ESLint, Prettier
   - Backend: Ruff, Black, mypy

2. **Unit Tests**
   - Frontend: Vitest (coverage threshold 80%)
   - Backend: pytest (coverage threshold 80%)

3. **Build Docker Images**
   - Build frontend and backend images
   - Tag with commit SHA and `latest`

4. **Integration Tests**
   - Spin up services with docker-compose
   - Run API integration tests (pytest + httpx)
   - Run E2E tests (Playwright)

5. **Security Scans**
   - `npm audit` (frontend dependencies)
   - `pip-audit` (backend dependencies)
   - Trivy (Docker image vulnerabilities)

6. **Push Images**
   - Push to AWS ECR (Elastic Container Registry)

7. **Deploy to Staging**
   - Update Kubernetes deployment with new image
   - Run smoke tests

8. **Manual Approval Gate**
   - Require approval for production deploy

9. **Deploy to Production**
   - Blue-green deployment strategy
   - Gradual rollout (10%, 50%, 100%)
   - Automatic rollback if error rate spikes

**GitHub Actions Workflow File:**
```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-and-test:
    # ... (lint, test, build stages)

  deploy-staging:
    needs: lint-and-test
    if: github.ref == 'refs/heads/develop'
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Staging
        run: |
          helm upgrade --install sovd-webapp ./helm \
            -f values-staging.yaml -n staging

  deploy-production:
    needs: lint-and-test
    if: github.ref == 'refs/heads/main'
    environment: production  # Manual approval
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to Production
        run: |
          helm upgrade --install sovd-webapp ./helm \
            -f values-production.yaml -n production
```
```

### Context: task-i5-t3 (from 02_Iteration_I5.md)

```markdown
*   **Task 5.3: Create GitHub Actions CI/CD Pipeline**
    *   **Task ID:** `I5.T3`
    *   **Description:** Implement comprehensive CI/CD pipeline in `.github/workflows/ci-cd.yml`. Pipeline stages: 1) **Lint & Format Check** (parallel jobs): backend linting (ruff, black --check, mypy), frontend linting (eslint, prettier --check), 2) **Unit Tests** (parallel): backend unit tests with coverage, frontend unit tests with coverage, fail if coverage <80%, 3) **Integration Tests**: start services with docker-compose, run backend integration tests, run frontend integration tests, 4) **E2E Tests**: start full stack, run Playwright E2E tests, 5) **Security Scans** (parallel): pip-audit (backend), npm audit (frontend), Bandit security scan, Docker image scan with Trivy, 6) **Build Docker Images**: build backend and frontend production images, tag with commit SHA and `latest`, 7) **Push Images**: push to container registry (GitHub Container Registry or AWS ECR) - requires authentication setup, 8) **Deploy to Staging** (on push to `develop` branch): deploy Helm chart to staging namespace with staging values, run smoke tests, 9) **Deploy to Production** (on push to `main` branch): manual approval gate (GitHub environment protection), deploy Helm chart to production namespace, gradual rollout (use Helm or custom script), run smoke tests, automatic rollback on failure. Configure caching for dependencies (pip cache, npm cache) to speed up builds. Add status badges to README.
    *   **Agent Type Hint:** `BackendAgent` + `DevOpsAgent`
    *   **Inputs:** Architecture Blueprint Section 3.9 (CI/CD Pipeline); GitHub Actions documentation.
    *   **Input Files:** []
    *   **Target Files:**
        *   `.github/workflows/ci-cd.yml`
        *   `scripts/smoke_tests.sh` (smoke test script for post-deployment validation)
        *   Updates to `README.md` (add CI/CD status badges)
    *   **Deliverables:** Complete GitHub Actions CI/CD workflow; smoke test script; README badges; deployment automation.
    *   **Acceptance Criteria:**
        *   Pipeline triggers on push to `develop` and `main` branches, and on pull requests
        *   Lint & Format Check jobs run in parallel, fail if linting errors
        *   Unit test jobs run in parallel, fail if tests fail or coverage <80%
        *   Integration tests start docker-compose, run tests, stop services (even on failure)
        *   E2E tests run Playwright with headless browser, capture screenshots on failure
        *   Security scan jobs run in parallel, fail on critical vulnerabilities
        *   Docker build jobs build production images, tag with SHA and `latest`
        *   Images pushed to registry (verify in GitHub Container Registry or ECR)
        *   Staging deployment triggers automatically on push to `develop`
        *   Production deployment requires manual approval (GitHub environment: `production`)
        *   Smoke tests verify key endpoints: `/health/ready`, `/api/v1/vehicles`, frontend loads
        *   Pipeline caches dependencies (verify build time improvement on second run)
        *   README displays CI/CD status badges (build, test, coverage)
        *   All pipeline stages complete successfully in <15 minutes
    *   **Dependencies:** `I5.T1` (Dockerfiles), `I5.T2` (Helm chart), `I3.T9` (E2E tests)
    *   **Parallelizable:** No (orchestrates all previous work)
```

### Context: deployment-staging (from docs/runbooks/deployment.md)

```markdown
## Staging Deployment

Staging deployment uses Kubernetes (AWS EKS) with Helm charts. The staging environment mirrors production but with reduced resources.

### Prerequisites
- AWS CLI configured: `aws configure`
- kubectl configured for staging cluster: `aws eks update-kubeconfig --region us-east-1 --name sovd-staging-cluster`
- Helm 3 installed
- Docker images pushed to ECR

### Step 1: Authenticate to AWS ECR

```bash
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.us-east-1.amazonaws.com
```

**Verification**: Login should succeed with "Login Succeeded" message.

### Step 2: Build and Push Docker Images

Build frontend and backend images:

```bash
# Backend
cd backend
docker build -t sovd-backend:${COMMIT_SHA} .
docker tag sovd-backend:${COMMIT_SHA} <ecr-repo>/sovd-backend:${COMMIT_SHA}
docker tag sovd-backend:${COMMIT_SHA} <ecr-repo>/sovd-backend:latest
docker push <ecr-repo>/sovd-backend:${COMMIT_SHA}
docker push <ecr-repo>/sovd-backend:latest

# Frontend
cd ../frontend
docker build -t sovd-frontend:${COMMIT_SHA} .
docker tag sovd-frontend:${COMMIT_SHA} <ecr-repo>/sovd-frontend:${COMMIT_SHA}
docker tag sovd-frontend:${COMMIT_SHA} <ecr-repo>/sovd-frontend:latest
docker push <ecr-repo>/sovd-frontend:${COMMIT_SHA}
docker push <ecr-repo>/sovd-frontend:latest
```

### Step 4: Deploy with Helm

Navigate to the Helm chart directory:

```bash
cd sovd-helm-chart
```

Deploy or upgrade the release:

```bash
helm upgrade --install sovd-webapp . \
  -f values-staging.yaml \
  -n staging \
  --set backend.image.tag=${COMMIT_SHA} \
  --set frontend.image.tag=${COMMIT_SHA} \
  --wait \
  --timeout 5m
```

### Step 6: Run Smoke Tests

Execute automated smoke tests:

```bash
# From project root
export API_BASE_URL=http://${ALB_URL}
pytest tests/smoke/ -v
```

**Verification**: All smoke tests should pass. If any fail, investigate before proceeding.
```

### Context: deployment-production (from docs/runbooks/deployment.md)

```markdown
## Production Deployment

Production deployment follows the same Helm-based process as staging but includes additional safeguards and a blue-green deployment strategy.

### Prerequisites
- All staging smoke tests passed
- Change ticket approved (for tracking)
- Rollback plan prepared
- On-call engineer available

### Step 3: Deploy with Gradual Rollout

Production uses a gradual rollout strategy (10% → 50% → 100%) with automatic rollback on errors.

```bash
cd sovd-helm-chart

# Deploy with gradual rollout
helm upgrade --install sovd-webapp . \
  -f values-production.yaml \
  -n production \
  --set backend.image.tag=${COMMIT_SHA} \
  --set frontend.image.tag=${COMMIT_SHA} \
  --set deployment.strategy.type=RollingUpdate \
  --set deployment.strategy.rollingUpdate.maxSurge=1 \
  --set deployment.strategy.rollingUpdate.maxUnavailable=0 \
  --wait \
  --timeout 10m
```

### Step 5: Post-Deployment Verification

Run production smoke tests:

```bash
export API_BASE_URL=https://sovd.yourdomain.com
pytest tests/smoke/ -v --production
```

**Verification**:
- Smoke tests pass
- Health endpoints return 200
- Login functionality works
- Command submission works
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `.github/workflows/ci-cd.yml`
    *   **Summary:** This file currently contains **ONLY** the first 5 stages of the CI/CD pipeline: frontend linting, frontend testing (with Lighthouse), backend linting, backend testing (with DB/Redis services), and security scanning (Bandit, pip-audit, npm audit). The file is INCOMPLETE - it is missing stages 6-9 (Build Images, Push Images, Deploy Staging, Deploy Production).
    *   **Recommendation:** You MUST extend this existing file by adding the missing stages. DO NOT replace the entire file - keep the existing jobs and add new ones. The existing jobs provide a good foundation for stages 1-5.
    *   **Current State:**
        - Has `frontend-lint`, `frontend-test`, `frontend-lighthouse`, `backend-lint`, `backend-test`, `backend-security`, `frontend-security` jobs
        - Has a `ci-success` job that aggregates all job results
        - Uses caching for npm and pip dependencies (already implemented)
        - Uses GitHub Services for PostgreSQL and Redis in backend tests
        - Triggers on push to `main`, `master`, `develop` branches and on PRs
    *   **What's Missing:**
        - No Docker image build job
        - No Docker image push job
        - No deployment jobs (staging/production)
        - No integration tests job (using docker-compose)
        - No E2E tests job (though E2E tests exist in tests/e2e/)
        - No smoke tests script reference
        - No Trivy security scanning for Docker images

*   **File:** `Makefile`
    *   **Summary:** This file contains useful targets for local development including `up`, `down`, `test`, `e2e`, `lint`. The `e2e` target is particularly important as it shows how to run E2E tests with docker-compose orchestration.
    *   **Recommendation:** You SHOULD reference the Makefile's `e2e` target logic when implementing the E2E job in CI/CD. The Makefile shows the correct pattern: start docker-compose, wait for services, run tests, stop services (even on failure).
    *   **Key Pattern from Makefile:**
        ```bash
        docker-compose up -d
        # Wait for services (health checks)
        # Run tests
        docker-compose down  # Always runs, even if tests fail
        ```
    *   **Integration Tests:** The current `test` target runs pytest with coverage but doesn't distinguish between unit and integration tests. Your CI/CD should run integration tests separately from unit tests.

*   **File:** `backend/Dockerfile.prod`
    *   **Summary:** Production-ready multi-stage Dockerfile for the backend. Uses Python 3.11-slim, installs dependencies in builder stage, creates minimal runtime image with non-root user (appuser, UID 1001), exposes port 8000, includes health check on `/health/ready`.
    *   **Recommendation:** You MUST use this file with `-f backend/Dockerfile.prod` when building backend production images in stage 6. The image name should follow the pattern `sovd-backend` and be tagged with both `${GITHUB_SHA}` and `latest`.
    *   **Build Context:** The build context should be the `backend/` directory. Build command should be: `docker build -f backend/Dockerfile.prod -t sovd-backend:${GITHUB_SHA} backend/`

*   **File:** `frontend/Dockerfile.prod`
    *   **Summary:** Production-ready multi-stage Dockerfile for the frontend. Uses Node 20-alpine builder + nginx:alpine runtime, builds React app with Vite, serves static files from `/usr/share/nginx/html`, exposes port 80, runs as nginx user (UID 101).
    *   **Recommendation:** You MUST use this file when building frontend production images. Note the special requirement: the nginx.conf file must be copied from `infrastructure/docker/nginx.conf` to `frontend/nginx.conf` BEFORE building (or handle this in the Dockerfile COPY command).
    *   **Build Context:** The frontend Dockerfile expects `nginx.conf` to be in the frontend directory. Your build step should handle this with:
        ```bash
        cp infrastructure/docker/nginx.conf frontend/nginx.conf
        docker build -f frontend/Dockerfile.prod -t sovd-frontend:${GITHUB_SHA} frontend/
        ```

*   **File:** `infrastructure/helm/sovd-webapp/values.yaml`
    *   **Summary:** Helm chart default values. Shows the image repository format: `YOUR_ECR_REGISTRY/sovd-backend` and `YOUR_ECR_REGISTRY/sovd-frontend`. The tag defaults to `latest` but should be overridden in production.
    *   **Recommendation:** Your deployment jobs MUST override the image tags using `--set backend.image.tag=${GITHUB_SHA}` and `--set frontend.image.tag=${GITHUB_SHA}` when deploying. This ensures deployments use the specific commit version, not `latest`.
    *   **Image Registry:** The values file shows `YOUR_ECR_REGISTRY` as a placeholder. In your CI/CD, you should use GitHub Container Registry (ghcr.io) since it's easier to set up than AWS ECR and doesn't require AWS credentials. Format: `ghcr.io/${{ github.repository_owner }}/sovd-backend:${GITHUB_SHA}`

*   **File:** `tests/e2e/`
    *   **Summary:** Directory contains Playwright E2E tests with three test suites: `auth.spec.ts`, `command_execution.spec.ts`, `vehicle_management.spec.ts`. Has `playwright.config.ts` for configuration.
    *   **Recommendation:** You MUST integrate these E2E tests into stage 4 of your CI/CD. The tests expect the full stack to be running (frontend + backend + DB + Redis). Use docker-compose to start services, then run `npx playwright test` from the `tests/e2e/` directory.
    *   **Configuration:** The playwright.config.ts likely points to `http://localhost:3000` for the frontend. Ensure your CI job starts docker-compose and waits for services before running tests.

*   **File:** `backend/tests/integration/` and `backend/tests/unit/`
    *   **Summary:** Backend tests are organized into unit and integration directories. Integration tests likely require database and Redis connections.
    *   **Recommendation:** Your CI/CD should run integration tests AFTER unit tests, in stage 3. The current `backend-test` job runs all tests together with DB/Redis services - you may want to split this into unit tests (stage 2, no services) and integration tests (stage 3, with services).
    *   **Coverage Threshold:** The current backend-test job uses `--cov-fail-under=80` which is correct. Keep this requirement.

### Implementation Tips & Notes

*   **Tip - Container Registry Choice:** Use GitHub Container Registry (ghcr.io) instead of AWS ECR for simplicity. GitHub Actions has built-in authentication to ghcr.io via `GITHUB_TOKEN`, so no additional secrets are needed. Image naming format:
    ```yaml
    ghcr.io/${{ github.repository_owner }}/sovd-backend:${{ github.sha }}
    ghcr.io/${{ github.repository_owner }}/sovd-frontend:${{ github.sha }}
    ```

*   **Tip - Docker Build and Push Pattern:** Use the official `docker/build-push-action@v5` action for building and pushing images. It handles multi-platform builds, caching, and pushing efficiently:
    ```yaml
    - name: Build and push backend image
      uses: docker/build-push-action@v5
      with:
        context: backend
        file: backend/Dockerfile.prod
        push: true
        tags: |
          ghcr.io/${{ github.repository_owner }}/sovd-backend:${{ github.sha }}
          ghcr.io/${{ github.repository_owner }}/sovd-backend:latest
        cache-from: type=gha
        cache-to: type=gha,mode=max
    ```

*   **Tip - Docker Registry Login:** Before building/pushing, you MUST log in to ghcr.io using:
    ```yaml
    - name: Log in to GitHub Container Registry
      uses: docker/login-action@v3
      with:
        registry: ghcr.io
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
    ```

*   **Tip - Integration Tests with docker-compose:** For stage 3, you need to start docker-compose, run integration tests, then stop docker-compose. Use this pattern:
    ```yaml
    - name: Start services with docker-compose
      run: docker-compose up -d

    - name: Wait for services to be healthy
      run: |
        timeout 60 bash -c 'until docker-compose ps | grep healthy; do sleep 2; done'

    - name: Run integration tests
      run: |
        cd backend
        pytest tests/integration/ -v

    - name: Stop services
      if: always()  # Always run, even if tests fail
      run: docker-compose down
    ```

*   **Tip - E2E Tests:** Stage 4 should use the same docker-compose pattern but run Playwright tests from `tests/e2e/`:
    ```yaml
    - name: Run E2E tests
      run: |
        cd tests/e2e
        npx playwright test

    - name: Upload Playwright screenshots on failure
      uses: actions/upload-artifact@v3
      if: failure()
      with:
        name: playwright-screenshots
        path: tests/e2e/test-results/
    ```

*   **Tip - Trivy Security Scanning:** Add Trivy scanning in stage 5 to scan the built Docker images for vulnerabilities:
    ```yaml
    - name: Run Trivy vulnerability scanner on backend image
      uses: aquasecurity/trivy-action@master
      with:
        image-ref: ghcr.io/${{ github.repository_owner }}/sovd-backend:${{ github.sha }}
        format: 'sarif'
        output: 'trivy-backend-results.sarif'

    - name: Upload Trivy results to GitHub Security tab
      uses: github/codeql-action/upload-sarif@v2
      if: always()
      with:
        sarif_file: 'trivy-backend-results.sarif'
    ```

*   **Note - Smoke Tests Script:** You MUST create `scripts/smoke_tests.sh` that tests critical endpoints after deployment. The script should:
    - Accept an API_BASE_URL environment variable (e.g., staging or production URL)
    - Test `/health/ready` endpoint (should return 200 with healthy status)
    - Test `/api/v1/vehicles` endpoint (should return 200, requires authentication or public access)
    - Test frontend loads (curl the base URL, check for 200)
    - Exit with code 0 if all tests pass, non-zero if any fail
    - Example structure:
        ```bash
        #!/bin/bash
        set -e
        API_BASE_URL=${API_BASE_URL:-http://localhost:8000}

        echo "Testing health endpoint..."
        curl -f ${API_BASE_URL}/health/ready || exit 1

        echo "Testing API documentation..."
        curl -f ${API_BASE_URL}/docs || exit 1

        echo "All smoke tests passed!"
        ```

*   **Tip - Deployment Jobs:** Stage 8 (staging) and stage 9 (production) should be separate jobs that:
    - Run AFTER all build/test/scan jobs succeed (use `needs: [build-images, ...]`)
    - Use conditional execution: staging runs on `github.ref == 'refs/heads/develop'`, production runs on `github.ref == 'refs/heads/main'`
    - Production should use `environment: production` to enable manual approval gate in GitHub settings
    - Both should install kubectl and helm, configure kubeconfig (for now, can be mocked/skipped since we don't have real clusters)
    - Run helm upgrade with appropriate values file
    - Run smoke tests after deployment
    - For production, include rollback logic if smoke tests fail

*   **Tip - GitHub Environment Setup (for Manual Approval):** The production deployment job requires a GitHub environment named `production` with protection rules. This is configured in GitHub repository settings (Settings → Environments → New environment → "production" → Add required reviewers). In your workflow, reference it with:
    ```yaml
    deploy-production:
      environment: production  # This triggers the approval gate
    ```

*   **Note - Caching:** The current workflow already implements caching for npm (Node.js) and pip (Python). When you add docker builds, also add Docker layer caching using `cache-from: type=gha` and `cache-to: type=gha,mode=max` in the `docker/build-push-action` step.

*   **Tip - README Badges:** Add GitHub Actions badges to README.md at the top of the file:
    ```markdown
    # Cloud-to-Vehicle SOVD Command WebApp

    ![CI/CD Pipeline](https://github.com/{owner}/{repo}/actions/workflows/ci-cd.yml/badge.svg)
    ![Backend Coverage](https://img.shields.io/badge/backend%20coverage-80%25-brightgreen)
    ![Frontend Coverage](https://img.shields.io/badge/frontend%20coverage-80%25-brightgreen)

    ## Project Overview
    ...
    ```
    Replace `{owner}/{repo}` with actual repository details or use `${{ github.repository }}` pattern.

*   **Warning - Kubernetes Deployment Limitation:** Since this is likely a development/demo environment without real AWS EKS clusters, the deployment stages (8 and 9) may need to be **mocked or skipped initially**. You can:
    1. Create the deployment job structure but comment out the actual kubectl/helm commands
    2. Add a TODO comment explaining that real deployments require EKS cluster setup and AWS credentials
    3. Keep the smoke tests section functional for when real infrastructure is available
    4. Alternative: Use a local Kubernetes cluster (minikube or kind) in CI for testing deployments

*   **Tip - Job Dependencies and Ordering:** Structure your jobs with `needs` to enforce correct ordering:
    ```yaml
    jobs:
      # Stage 1: Linting (parallel)
      backend-lint: ...
      frontend-lint: ...

      # Stage 2: Unit tests (parallel, depend on lint)
      backend-test:
        needs: [backend-lint]
      frontend-test:
        needs: [frontend-lint]

      # Stage 3: Integration tests (depend on unit tests)
      integration-tests:
        needs: [backend-test, frontend-test]

      # Stage 4: E2E tests (depend on integration)
      e2e-tests:
        needs: [integration-tests]

      # Stage 5: Security scans (parallel, can run after unit tests)
      security-backend:
        needs: [backend-test]
      security-frontend:
        needs: [frontend-test]

      # Stage 6: Build images (depend on all tests passing)
      build-images:
        needs: [backend-test, frontend-test, integration-tests, e2e-tests]

      # Stage 7: Scan images (depends on build)
      trivy-scan:
        needs: [build-images]

      # Stage 8: Deploy staging (depends on all previous stages)
      deploy-staging:
        needs: [build-images, trivy-scan]
        if: github.ref == 'refs/heads/develop'

      # Stage 9: Deploy production (depends on all previous stages)
      deploy-production:
        needs: [build-images, trivy-scan]
        if: github.ref == 'refs/heads/main'
        environment: production
    ```

*   **Tip - Workflow Optimization for 15min Limit:** To keep the pipeline under 15 minutes:
    - Use aggressive caching (npm, pip, docker layers)
    - Run linting and unit tests in parallel
    - Run security scans in parallel with other stages when possible
    - Use `--parallel` flags for test runners where supported
    - Limit Playwright E2E tests to critical paths (not every single test if it's slow)
    - Use `docker/build-push-action` with layer caching instead of plain docker build commands

*   **Note - Integration vs Unit Tests:** The current `backend-test` job runs ALL backend tests (unit + integration) together. For better organization and faster feedback, consider:
    - Splitting into `backend-unit-test` (stage 2, no services, fast) using `pytest tests/unit/`
    - And `backend-integration-test` (stage 3, with services) using `pytest tests/integration/`
    - However, since the current job already uses GitHub Services for DB/Redis, it's acceptable to keep it as-is for simplicity. Just ensure it's placed in the right stage.

*   **Tip - Helm Installation in CI:** For deployment jobs, install Helm using the official action:
    ```yaml
    - name: Install Helm
      uses: azure/setup-helm@v3
      with:
        version: '3.13.0'
    ```

*   **Tip - Kubeconfig Setup (when ready):** For real deployments, configure kubectl with:
    ```yaml
    - name: Configure kubectl
      run: |
        mkdir -p $HOME/.kube
        echo "${{ secrets.KUBECONFIG_STAGING }}" | base64 -d > $HOME/.kube/config
        kubectl config current-context
    ```
    (Requires KUBECONFIG_STAGING secret in GitHub repository)

### Workflow Structure Summary

Based on the architecture blueprint and existing code, your complete CI/CD workflow should have these jobs:

1. **frontend-lint** (existing) - Keep as-is
2. **frontend-test** (existing) - Keep as-is
3. **frontend-lighthouse** (existing) - Keep as-is
4. **backend-lint** (existing) - Keep as-is
5. **backend-test** (existing) - Keep as-is, but consider renaming to backend-unit-test
6. **backend-security** (existing) - Keep as-is
7. **frontend-security** (existing) - Keep as-is
8. **integration-tests** (NEW) - Add this for stage 3
9. **e2e-tests** (NEW) - Add this for stage 4
10. **build-backend-image** (NEW) - Add this for stage 6
11. **build-frontend-image** (NEW) - Add this for stage 6
12. **trivy-scan-backend** (NEW) - Add this for stage 5 (after build)
13. **trivy-scan-frontend** (NEW) - Add this for stage 5 (after build)
14. **deploy-staging** (NEW) - Add this for stage 8
15. **deploy-production** (NEW) - Add this for stage 9
16. **ci-success** (existing) - Update to include all new jobs in the needs list

Total: ~15-16 jobs organized into 9 stages as specified in the architecture blueprint.
