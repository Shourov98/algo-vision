# AlgoVision Backend Architecture & CLI LLM Implementation Guide

## 1. Purpose

This document is the implementation contract for the **AlgoVision
backend**.

Build the backend using:

-   **Python 3.12+**
-   **FastAPI**
-   **Pydantic v2**
-   **SQLAlchemy 2.x**
-   **PostgreSQL**
-   **Alembic**
-   **asyncpg**
-   **pytest**
-   **httpx**
-   **Ruff**
-   **mypy** where practical

The backend provides:

-   authentication
-   user accounts
-   algorithm catalog
-   data structure catalog
-   interview problems
-   topics/categories
-   progress tracking
-   dashboard aggregation
-   roadmap data
-   recently viewed items
-   API contracts for the Next.js frontend

The backend must NOT become a monolithic "everything service".

------------------------------------------------------------------------

# 2. Backend Principle

The backend should follow:

``` text
HTTP
 ↓
API Router
 ↓
Application Service
 ↓
Domain
 ↓
Repository
 ↓
SQLAlchemy
 ↓
PostgreSQL
```

Do not allow API routers to contain business logic.

Do not allow SQL queries to leak into route handlers.

Do not allow Pydantic schemas to become domain models.

------------------------------------------------------------------------

# 3. Architecture Style

Use a modular layered architecture.

Recommended:

``` text
src/
├── main.py
│
├── core/
│   ├── config.py
│   ├── security.py
│   ├── database.py
│   ├── logging.py
│   └── exceptions.py
│
├── modules/
│   ├── auth/
│   ├── users/
│   ├── algorithms/
│   ├── data_structures/
│   ├── problems/
│   ├── progress/
│   ├── dashboard/
│   └── roadmap/
│
├── shared/
│   ├── pagination.py
│   ├── responses.py
│   └── enums.py
│
└── migrations/
```

Each module should contain:

``` text
module/
├── router.py
├── schemas.py
├── models.py
├── repository.py
├── service.py
├── dependencies.py
└── exceptions.py
```

For complex modules:

``` text
module/
├── api/
├── application/
├── domain/
├── infrastructure/
└── tests/
```

Use the larger structure only when complexity justifies it.

------------------------------------------------------------------------

# 4. Responsibilities

## Router

Responsible only for:

-   HTTP method
-   path parameters
-   request validation
-   dependency injection
-   calling application service
-   response serialization

Bad:

``` python
@router.get("/algorithms")
async def get_algorithms(db):
    result = await db.execute(...)
    ...
```

Good:

``` python
@router.get("/algorithms")
async def get_algorithms(
    service: AlgorithmService = Depends(get_algorithm_service),
):
    return await service.list_algorithms()
```

------------------------------------------------------------------------

# 5. Service Layer

Services contain application/business orchestration.

Example:

``` python
class ProgressService:
    async def mark_algorithm_completed(
        self,
        user_id: UUID,
        algorithm_id: UUID,
    ) -> Progress:
        ...
```

Services may coordinate:

-   repositories
-   domain rules
-   transactions
-   events

Services should not know about HTTP.

------------------------------------------------------------------------

# 6. Repository Layer

Repositories own persistence operations.

Example:

``` python
class AlgorithmRepository:
    async def get_by_slug(self, slug: str) -> Algorithm | None:
        ...

    async def list(
        self,
        filters: AlgorithmFilters,
    ) -> list[Algorithm]:
        ...
```

Do not put business rules inside repositories.

Repositories should not return API-specific DTOs.

------------------------------------------------------------------------

# 7. Database

Use PostgreSQL.

Use SQLAlchemy 2.x async ORM.

Use:

``` text
asyncpg
```

for PostgreSQL connectivity.

Use Alembic for all schema migrations.

Never manually modify production schema.

------------------------------------------------------------------------

# 8. Database Principles

Use normalized relational design.

Prefer:

``` text
users
algorithms
algorithm_categories
topics
problems
problem_topics
user_algorithm_progress
user_problem_progress
user_recent_items
roadmap_items
```

Avoid storing relational data as large JSON blobs when the data needs to
be queried.

JSONB may be used for genuinely flexible educational metadata.

------------------------------------------------------------------------

# 9. PostgreSQL Schema

## users

``` sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    display_name VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Indexes:

``` sql
CREATE UNIQUE INDEX ix_users_email_lower
ON users (LOWER(email));
```

If the application normalizes emails in application code, the unique
index strategy should remain consistent.

------------------------------------------------------------------------

# 10. Algorithm Categories

``` sql
CREATE TABLE algorithm_categories (
    id UUID PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Examples:

``` text
sorting
searching
arrays
recursion
trees
graphs
dynamic-programming
greedy
```

------------------------------------------------------------------------

# 11. Algorithms

``` sql
CREATE TABLE algorithms (
    id UUID PRIMARY KEY,
    category_id UUID NOT NULL REFERENCES algorithm_categories(id),
    slug VARCHAR(150) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    visualization_type VARCHAR(50) NOT NULL,

    best_time VARCHAR(50),
    average_time VARCHAR(50),
    worst_time VARCHAR(50),
    space_complexity VARCHAR(50),

    is_published BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT algorithms_difficulty_check
        CHECK (difficulty IN ('easy', 'medium', 'hard'))
);
```

`visualization_type` examples:

``` text
array
linked-list
tree
graph
heap
dp-table
recursion-tree
```

------------------------------------------------------------------------

# 12. Algorithm Source Code

Source code should be versioned.

Use:

``` sql
CREATE TABLE algorithm_code_versions (
    id UUID PRIMARY KEY,
    algorithm_id UUID NOT NULL REFERENCES algorithms(id) ON DELETE CASCADE,
    language VARCHAR(30) NOT NULL,
    source_code TEXT NOT NULL,
    version INTEGER NOT NULL,
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (algorithm_id, language, version)
);
```

Do not overwrite historical versions.

------------------------------------------------------------------------

# 13. Topics

``` sql
CREATE TABLE topics (
    id UUID PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL
);
```

Examples:

``` text
array
hash-map
two-pointer
sliding-window
divide-and-conquer
greedy
dynamic-programming
graph
tree
heap
```

------------------------------------------------------------------------

# 14. Algorithm Topics

Algorithms may have multiple topics.

``` sql
CREATE TABLE algorithm_topics (
    algorithm_id UUID NOT NULL REFERENCES algorithms(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,

    PRIMARY KEY (algorithm_id, topic_id)
);
```

This is a many-to-many relationship.

------------------------------------------------------------------------

# 15. Data Structures

``` sql
CREATE TABLE data_structures (
    id UUID PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    visualization_type VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Examples:

``` text
array
linked-list
stack
queue
hash-map
binary-tree
bst
heap
trie
graph
union-find
```

------------------------------------------------------------------------

# 16. Interview Problems

``` sql
CREATE TABLE problems (
    id UUID PRIMARY KEY,
    slug VARCHAR(200) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    difficulty VARCHAR(20) NOT NULL,

    solution_explanation TEXT,
    visualization_available BOOLEAN NOT NULL DEFAULT FALSE,

    external_reference VARCHAR(500),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT problems_difficulty_check
        CHECK (difficulty IN ('easy', 'medium', 'hard'))
);
```

Do not store arbitrary executable code from users.

------------------------------------------------------------------------

# 17. Problem Topics

``` sql
CREATE TABLE problem_topics (
    problem_id UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,

    PRIMARY KEY (problem_id, topic_id)
);
```

------------------------------------------------------------------------

# 18. Problem Companies

If company filtering is required:

``` sql
CREATE TABLE companies (
    id UUID PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL
);
```

Relationship:

``` sql
CREATE TABLE problem_companies (
    problem_id UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,

    PRIMARY KEY (problem_id, company_id)
);
```

This supports the Interview Preparation design where users can filter by
companies such as Google, Meta, and Amazon.

------------------------------------------------------------------------

# 19. User Algorithm Progress

``` sql
CREATE TABLE user_algorithm_progress (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    algorithm_id UUID NOT NULL REFERENCES algorithms(id) ON DELETE CASCADE,

    status VARCHAR(30) NOT NULL DEFAULT 'not_started',
    completion_percentage SMALLINT NOT NULL DEFAULT 0,

    first_viewed_at TIMESTAMPTZ,
    last_viewed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    total_sessions INTEGER NOT NULL DEFAULT 0,

    PRIMARY KEY (user_id, algorithm_id),

    CHECK (
        completion_percentage >= 0
        AND completion_percentage <= 100
    )
);
```

------------------------------------------------------------------------

# 20. User Problem Progress

``` sql
CREATE TABLE user_problem_progress (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    problem_id UUID NOT NULL REFERENCES problems(id) ON DELETE CASCADE,

    status VARCHAR(30) NOT NULL DEFAULT 'not_started',
    attempts INTEGER NOT NULL DEFAULT 0,

    first_viewed_at TIMESTAMPTZ,
    last_viewed_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    PRIMARY KEY (user_id, problem_id)
);
```

------------------------------------------------------------------------

# 21. Recently Viewed

``` sql
CREATE TABLE user_recent_items (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,

    item_type VARCHAR(30) NOT NULL,
    item_id UUID NOT NULL,

    viewed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Index:

``` sql
CREATE INDEX ix_recent_user_viewed
ON user_recent_items(user_id, viewed_at DESC);
```

Keep only a reasonable number of recent records per user, such as the
latest 50, using application logic.

------------------------------------------------------------------------

# 22. Roadmap

``` sql
CREATE TABLE roadmap_stages (
    id UUID PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(150) NOT NULL,
    description TEXT,
    sort_order INTEGER NOT NULL
);
```

Roadmap items:

``` sql
CREATE TABLE roadmap_items (
    id UUID PRIMARY KEY,
    stage_id UUID NOT NULL REFERENCES roadmap_stages(id) ON DELETE CASCADE,

    item_type VARCHAR(30) NOT NULL,
    algorithm_id UUID REFERENCES algorithms(id),
    topic_id UUID REFERENCES topics(id),

    sort_order INTEGER NOT NULL,

    UNIQUE(stage_id, sort_order)
);
```

This allows the roadmap to reference different learning entities without
duplicating them.

------------------------------------------------------------------------

# 23. Dashboard Data

Do not create a giant `dashboard` table.

The dashboard should be an application-level projection built from
normalized data.

For example:

``` text
user_algorithm_progress
user_problem_progress
user_recent_items
roadmap_items
```

are aggregated into:

``` json
{
  "algorithmsLearned": 18,
  "algorithmsTotal": 42,
  "problemsSolved": 27,
  "interviewReadiness": 68,
  "currentStreak": 7
}
```

The DashboardService owns this aggregation.

------------------------------------------------------------------------

# 24. Database Indexing

Add indexes based on actual query patterns.

At minimum:

``` text
users.email
algorithms.slug
algorithms.category_id
algorithms.difficulty
algorithms.is_published
problems.slug
problems.difficulty
problem_companies.company_id
problem_topics.topic_id
user_algorithm_progress.user_id
user_problem_progress.user_id
user_recent_items(user_id, viewed_at)
```

Do not add indexes blindly.

Every index has write/storage cost.

------------------------------------------------------------------------

# 25. API Design

Base path:

``` text
/api/v1
```

## Auth

``` text
POST /auth/register
POST /auth/login
POST /auth/logout
GET  /auth/me
POST /auth/refresh
```

## Algorithms

``` text
GET /algorithms
GET /algorithms/{slug}
GET /algorithms/categories
```

Filters:

``` text
category
difficulty
search
topic
page
page_size
```

## Data Structures

``` text
GET /data-structures
GET /data-structures/{slug}
```

## Problems

``` text
GET /problems
GET /problems/{slug}
GET /problems/{slug}/topics
GET /problems/{slug}/companies
```

## Progress

``` text
GET  /progress
GET  /progress/algorithms
GET  /progress/problems

POST /progress/algorithms/{algorithm_id}
POST /progress/problems/{problem_id}
```

## Dashboard

``` text
GET /dashboard
```

## Roadmap

``` text
GET /roadmap
```

------------------------------------------------------------------------

# 26. API Response Design

Use consistent response models.

Do not expose SQLAlchemy models directly.

Example:

``` python
class AlgorithmResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str
    difficulty: Difficulty
    visualization_type: str
    best_time: str | None
    average_time: str | None
    worst_time: str | None
    space_complexity: str | None

    model_config = ConfigDict(from_attributes=True)
```

------------------------------------------------------------------------

# 27. Pagination

Use consistent pagination.

Example:

``` json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 42,
  "total_pages": 3
}
```

Create a reusable pagination abstraction.

Do not duplicate pagination calculations in every router.

------------------------------------------------------------------------

# 28. Filtering

Use typed filter objects.

Example:

``` python
class AlgorithmFilters:
    search: str | None
    category: str | None
    difficulty: Difficulty | None
    topic: str | None
```

The repository translates filters into SQL.

The router only parses HTTP query parameters.

------------------------------------------------------------------------

# 29. Authentication

Recommended architecture:

``` text
HTTP-only secure cookie
        ↓
FastAPI auth dependency
        ↓
CurrentUser
        ↓
Protected service
```

Passwords must be hashed using a modern password hashing algorithm such
as Argon2id.

Never store plaintext passwords.

Never log:

-   passwords
-   password hashes
-   access tokens
-   refresh tokens
-   session secrets

------------------------------------------------------------------------

# 30. Authorization

Create reusable dependencies:

``` python
get_current_user()
require_current_user()
```

Future roles:

``` text
user
admin
editor
```

Do not scatter authorization checks throughout services.

------------------------------------------------------------------------

# 31. Transaction Management

Use a request/service transaction boundary.

Preferred pattern:

``` text
API request
    ↓
Service
    ↓
Repository operations
    ↓
commit/rollback
```

Avoid committing inside every repository method.

This allows a service to perform multiple changes atomically.

------------------------------------------------------------------------

# 32. Async SQLAlchemy

Use SQLAlchemy 2.x async APIs.

Recommended:

``` python
AsyncEngine
async_sessionmaker
AsyncSession
```

Database dependency:

``` python
async def get_db() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session
```

Do not use blocking database calls inside async routes.

------------------------------------------------------------------------

# 33. Alembic

Every schema change must be an Alembic migration.

Typical workflow:

``` bash
alembic revision --autogenerate -m "create algorithm tables"
alembic upgrade head
```

Before committing a migration:

1.  inspect generated SQL/migration
2.  verify constraints
3.  verify indexes
4.  verify foreign keys
5.  test upgrade
6.  test downgrade when practical

Never edit an already-applied migration casually.

Create a new migration.

------------------------------------------------------------------------

# 34. Seed Data

Create deterministic seed scripts for:

-   categories
-   algorithms
-   topics
-   data structures
-   interview problems
-   companies
-   roadmap stages

Seed scripts must be idempotent.

Running them twice must not create duplicates.

------------------------------------------------------------------------

# 35. Algorithm Execution Boundary

The initial product should NOT execute arbitrary user code on the
backend.

The backend stores:

-   algorithm metadata
-   educational source code
-   explanations
-   complexity
-   categories
-   topics

The frontend owns controlled deterministic visualization execution.

Architecture:

``` text
PostgreSQL
    ↓
FastAPI
    ↓
Next.js API client
    ↓
Algorithm Registry
    ↓
Execution Engine
    ↓
Visualization
```

This avoids the security risk of running arbitrary code.

If server-side execution is added later, it must be isolated in a
sandboxed execution service rather than inside the main FastAPI process.

------------------------------------------------------------------------

# 36. Error Handling

Create domain/application exceptions.

Examples:

``` text
NotFoundError
ConflictError
AuthenticationError
AuthorizationError
ValidationError
```

Map them centrally to HTTP responses.

Example:

``` json
{
  "error": {
    "code": "ALGORITHM_NOT_FOUND",
    "message": "Algorithm not found."
  }
}
```

Do not leak internal exception details.

------------------------------------------------------------------------

# 37. Logging

Use structured logging.

Log:

-   request ID
-   method
-   route
-   status
-   duration
-   important domain events

Do not log sensitive data.

Production logs should be machine-readable.

------------------------------------------------------------------------

# 38. Configuration

Use environment variables.

Example:

``` text
APP_ENV=development

DATABASE_URL=postgresql+asyncpg://...

JWT_SECRET=...

CORS_ORIGINS=http://localhost:3000
```

Use Pydantic Settings.

Never hardcode secrets.

Provide:

``` text
.env.example
```

but never commit `.env`.

------------------------------------------------------------------------

# 39. Dependency Injection

FastAPI dependency injection should provide:

``` text
database session
current user
repositories
services
configuration
```

Example:

``` text
get_db()
get_current_user()
get_algorithm_service()
get_progress_service()
```

Keep construction logic centralized.

------------------------------------------------------------------------

# 40. SOLID Principles

## Single Responsibility

Routers handle HTTP.

Services handle application rules.

Repositories handle persistence.

Schemas handle API serialization/validation.

Models represent persistence.

## Open/Closed

Adding a new algorithm category should not require modifying every
service.

Adding a new repository implementation should not require rewriting
services.

## Liskov Substitution

Repository implementations should satisfy their contracts.

## Interface Segregation

Avoid one giant:

``` text
Repository
```

interface.

Prefer:

``` text
AlgorithmRepository
ProblemRepository
ProgressRepository
UserRepository
```

## Dependency Inversion

Services depend on repository abstractions where useful.

Example:

``` python
class AlgorithmService:
    def __init__(
        self,
        repository: AlgorithmRepositoryProtocol,
    ):
        self.repository = repository
```

------------------------------------------------------------------------

# 41. DRY Rules

Never duplicate:

-   pagination
-   authentication extraction
-   password hashing
-   error mapping
-   filtering
-   timestamp handling
-   serialization rules
-   dashboard calculations
-   repository query fragments

But do not over-abstract.

Two pieces of code are not automatically duplicates simply because they
look similar.

Abstract repeated **behavior**, not accidental similarity.

------------------------------------------------------------------------

# 42. Testing Strategy

## Unit tests

Test:

-   services
-   domain rules
-   filter construction
-   dashboard calculations
-   authentication utilities

## Repository tests

Use a real PostgreSQL test database where practical.

Do not rely exclusively on SQLite for PostgreSQL-specific behavior.

Test:

-   constraints
-   joins
-   pagination
-   indexes/query behavior where important

## API tests

Use FastAPI TestClient/httpx.

Test:

``` text
register
login
me
algorithm listing
algorithm detail
problem listing
progress update
dashboard
roadmap
```

## Integration tests

Verify:

``` text
API → Service → Repository → PostgreSQL
```

for critical flows.

------------------------------------------------------------------------

# 43. Security Requirements

Implement:

-   password hashing
-   secure authentication cookies
-   CORS restrictions
-   request validation
-   SQLAlchemy parameterized queries
-   rate limiting strategy for authentication endpoints
-   secure headers at deployment layer
-   secret management
-   non-sensitive logging

Never:

-   execute arbitrary submitted Python/JS
-   interpolate SQL strings with user input
-   expose database credentials
-   expose internal stack traces
-   trust client-side progress blindly

------------------------------------------------------------------------

# 44. Frontend Contract

The FastAPI API must be designed around the Next.js frontend.

Important response groups:

``` text
Algorithm
AlgorithmDetail
DataStructure
Problem
ProblemDetail
DashboardSummary
Roadmap
Progress
User
```

Keep API schemas stable.

If a breaking API change is necessary, use:

``` text
/api/v2
```

or a controlled migration strategy.

------------------------------------------------------------------------

# 45. CLI LLM Instructions

This section is intended to be used as the instruction prompt for a CLI
coding agent such as a configured **z.ai CLI, Claude Code, Gemini CLI,
Codex CLI, or similar terminal LLM agent**.

## Master Agent Instruction

``` text
You are the senior backend engineer responsible for implementing AlgoVision.

Read BACKEND.md completely before changing code.

Your stack:
- Python
- FastAPI
- Pydantic v2
- SQLAlchemy 2 async
- PostgreSQL
- asyncpg
- Alembic
- pytest
- Ruff

Rules:

1. Follow the architecture in BACKEND.md.
2. Follow SOLID and DRY.
3. Routers must not contain business logic.
4. Repositories must not contain business rules.
5. Services must not depend on HTTP concepts.
6. Never expose SQLAlchemy models directly as API responses.
7. Every database schema change requires Alembic.
8. Never execute arbitrary user code.
9. Never store plaintext passwords.
10. Never log secrets.
11. Use typed Pydantic schemas.
12. Use async database access.
13. Use transactions deliberately.
14. Do not duplicate pagination/filter/authentication logic.
15. Do not rewrite unrelated modules.
16. Inspect the existing repository before creating new abstractions.
17. Prefer a small clean abstraction over a large generic framework.
18. Write tests for every business-critical feature.
19. Run formatting, linting, type checking, tests, and migrations verification.
20. Report all architectural decisions and remaining risks.

Implementation priority:

Phase 1:
- project foundation
- configuration
- PostgreSQL
- SQLAlchemy
- Alembic
- health endpoint

Phase 2:
- users
- authentication
- authorization

Phase 3:
- categories
- topics
- algorithms
- data structures

Phase 4:
- interview problems
- companies
- filters
- pagination

Phase 5:
- progress
- recently viewed
- roadmap
- dashboard

Phase 6:
- tests
- security
- performance
- documentation
```

------------------------------------------------------------------------

# 46. CLI Task Prompt

Use this for individual tasks:

``` text
Implement the next backend vertical slice of AlgoVision.

Before coding:

1. Read BACKEND.md.
2. Inspect the repository.
3. Inspect current migrations.
4. Inspect existing models/services/repositories.
5. Identify whether reusable code already exists.

Then:

1. State the implementation plan.
2. Implement models if required.
3. Create/update Alembic migration.
4. Implement repository.
5. Implement service.
6. Implement Pydantic schemas.
7. Implement router.
8. Add tests.
9. Run:
   - Ruff
   - pytest
   - type checking
   - migration verification
10. Review SOLID and DRY.

Do not:
- put SQL in routers
- duplicate business logic
- expose ORM models
- introduce unnecessary abstractions
- change unrelated code
- silently remove existing functionality

Report:
- files changed
- migration created
- API endpoints added
- tests added
- commands executed
- remaining issues
```

------------------------------------------------------------------------

# 47. Suggested CLI Commands

The exact CLI executable depends on the installed LLM tool.

The repository workflow should remain tool-independent.

Example development commands:

``` bash
python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn src.main:app --reload
```

Database:

``` bash
alembic upgrade head
```

Tests:

``` bash
pytest
```

Lint:

``` bash
ruff check .
ruff format .
```

The CLI LLM should run the project's actual package-manager/tooling
commands after inspecting the repository rather than assuming these
exact commands if the project uses `uv`, Poetry, or another manager.

------------------------------------------------------------------------

# 48. API Documentation

FastAPI should provide:

``` text
/docs
/redoc
/openapi.json
```

Keep endpoint descriptions useful.

Document:

-   parameters
-   authentication requirements
-   response models
-   error codes

------------------------------------------------------------------------

# 49. Health Endpoint

Provide:

``` text
GET /health
```

Response:

``` json
{
  "status": "ok"
}
```

For a deeper operational health check, optionally provide:

``` text
GET /health/ready
```

which checks PostgreSQL connectivity.

Do not make the basic liveness endpoint dependent on the database.

------------------------------------------------------------------------

# 50. Definition of Done

Backend work is complete only when:

-   FastAPI starts successfully
-   PostgreSQL connection works
-   migrations work
-   models are normalized
-   API schemas are typed
-   routers contain no business logic
-   services contain business rules
-   repositories contain persistence logic
-   authentication is secure
-   progress updates are transactional
-   dashboard aggregation is correct
-   API pagination/filtering is consistent
-   tests pass
-   lint passes
-   migrations are verified
-   no secrets are committed
-   frontend API contract is documented

The backend should remain modular enough that a future mobile
application could consume the same API without changing the domain
layer.
