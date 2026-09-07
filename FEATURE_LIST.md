# AlgoVision Feature List (Observable)

> Single source of truth for every feature across backend and frontend.
> Use this to track progress, plan sprints, and observe completion.
>
> **Update rule:** when a feature is implemented and merged, mark its
> status `✅ Done` and link the PR. When in progress, mark `🚧 In
> Progress` and link the branch.

---

## 0. Status Legend

``` text
⬜ Not Started       — feature not yet begun
🚧 In Progress      — branch open, work in progress
🔍 In Review        — PR open, awaiting review/CI
✅ Done             — merged to develop, all acceptance criteria met
⛔ Blocked          — dependency missing; see "blocked by"
🗑️ Deferred         — postponed to later phase (with reason)
```

---

## 1. Progress Overview

### 1.1 Backend Phases

| Phase | Title                       | Features | Status | % Done |
|-------|-----------------------------|----------|--------|--------|
| B1    | Foundation                  | 12       | ⬜     | 0%     |
| B2    | Auth & Users                | 12       | ⬜     | 0%     |
| B3    | Catalog                     | 16       | ⬜     | 0%     |
| B4    | Problems                    | 12       | ⬜     | 0%     |
| B5    | Progress & Dashboard        | 18       | ⬜     | 0%     |
| B6    | Hardening                   | 14       | ⬜     | 0%     |
| **Total** |                          | **84**   |        | **0%** |

### 1.2 Frontend Phases

| Phase | Title                       | Features | Status | % Done |
|-------|-----------------------------|----------|--------|--------|
| F1    | Foundation                  | 14       | ⬜     | 0%     |
| F2    | Engine Core                 | 22       | ⬜     | 0%     |
| F3    | Search & Trees              | 14       | ⬜     | 0%     |
| F4    | Graphs                      | 12       | ⬜     | 0%     |
| F5    | Auth & Server State         | 12       | ⬜     | 0%     |
| F6    | Problems & Dashboard        | 16       | ⬜     | 0%     |
| F7    | Polish                      | 12       | ⬜     | 0%     |
| **Total** |                          | **102**  |        | **0%** |

### 1.3 Grand Total

``` text
Backend:    84 features
Frontend:  102 features
─────────────────────────
Total:     186 features
```

---

## 2. Backend Feature List

### B1 — Foundation

| ID    | Feature                                          | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------|--------|--------------|-------|
| B1.1  | Python project scaffold (pyproject.toml, src/)   | ⬜     |              |       |
| B1.2  | Pydantic Settings + .env.example                 | ⬜     |              |       |
| B1.3  | Structured logging (structlog JSON)              | ⬜     |              |       |
| B1.4  | Central exception handler + error envelope       | ⬜     |              |       |
| B1.5  | PostgreSQL + asyncpg + SQLAlchemy 2 async engine | ⬜     |              |       |
| B1.6  | Alembic initialized, base migration             | ⬜     |              |       |
| B1.7  | users table migration                            | ⬜     |              |       |
| B1.8  | /health endpoint (liveness, no DB)               | ⬜     |              |       |
| B1.9  | /health/ready endpoint (checks DB)               | ⬜     |              |       |
| B1.10 | docker-compose (api + db)                       | ⬜     |              |       |
| B1.11 | GitHub Actions CI (lint, typecheck, test, migrate)| ⬜    |              |       |
| B1.12 | Request ID middleware + X-Request-ID header     | ⬜     |              |       |

**B1 acceptance:** `docker-compose up` starts API + DB; `GET /health`
returns 200; CI passes on first push.

---

### B2 — Auth & Users

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| B2.1  | User SQLAlchemy model                                  | ⬜     |              |       |
| B2.2  | Email unique index (case-insensitive)                  | ⬜     |              |       |
| B2.3  | Argon2id password hashing utility                      | ⬜     |              |       |
| B2.4  | JWT access + refresh token issuance                     | ⬜     |              |       |
| B2.5  | HTTP-only Secure cookie auth dependency                | ⬜     |              |       |
| B2.6  | POST /auth/register endpoint                           | ⬜     |              |       |
| B2.7  | POST /auth/login endpoint                              | ⬜     |              |       |
| B2.8  | POST /auth/logout endpoint                             | ⬜     |              |       |
| B2.9  | GET  /auth/me endpoint                                 | ⬜     |              |       |
| B2.10 | POST /auth/refresh endpoint (single-use rotation)      | ⬜     |              |       |
| B2.11 | Rate limit on /auth/register, /auth/login (slowapi)    | ⬜     |              |       |
| B2.12 | Account lock after 5 failed logins (15 min)            | ⬜     |              |       |

**B2 acceptance:** User can register, log in, log out; cookie-based
session; refresh rotates; 6th failed login returns 423 within 15 min.

---

### B3 — Catalog

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| B3.1  | algorithm_categories model + migration                 | ⬜     |              |       |
| B3.2  | topics model + migration                               | ⬜     |              |       |
| B3.3  | algorithms model + indexes + migration                | ⬜     |              |       |
| B3.4  | algorithm_code_versions model (versioned) + migration  | ⬜     |              |       |
| B3.5  | algorithm_topics M:N + migration                       | ⬜     |              |       |
| B3.6  | data_structures model + migration                      | ⬜     |              |       |
| B3.7  | data_structure_operations model + migration            | ⬜     |              |       |
| B3.8  | AlgorithmRepository (get_by_slug, list, list_categories)| ⬜    |              |       |
| B3.9  | DataStructureRepository                                | ⬜     |              |       |
| B3.10 | AlgorithmService + DataStructureService                | ⬜     |              |       |
| B3.11 | Pydantic schemas + typed Filters                       | ⬜     |              |       |
| B3.12 | GET /algorithms (filters + pagination)                 | ⬜     |              |       |
| B3.13 | GET /algorithms/{slug} (with code + complexity)        | ⬜     |              |       |
| B3.14 | GET /algorithms/categories                            | ⬜     |              |       |
| B3.15 | GET /data-structures + /data-structures/{slug}         | ⬜     |              |       |
| B3.16 | Seed script (categories, topics, algorithms, code)     | ⬜     |              |       |

**B3 acceptance:** Browse `/algorithms` (40+ items), filter by
category/difficulty, view detail with source code; ETag returns 304 on
repeat fetch.

---

### B4 — Problems

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| B4.1  | problems model + indexes + migration                   | ⬜     |              |       |
| B4.2  | companies model + migration                            | ⬜     |              |       |
| B4.3  | problem_companies M:N + migration                      | ⬜     |              |       |
| B4.4  | problem_topics M:N + migration                         | ⬜     |              |       |
| B4.5  | ProblemRepository (filters: difficulty, topic, company, status) | ⬜ |       |       |
| B4.6  | ProblemService                                         | ⬜     |              |       |
| B4.7  | Pydantic schemas + typed Filters                       | ⬜     |              |       |
| B4.8  | GET /problems (with all filters)                       | ⬜     |              |       |
| B4.9  | GET /problems/{slug} (with description + linked algo)  | ⬜     |              |       |
| B4.10 | GET /problems/{slug}/topics                            | ⬜     |              |       |
| B4.11 | GET /problems/{slug}/companies                         | ⬜     |              |       |
| B4.12 | Seed script (~50 problems, 10 companies, M:N)          | ⬜     |              |       |

**B4 acceptance:** Browse `/problems` (50+ items), filter by all four
facets, view detail with related algorithm link.

---

### B5 — Progress & Dashboard

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| B5.1  | user_algorithm_progress model + indexes + migration    | ⬜     |              |       |
| B5.2  | user_problem_progress model + indexes + migration      | ⬜     |              |       |
| B5.3  | user_recent_items model + index (user_id, viewed_at)   | ⬜     |              |       |
| B5.4  | UserAlgorithmProgressRepository                       | ⬜     |              |       |
| B5.5  | UserProblemProgressRepository                         | ⬜     |              |       |
| B5.6  | UserRecentItemsRepository                              | ⬜     |              |       |
| B5.7  | ProgressService (mark_*, get_overview, list_*, record_view) | ⬜ |              |       |
| B5.8  | Event dispatcher (ItemViewedEvent)                    | ⬜     |              |       |
| B5.9  | Progress endpoints (POST /progress/algorithms/{id}, POST /progress/problems/{id}) | ⬜ | |       |
| B5.10 | GET /progress (overview counts)                        | ⬜     |              |       |
| B5.11 | GET /progress/algorithms (paginated list)              | ⬜     |              |       |
| B5.12 | GET /progress/problems (paginated list)                | ⬜     |              |       |
| B5.13 | ReadinessCalculator (with Protocol)                    | ⬜     |              |       |
| B5.14 | SkillMapper (with Protocol)                            | ⬜     |              |       |
| B5.15 | FocusAreaSelector (with Protocol)                      | ⬜     |              |       |
| B5.16 | StreakCalculator (with Protocol)                       | ⬜     |              |       |
| B5.17 | DashboardService orchestrator (injects calculators)    | ⬜     |              |       |
| B5.18 | GET /dashboard endpoint                                | ⬜     |              |       |

**B5 acceptance:** Mark algorithm as completed → dashboard count
increments atomically; recent items shows last viewed; each
calculator independently testable; orchestrator uses DI.

---

### B6 — Hardening

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| B6.1  | Cache headers per the policy table                     | ⬜     |              |       |
| B6.2  | Rate limit policy on all auth + write endpoints        | ⬜     |              |       |
| B6.3  | ETag / 304 Not Modified on /algorithms                 | ⬜     |              |       |
| B6.4  | Slow query log (queries > 100 ms)                      | ⬜     |              |       |
| B6.5  | Dashboard query performance pass (p95 < 300 ms)        | ⬜     |              |       |
| B6.6  | OpenTelemetry instrumentation (optional)               | ⬜     |              |       |
| B6.7  | Prometheus /metrics endpoint (optional)                | ⬜     |              |       |
| B6.8  | Sentry error reporting (optional)                      | ⬜     |              |       |
| B6.9  | Dockerfile (multi-stage, non-root runtime)             | ⬜     |              |       |
| B6.10 | Docker build step in CI                                | ⬜     |              |       |
| B6.11 | Secrets manager integration docs                      | ⬜     |              |       |
| B6.12 | OpenAPI spec published at /openapi.json                | ⬜     |              |       |
| B6.13 | Security audit (secrets scan, no-log-secrets check)    | ⬜     |              |       |
| B6.14 | README + runbook (deploy, rollback, debug)             | ⬜     |              |       |

**B6 acceptance:** Production deployment via `docker run` works; CI
builds and tests the container; all metrics, traces, and security
checks configured.

---

## 3. Frontend Feature List

### F1 — Foundation

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| F1.1  | Next.js + TypeScript strict scaffold (pnpm)            | ⬜     |              |       |
| F1.2  | Tailwind config + design tokens in globals.css         | ⬜     |              |       |
| F1.3  | shadcn/ui setup (Button, Card, Input, Dialog, Tabs, Select) | ⬜ |              |       |
| F1.4  | Base layout (Header, Footer, nav)                      | ⬜     |              |       |
| F1.5  | Home page (hero + "See algorithms think.")             | ⬜     |              |       |
| F1.6  | Home page mini sorting demo (uses engine)              | ⬜     |              |       |
| F1.7  | Algorithms Explorer page layout (sidebar + grid)       | ⬜     |              |       |
| F1.8  | Static algorithm cards (mocked data)                   | ⬜     |              |       |
| F1.9  | lib/api/client.ts (typed fetch wrapper)                | ⬜     |              |       |
| F1.10 | TanStack Query provider setup                          | ⬜     |              |       |
| F1.11 | ESLint + Prettier config                               | ⬜     |              |       |
| F1.12 | Vitest + RTL setup + one smoke test                    | ⬜     |              |       |
| F1.13 | LoadingState + ErrorState + EmptyState components      | ⬜     |              |       |
| F1.14 | Dark theme tokens applied + no light-mode toggle       | ⬜     |              |       |

**F1 acceptance:** Home and Explorer pages render correctly with mock
data; CI runs typecheck/lint/test/build.

---

### F2 — Engine Core

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| F2.1  | AlgorithmEvent discriminated union (events/types.ts)   | ⬜     |              |       |
| F2.2  | VisualizationAdapter<S> contract                       | ⬜     |              |       |
| F2.3  | ArrayAdapter implementation                            | ⬜     |              |       |
| F2.4  | AlgorithmModuleBase + segregated interfaces            | ⬜     |              |       |
| F2.5  | engineStore (Zustand) — algorithm state                | ⬜     |              |       |
| F2.6  | uiStore (Zustand) — panel/layout state                 | ⬜     |              |       |
| F2.7  | Player state machine (transition function)             | ⬜     |              |       |
| F2.8  | Step scheduler (msPerStep, pause/seek/reset)           | ⬜     |              |       |
| F2.9  | Bubble Sort module (run.ts, meta.ts, code/)            | ⬜     |              |       |
| F2.10 | Bubble Sort canonical trace test                       | ⬜     |              |       |
| F2.11 | Quick Sort module + canonical trace                    | ⬜     |              |       |
| F2.12 | VisualizationShell component                           | ⬜     |              |       |
| F2.13 | VisualizationCanvas (delegates to adapter)             | ⬜     |              |       |
| F2.14 | VisualizationControls (play/pause/next/prev/reset/speed/seek) | ⬜ |              |       |
| F2.15 | CodePanel with line highlighting + language switcher   | ⬜     |              |       |
| F2.16 | CurrentStepPanel                                       | ⬜     |              |       |
| F2.17 | ComplexityPanel                                        | ⬜     |              |       |
| F2.18 | /algorithms/[slug] page composing all panels            | ⬜     |              |       |
| F2.19 | Keyboard shortcuts (Space, ←, →, R) + tooltips         | ⬜     |              |       |
| F2.20 | prefers-reduced-motion honored in animations              | ⬜     |              |       |
| F2.21 | Engine bundle size verification (≤ 90 KB gz)            | ⬜     |              |       |
| F2.22 | Linked List data-structure page                        | ⬜     |              |       |

**F2 acceptance:** Open `/algorithms/quick-sort`, press Play, see
deterministic step-by-step animation with code highlighting, line
counter, and complexity panel. Engine bundle ≤ 90 KB gz.

---

### F3 — Search & Trees

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| F3.1  | Binary Search module (ArrayAdapter)                    | ⬜     |              |       |
| F3.2  | Binary Search canonical trace                          | ⬜     |              |       |
| F3.3  | TreeAdapter                                            | ⬜     |              |       |
| F3.4  | BST insert module                                      | ⬜     |              |       |
| F3.5  | BST search module                                      | ⬜     |              |       |
| F3.6  | Tree traversal: in-order                               | ⬜     |              |       |
| F3.7  | Tree traversal: pre-order                              | ⬜     |              |       |
| F3.8  | Tree traversal: post-order                             | ⬜     |              |       |
| F3.9  | HeapAdapter                                            | ⬜     |              |       |
| F3.10 | Heap Sort module                                       | ⬜     |              |       |
| F3.11 | Heap Sort canonical trace                              | ⬜     |              |       |
| F3.12 | Tree canvas component                                  | ⬜     |              |       |
| F3.13 | Heap canvas component                                  | ⬜     |              |       |
| F3.14 | Algorithm page polish for tree + heap pages            | ⬜     |              |       |

**F3 acceptance:** `/algorithms/binary-search`, `/algorithms/bst-*`,
`/algorithms/heap-sort` all visualize correctly with canonical
traces passing.

---

### F4 — Graphs

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| F4.1  | GraphAdapter (static layout, positions in input)       | ⬜     |              |       |
| F4.2  | GraphCanvas with GraphNode + GraphEdge components      | ⬜     |              |       |
| F4.3  | GraphControls (reset, focus node)                      | ⬜     |              |       |
| F4.4  | BFS module                                             | ⬜     |              |       |
| F4.5  | BFS canonical trace                                    | ⬜     |              |       |
| F4.6  | DFS module                                             | ⬜     |              |       |
| F4.7  | DFS canonical trace                                    | ⬜     |              |       |
| F4.8  | Dijkstra module                                        | ⬜     |              |       |
| F4.9  | Dijkstra canonical trace                               | ⬜     |              |       |
| F4.10 | PriorityQueuePanel for Dijkstra                        | ⬜     |              |       |
| F4.11 | DistancePanel for Dijkstra                             | ⬜     |              |       |
| F4.12 | Graph page polish (focus, highlight visited)           | ⬜     |              |       |

**F4 acceptance:** `/algorithms/bfs`, `/algorithms/dfs`,
`/algorithms/dijkstra` visualize correctly. Distance panel updates
in sync with edge relaxations.

---

### F5 — Auth & Server State

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| F5.1  | AuthProvider context                                   | ⬜     |              |       |
| F5.2  | useCurrentUser hook                                    | ⬜     |              |       |
| F5.3  | Login page (React Hook Form + Zod)                     | ⬜     |              |       |
| F5.4  | Register page                                          | ⬜     |              |       |
| F5.5  | ProtectedRoute component                               | ⬜     |              |       |
| F5.6  | Hook: useAlgorithms(filters) wired to real API         | ⬜     |              |       |
| F5.7  | Hook: useAlgorithm(slug) wired to real API              | ⬜     |              |       |
| F5.8  | Hook: useProgress wired to real API                    | ⬜     |              |       |
| F5.9  | Hook: useRoadmap wired to real API                     | ⬜     |              |       |
| F5.10 | Progress reporting (fire-and-forget POST on complete)  | ⬜     |              |       |
| F5.11 | Error toast/notification system                         | ⬜     |              |       |
| F5.12 | Logout from settings or header                         | ⬜     |              |       |

**F5 acceptance:** Public pages still work without auth; dashboard
requires auth; login → dashboard reflects real data; tokens never
stored in JS.

---

### F6 — Problems & Dashboard

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| F6.1  | /problems page layout                                  | ⬜     |              |       |
| F6.2  | /problems filter bar (difficulty, topic, company, status)| ⬜  |              |       |
| F6.3  | /problems filter chips with counts                     | ⬜     |              |       |
| F6.4  | /problems table or card list (data-driven)             | ⬜     |              |       |
| F6.5  | /problems/[slug] detail page                           | ⬜     |              |       |
| F6.6  | /problems/[slug] "Visualize" CTA                       | ⬜     |              |       |
| F6.7  | /problems/[slug]/visualize page (uses engine)          | ⬜     |              |       |
| F6.8  | Hook: useProblems(filters)                             | ⬜     |              |       |
| F6.9  | Hook: useProblem(slug)                                 | ⬜     |              |       |
| F6.10 | /dashboard page (algorithmsLearned, problemsSolved, etc.) | ⬜ |              |       |
| F6.11 | /dashboard skill mapping visualization                 | ⬜     |              |       |
| F6.12 | /dashboard focus areas                                 | ⬜     |              |       |
| F6.13 | /dashboard recently viewed                             | ⬜     |              |       |
| F6.14 | /dashboard activity graph                              | ⬜     |              |       |
| F6.15 | /roadmap page (stages + items)                         | ⬜     |              |       |
| F6.16 | /settings page                                         | ⬜     |              |       |

**F6 acceptance:** All authenticated pages render real data; filter
URLs are shareable; "Visualize" navigates to a working visualization.

---

### F7 — Polish

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| F7.1  | Lighthouse Performance ≥ 85 on key pages               | ⬜     |              |       |
| F7.2  | Bundle analysis + splitting (engine stays ≤ 90 KB gz)  | ⬜     |              |       |
| F7.3  | axe-core in component tests, zero serious violations   | ⬜     |              |       |
| F7.4  | Keyboard shortcuts surfaced in tooltips                | ⬜     |              |       |
| F7.5  | Mobile responsive layout for visualization page        | ⬜     |              |       |
| F7.6  | Code accordion on mobile                               | ⬜     |              |       |
| F7.7  | Playwright E2E: Home → Algorithms → Quick Sort flow   | ⬜     |              |       |
| F7.8  | Playwright E2E: Home → Problems → Two Sum flow         | ⬜     |              |       |
| F7.9  | Playwright E2E: Login → Dashboard flow                 | ⬜     |              |       |
| F7.10 | Playwright E2E: Algorithms → Search flow               | ⬜     |              |       |
| F7.11 | Documentation page (/documentation)                    | ⬜     |              |       |
| F7.12 | 404 + error pages                                      | ⬜     |              |       |

**F7 acceptance:** Lighthouse + axe + Playwright all green on CI;
mobile + desktop visual parity for visualizations.

---

## 4. Cross-Cutting Features (Both Backend + Frontend)

| ID    | Feature                                                | Status | Branch / PR  | Notes |
|-------|--------------------------------------------------------|--------|--------------|-------|
| X.1   | Git repository initialized with develop + main          | ✅     | commit 7af35e9 |       |
| X.2   | Branch protection on main + develop + dev-frontend + dev-backend (incl. "no direct push", "no direct merge") | ⬜ |              |       |
| X.3   | Pre-commit hooks (lefthook: lint, typecheck, tests, secrets) | ⬜ |              |       |
| X.4   | Conventional Commits enforced via commitlint            | ⬜     |              |       |
| X.5   | PR template (.github/pull_request_template.md)         | ⬜     |              |       |
| X.6   | CI pipeline green on first push                         | ⬜     |              |       |
| X.7   | CHANGELOG.md generation via release-please              | ⬜     |              |       |
| X.8   | README with setup instructions                          | ⬜     |              |       |
| X.9   | Docker Compose for full local stack (api + web + db)   | ⬜     |              |       |
| X.10  | CORS configured (frontend ↔ backend credentials mode)   | ⬜     |              |       |
| X.11  | 400-line file size rule enforced (lefthook pre-commit + CI check) | ⬜ |            |       |

---

## 5. Dependency Map

Features depending on others (build order):

``` text
B1.* (Foundation)
  ├── B2.* (Auth) requires B1.5, B1.6, B1.7
  │     └── B5.* (Progress/Dashboard) requires B2.*
  ├── B3.* (Catalog) requires B1.*
  │     └── B4.* (Problems) requires B3.2 (topics) — actually can run parallel
  └── B6.* (Hardening) requires all above

F1.* (Foundation)
  ├── F2.* (Engine) requires F1.*
  │     ├── F3.* (Trees) requires F2.3 (ArrayAdapter) + F2.4 (ModuleBase)
  │     ├── F4.* (Graphs) requires F2.4 (ModuleBase)
  │     └── F5.* (Auth/Server State) requires F2 + B2 (backend)
  │           └── F6.* (Problems/Dashboard) requires F5
  └── F7.* (Polish) requires all above
```

---

## 6. Branch Routing Rule (STRICT)

Each feature must be developed on a branch forked from the correct
integration branch, and PR'd back to that same branch. Cross-cutting
work goes to `develop`. **Nothing merges without a PR.**

| Feature ID prefix       | Base branch    | PR target branch | Why                                 |
|-------------------------|----------------|------------------|-------------------------------------|
| `B1.*` – `B6.*`         | `dev-backend`  | `dev-backend`    | Backend integration isolation       |
| `F1.*` – `F7.*`         | `dev-frontend` | `dev-frontend`   | Frontend integration isolation      |
| `X.*` (cross-cutting)  | `develop`      | `develop`        | Touches both or neither             |

**Violations are blocked:**

- ❌ B* PR'd to `develop` or `dev-frontend` → blocked
- ❌ F* PR'd to `develop` or `dev-backend` → blocked
- ❌ X* PR'd to `dev-frontend` or `dev-backend` → blocked
- ❌ Direct push or merge to `main`, `develop`, `dev-frontend`,
  `dev-backend` (no exceptions, including hotfixes)

**Promote cadence:**

`dev-frontend` and `dev-backend` are fast-forwarded (or merged
`--no-ff`) into `develop` **at phase boundaries only** — never per
commit. Releases cut from `develop` go into `main` after the
release-please / CHANGELOG step.

Full details: `GIT_WORKFLOW.md` §1.2.

---

## 7. Observation Checkpoints

For each phase close, verify:

### 7.1 Code-Level Checkpoints

``` text
□ Branch merged to its target via squash-merge (B* → dev-backend,
  F* → dev-frontend, X* → develop)
□ All PRs have required approvals
□ CI green (lint, typecheck, test, build, migrate)
□ Coverage maintained or improved
□ Bundle size within budget
□ No secrets in diff
□ No architectural drift (no edits to out-of-scope files)
□ Commits follow Conventional Commits with Refs: footer
```

### 7.2 Product-Level Checkpoints

``` text
□ Vertical slice works end-to-end (curl OR browser)
□ Acceptance criteria from feature table met
□ Phase Definition of Done met
□ Next phase is unblocked
```

### 7.3 How to Observe Progress

**For the user:**

1.  Open `FEATURE_LIST.md` in your editor.
2.  When Puku reports a feature complete, change `⬜` → `✅` and paste
    the PR URL.
3.  When work begins, change `⬜` → `🚧`.
4.  When PR opens, change to `🔍`.

**For Puku (every session end):**

Output a delta:

``` text
SESSION DELTA
=============
Started:    B2.3, B2.7, B2.8
Completed:  B2.3 → ✅ (PR #42), B2.7 → ✅ (PR #43)
In review:  B2.8 → 🔍 (PR #44)
Blocked:    none
Coverage:   84% → 87%
```

---

## 8. Milestones

Track major releases:

| Milestone | Phase | Backend Features | Frontend Features | Definition |
|-----------|-------|------------------|-------------------|------------|
| **M0: Empty Repo + Docs** | — | 0/84 | 0/102 | All docs in place, repo init, CI green on docs-only commit |
| **M1: Foundation** | B1+F1 | 12/84 | 14/102 | Local stack runs; home + explorer render with mock data |
| **M2: First Visualization** | B1-B3 + F1-F2 | 40/84 | 36/102 | `/algorithms/quick-sort` works end-to-end with real backend data |
| **M3: Auth + Progress** | +B2-B5 + F5 | 76/84 | 50/102 | Users can register, log in, mark algorithms complete, see dashboard |
| **M4: Full Catalog** | +B3-B4 + F3-F4 | 102/84 | 76/102 | All 12+ algorithms + 50 problems visualizable |
| **M5: Production Ready** | +B6 + F6-F7 | 84/84 | 102/102 | Hardened, E2E tested, deployed |

---

## 9. Update Protocol

**Who updates this file:**

- **Puku** updates the **Status** column when:
  - Starting work (⬜ → 🚧)
  - Opening PR (🚧 → 🔍)
  - Merging (🔍 → ✅)
- **The user** updates when:
  - Marking ⛔ Blocked (with reason in Notes)
  - Marking 🗑️ Deferred (with reason in Notes)
  - Adding new features discovered during work (via PR)

**Update timing:**

- Every commit message can include `Updates: FEATURE_LIST.md`
  (optional).
- Every PR that closes features should reference them in the body.
- Every session-end report includes a session delta.

**Conflict resolution:**

- If a feature changes scope, update the description **before**
  implementing.
- If a feature is removed, change to 🗑️ with reason.

---

## 10. References

- Backend agent: `PUKU_BACKEND_AGENT.md`
- Frontend agent: `PUKU_FRONTEND_AGENT.md`
- Git workflow: `GIT_WORKFLOW.md`
- Architecture: `ARCHITECTURE.md`
- Database design: `DATABASE_DESIGN.md`
- Backend plan: `ALGOVISION_BACKEND_PLAN.md`
- Frontend plan: `ALGOVISION_FRONTEND_PLAN.md`
- Backend contract: `AlgoVision_BACKEND.md`
- Frontend contract: `AlgoVision_FRONTEND.md`