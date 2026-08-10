# AlgoVision Backend Plan (High-Level Roadmap)

> Companion to `AlgoVision_BACKEND.md`. This file is the planning
> overview — architecture decisions, module boundaries, function design,
> API surface, and phase roadmap. The implementation contract lives in
> `AlgoVision_BACKEND.md`.

---

## 1. Goal

Provide a typed, secure, modular API for the AlgoVision Next.js
frontend. The backend delivers algorithm catalog, data structure
catalog, interview problems, progress tracking, dashboard aggregation,
and roadmap data. It does **not** execute user code.

## 2. Stack

| Concern        | Choice                                            |
|----------------|---------------------------------------------------|
| Language       | Python 3.12+                                      |
| Framework      | FastAPI                                           |
| Validation     | Pydantic v2                                       |
| ORM            | SQLAlchemy 2.x (async)                            |
| Driver         | asyncpg                                           |
| Database       | PostgreSQL 16                                     |
| Migrations     | Alembic                                           |
| Auth           | Argon2id passwords, HTTP-only cookies             |
| Rate limit     | slowapi                                           |
| Logging        | structlog (JSON in non-dev)                       |
| Tracing (opt.) | OpenTelemetry                                     |
| Metrics (opt.) | Prometheus `/metrics`                             |
| Tests          | pytest + httpx + real PostgreSQL test DB          |
| Lint/format    | Ruff                                              |
| Types          | mypy (practical)                                  |
| Container      | Multi-stage Docker, non-root runtime               |
| CI             | GitHub Actions: lint, typecheck, test, migrate    |

## 3. Architectural Style

Strict modular layering. No layer leaks into another.

``` text
HTTP
 ↓
API Router          (HTTP, validation, DI wiring — no business logic)
 ↓
Application Service (business rules, transactions, orchestration)
 ↓
Repository          (persistence, queries — no business rules)
 ↓
SQLAlchemy          (mapping)
 ↓
PostgreSQL
```

Pydantic schemas handle I/O. SQLAlchemy models handle persistence.
Domain objects are pure Python where useful.

## 4. Module Map

``` text
src/
├── main.py
├── core/                  # config, security, db, logging, exceptions
├── modules/
│   ├── auth/              # register, login, logout, refresh, me
│   ├── users/             # profile, settings, account
│   ├── algorithms/        # catalog + categories + topics + code
│   ├── data_structures/   # catalog
│   ├── problems/          # interview problems + topics + companies
│   ├── progress/          # user_algorithm_progress, user_problem_progress
│   ├── dashboard/         # aggregations only — no own tables
│   └── roadmap/           # stages + items
├── shared/                # pagination, responses, enums, errors
└── migrations/            # Alembic
```

Each module contains `router.py`, `schemas.py`, `models.py`,
`repository.py`, `service.py`, `dependencies.py`, and where useful
`exceptions.py`.

## 5. Database Design (Normalized)

Tables (relationships shown in `AlgoVision_BACKEND.md`):

``` text
users
algorithm_categories        algorithms          algorithm_code_versions
topics                      algorithm_topics    data_structures
problems                    problem_topics      companies
problem_companies
user_algorithm_progress     user_problem_progress
user_recent_items
roadmap_stages              roadmap_items
```

Design rules:

-   No JSON blobs where relations are needed.
-   Many-to-many tables have explicit `PRIMARY KEY` on both columns.
-   All FKs use `ON DELETE CASCADE` only when deletion is safe.
-   Indexes are added based on actual query patterns, not preemptively.
-   Source code for algorithms is **versioned**, never overwritten.

## 6. Function Design — Public Service Surface

This is the stable catalog of service methods. Each method maps to one
or more router endpoints. New methods may be added; these signatures
must not change without versioning.

``` text
AuthService
  register(dto) -> User
  login(dto) -> User
  logout(session) -> None
  refresh(refresh_token) -> TokenPair
  get_current_user(user_id) -> User

UserService
  get_profile(user_id) -> UserProfile
  update_profile(user_id, dto) -> UserProfile
  delete_account(user_id) -> None

AlgorithmService
  list(filters) -> Page[Algorithm]
  get_by_slug(slug, user_id?) -> AlgorithmDetail
  list_categories() -> list[AlgorithmCategory]
  list_topics() -> list[Topic]

DataStructureService
  list(filters) -> Page[DataStructure]
  get_by_slug(slug) -> DataStructureDetail

ProblemService
  list(filters) -> Page[Problem]
  get_by_slug(slug, user_id?) -> ProblemDetail
  list_topics() -> list[Topic]
  list_companies() -> list[Company]

ProgressService
  mark_algorithm(user_id, algorithm_id, dto) -> UserAlgorithmProgress
  mark_problem(user_id, problem_id, dto) -> UserProblemProgress
  get_overview(user_id) -> ProgressOverview
  list_algorithm_progress(user_id, filters) -> Page[...]
  list_problem_progress(user_id, filters) -> Page[...]
  record_view(user_id, item_type, item_id) -> None

DashboardService (orchestrator only — no business rules)
  summary(user_id) -> DashboardSummary

ReadinessCalculator (SOLID: one reason to change = "what is readiness?")
  compute(user_id) -> int                # 0..100

SkillMapper (one reason to change = "what topics and scores?")
  compute(user_id) -> list[SkillMetric]

FocusAreaSelector (one reason to change = "how do we pick focus areas?")
  select(user_id) -> list[FocusArea]

StreakCalculator (one reason to change = "what is a streak?")
  compute(user_id) -> int

RoadmapService
  list_stages() -> list[RoadmapStageWithItems]
```

`record_view` is invoked via a **domain event** (see §6.7), not by
direct call from `AlgorithmService` or `ProblemService`. This decouples
catalog services from progress services (Dependency Inversion).

### Transaction Boundary

Services own the transaction:

``` text
API request → Service → [Repository ops] → commit/rollback
```

Repositories do **not** commit. This lets a service coordinate multiple
writes atomically (e.g., `mark_algorithm` updates progress **and** inserts
a `user_recent_items` row in one transaction).

### Service Decoupling via Domain Events (SOLID: Dependency Inversion)

Catalog services (`AlgorithmService`, `ProblemService`,
`DataStructureService`) **must not** import or call
`ProgressService`. Instead, they emit a domain event:

``` python
@dataclass(frozen=True)
class ItemViewedEvent:
    user_id: UUID
    item_type: str          # 'algorithm' | 'data_structure' | 'problem'
    item_id: UUID
    viewed_at: datetime
```

The event is dispatched in-process via a simple handler registry. The
`ProgressService.record_view` handler subscribes to `ItemViewedEvent`.

``` python
# AlgorithmService.get_by_slug
async def get_by_slug(self, slug: str, user_id: UUID | None = None):
    detail = await self._repo.get_by_slug(slug)
    if user_id is not None:
        await self._events.dispatch(
            ItemViewedEvent(user_id=user_id, item_type="algorithm",
                            item_id=detail.id, viewed_at=utcnow())
        )
    return detail
```

Benefits:

- `AlgorithmService` has no knowledge of `ProgressService`.
- New side effects (analytics, recommendations) subscribe to the same
  event without modifying catalog services (Open/Closed).
- The handler runs in the same transaction if dispatched within an
  explicit `transactional()` context, or in its own transaction if
  fired after commit (current default: post-commit, best-effort).

### Dashboard Composition (SOLID: Single Responsibility + DI)

`DashboardService` is an **orchestrator only**. Business rules live
in calculator classes that are injected via protocols.

``` python
class ReadinessCalculatorProtocol(Protocol):
    async def compute(self, user_id: UUID) -> int: ...

class SkillMapperProtocol(Protocol):
    async def compute(self, user_id: UUID) -> list[SkillMetric]: ...

class FocusAreaSelectorProtocol(Protocol):
    async def select(self, user_id: UUID) -> list[FocusArea]: ...

class StreakCalculatorProtocol(Protocol):
    async def compute(self, user_id: UUID) -> int: ...

class DashboardService:
    def __init__(
        self,
        readiness: ReadinessCalculatorProtocol,
        skill_mapper: SkillMapperProtocol,
        focus_selector: FocusAreaSelectorProtocol,
        streak: StreakCalculatorProtocol,
        progress_overview_fetcher: Callable[[UUID], Awaitable[ProgressOverview]],
    ):
        self._readiness = readiness
        self._skill = skill_mapper
        self._focus = focus_selector
        self._streak = streak
        self._overview = progress_overview_fetcher

    async def summary(self, user_id: UUID) -> DashboardSummary:
        overview, readiness, skills, focus, streak = await asyncio.gather(
            self._overview(user_id),
            self._readiness.compute(user_id),
            self._skill.compute(user_id),
            self._focus.select(user_id),
            self._streak.compute(user_id),
        )
        return DashboardSummary(
            algorithms_learned=overview.algorithms.completed,
            algorithms_total=overview.algorithms.total,
            problems_solved=overview.problems.completed,
            interview_readiness=readiness,
            skill_mapping=skills,
            focus_areas=focus,
            current_streak=streak,
            activity=await self._activity_fetcher(user_id),
            recently_viewed=await self._recent_fetcher(user_id),
        )
```

Each calculator:

- Has **one reason to change** (the formula).
- Is **independently testable** with a fake `user_id`.
- Can be **swapped** (e.g., an ML-based readiness model) without
  touching `DashboardService`.

### Calculator Module Layout

``` text
src/modules/dashboard/
├── service.py                 # DashboardService orchestrator only
├── calculators/
│   ├── __init__.py
│   ├── readiness.py           # ReadinessCalculator
│   ├── skill_mapper.py        # SkillMapper
│   ├── focus_selector.py      # FocusAreaSelector
│   └── streak.py              # StreakCalculator
└── dependencies.py            # FastAPI wiring + composition root
```

### Error Handling

Domain exceptions raised by services:

``` text
NotFoundError        → 404
ConflictError        → 409
AuthenticationError  → 401
AuthorizationError   → 403
ValidationError      → 422
RateLimitError       → 429
```

A central exception handler maps them to:

``` json
{ "error": { "code": "ALGORITHM_NOT_FOUND", "message": "...", "details": {} } }
```

## 7. API Design

Base path: `/api/v1`. Versioning strategy: breaking changes → `/api/v2`;
additive changes stay on current version.

``` text
# Auth
POST   /auth/register
POST   /auth/login
POST   /auth/logout
GET    /auth/me
POST   /auth/refresh

# Algorithms
GET    /algorithms
GET    /algorithms/{slug}
GET    /algorithms/categories

# Data Structures
GET    /data-structures
GET    /data-structures/{slug}

# Problems
GET    /problems
GET    /problems/{slug}
GET    /problems/{slug}/topics
GET    /problems/{slug}/companies

# Progress (auth)
GET    /progress
GET    /progress/algorithms
GET    /progress/problems
POST   /progress/algorithms/{algorithm_id}
POST   /progress/problems/{problem_id}

# Dashboard (auth)
GET    /dashboard

# Roadmap
GET    /roadmap

# Ops
GET    /health          # liveness, no DB
GET    /health/ready    # readiness, checks DB
```

### Filtering & Pagination

-   Query params are parsed at the router into typed `*Filters` dataclasses.
-   Repositories accept `*Filters`, not raw query strings.
-   Pagination envelope:

``` json
{ "items": [...], "page": 1, "page_size": 20, "total": 42, "total_pages": 3 }
```

### Caching

``` text
GET /algorithms, /algorithms/{slug}     ETag on updated_at, Cache-Control: public, max-age=300
GET /algorithms/categories             public, max-age=3600
GET /data-structures                    public, max-age=300
GET /problems, /problems/{slug}         private/public by field, max-age=300
GET /roadmap                            public, max-age=3600
GET /dashboard, /progress/*             private, no-store
```

### Rate Limits

``` text
POST /auth/register     5 / hour / IP
POST /auth/login        10 / 10 min / IP      lock 15 min after 5 fails
POST /auth/refresh      60 / hour / user
POST /progress/*        120 / min / user
GET  *                  600 / min / user
```

## 8. Authentication Architecture

``` text
HTTP-only secure cookies
        ↓
FastAPI auth dependency
        ↓
CurrentUser
        ↓
Protected service
```

-   Passwords: Argon2id.
-   Access token: HTTP-only `Secure` `SameSite=Lax`, 15 min TTL.
-   Refresh token: HTTP-only `Secure` `SameSite=Strict`, 7 day TTL,
    single-use rotation.
-   CORS: `Allow-Credentials: true`, origin from env (never `*`).
-   Never log tokens, hashes, cookies, or passwords.
-   Dependencies: `get_current_user()`, `require_current_user()`,
    `require_role(role)`.

## 9. Dashboard as a Projection

There is **no** `dashboard` table. `DashboardService.summary` aggregates
`user_algorithm_progress`, `user_problem_progress`,
`user_recent_items`, and progress activity over the last 30 days.

``` json
{
  "algorithms_learned": 18, "algorithms_total": 42,
  "problems_solved": 27,    "interview_readiness": 68,
  "current_streak": 7,
  "activity": [...], "skill_mapping": [...], "focus_areas": [...],
  "recently_viewed": [...]
}
```

`interview_readiness`, `skill_mapping`, and `focus_areas` are computed,
not stored. Each compute method is independently testable.

## 10. Algorithm Execution Boundary

The backend stores metadata, complexity, and educational source code.
It does **not** run user code. The frontend owns deterministic
visualization execution via its algorithm registry.

If server-side execution is added later, it must be a separate
sandboxed service, not part of the main FastAPI process.

## 11. Observability

-   Structured logs (structlog JSON): `timestamp, level, request_id,
    route, method, status, duration_ms, user_id, event`.
-   `X-Request-ID` header on every response; bound via `contextvars`.
-   Optional OpenTelemetry spans for HTTP, DB, slow services.
-   Optional Prometheus `/metrics` (off by default).
-   Optional Sentry with `before_send` scrubbing for sensitive fields.

## 12. Deployment & CI

-   Multi-stage `Dockerfile`; runtime as non-root user.
-   `compose.yml` for local: `api` + `db` (+ optional `mailhog`).
-   GitHub Actions pipeline:

``` text
lint (ruff check, ruff format --check)
typecheck (mypy src/)
test (pytest --cov=src --cov-fail-under=80)
migration-verify (alembic upgrade head against ephemeral pg)
build (docker build)
```

-   Production: container behind reverse proxy terminating TLS,
    managed PostgreSQL with encrypted backups, secrets from a secret
    manager, never committed.

## 13. Phase Roadmap

``` text
Phase 1 — Foundation
  • project scaffold, settings, logging, error mapping
  • PostgreSQL + asyncpg + SQLAlchemy 2 async engine
  • Alembic initialized, base migration (users)
  • /health endpoint
  • local compose (api + db)

Phase 2 — Auth & Users
  • User model, register/login/logout/refresh/me
  • Argon2id, HTTP-only cookies
  • Rate limits on auth endpoints
  • Auth service + tests

Phase 3 — Catalog
  • categories, topics, algorithms, data_structures, algorithm_topics
  • algorithm_code_versions + seed
  • public read endpoints with pagination + filters
  • ETag support

Phase 4 — Problems
  • problems, problem_topics, companies, problem_companies
  • filter endpoints (topic/company/difficulty/status)
  • seed ~50 canonical problems

Phase 5 — Progress & Dashboard
  • user_algorithm_progress, user_problem_progress, user_recent_items
  • progress endpoints with transactional updates
  • DashboardService aggregations
  • /roadmap endpoints

Phase 6 — Hardening
  • cache headers, rate limits, request ID, structured logs
  • OpenTelemetry + Prometheus (optional)
  • Docker + CI pipeline
  • dashboard query performance pass
```

Each phase ends with a working vertical slice (API → service → repo →
DB → tests).

## 14. Module Boundaries — What Each Module Owns

| Module            | Owns                                                       | Does NOT Own                              |
|-------------------|------------------------------------------------------------|-------------------------------------------|
| auth              | session, token issuance, password hashing                  | user profile fields                       |
| users             | profile fields, account deletion                           | auth tokens                               |
| algorithms        | catalog read, metadata, code versions, view tracking call  | progress writes                           |
| data_structures   | catalog read                                               | progress                                  |
| problems          | catalog read, filter facets                                | progress writes                           |
| progress          | user_algorithm_progress, user_problem_progress, recent     | catalog data                              |
| dashboard         | aggregations and projections                               | persistence of derived data               |
| roadmap           | stages + items read                                        | user progress on items                    |

## 15. SOLID Application Map

``` text
Single Responsibility   router=HTTP, service=rules, repo=persistence, schema=IO
Open/Closed             add a new category without touching service code
Liskov                  repository protocols interchangeable in tests
Interface Segregation   AlgorithmRepository ≠ ProgressRepository
Dependency Inversion    services depend on repo protocols
```

## 16. DRY Anchors (Do Not Duplicate)

-   Pagination math (`shared/pagination.py`)
-   Auth extraction (`get_current_user`)
-   Password hashing (`core/security.py`)
-   Error → HTTP mapping (`core/exceptions.py`)
-   Filter objects (one per entity)
-   Timestamp handling (`core/time.py` if needed)
-   Dashboard calculations (`DashboardService`)
-   Query fragments (reusable SQL expressions in repositories)

## 17. Testing Strategy

``` text
Unit           services, domain rules, filter construction,
               dashboard calculations, security utils
Repository     real PostgreSQL test DB; constraints, joins,
               pagination, indexes
API            FastAPI TestClient/httpx; auth flows, list, detail,
               progress, dashboard, roadmap
Integration    API → Service → Repo → PostgreSQL for critical paths
```

Test DB is a real PostgreSQL container; SQLite is not a substitute for
PG-specific behavior.

## 18. Security Checklist

``` text
✓ Argon2id password hashing
✓ HTTP-only Secure cookies; SameSite=Lax/Strict as appropriate
✓ CORS restricted to configured origins; Allow-Credentials set
✓ Pydantic validation on every request body and query
✓ Parameterized SQL via SQLAlchemy (no string interpolation)
✓ Rate limits on auth + write endpoints
✓ No secrets in repo (.env ignored, .env.example committed)
✓ No logging of passwords, hashes, tokens, cookies
✓ No execution of user-submitted code
✓ Internal stack traces never returned to clients
✓ Progress updates idempotent on re-post
```

## 19. Definition of Done — Backend

``` text
□ FastAPI starts; PostgreSQL connection works
□ Alembic migrations apply and (where practical) downgrade
□ Models are normalized; no JSON blobs for relational data
□ API schemas are typed; ORM models never returned directly
□ Routers contain no business logic
□ Services contain business rules + transactions
□ Repositories contain persistence only
□ Pagination envelope is consistent across list endpoints
□ Filters are typed; routers parse, repositories execute
□ Authentication is Argon2id + HTTP-only cookies
□ Progress updates are transactional (progress + recent together)
□ Dashboard aggregation is correct and tested
□ Rate limits active on auth and write endpoints
□ Cache headers set per the policy table
□ ETag works on /algorithms and /algorithms/{slug}
□ /health and /health/ready endpoints behave correctly
□ All migrations tested in CI
□ Tests pass; coverage ≥ 80% on src/
□ Lint + format pass
□ No secrets committed
□ Frontend API contract documented (this file + /openapi.json)
```

## 20. Open Questions / Future Decisions

These are deferred but documented for future phases:

-   Email verification flow (requires SMTP / SES integration).
-   OAuth providers (Google, GitHub).
-   Admin/editor roles (model exists in plan; no UI yet).
-   Comments / discussions on algorithms.
-   Bookmarks separate from `user_recent_items`.
-   Search backend: PostgreSQL `tsvector` first; consider Meilisearch
    only when volume demands it.
