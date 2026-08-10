# AlgoVision Architecture

> System design document. Companion to `ALGOVISION_BACKEND_PLAN.md`
> and `ALGOVISION_FRONTEND_PLAN.md`. This document captures the
> high-level architecture using the **C4 model**, sequence diagrams,
> deployment topology, and data flow.

---

## 1. C4 Model

The C4 model describes software architecture at four levels of
abstraction: **Context**, **Container**, **Component**, and **Code**.

### 1.1 Level 1 — System Context

Who uses AlgoVision and what external systems does it talk to?

``` text
┌─────────────────────────────────────────────────────────────────┐
│                        AlgoVision System                        │
│                                                                 │
│   ┌──────────────┐                      ┌──────────────────┐    │
│   │   Web App    │                      │  Admin Console   │    │
│   │ (Next.js +   │                      │  (future, same   │    │
│   │  TypeScript) │                      │   web app)       │    │
│   └──────┬───────┘                      └────────┬─────────┘    │
│          │                                        │              │
└──────────┼────────────────────────────────────────┼──────────────┘
           │                                        │
           │ HTTPS                                  │ HTTPS
           │ (cookies)                             │ (auth)
           ▼                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                       AlgoVision API                            │
│                       (FastAPI backend)                         │
│                                                                 │
└──────────┬──────────────────────────────────────────────────────┘
           │
           │ SQL (asyncpg)
           ▼
┌──────────────────────┐         ┌─────────────────────────────┐
│   PostgreSQL 16      │         │  Object store (future)      │
│   (managed, RDS-     │         │  for user uploads           │
│    like, encrypted   │         │                             │
│    backups)          │         │                             │
└──────────────────────┘         └─────────────────────────────┘
```

**Actors:**

- **Learner** — primary user. Uses the web app to explore algorithms,
  watch visualizations, solve problems, track progress.
- **Future Admin/Editor** — manages catalog content (algorithms,
  problems, topics). Same web app with elevated role.
- **AlgoVision API** — backend system.
- **PostgreSQL** — primary persistence.
- **Object store** — future, for any user-uploaded content.

### 1.2 Level 2 — Container Diagram

The deployable units inside AlgoVision.

``` text
┌─────────────────────────────────────────────────────────────────────┐
│                          Web Browser (User)                         │
└───────────────────────────────┬─────────────────────────────────────┘
                                │ HTTPS
                                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Reverse Proxy (Caddy / Nginx)                      │
│                  - TLS termination                                  │
│                  - Security headers                                 │
│                  - Rate limiting (coarse)                           │
└───────────────┬─────────────────────────────────┬───────────────────┘
                │                                 │
                ▼                                 ▼
┌────────────────────────────┐    ┌──────────────────────────────────┐
│   Next.js Web App          │    │   FastAPI Backend                │
│   (Node.js runtime)        │    │   (Python 3.12, uvicorn workers) │
│                            │    │                                  │
│   - SSR + RSC              │    │   - Auth, catalog, progress,     │
│   - Static assets          │    │     dashboard, roadmap APIs      │
│   - Visualization engine   │    │   - Business logic               │
│   - Algorithm registry     │    │   - Background aggregation       │
│                            │    │                                  │
│   Talks to: ───────────────┼────│─→ PostgreSQL                     │
│            Backend via ────────  │                                  │
│            HTTPS /api/v1/*  │    │   Talks to: PostgreSQL           │
└────────────────────────────┘    └──────────────┬───────────────────┘
                                                 │ SQL (asyncpg)
                                                 ▼
                                  ┌──────────────────────────────┐
                                  │   PostgreSQL 16               │
                                  │   - 14 normalized tables      │
                                  │   - Indexes per query pattern │
                                  └──────────────────────────────┘

Sidecars (optional, prod):
  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
  │  OpenTelemetry   │  │  Prometheus      │  │  Sentry          │
  │  Collector       │  │  scraper         │  │  error reporter  │
  └──────────────────┘  └──────────────────┘  └──────────────────┘
```

**Container responsibilities:**

| Container       | Tech              | Owns                                            |
|-----------------|-------------------|-------------------------------------------------|
| Web app         | Next.js + Node    | UI, SSR, visualization engine, client caching   |
| API             | FastAPI + Python  | Business logic, auth, all `/api/v1/*` endpoints |
| Database        | PostgreSQL 16     | Persistence                                     |
| Reverse proxy   | Caddy/Nginx       | TLS, headers, coarse rate limiting              |
| OTEL collector  | OpenTelemetry     | Trace aggregation (optional)                    |
| Prometheus      | Prometheus        | Metrics scraping (optional)                     |
| Sentry          | Sentry SDK        | Error reporting (optional)                      |

### 1.3 Level 3 — Component Diagram (Backend)

``` text
┌─────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      API Routers                             │   │
│  │  /auth  /algorithms  /problems  /progress  /dashboard  ...   │   │
│  └────────┬─────────────────────────────────────────┬────────────┘   │
│           │ HTTP, validation, DI                     │                │
│           ▼                                         ▼                │
│  ┌────────────────────┐              ┌────────────────────────────┐  │
│  │ Application        │              │ Shared / Cross-cutting     │  │
│  │ Services           │              │                            │  │
│  │                    │              │  - pagination              │  │
│  │  AuthService       │              │  - error envelope          │  │
│  │  UserService       │              │  - filter parsers          │  │
│  │  AlgorithmService  │◄─────────────│  - request id middleware   │  │
│  │  DataStructureSvc  │              │  - rate limiter (slowapi)  │  │
│  │  ProblemService    │              │  - CORS middleware         │  │
│  │  ProgressService   │              │  - logging middleware      │  │
│  │  DashboardService  │              │                            │  │
│  │  RoadmapService    │              │                            │  │
│  │                    │              │                            │  │
│  │  Composition root: │              │                            │  │
│  │  Calculator interfaces are       │                            │  │
│  │  injected (SOLID)  │              │                            │  │
│  └─────────┬──────────┘              └────────────────────────────┘  │
│            │                                                            │
│            ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                       Domain / Repositories                  │     │
│  │                                                             │     │
│  │   UserRepository    AlgorithmRepository    DataStructureRepo│     │
│  │   ProblemRepository ProgressRepository     RoadmapRepo      │     │
│  │                                                             │     │
│  │   Returns tuples (items, total); services compose Page[T]   │     │
│  └─────────┬───────────────────────────────────────────────────┘     │
│            │                                                            │
│            ▼                                                            │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │                SQLAlchemy 2.x Async ORM                      │     │
│  │                asyncpg driver                                │     │
│  └─────────┬───────────────────────────────────────────────────┘     │
└────────────┼─────────────────────────────────────────────────────────┘
             │ SQL
             ▼
        PostgreSQL
```

### 1.4 Level 3 — Component Diagram (Frontend)

``` text
┌─────────────────────────────────────────────────────────────────────┐
│                         Next.js Web App                             │
│                                                                     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                       App Router                              │   │
│  │   /   /algorithms   /problems   /dashboard   /roadmap        │   │
│  └────────┬─────────────────────────────────────┬───────────────┘   │
│           │                                     │                   │
│           ▼                                     ▼                   │
│  ┌─────────────────────┐         ┌───────────────────────────────┐  │
│  │  Features           │         │  Shared Components            │  │
│  │                     │         │                               │  │
│  │  - algorithms       │         │  - VisualizationShell         │  │
│  │  - visualization ◄──┼─────────┼─- AlgorithmCard               │  │
│  │    (engine core)    │         │  - CodePanel                  │  │
│  │  - data-structures  │         │  - StepPanel                  │  │
│  │  - problems         │         │  - LoadingState/ErrorState    │  │
│  │  - dashboard        │         │  - AuthProvider               │  │
│  │  - auth             │         │  - ProtectedRoute             │  │
│  └────┬────────────────┘         └───────────────────────────────┘  │
│       │                                                                │
│       ▼                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │              Visualization Engine (Product Core)                ││
│  │                                                                 ││
│  │  ┌──────────────────┐    ┌──────────────────┐                   ││
│  │  │  engineStore     │    │  uiStore         │  (split per SOLID)││
│  │  │  events, step,   │    │  code panel,     │                   ││
│  │  │  status, speed   │    │  explanation     │                   ││
│  │  └────────┬─────────┘    └────────┬─────────┘                   ││
│  │           │                       │                              ││
│  │           ▼                       ▼                              ││
│  │  ┌──────────────────────────────────────────────────────────┐   ││
│  │  │           Player State Machine                            │   ││
│  │  │   idle → playing → paused → complete                     │   ││
│  │  └──────────────────────────────────────────────────────────┘   ││
│  │                                                                 ││
│  │  ┌──────────────────────────────────────────────────────────┐   ││
│  │  │  Adapters: ArrayAdapter, LinkedListAdapter, GraphAdapter, │   ││
│  │  │            TreeAdapter, HeapAdapter, DpTableAdapter, ...  │   ││
│  │  └──────────────────────────────────────────────────────────┘   ││
│  │                                                                 ││
│  │  ┌──────────────────────────────────────────────────────────┐   ││
│  │  │  Algorithm Registry + Modules (bubble, quick, dijkstra...) │   ││
│  │  └──────────────────────────────────────────────────────────┘   ││
│  └─────────────────────────────────────────────────────────────────┘│
│       │                                                                │
│       ▼                                                                │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │  Data Layer                                                      ││
│  │  - lib/api/* (typed fetch client)                                ││
│  │  - TanStack Query (server state cache)                           ││
│  │  - Zod (runtime validation)                                      ││
│  │  - React Hook Form (forms)                                       ││
│  └─────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

### 1.5 Level 4 — Code (Example: Mark Algorithm Completed)

For one critical path, here's the code-level call chain.

``` text
User clicks "Mark Complete" on /algorithms/quick-sort
  ↓
Component: AlgorithmCompleteButton.tsx
  ↓ calls
Hook: useUpdateAlgorithmProgress()
  ↓ calls
TanStack Query mutation: useMutation({ mutationFn: updateAlgorithmProgress })
  ↓ calls
lib/api/progress.ts: updateAlgorithmProgress(algorithmId, dto)
  ↓ calls
lib/api/client.ts: apiFetch('/progress/algorithms/{id}', { method: 'POST', body })
  ↓ HTTP POST
FastAPI router: ProgressRouter.mark_algorithm()
  ↓ depends on
Service: ProgressService.mark_algorithm(user_id, algorithm_id, dto)
  - validates ownership
  - opens transaction
  - calls repositories
  - emits "recently viewed" side-effect (via ProgressService.record_view, NOT via AlgorithmService)
  - commits transaction
  ↓ calls (within tx)
Repository: UserAlgorithmProgressRepository.upsert()
Repository: UserRecentItemsRepository.insert()
  ↓
SQLAlchemy async session.execute()  × 2  (single tx)
  ↓
PostgreSQL COMMIT
  ↓
Response: 200 OK with updated progress
  ↓
TanStack Query invalidates ['progress', 'dashboard']
  ↓
UI re-fetches dashboard summary; updated count appears
```

---

## 2. Sequence Diagrams

### 2.1 Login Flow

``` text
User                Browser              Web App            API              DB
 │  click login       │                   │                  │                │
 │───────────────────▶│                   │                  │                │
 │                    │  POST /login      │                  │                │
 │                    │──────────────────▶│  POST /auth/login│                │
 │                    │                   │─────────────────▶│                │
 │                    │                   │                  │  SELECT user   │
 │                    │                   │                  │───────────────▶│
 │                    │                   │                  │◀───────────────│
 │                    │                   │                  │ verify Argon2  │
 │                    │                   │                  │ mint tokens    │
 │                    │                   │                  │ INSERT session │
 │                    │                   │                  │───────────────▶│
 │                    │  200 + Set-Cookie │◀─────────────────│◀───────────────│
 │                    │◀──────────────────│                  │                │
 │  redirected to /   │                   │                  │                │
 │◀───────────────────│                   │                  │                │
```

### 2.2 Algorithm Visualization Flow (Public, No Login)

``` text
User           Web App                Engine             Adapter         Render
 │  /algorithms/quick-sort                                       │
 │─────────────▶│                                                    │
 │              │ getAlgorithm(slug)                                 │
 │              │  (TanStack Query → API)                            │
 │              │◀─── metadata + code + complexity                   │
 │              │                                                    │
 │              │ getAlgorithm(slug) from registry                   │
 │              │───────────────────────────────────────────▶         │
 │              │                                                    │
 │              │ run(input)                                         │
 │              │──────────────────────────────────▶ events[]         │
 │              │◀──────────────────────────────────────              │
 │              │ createInitialState(input)                          │
 │              │─────────────────────────────────────▶ state        │
 │              │ reduce(state, e) × n                                │
 │              │─────────────────────────────────────▶ states[]     │
 │              │                                                    │
 │              │ render with state[currentStep]                     │
 │              │────────────────────────────────────────────────▶   │
 │  sees bars   │                                                    │
 │◀─────────────│                                                    │
 │              │                                                    │
 │  click play  │                                                    │
 │─────────────▶│                                                    │
 │              │ play() → scheduler starts                          │
 │              │ advance step → state[currentStep+1]                │
 │              │────────────────────────────────────────────────▶   │
 │              │ ...                                                │
```

### 2.3 Progress Update Flow

``` text
User            Web App              API              ProgressService       Repos         DB
 │ complete algo │                   │                     │                  │            │
 │──────────────▶│                   │                     │                  │            │
 │               │ POST /progress/   │                     │                  │            │
 │               │ algorithms/{id}   │                     │                  │            │
 │               │──────────────────▶│                     │                  │            │
 │               │                   │ mark_algorithm()    │                  │            │
 │               │                   │────────────────────▶│                  │            │
 │               │                   │                     │ BEGIN tx         │            │
 │               │                   │                     │ upsert progress  │            │
 │               │                   │                     │─────────────────▶│            │
 │               │                   │                     │                  │ INSERT/UPSERT
 │               │                   │                     │                  │───────────▶│
 │               │                   │                     │ insert recent    │            │
 │               │                   │                     │─────────────────▶│            │
 │               │                   │                     │                  │ INSERT     │
 │               │                   │                     │                  │───────────▶│
 │               │                   │                     │ COMMIT           │            │
 │               │                   │                     │─────────────────▶│            │
 │               │                   │◀────────────────────│                  │            │
 │               │ 200 + payload     │                     │                  │            │
 │               │◀──────────────────│                     │                  │            │
 │               │ invalidate ['progress','dashboard']      │                  │            │
 │               │ refetch dashboard                       │                  │            │
 │               │──────────────────▶│ GET /dashboard       │                  │            │
 │               │                   │ summary()           │                  │            │
 │               │                   │────────────────────▶│ aggregate        │            │
 │               │                   │                     │ SELECT ...       │            │
 │               │                   │                     │─────────────────▶│            │
 │               │                   │◀────────────────────│                  │            │
 │               │ 200 + DashboardSummary                    │                  │            │
 │               │◀──────────────────│                     │                  │            │
```

### 2.4 Dashboard Load Flow

``` text
User          Web App            API          DashboardService    Calculators    DB
 │ /dashboard  │                 │                  │                 │             │
 │────────────▶│                 │                  │                 │             │
 │             │ getDashboard()  │                 │                 │             │
 │             │ (cached 30s)    │                 │                 │             │
 │             │                 │                 │                 │             │
 │             │ GET /dashboard  │                 │                 │             │
 │             │────────────────▶│                 │                 │             │
 │             │                 │ summary(user)   │                 │             │
 │             │                 │────────────────▶│                 │             │
 │             │                 │                 │ readiness()     │             │
 │             │                 │                 │────────────────▶│             │
 │             │                 │                 │                 │ SELECT …    │
 │             │                 │                 │                 │────────────▶│
 │             │                 │                 │                 │◀────────────│
 │             │                 │                 │ skill_mapping() │             │
 │             │                 │                 │────────────────▶│             │
 │             │                 │                 │                 │ SELECT …    │
 │             │                 │                 │                 │────────────▶│
 │             │                 │                 │ focus_areas()   │             │
 │             │                 │                 │ streak()        │             │
 │             │                 │                 │                 │             │
 │             │                 │◀────────────────│                 │             │
 │             │ 200 DashboardSummary                              │             │
 │             │◀────────────────│                 │                 │             │
 │             │ render UI       │                 │                 │             │
```

---

## 3. Deployment Topology

### 3.1 Local Development

``` text
docker-compose.yml
  ┌─────────────┐    ┌─────────────────┐    ┌──────────────────┐
  │   api       │    │   web           │    │   db             │
  │   :8000     │───▶│   :3000         │    │   postgres:16    │
  │   FastAPI   │    │   Next.js dev   │    │   :5432          │
  │             │◀───│                 │◀──▶│                  │
  └─────────────┘    └─────────────────┘    └──────────────────┘
       │                    │
       └────────────────────┴──► mailhog (optional, future)
```

### 3.2 Production

``` text
                            ┌─────────────────────┐
                            │   CloudFront / CDN  │
                            │   (static assets)   │
                            └──────────┬──────────┘
                                       │
                                       ▼
                            ┌─────────────────────┐
                            │  Reverse Proxy      │
                            │  (Caddy/Nginx)      │
                            │  TLS, headers       │
                            └──────┬──────────────┘
                                   │
              ┌────────────────────┼────────────────────┐
              ▼                    ▼                    ▼
     ┌────────────────┐   ┌────────────────┐   ┌────────────────┐
     │  Web tier      │   │  API tier      │   │  Worker tier   │
     │  Next.js (2+)  │   │  FastAPI (4+)  │   │  (future:      │
     │  behind LB     │   │  behind LB     │   │   aggregations)│
     └────────────────┘   └───────┬────────┘   └────────────────┘
                                  │
                                  ▼
                          ┌────────────────┐
                          │  Managed PG    │
                          │  + read replica│
                          │  + PITR backup │
                          └────────────────┘

Sidecars:
  - Secrets manager (AWS SM / Doppler / Vault)
  - OpenTelemetry collector
  - Prometheus + Grafana
  - Sentry
  - Log aggregator (Loki / CloudWatch)
```

**Key deployment properties:**

- Stateless API containers — scale horizontally.
- Web tier is mostly static; SSR only for `/dashboard` and personalized
  pages.
- Database is managed; backups are automated and encrypted.
- Secrets injected via env from a secret manager.
- Migrations run as a one-off Job before rolling out new API version.

---

## 4. Data Flow Diagram

How data moves through the system end-to-end.

``` text
┌──────────────────────────────────────────────────────────────────────┐
│                            DATA FLOW                                 │
│                                                                      │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────────┐    │
│  │ Source   │───▶│ Ingestion│───▶│ Storage  │───▶│ Processing   │    │
│  └──────────┘    └──────────┘    └──────────┘    └──────┬───────┘    │
│                                                            │           │
│  Algorithm metadata ──▶ seed scripts ──▶ PostgreSQL         │           │
│  Problem catalog    ──▶ seed scripts ──▶ PostgreSQL         │           │
│  User registration  ──▶ API service   ──▶ PostgreSQL         │           │
│  User progress      ──▶ API service   ──▶ PostgreSQL         │           │
│                                                            ▼           │
│                                                  ┌──────────────────┐ │
│                                                  │ Serving          │ │
│                                                  │                  │ │
│                                                  │  - API endpoints │ │
│                                                  │  - TanStack Query│ │
│                                                  │    cache (FE)    │ │
│                                                  │  - HTTP cache    │ │
│                                                  │    (CDN/proxy)   │ │
│                                                  └──────┬───────────┘ │
│                                                         │             │
│                                                         ▼             │
│                                                  ┌──────────────────┐│
│                                                  │ Presentation     ││
│                                                  │                  ││
│                                                  │  - Algorithm page││
│                                                  │  - Visualization ││
│                                                  │  - Dashboard     ││
│                                                  │  - Problems      ││
│                                                  └──────────────────┘│
└──────────────────────────────────────────────────────────────────────┘
```

### Data Categories

| Category             | Source                       | Storage             | Read by                          |
|----------------------|------------------------------|---------------------|----------------------------------|
| Algorithm catalog    | Seed scripts                 | PostgreSQL          | Public API, algorithm page       |
| Problem catalog      | Seed scripts                 | PostgreSQL          | Public API, problems page        |
| Source code versions | Seed scripts                 | PostgreSQL          | CodePanel                        |
| User accounts        | Registration                 | PostgreSQL          | Auth, profile, dashboard         |
| User progress        | Activity on platform         | PostgreSQL          | Dashboard, progress endpoints    |
| Recently viewed      | Auto-recorded by services    | PostgreSQL (capped) | Dashboard sidebar                |
| Roadmap              | Seed scripts                 | PostgreSQL          | Roadmap page                     |
| Algorithm events     | Generated client-side        | None (transient)    | Visualization engine only        |
| Auth tokens          | Issued by API on login       | HTTP-only cookies   | Browser → API auto-sent          |

### Critical Data Invariants

1. **Algorithm execution events never touch the database.** They live
   only in the frontend engine.
2. **Progress updates are atomic** — a single transaction updates
   `user_algorithm_progress` AND `user_recent_items`.
3. **Dashboard values are computed, not stored.** No `dashboard` table.
4. **Source code is versioned, never overwritten.**

---

## 5. Cross-Cutting Concerns

### 5.1 Authentication & Authorization

``` text
Login → Argon2id verify → mint access (15 min) + refresh (7 day) tokens
     → set HTTP-only Secure cookies
     → store session metadata in DB (optional: sessions table)

Every protected request:
  - Read access cookie
  - Verify signature + expiry
  - Resolve user_id
  - Pass via Depends(get_current_user)
```

Authorization is role-based (`user`, `editor`, `admin`). Role checks
go through `require_role(role)` dependency, never scattered through
services.

### 5.2 Observability

Every request gets:

- `X-Request-ID` UUID (generated if absent)
- Structured log line with `request_id`, `route`, `method`, `status`,
  `duration_ms`
- (Optional) OpenTelemetry span covering HTTP → DB
- (Optional) Prometheus metrics

Errors flow to Sentry with `before_send` scrubbing.

### 5.3 Error Handling

``` text
Domain exception
  ↓
Central exception handler
  ↓
Uniform JSON envelope
  ↓
HTTP response with appropriate status
```

The frontend's `ApiError` normalizes this envelope and surfaces a
typed error to hooks.

### 5.4 Rate Limiting

Implemented at two layers:

- **Reverse proxy** — coarse IP-based limits (DOS protection).
- **slowapi** in FastAPI — fine-grained per-user or per-IP limits for
  auth and write endpoints.

### 5.5 Caching Strategy

| Layer            | What                            | TTL                          |
|------------------|---------------------------------|------------------------------|
| HTTP cache       | Public catalog endpoints        | 60 s – 1 h                   |
| TanStack Query   | Per-hook cache                  | 30 s – 5 min                 |
| React component  | URL state for filters           | Persistent in URL            |
| Zustand          | Engine session state            | In-memory, cleared on reset  |

---

## 6. Quality Attributes

| Attribute         | Target                                            |
|-------------------|---------------------------------------------------|
| Availability      | 99.5% (single-region MVP)                         |
| Latency           | API p95 < 200 ms; dashboard p95 < 300 ms          |
| Scalability       | 10k concurrent users (single API tier)            |
| Security          | OWASP Top 10 baseline; secrets via manager         |
| Maintainability   | Per-module DoD; CI blocks on lint/test/migration   |
| Observability     | Request ID + structured logs; optional tracing    |
| Accessibility     | WCAG 2.1 AA                                       |
| Performance       | Lighthouse ≥ 85 on key pages                      |

---

## 7. Architectural Decisions (ADRs)

### ADR-001: Backend does not execute user code

- **Decision:** Frontend owns deterministic visualization execution.
- **Why:** Avoids sandboxing complexity; faster iteration; safer.
- **Consequence:** If server-side execution is needed later, add a
  separate sandboxed service.

### ADR-002: Dashboard is a projection, not a table

- **Decision:** Compute `interview_readiness`, `skill_mapping`,
  `focus_areas` in `DashboardService`.
- **Why:** Avoid stale computed data; easier to evolve formulas.
- **Consequence:** Dashboard query must be optimized; p95 < 300 ms.

### ADR-003: Visualization engine is event-driven, not state-driven

- **Decision:** Algorithms emit `AlgorithmEvent[]`; reducer folds
  events into adapter-specific state.
- **Why:** Same engine handles array, tree, graph, etc.; deterministic;
  testable; supports scrubbing.
- **Consequence:** Every algorithm needs an adapter; this is the cost
  of generality.

### ADR-004: Single Zustand store split by concern

- **Decision:** `engineStore` (algorithm state) and `uiStore`
  (panels/visibility) are separate.
- **Why:** Different change reasons; one should not re-render consumers
  of the other.
- **Consequence:** Slightly more imports in components; cleaner
  separation.

### ADR-005: Argon2id over bcrypt

- **Decision:** Use Argon2id for password hashing.
- **Why:** Modern; resistant to GPU and side-channel attacks.
- **Consequence:** Slightly higher CPU on login; acceptable.

### ADR-006: PostgreSQL over NoSQL

- **Decision:** Use PostgreSQL for all data.
- **Why:** Strong relational model; mature; supports JSONB where
  needed; one less moving part.
- **Consequence:** Schema migrations required; Alembic handles this.

---

## 8. Open Architecture Questions

These are deliberately deferred:

- **Read replicas** for `/dashboard` aggregation at scale.
- **WebSocket / SSE** for real-time features (collaborative
  visualizations — out of scope for v1).
- **Multi-tenant** — single-tenant at v1.
- **CDN strategy** for algorithm static assets (e.g., precomputed
  visualization snapshots).
- **Edge rendering** for `/algorithms/[slug]` if traffic warrants.

---

## 9. References

- Backend plan: `ALGOVISION_BACKEND_PLAN.md`
- Frontend plan: `ALGOVISION_FRONTEND_PLAN.md`
- Backend contract: `AlgoVision_BACKEND.md`
- Frontend contract: `AlgoVision_FRONTEND.md`
- Database design: `DATABASE_DESIGN.md`
- Git workflow: `GIT_WORKFLOW.md`