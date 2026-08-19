# AlgoVision Backend

FastAPI + PostgreSQL API for the AlgoVision interactive algorithm and
data structure visualization platform.

> This README covers **project scaffold (B1.1)**. It will grow as the
> phase-1 foundation lands. For architecture, design, and contracts see
> the docs in the repo root.

---

## Stack

| Concern        | Choice                                    |
|----------------|-------------------------------------------|
| Language       | Python 3.12+                              |
| Framework      | FastAPI                                   |
| Validation     | Pydantic v2 + pydantic-settings           |
| ORM            | SQLAlchemy 2.x (async)                    |
| Driver         | asyncpg (app), psycopg2 (Alembic)         |
| Database       | PostgreSQL 16 (Supabase managed)          |
| Migrations     | Alembic                                   |
| Auth           | Argon2id, HTTP-only secure cookies        |
| Rate limit     | slowapi                                   |
| Logging        | structlog (JSON in non-dev)               |
| Tests          | pytest + httpx + real Postgres            |
| Lint / format  | ruff                                      |
| Types          | mypy (practical)                          |

Source of truth for stack & rules: `PUKU_BACKEND_AGENT.md` §2 and
`AlgoVision_BACKEND.md`.

---

## Layout

```
backend/
├── pyproject.toml
├── .env.example
├── README.md                  ← you are here
├── src/
│   ├── main.py                # FastAPI app factory
│   ├── core/                  # settings, logging, errors, db, security
│   ├── shared/                # pagination, filters, ids
│   └── modules/
│       ├── auth/              # registration, login, refresh
│       ├── catalog/           # algorithms, categories, data structures
│       ├── problems/          # interview problems with tags
│       ├── progress/          # user marks, recent items
│       └── dashboard/
│           └── calculators/   # ReadinessCalculator, SkillMapper,
│                                FocusAreaSelector, StreakCalculator
└── tests/
    ├── integration/           # cross-module end-to-end
    └── unit/                  # cross-feature helper tests
```

Each feature module is a vertical slice: `models.py`, `schemas.py`,
`repository.py`, `service.py`, `router.py`, `events.py` (optional),
and a `tests/` folder.

---

## Quick start (development)

> B1.1 is pure scaffolding — there is no DB connection yet. These
> steps will start working end-to-end as phase 1 progresses.

```bash
# 1. Create a virtualenv
python3.12 -m venv .venv
source .venv/bin/activate

# 2. Install dependencies (runtime + dev)
pip install -e ".[dev]"

# 3. Copy the env template and fill in Supabase credentials
cp .env.example .env
# Edit .env: set DATABASE_URL, DATABASE_URL_SYNC, SECRET_KEY, ...

# 4. Run the API (smoke check)
uvicorn src.main:app --reload --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000/docs
```

Migrations and the real DB session factory arrive in B1.5 / B1.6 /
B1.7.

---

## Supabase setup

1. Create a project at <https://supabase.com>.
2. Project settings → Database → reset database password if needed.
3. Copy the **Direct connection** string (port 5432) into
   `DATABASE_URL` and `DATABASE_URL_SYNC` in `.env`. Replace
   `[YOUR-PASSWORD]` and `[YOUR-PROJECT-REF]` with your values.
4. We **own auth** — Argon2id + signed cookies. Supabase Auth is
   **not** used; only the managed Postgres is.

---

## Verification commands

Run before every commit (see `PUKU_BACKEND_AGENT.md` §10):

```bash
# Lint + format check
ruff check .
ruff format --check .

# Types
mypy src/

# Tests (pytest rootdir is backend/)
pytest --cov=src --cov-report=term-missing

# Migrations (after B1.5)
alembic upgrade head
alembic downgrade -1
alembic upgrade head
```

The 400-line file size rule is enforced by pre-commit hook (see
`GIT_WORKFLOW.md` §12).

---

## References

- `PUKU.md` — master instructions
- `PUKU_BACKEND_AGENT.md` — backend-specific rules & phase roadmap
- `ALGOVISION_BACKEND_PLAN.md` — feature-by-feature planning
- `AlgoVision_BACKEND.md` — implementation contract (hard rules)
- `ARCHITECTURE.md` — C4 model, sequences, deployment, ADRs
- `DATABASE_DESIGN.md` — ERD, indexes, migrations