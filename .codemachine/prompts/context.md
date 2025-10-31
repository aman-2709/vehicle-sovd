# Task Briefing Package

This package contains all necessary information and strategic guidance for the Coder Agent.

---

## 1. Current Task Details

This is the full specification of the task you must complete.

```json
{
  "task_id": "I4.T9",
  "iteration_id": "I4",
  "iteration_goal": "Production Readiness - Command History, Monitoring & Refinements",
  "description": "Optimize frontend performance and reduce bundle size. Implement: 1) Code splitting for routes (use React.lazy() for page components in `App.tsx`), 2) Image optimization (if images added, use appropriate formats and compression), 3) Analyze bundle size using `vite-plugin-bundle-analyzer`, identify large dependencies, 4) Tree-shake unused MUI components (import specific components instead of entire library), 5) Configure Vite build optimizations in `vite.config.ts` (minification, compression), 6) Add compression middleware to Nginx configuration (gzip for static files), 7) Implement service worker for caching static assets (optional, using Vite PWA plugin), 8) Measure and document performance metrics: First Contentful Paint (FCP), Time to Interactive (TTI), bundle size. Configure Lighthouse CI in GitHub Actions to track performance scores. Document performance benchmarks in README.",
  "agent_type_hint": "FrontendAgent",
  "inputs": "Architecture Blueprint Section 2.2 (NFRs - Performance - Frontend Load Time).",
  "target_files": [
    "frontend/vite.config.ts",
    "frontend/src/App.tsx",
    "infrastructure/docker/nginx.conf",
    "frontend/package.json",
    ".github/workflows/ci-cd.yml",
    "README.md"
  ],
  "input_files": [
    "frontend/vite.config.ts",
    "frontend/src/App.tsx"
  ],
  "deliverables": "Optimized frontend bundle with code splitting; bundle analyzer integration; Nginx compression; performance metrics documentation; Lighthouse CI.",
  "acceptance_criteria": "`npm run build` generates production bundle with code splitting (multiple chunk files in `dist/assets/`); Bundle size for main chunk <500 KB (verify with bundle analyzer report); Total bundle size <2 MB; FCP <1.5 seconds on standard broadband (measure with Lighthouse); TTI <3 seconds (requirement met); Lighthouse performance score >90 (verify in CI); Nginx serves static files with gzip compression (verify response headers); Code splitting reduces initial load time (verify in network tab); README includes performance metrics and optimization strategies; Lighthouse CI job added to GitHub Actions (runs on every commit)",
  "dependencies": ["I3.T4"],
  "parallelizable": true,
  "done": false
}
```

---

## 2. Architectural & Planning Context

The following are the relevant sections from the architecture and plan documents, which I found by analyzing the task description.

### Context: nfr-performance (from 01_Context_and_Drivers.md)

```markdown
#### Performance
- **Response Time**: 95th percentile round-trip time < 2 seconds for standard commands
- **Throughput**: Support 100 concurrent users executing commands
- **Database Performance**: Query response time < 100ms for 95% of operations
- **Frontend Load Time**: Initial page load < 3 seconds on standard broadband

**Architectural Impact**: Requires stateless, horizontally scalable services, efficient database indexing, and optimized frontend bundle size.
```

### Context: performance-optimization (from 05_Operational_Architecture.md)

```markdown
**Performance Optimization Techniques**

**Backend Optimizations:**
- **Async I/O**: FastAPI async endpoints; asyncio for concurrent operations
- **Database Query Optimization**: Indexed queries; eager loading for relationships; EXPLAIN ANALYZE
- **Caching**:
  - Vehicle status cached in Redis (TTL=30s)
  - Recent command responses cached (TTL=5min)
  - Cache invalidation on status change
- **Connection Pooling**: Reuse database and gRPC connections

**Frontend Optimizations:**
- **Code Splitting**: React lazy loading for routes; Vite automatic chunking
- **Bundle Optimization**: Tree-shaking; minification; gzip compression
- **API Caching**: React Query caches GET requests; stale-while-revalidate
- **Pagination**: Vehicle list and command history paginated (limit=20)
- **Debouncing**: Search inputs debounced (300ms) to reduce API calls

**Network Optimizations:**
- **HTTP/2**: Multiplexing reduces connection overhead
- **gRPC**: Efficient binary protocol for vehicle communication
- **CDN**: Frontend static assets served from CloudFront (AWS CDN)
- **Compression**: Gzip for HTTP responses; protobuf for gRPC

**Monitoring Performance:**
- Target: 95th percentile response time < 2 seconds
- Alerting if p95 > 3 seconds
- Regular load testing (k6 or Locust) to identify bottlenecks
```

### Context: task-i4-t9 (from 02_Iteration_I4.md)

```markdown
*   **Task 4.9: Performance Optimization and Bundle Analysis**
    *   **Task ID:** `I4.T9`
    *   **Description:** Optimize frontend performance and reduce bundle size. Implement: 1) Code splitting for routes (use React.lazy() for page components in `App.tsx`), 2) Image optimization (if images added, use appropriate formats and compression), 3) Analyze bundle size using `vite-plugin-bundle-analyzer`, identify large dependencies, 4) Tree-shake unused MUI components (import specific components instead of entire library), 5) Configure Vite build optimizations in `vite.config.ts` (minification, compression), 6) Add compression middleware to Nginx configuration (gzip for static files), 7) Implement service worker for caching static assets (optional, using Vite PWA plugin), 8) Measure and document performance metrics: First Contentful Paint (FCP), Time to Interactive (TTI), bundle size. Configure Lighthouse CI in GitHub Actions to track performance scores. Document performance benchmarks in README.
    *   **Agent Type Hint:** `FrontendAgent`
    *   **Inputs:** Architecture Blueprint Section 2.2 (NFRs - Performance - Frontend Load Time).
    *   **Input Files:** [`frontend/vite.config.ts`, `frontend/src/App.tsx`]
    *   **Target Files:**
        *   Updates to `frontend/vite.config.ts` (add bundle analyzer, optimizations)
        *   Updates to `frontend/src/App.tsx` (implement code splitting)
        *   Updates to `infrastructure/docker/nginx.conf` (add compression)
        *   Updates to `frontend/package.json` (add bundle analyzer dependency)
        *   Updates to `.github/workflows/ci-cd.yml` (add Lighthouse CI step)
        *   Updates to `README.md` (document performance metrics)
    *   **Deliverables:** Optimized frontend bundle with code splitting; bundle analyzer integration; Nginx compression; performance metrics documentation; Lighthouse CI.
    *   **Acceptance Criteria:**
        *   `npm run build` generates production bundle with code splitting (multiple chunk files in `dist/assets/`)
        *   Bundle size for main chunk <500 KB (verify with bundle analyzer report)
        *   Total bundle size <2 MB
        *   FCP <1.5 seconds on standard broadband (measure with Lighthouse)
        *   TTI <3 seconds (requirement met)
        *   Lighthouse performance score >90 (verify in CI)
        *   Nginx serves static files with gzip compression (verify response headers)
        *   Code splitting reduces initial load time (verify in network tab)
        *   README includes performance metrics and optimization strategies
        *   Lighthouse CI job added to GitHub Actions (runs on every commit)
    *   **Dependencies:** `I3` (frontend implementation)
    *   **Parallelizable:** Yes (optimization task)
```

---

## 3. Codebase Analysis & Strategic Guidance

The following analysis is based on my direct review of the current codebase. Use these notes and tips to guide your implementation.

### Relevant Existing Code

*   **File:** `frontend/vite.config.ts`
    *   **Summary:** Current Vite configuration is minimal with only basic React plugin and test configuration. It does NOT have any build optimization settings, bundle analysis, or compression configured.
    *   **Recommendation:** You MUST extend this file to add:
        - `rollup-plugin-visualizer` (bundle analyzer) - note: use the rollup version, not vite-plugin-visualizer
        - Build optimization settings in a `build: {}` section
        - Consider adding `vite-plugin-compression` for build-time gzip generation
    *   **Current State:** The config only has `plugins: [react()]`, `server`, `preview`, and `test` sections. The production build settings are using all Vite defaults.

*   **File:** `frontend/src/App.tsx`
    *   **Summary:** This is the main routing component. All page components are currently imported synchronously at the top: `LoginPage`, `DashboardPage`, `VehiclesPage`, `CommandPage`, `HistoryPage`, `CommandDetailPage`, and `Layout` component.
    *   **Recommendation:** You MUST convert all page imports to use `React.lazy()` for code splitting. The pattern should be:
        ```typescript
        const DashboardPage = React.lazy(() => import('./pages/DashboardPage'));
        ```
        Then wrap routes with `<Suspense fallback={<LoadingSpinner />}>` component.
    *   **Important Note:** The `Layout`, `ProtectedRoute`, and `LoginPage` components can remain synchronously imported as they're needed immediately on app initialization. Focus lazy loading on the protected route pages (DashboardPage, VehiclesPage, CommandPage, HistoryPage, CommandDetailPage).

*   **File:** `frontend/package.json`
    *   **Summary:** Contains all frontend dependencies. Currently has React 18, MUI 5.14, React Router 6.20, Tanstack Query 5.8, Axios 1.6, and various dev dependencies.
    *   **Recommendation:** You MUST add these dev dependencies:
        - `rollup-plugin-visualizer` (for bundle analysis)
        - `vite-plugin-compression` (optional, for gzip)
        - `@lhci/cli` (for Lighthouse CI)
        - Consider adding a new script: `"analyze": "vite build && open stats.html"`
    *   **Analysis:** The current dependencies are reasonable. MUI is known to be large, so ensure you're importing components specifically (which the codebase already seems to do based on the component files I surveyed).

*   **File:** `.github/workflows/ci-cd.yml`
    *   **Summary:** Existing CI/CD pipeline has frontend-lint, frontend-test, backend-lint, backend-test jobs. It uses Node 18, runs on ubuntu-latest, and includes coverage checks with 80% threshold.
    *   **Recommendation:** You MUST add a new job called `frontend-lighthouse` that:
        - Depends on the `frontend-test` job
        - Builds the production frontend bundle
        - Runs Lighthouse CI using `@lhci/cli`
        - Sets performance budget thresholds (score >90, FCP <1.5s, TTI <3s)
        - Uploads results as artifacts
    *   **Integration Point:** Add after the `frontend-test` job and before `ci-success`. Update the `ci-success` needs array to include the new lighthouse job.

*   **File:** `infrastructure/docker/nginx.conf`
    *   **Summary:** This file does NOT currently exist in the infrastructure/docker directory. You will need to CREATE it from scratch.
    *   **Recommendation:** You MUST create a production-ready Nginx configuration file that:
        - Enables gzip compression for static assets (JS, CSS, HTML, JSON, SVG)
        - Sets appropriate cache headers for static files (max-age for JS/CSS with hashes)
        - Serves the React SPA from `/usr/share/nginx/html`
        - Handles client-side routing (all routes return index.html via try_files)
        - Includes security headers (you can keep it basic for this task)
    *   **Location:** Create at `infrastructure/docker/nginx.conf` (this will be used by a production Dockerfile in the future)

*   **File:** `frontend/src/main.tsx`
    *   **Summary:** Entry point sets up React with BrowserRouter, ThemeProvider, QueryClient, AuthProvider, ErrorProvider. The React.StrictMode is enabled.
    *   **Recommendation:** No changes needed to this file. The Suspense boundaries will be added in App.tsx around the routes.

*   **File:** `README.md`
    *   **Summary:** Current README has project overview, tech stack, quick start, and service descriptions. It does NOT have a performance metrics or optimization section.
    *   **Recommendation:** You MUST add a new section called "## Performance Metrics" (after the Docker Services section) that documents:
        - Target performance benchmarks (FCP, TTI, bundle size)
        - Current measured performance (after optimization)
        - Optimization strategies implemented
        - How to run performance tests locally (using Lighthouse in Chrome DevTools)
        - Link to Lighthouse CI reports in GitHub Actions

### Implementation Tips & Notes

*   **Tip:** When implementing React.lazy(), you MUST wrap the Routes with a Suspense boundary. The LoadingSpinner component already exists at `frontend/src/components/common/LoadingSpinner.tsx` - reuse it as the fallback.

*   **Tip:** For Vite bundle optimization, the key settings to configure in vite.config.ts are:
    ```typescript
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            'vendor': ['react', 'react-dom', 'react-router-dom'],
            'mui': ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
            'query': ['@tanstack/react-query'],
          }
        }
      },
      chunkSizeWarningLimit: 1000, // Increased to 1MB
      minify: 'terser', // Use terser for better minification
      sourcemap: false, // Disable sourcemaps in production
    }
    ```

*   **Note:** The project uses Vite 5.0, which has excellent default tree-shaking. The codebase already imports MUI components specifically (e.g., `import Button from '@mui/material/Button'`), so you don't need to change import patterns across the codebase.

*   **Note:** For Lighthouse CI, you'll need to create a `.lighthouserc.js` configuration file at the project root with performance budgets. Example configuration:
    ```javascript
    module.exports = {
      ci: {
        collect: {
          staticDistDir: './frontend/dist',
        },
        assert: {
          preset: 'lighthouse:recommended',
          assertions: {
            'categories:performance': ['error', { minScore: 0.9 }],
            'first-contentful-paint': ['error', { maxNumericValue: 1500 }],
            'interactive': ['error', { maxNumericValue: 3000 }],
          },
        },
      },
    };
    ```

*   **Warning:** The current frontend Dockerfile is a development Dockerfile only (uses Vite dev server). The nginx.conf you create will be used in a future production Dockerfile task (I5.T1). For now, just create the config file - it won't be used in docker-compose yet.

*   **Tip:** When adding the bundle analyzer, configure it to generate an HTML report in `frontend/stats.html` so developers can visualize the bundle locally. Add `stats.html` to `.gitignore`.

*   **Performance Target Summary:**
    - Main chunk: <500 KB
    - Total bundle: <2 MB
    - FCP: <1.5 seconds
    - TTI: <3 seconds
    - Lighthouse score: >90

*   **Testing Your Changes:**
    1. Run `npm run build` in frontend directory
    2. Check dist/assets/ for multiple chunk files (evidence of code splitting)
    3. Open stats.html in browser to analyze bundle composition
    4. Use `npx serve dist` to test production build locally
    5. Run Lighthouse audit in Chrome DevTools on the production build
    6. Verify gzip headers would be present with Nginx (you can test this later when production Dockerfile is created)

### Project Conventions

*   **Code Style:** The project uses ESLint and Prettier. All TypeScript code follows strict typing (`"strict": true` in tsconfig.json).

*   **File Naming:** React components use PascalCase (e.g., `DashboardPage.tsx`), utilities use camelCase (e.g., `errorMessages.ts`).

*   **Import Organization:** The codebase follows a pattern of external imports first, then internal imports organized by feature.

*   **Documentation:** All configuration files have detailed comments explaining each setting. Maintain this pattern when updating vite.config.ts.

*   **Git Workflow:** The project uses develop and main branches. This task should be implemented on a feature branch.

### Additional Context from Codebase Survey

*   **Available Components:** I confirmed that `LoadingSpinner` exists at `frontend/src/components/common/LoadingSpinner.tsx`. You can import it with: `import LoadingSpinner from './components/common/LoadingSpinner';`

*   **Current Build Setup:** The frontend uses Vite 5.0 with the React plugin. The build command is `vite build` (via `npm run build`). Output goes to `frontend/dist/`.

*   **Existing Optimizations:** The codebase already uses React Query for API caching, which is good. The error handling and offline detection were implemented in I4.T8, so the UX is already improved.

*   **Infrastructure Directory:** The `infrastructure/docker/` directory exists with `prometheus.yml` and a `grafana/` folder. You'll be adding `nginx.conf` alongside these files.

*   **CI/CD Integration:** The existing workflow uses `actions/checkout@v3`, `actions/setup-node@v3` with Node 18, and caches npm dependencies. Follow this same pattern for the Lighthouse job.
