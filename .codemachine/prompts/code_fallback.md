# Code Refinement Task

The previous code submission did not pass verification. You must fix the following issues and resubmit your work.

---

## Original Task Description

{
  "task_id": "I5.T1",
  "iteration_id": "I5",
  "iteration_goal": "Production Deployment Infrastructure - Kubernetes, CI/CD & gRPC Foundation",
  "description": "Create optimized production Dockerfiles for frontend and backend with multi-stage builds. Backend: build stage (install deps) + runtime stage (copy app, non-root user). Frontend: build stage (npm build) + runtime stage (Nginx Alpine, static files). Create Nginx config for frontend with gzip, security headers, API reverse proxy. Create .dockerignore files.",
  "agent_type_hint": "BackendAgent",
  "inputs": "Architecture Blueprint Section 3.9; Docker best practices.",
  "target_files": [
    "backend/Dockerfile.prod",
    "backend/.dockerignore",
    "frontend/Dockerfile.prod",
    "frontend/.dockerignore",
    "infrastructure/docker/nginx.conf"
  ],
  "input_files": [
    "backend/requirements.txt",
    "frontend/package.json"
  ],
  "deliverables": "Production Dockerfiles; Nginx config; .dockerignore files; tested images.",
  "acceptance_criteria": "Backend build succeeds, image <500MB, runs as non-root; Frontend build succeeds, image <50MB, serves at :80; Nginx has gzip+security headers+API proxy; .dockerignore excludes tests/node_modules; No build errors",
  "dependencies": ["I4.T1"],
  "parallelizable": true,
  "done": false
}

---

## Issues Detected

* **Build Failure:** `frontend/Dockerfile.prod` assumes the build context is the repository root (`COPY frontend/...` and `COPY infrastructure/...`), so running the documented command `cd frontend && docker build -f Dockerfile.prod ... .` fails with "not found" errors for both the application sources and `infrastructure/docker/nginx.conf`. This violates the acceptance criteria that the frontend build must succeed with no errors.
* **User Privileges:** The runtime stage of `frontend/Dockerfile.prod` never switches to the `nginx` user. The container therefore runs as root, conflicting with the task requirement to run production images as non-root.

---

## Best Approach to Fix

Update `frontend/Dockerfile.prod` so it works when the build context is the `frontend/` directory: remove the `frontend/` path prefix from `COPY` directives, add a `COPY ../infrastructure/docker/nginx.conf ...` style solution by passing the config in via a build ARG or by building from the repo root while still honoring a `.dockerignore` (for example, move a suitable `.dockerignore` to the root of the chosen context). After restructuring the copy steps, ensure the final stage switches to `USER nginx` so the container runs as a non-root user. Rebuild the image locally (`cd frontend && docker build -f Dockerfile.prod ...`) to confirm the fixes.
