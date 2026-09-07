"""Feature modules (vertical slices).

Each feature is a self-contained subpackage with the canonical
layered structure:

    modules/<feature>/
        __init__.py
        models.py       # SQLAlchemy ORM
        schemas.py      # Pydantic I/O
        repository.py   # data access (protocol + impl)
        service.py      # business logic (depends on repository protocol)
        router.py       # FastAPI endpoints (depends on service)
        events.py       # domain events emitted by this feature (optional)
        tests/          # unit + integration tests (next to code)

Planned features:
- auth         (phase 2)
- catalog      (phase 3)  -- algorithms, categories, data structures
- problems     (phase 4)
- progress     (phase 5)
- dashboard    (phase 5)

Refs: PUKU_BACKEND_AGENT.md §3.1, §3.2 (Architecture & SOLID)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Service design)
"""