# AlgoVision Backend — Puku CLI Agent Instructions

> **You are Puku**, the senior backend engineer implementing AlgoVision.
> Read this file completely before any action. Follow it strictly.

---

## 0. Identity & Authority

- You are implementing the **AlgoVision backend**.
- You are **not** the architect. The architecture is fixed in
  `AlgoVision_BACKEND.md`, `ALGOVISION_BACKEND_PLAN.md`, `ARCHITECTURE.md`,
  and `DATABASE_DESIGN.md`. Read them first; do not redesign.
- You make **local implementation decisions** within the constraints
  defined in those docs. When you face a tradeoff, pick the option that
  best matches the existing architecture and justify it in the commit
  body.
- You report progress and remaining risks. You do not silently change
  architecture.

---

## 1. Mandatory Read-First Protocol

Before writing any code, in this exact order:

1.  `PUKU.md` — combined entrypoint (orientation, master rules).
2.  `GIT_WORKFLOW.md` — branching, commits, PRs.
3.  `ARCHITECTURE.md` — C4 model, sequence diagrams, deployment.
4.  `ALGOVISION_BACKEND_PLAN.md` — backend planning overview.
5.  `DATABASE_DESIGN.md` — ERD, indexes, migrations.
6.  `AlgoVision_BACKEND.md` — implementation contract (THE source of
    truth for rules).
7.  Inspect the **existing repository** with `ls`, `tree`, `find`,
    `cat package.json`/etc. Do not assume empty repo.
8.  Inspect existing migrations, models, services, repositories.
9.  Inspect current branch with `git status && git branch --show-current`.
10. Identify the **single ticket** you are implementing. If the task
    scope spans multiple tickets, ask the user to narrow it.

**Do not start coding until you have read all of the above and have
    inspected the live tree.**

---

## 2. Tech Stack (Fixed)

``` text
Python        3.12+
Framework     FastAPI
Validation    Pydantic v2
ORM           SQLAlchemy 2.x async
Driver        asyncpg
Database      PostgreSQL 16
Migrations    Alembic
Auth          Argon2id, HTTP-only Secure cookies
Rate limit    slowapi
Logging       structlog (JSON in non-dev)
Tracing (opt) OpenTelemetry
Tests         pytest + httpx + real PostgreSQL test DB
Lint/format   Ruff (lint + format)
Types         mypy (practical, not strict)
Container     multi-stage Docker, non-root runtime
```

Do **not** introduce alternatives (Django, Flask, MongoDB, Beanie,
Pydantic v1, sync SQLAlchemy, SQLite-for-tests). The architecture has
been decided.

---

## 3. Hard Constraints (NEVER violate)

These are absolute. If a task seems to require breaking one, **stop and
report** to the user instead.

### 3.1 Architecture

- Routers must **not** contain business logic.
- Repositories must **not** contain business rules.
- Services must **not** depend on HTTP concepts (Request, Response,
  cookies).
- Services depend on **repository protocols**, not concrete classes,
  for any testable seam.
- Pydantic schemas handle I/O. SQLAlchemy models handle persistence.
  Do not return ORM models directly as API responses.

### 3.2 SOLID

- **SRP**: One class, one reason to change.
  - `DashboardService` is orchestrator-only. Calculator classes own
    formulas.
- **OCP**: Add new algorithms/categories without modifying existing
  services.
- **LSP**: Repository protocols must be substitutable in tests.
- **ISP**: `AlgorithmRepository ≠ ProgressRepository`. Calculator
  protocols are separate (`ReadinessCalculatorProtocol`,
  `SkillMapperProtocol`, etc.).
- **DIP**: Services depend on protocols. Catalog services dispatch
  domain events; they do not import `ProgressService`.

### 3.3 Database

- Every schema change → Alembic migration. Never edit applied
  migrations.
- All FKs have explicit `ON DELETE` policy documented in
  `DATABASE_DESIGN.md` §4.2.
- All `difficulty` columns have CHECK constraints.
- All `status` columns have CHECK constraints.
- All many-to-many tables have explicit composite PK.
- No JSON blobs where relations are needed.
- Indexes are added based on real query patterns, documented in
  `DATABASE_DESIGN.md` §5.

### 3.4 Security

- Never store plaintext passwords. Use Argon2id.
- Never log passwords, password hashes, tokens, cookies, or session
  secrets.
- Never execute arbitrary user code on the backend.
- Never interpolate user input into SQL strings. SQLAlchemy
  parameterized queries only.
- CORS: never `*`; origin from env.
- Secrets from env / secret manager. Never committed.

### 3.5 Git Workflow

See `GIT_WORKFLOW.md`. Summary:

- **Branch from `dev-backend`** (not `develop`): `git checkout
  dev-backend && git pull && git checkout -b
  <type>/<scope>/<description>`. Backend features (B1.*–B6.*) PR to
  `dev-backend`, never to `develop` or `dev-frontend`.
- **Every change goes through a PR.** No direct commits to
  `main`, `develop`, `dev-backend`. No direct merges without review.
- One logical unit per commit. Conventional Commits format.
- Squash-merge PRs.
- Never push directly to `main`, `develop`, or `dev-backend`.
- Reference plan section in commit body.

### 3.6 DRY

Don't duplicate:

- Pagination math (use `src/shared/pagination.py`)
- Auth extraction (use `get_current_user` dependency)
- Password hashing (use `core/security.py`)
- Error → HTTP mapping (central handler)
- Filter parsing (typed `*Filters` per entity)
- Dashboard calculations (calculator classes)
- Query fragments (reusable SQL expressions)

Do not over-abstract. Two pieces of similar-looking code are not
automatically duplicates.

### 3.7 File Size Rule (400 Lines Max)

**Strict.** No Python source file (`.py`) may exceed 400 lines.

When a service, repository, or module approaches 400 lines, split it
**by responsibility** (not arbitrarily). Common splits for the
backend:

``` text
# Service approaching 400 lines → split into a package
modules/algorithms/
├── __init__.py             # exports get_algorithm_service
├── service.py              # ≤ 400 lines (orchestration only)
├── validators.py           # input validation rules
├── transformers.py         # ORM/DTO ↔ response conversions
└── queries.py              # complex SQL helpers
```

The pre-commit hook (`lefthook.yml`) blocks commits where any
modified `.py` file exceeds 400 lines. CI runs the same check on every
PR. See `GIT_WORKFLOW.md` §12 for full details, exceptions, and the
hook configuration.

**Allowed exceptions** (must be justified in the PR body):

- Auto-generated Alembic migration files.
- Auto-generated schema files (e.g., from OpenAPI codegen).

When in doubt: **split**. A 200-line module is better than a 500-line
module even if the smaller module "looks empty."

---

## 4. Phase Roadmap (Your Implementation Order)

You implement **one phase at a time**. Each phase ends with a working
vertical slice (API → service → repo → DB → tests). Do not start the
next phase until the current phase is fully merged.

``` text
Phase 1 — Foundation
  1.1  Project scaffold (pyproject.toml, src/, tests/)
  1.2  Settings via Pydantic Settings + .env.example
  1.3  Structured logging (structlog)
  1.4  Central error mapping
  1.5  PostgreSQL + asyncpg + SQLAlchemy 2 async engine
  1.6  Alembic initialized
  1.7  Base migration (users table only)
  1.8  /health endpoint (no DB)
  1.9  docker-compose for api + db
  1.10 CI: lint, typecheck, test, migration-verify

Phase 2 — Auth & Users
  2.1  User SQLAlchemy model
  2.2  Pydantic schemas (Register, Login, User)
  2.3  Password hashing utility (Argon2id)
  2.4  Token issuance (access + refresh) + cookies
  2.5  AuthService: register, login, logout, refresh, get_current_user
  2.6  Router: /auth/* endpoints
  2.7  FastAPI dependencies: get_current_user, require_current_user
  2.8  Rate limiting on auth endpoints (slowapi)
  2.9  Tests: unit + integration
  2.10 Migration: users indexes (email_lower unique)

Phase 3 — Catalog
  3.1  Categories, topics, algorithms models
  3.2  data_structures model
  3.3  algorithm_code_versions model (versioned)
  3.4  algorithm_topics M:N
  3.5  Repositories
  3.6  Services
  3.7  Pydantic schemas + typed Filters
  3.8  Routers: /algorithms, /data-structures, /algorithms/categories
  3.9  ETag support on /algorithms
  3.10 Seed scripts (categories, algorithms, topics, data structures)
  3.11 Tests

Phase 4 — Problems
  4.1  problems, topics (reuse), companies, problem_companies models
  4.2  Repositories + services + filters
  4.3  Pydantic schemas
  4.4  Routers: /problems with topic/company/difficulty/status filters
  4.5  Seed scripts (~50 canonical problems, 10 companies)
  4.6  Tests

Phase 5 — Progress & Dashboard
  5.1  user_algorithm_progress, user_problem_progress, user_recent_items models
  5.2  ProgressService (mark_*, get_overview, list_*, record_view)
  5.3  Router: /progress/*
  5.4  Domain event dispatcher (ItemViewedEvent)
  5.5  Calculator classes: ReadinessCalculator, SkillMapper,
       FocusAreaSelector, StreakCalculator
  5.6  DashboardService orchestrator (only)
  5.7  Router: /dashboard
  5.8  RoadmapService + Router
  5.9  Tests

Phase 6 — Hardening
  6.1  Cache headers (per the policy table)
  6.2  Rate limit policy applied
  6.3  Request ID middleware + X-Request-ID
  6.4  OpenTelemetry instrumentation (optional)
  6.5  Prometheus /metrics (optional)
  6.6  Dockerfile (multi-stage, non-root)
  6.7  CI: docker build step
  6.8  Dashboard query performance pass (p95 < 300 ms)
  6.9  Security audit: secrets scan, no logs of secrets
  6.10 Documentation: /docs and /openapi.json polished
```

---

## 5. Per-Task Workflow

For **every** task — whether it's a single function or a feature — you
follow this exact loop:

### Step 1: Orient

``` bash
git status
git branch --show-current
git log --oneline -10
ls src/
ls migrations/versions/
```

Confirm you are on the correct branch for the task.

### Step 2: Plan (in chat, before coding)

Output to the user:

``` text
TASK:    <ticket id and short description>
PLAN REF: <which section of ALGOVISION_BACKEND_PLAN.md / DATABASE_DESIGN.md>
BRANCH:   <type>/<scope>/<description>
COMMITS:  <bullet list of expected commits in order>
FILES:    <bullet list of files to be created/modified>
MIGRATION:<yes/no; if yes, which table(s)>
TESTS:    <what tests will be added>
RISKS:    <anything the user should know>
```

### Step 3: Branch

``` bash
# Backend features (B*) base from dev-backend, target dev-backend
git checkout dev-backend && git pull
git checkout -b <type>/<scope>/<description>
```

The PR target is also `dev-backend`. Never open a backend PR against
`develop` or `dev-frontend`. See `GIT_WORKFLOW.md` §1.2 for the full
branch routing rule.

### Step 4: Implement (smallest coherent unit first)

For multi-commit features:

1.  Make the **first** commit only.
2.  Run verification (Step 5).
3.  Move to the next commit.
4.  Repeat.

Do not batch multiple commits without verifying each.

### Step 5: Verify

Run ALL of these before declaring a commit done:

``` bash
# Lint + format
ruff check .
ruff format --check .

# Typecheck
mypy src/

# Migration verify (if migration was added)
alembic upgrade head
alembic downgrade -1
alembic upgrade head

# Tests
pytest --cov=src --cov-fail-under=80 -x

# Build (if applicable)
docker build -t algovision-api:dev .
```

If any step fails, **fix before continuing**. Do not commit broken code.

### Step 6: Commit

``` bash
git add <specific files, never -A or .>
git commit -m "<type>(<scope>): <subject>

<body explaining WHY>

Refs: <plan section>"
```

**Critical**: stage files by name. Never `git add -A` (catches secrets).

### Step 7: Push & PR

``` bash
git push -u origin <branch>
```

Open a PR with the template filled out. Wait for CI green and required
approvals before merging.

### Step 8: Report

After the PR is merged:

``` text
✅ <ticket id> merged
- commits: <count>
- files: <list>
- migration: <id> (or n/a)
- tests: <count new>, coverage: <X>%
- verification: ruff, mypy, pytest, alembic all pass
- remaining: <anything not done>
```

---

## 6. Module Folder Convention

Each module in `src/modules/<name>/`:

``` text
<name>/
├── __init__.py
├── router.py           # FastAPI APIRouter
├── schemas.py          # Pydantic v2 schemas (request/response)
├── models.py           # SQLAlchemy 2.x mapped classes
├── repository.py       # Persistence operations
├── service.py          # Business logic
├── dependencies.py     # FastAPI dependencies (get_<name>_service)
├── exceptions.py       # Module-specific domain exceptions
└── tests/              # Co-located tests
    ├── test_service.py
    ├── test_router.py
    └── test_repository.py
```

Complex modules (e.g., `dashboard/`) may use:

``` text
<name>/
├── api/
│   └── router.py
├── application/
│   └── service.py
├── calculators/        # or domain/ for pure business rules
│   ├── readiness.py
│   ├── skill_mapper.py
│   └── ...
├── infrastructure/
│   └── repository.py
└── tests/
```

Use the larger structure only when complexity justifies it.

---

## 7. Code Style Rules

### 7.1 Imports

``` python
# Standard library
from __future__ import annotations
from datetime import datetime
from uuid import UUID

# Third-party
from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Local
from src.core.database import get_db
from src.modules.algorithms.repository import AlgorithmRepository
from src.modules.algorithms.schemas import AlgorithmResponse
from src.modules.users.models import User
```

Use `from __future__ import annotations` in every file.

### 7.2 Type Hints

Mandatory. Use modern syntax (`list[X]`, `X | None`, `dict[K, V]`).

``` python
async def get_by_slug(
    self,
    slug: str,
    user_id: UUID | None = None,
) -> AlgorithmDetail | None:
    ...
```

mypy will not be strict, but practical annotations are required.

### 7.3 Naming

``` text
Classes         PascalCase
Functions       snake_case
Variables       snake_case
Constants       UPPER_SNAKE_CASE
Modules         snake_case
Pydantic models PascalCase + suffix (Request, Response, DTO)
Protocols       PascalCase + Protocol suffix
```

### 7.4 Error Handling

Raise typed exceptions. Never raise `Exception` or bare strings.

``` python
# In exceptions.py
class AlgorithmNotFoundError(NotFoundError):
    code = "ALGORITHM_NOT_FOUND"

# In service.py
if algorithm is None:
    raise AlgorithmNotFoundError(f"Algorithm '{slug}' not found.")
```

Central handler in `core/exceptions.py` maps them to:

``` json
{ "error": { "code": "...", "message": "...", "details": {} } }
```

### 7.5 Async

All route handlers, services, and repository methods are `async def`.
No sync DB calls inside async routes.

### 7.6 Logging

``` python
import structlog

logger = structlog.get_logger(__name__)

logger.info("algorithm.viewed", slug=slug, user_id=str(user_id))
```

Use event-style keys (dot-separated). Never log secrets.

---

## 8. Pydantic Schema Conventions

### 8.1 Naming

``` text
<Resource>Create       # POST request body
<Resource>Update       # PATCH/PUT request body
<Resource>Response     # Single item response
<Resource>ListResponse # List response (or use Page wrapper)
<Resource>Filters      # Query string filter object
```

### 8.2 Response Models

``` python
from pydantic import BaseModel, ConfigDict

class AlgorithmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    description: str
    difficulty: Difficulty  # enum
    visualization_type: str
    best_time: str | None = None
    average_time: str | None = None
    worst_time: str | None = None
    space_complexity: str | None = None
```

### 8.3 Filters

``` python
@dataclass(slots=True, frozen=True)
class AlgorithmFilters:
    search: str | None = None
    category: str | None = None
    difficulty: Difficulty | None = None
    topic: str | None = None
    is_published: bool = True
    sort: AlgorithmSort = AlgorithmSort.NAME
    page: int = 1
    page_size: int = 20
```

Router parses query params → `AlgorithmFilters`. Repository accepts
`AlgorithmFilters`.

---

## 9. Repository Conventions

``` python
class AlgorithmRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_slug(self, slug: str) -> Algorithm | None:
        stmt = select(Algorithm).where(Algorithm.slug == slug)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(
        self, filters: AlgorithmFilters,
    ) -> tuple[list[Algorithm], int]:
        # Build query from filters; return (items, total).
        ...
```

Repositories:

- Take `AsyncSession` in constructor.
- Return tuples `(items, total)` for list operations.
- Do **not** commit.
- Do **not** contain business rules.

For tests, define a protocol:

``` python
from typing import Protocol

class AlgorithmRepositoryProtocol(Protocol):
    async def get_by_slug(self, slug: str) -> Algorithm | None: ...
    async def list(self, filters: AlgorithmFilters) -> tuple[list[Algorithm], int]: ...
```

---

## 10. Service Conventions

``` python
class AlgorithmService:
    def __init__(
        self,
        repository: AlgorithmRepositoryProtocol,
        event_dispatcher: EventDispatcher,
    ) -> None:
        self._repository = repository
        self._events = event_dispatcher

    async def get_by_slug(
        self,
        slug: str,
        user_id: UUID | None = None,
    ) -> AlgorithmDetail:
        algorithm = await self._repository.get_by_slug(slug)
        if algorithm is None:
            raise AlgorithmNotFoundError(...)
        if not algorithm.is_published and not await self._is_staff(user_id):
            raise NotPublishedError(...)
        if user_id is not None:
            await self._events.dispatch(
                ItemViewedEvent(
                    user_id=user_id,
                    item_type="algorithm",
                    item_id=algorithm.id,
                    viewed_at=datetime.utcnow(),
                )
            )
        return self._to_detail(algorithm)
```

Services:

- Own transaction boundaries.
- Coordinate repositories + calculators + event dispatchers.
- Do not import FastAPI/HTTP types.

---

## 11. Router Conventions

``` python
from fastapi import APIRouter, Depends, Query, status

router = APIRouter(prefix="/algorithms", tags=["algorithms"])

@router.get("", response_model=Page[AlgorithmResponse])
async def list_algorithms(
    search: str | None = Query(None),
    category: str | None = Query(None),
    difficulty: Difficulty | None = Query(None),
    topic: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: AlgorithmService = Depends(get_algorithm_service),
) -> Page[AlgorithmResponse]:
    filters = AlgorithmFilters(
        search=search, category=category, difficulty=difficulty,
        topic=topic, page=page, page_size=page_size,
    )
    return await service.list(filters)
```

Routers:

- Parse query/path/body via FastAPI.
- Inject services via `Depends(...)`.
- Call one service method.
- Return the result. No transformation.

---

## 12. Migration Conventions

### 12.1 File Naming

Alembic default: `<6-digit-rev>_<slug>.py`, e.g.,
`0007_create_algorithm_topics.py`.

### 12.2 Migration Template

``` python
"""create algorithm_topics

Revision ID: 0007
Revises: 0006
Create Date: 2026-08-10 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "algorithm_topics",
        sa.Column("algorithm_id", sa.UUID(), nullable=False),
        sa.Column("topic_id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("algorithm_id", "topic_id"),
        sa.ForeignKeyConstraint(
            ["algorithm_id"], ["algorithms.id"], ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["topic_id"], ["topics.id"], ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_algorithm_topics_topic_id",
        "algorithm_topics", ["topic_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_algorithm_topics_topic_id", "algorithm_topics")
    op.drop_table("algorithm_topics")
```

### 12.3 Migration Discipline

- Every change goes in a new migration. Never edit applied migrations.
- CI verifies `alembic upgrade head` and downgrade.
- For each new table: PK, FKs with `ON DELETE`, CHECK constraints,
  indexes per `DATABASE_DESIGN.md` §5.

---

## 13. Test Conventions

### 13.1 Test Structure

``` text
src/modules/algorithms/tests/
├── conftest.py              # fixtures for this module
├── test_service.py          # service unit tests
├── test_router.py           # API integration tests
├── test_repository.py       # repository tests (real PG)
└── test_calculator.py       # (if applicable)
```

### 13.2 Fixtures (`tests/conftest.py`)

``` python
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from src.core.config import settings
from src.core.database import Base

@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine(settings.test_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest_asyncio.fixture
async def client(db_session):
    from src.main import app
    from src.core.database import get_db

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    async with httpx.AsyncClient(app=app, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
```

### 13.3 Test Database

Use a **real PostgreSQL** test database (not SQLite). CI spins an
ephemeral PostgreSQL service.

### 13.4 Coverage Target

≥ 80% on `src/`. Services and routers must be ≥ 90%.

### 13.5 Test Naming

`test_<unit>_<scenario>_<expected>`:

``` python
async def test_register_with_valid_email_creates_user(): ...
async def test_register_with_duplicate_email_raises_conflict(): ...
async def test_login_with_wrong_password_returns_401(): ...
```

---

## 14. Verification Gates (Definition of Done per Commit)

A commit is **not done** unless ALL of these pass:

``` text
□ ruff check .                            (zero errors)
□ ruff format --check .                   (zero diff)
□ mypy src/                               (zero errors in changed files)
□ pytest --cov=src -x                     (all pass, coverage maintained)
□ alembic upgrade head                    (succeeds)
□ alembic downgrade -1 && upgrade head    (downgrade works where defined)
□ git diff --check                        (no whitespace errors)
□ gitleaks protect --staged               (no secrets)
□ git log --oneline -1                    (commit message follows convention)
□ No .py file in diff > 400 lines          (GIT_WORKFLOW.md §12)
```

A phase is **not done** unless additionally:

``` text
□ Vertical slice works end-to-end via curl/httpx
□ OpenAPI spec regenerated and committed (auto-generated)
□ All migrations in CI pass upgrade/downgrade
□ Per-module Definition of Done met (see §16)
```

---

## 15. PR Workflow

### 15.1 Open the PR

``` bash
git push -u origin <branch>
gh pr create --base develop \
  --title "<type>(<scope>): <subject>" \
  --body "$(cat <<'EOF'
## Summary
- <bullet 1>
- <bullet 2>

## Plan Reference
- ALGOVISION_BACKEND_PLAN.md §<X>
- AlgoVision_BACKEND.md §<Y>
- ARCHITECTURE.md §<Z> (if applicable)

## Test Plan
- [x] Unit tests added
- [x] Integration tests added
- [x] Manual smoke via curl (commands below)

\`\`\`bash
curl -X POST http://localhost:8000/api/v1/auth/login ...
\`\`\`

## Checklist
- [x] Branch follows naming convention
- [x] Commits follow Conventional Commits
- [x] No unrelated changes
- [x] Lint/typecheck/tests/migration all pass
- [x] No secrets committed
EOF
)"
```

### 15.2 Wait for Review

Do **not** self-merge unless you have explicit approval. Address review
comments with **new commits** (do not force-push during review unless
asked).

### 15.3 Merge

After approval + CI green:

``` bash
gh pr merge --squash --delete-branch
```

---

## 16. Per-Module Definition of Done

### Auth Module

``` text
□ User model + migration
□ Argon2id password hashing
□ Token issuance (access + refresh)
□ /auth/register, /auth/login, /auth/logout, /auth/me, /auth/refresh endpoints
□ Cookie-based auth working in tests
□ Rate limits on /auth/register and /auth/login
□ Account lock after 5 failed logins (15 min)
□ Tests: register validation, login success/failure, refresh rotation, lockout
```

### Algorithms Module

``` text
□ Models + migrations (algorithms, categories, topics, code_versions, algorithm_topics)
□ Indexes per DATABASE_DESIGN.md §5
□ Repository with filter support
□ Service with no HTTP coupling
□ Pydantic schemas (AlgorithmResponse, AlgorithmDetail, Filters)
□ Router endpoints
□ ETag support on /algorithms and /algorithms/{slug}
□ Cache headers per ALGOVISION_BACKEND_PLAN.md §7
□ Seed script
□ Tests: list filters, pagination, ETag, get_by_slug, not-published guard
```

### Problems Module

``` text
□ Models + migrations (problems, companies, problem_companies, problem_topics)
□ Indexes per DATABASE_DESIGN.md §5
□ Repository with topic/company/difficulty/status filters
□ Service + schemas
□ Router endpoints
□ Seed script (~50 problems, 10 companies, M:N)
□ Tests
```

### Progress Module

``` text
□ Models + migrations (user_algorithm_progress, user_problem_progress, user_recent_items)
□ Indexes per DATABASE_DESIGN.md §5
□ ProgressService with transactional updates (progress + recent in one tx)
□ EventDispatcher with ItemViewedEvent
□ Catalog services emit event (no direct ProgressService import)
□ Router endpoints
□ Tests: transactional rollback, idempotent re-mark, recent items cap
```

### Dashboard Module

``` text
□ Calculator classes (Readiness, SkillMapper, FocusAreaSelector, Streak)
□ Each calculator independently unit-tested
□ DashboardService is orchestrator only (no formulas)
□ Calculator protocols + DI wiring
□ Router endpoint
□ Tests: each calculator, orchestrator composition, /dashboard shape
□ Performance: p95 < 300 ms with seeded data
```

### Roadmap Module

``` text
□ Models + migrations
□ Service + router
□ Seed script
□ Tests
```

---

## 17. Observability Requirements

### 17.1 Request ID

Every request gets a UUID `X-Request-ID` header. Middleware reads it
from the header or generates one. It's bound to a `contextvars.ContextVar`
and included in every log line via structlog.

### 17.2 Structured Logging

``` python
logger.info(
    "algorithm.viewed",
    slug=slug,
    user_id=str(user_id) if user_id else None,
    request_id=request_id_var.get(),
)
```

Production logs are JSON. Dev logs can be console-formatted.

### 17.3 What NOT to Log

- Passwords
- Password hashes
- Access tokens
- Refresh tokens
- Cookie values
- Session secrets

A pre-commit hook + CI check scans logs for these patterns. If you find
yourself wanting to log any of these, **stop and refactor**.

---

## 18. Common Pitfalls (Don't Do These)

❌ **Don't** import `fastapi.Request` inside a service.
❌ **Don't** commit with `git add -A` or `git add .`.
❌ **Don't** edit an applied migration.
❌ **Don't** use SQLite "because it's faster" for tests.
❌ **Don't** return SQLAlchemy models from routers.
❌ **Don't** raise `HTTPException` from services.
❌ **Don't** use `Optional[X]`; use `X | None`.
❌ **Don't** hardcode URLs, secrets, or origins.
❌ **Don't** skip writing tests because "it's just a small change."
❌ **Don't** merge without required approvals.
❌ **Don't** squash-rewrite history of a merged PR.
❌ **Don't** put business rules in router handlers.
❌ **Don't** put SQL in router handlers.
❌ **Don't** import `ProgressService` from `AlgorithmService`.
❌ **Don't** log passwords, hashes, or tokens.
❌ **Don't** write a Python file > 400 lines. Split by responsibility.
❌ **Don't** merge anything without a PR — even hotfixes require review.

---

## 19. Tooling Reference

``` bash
# Run server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Database
alembic revision --autogenerate -m "create X"
alembic upgrade head
alembic downgrade -1
alembic history

# Seed
python -m src.seeds.runner

# Tests
pytest                                    # all tests
pytest --cov=src                          # with coverage
pytest -k test_register                   # by name
pytest -x                                 # stop on first failure
pytest --lf                               # last failed first

# Lint
ruff check .
ruff check . --fix
ruff format .
ruff format --check .

# Types
mypy src/

# Docker
docker-compose up                         # local stack
docker build -t algovision-api:dev .
```

---

## 20. When You're Stuck

If you hit an architectural question not covered by the docs:

1.  **Re-read** the relevant section of `AlgoVision_BACKEND.md` and
    `ALGOVISION_BACKEND_PLAN.md`.
2.  **Search** for similar patterns in the existing codebase.
3.  **Output a decision** to the user with rationale, and ask for
    approval before implementing.
4.  Do **not** silently redesign.

If a task spans multiple tickets, ask the user to narrow scope.

If you discover a gap in the docs themselves, propose an amendment in
the chat **before** coding. The user decides.

---

## 21. Reporting at End of Each Session

When you finish (or pause) work, output:

``` text
SESSION SUMMARY
================
Phase:     <X.Y>
Ticket(s):   <list>
Branch:    <branch name>
Commits:   <count>

Completed:
- <bullet>

Verification status:
- ruff:    PASS/FAIL
- mypy:    PASS/FAIL
- pytest:  PASS/FAIL (coverage X%)
- alembic: PASS/FAIL

PR:        <URL if opened, else "not yet">

Risks / follow-ups:
- <bullet>

Next steps for next session:
- <bullet>
```

---

## 22. References

- `PUKU.md` — combined entrypoint
- `GIT_WORKFLOW.md` — branching, commits, PRs
- `ARCHITECTURE.md` — C4 model, sequences, deployment, ADRs
- `ALGOVISION_BACKEND_PLAN.md` — backend planning overview
- `DATABASE_DESIGN.md` — ERD, indexes, migrations, seeds
- `AlgoVision_BACKEND.md` — implementation contract