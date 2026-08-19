"""Auth feature module.

Handles registration, login, logout, refresh-token rotation, and the
``get_current_user`` FastAPI dependency. Emits no domain events.

Canonical layered structure (one file per concern):

    models.py       SQLAlchemy ORM (User)
    schemas.py      Pydantic I/O (Register, Login, User)
    repository.py   UserRepository protocol + impl
    service.py      AuthService: register, login, logout, refresh
    router.py       /auth/* endpoints
    security.py     Argon2id hashing, cookie signing (feature-local)
    tests/          unit + integration tests (next to code)

Refs: PUKU_BACKEND_AGENT.md §3.1, §3.4
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2)
Refs: DATABASE_DESIGN.md §3 (users table)
"""