"""Core infrastructure: settings, logging, DB engine, security.

Modules in this package are domain-agnostic. They hold the wiring
that feature modules consume via dependency injection.

Planned contents (filled in subsequent phase-1 commits):
- settings.py    : Pydantic Settings loader (B1.2)
- logging.py     : structlog configuration (B1.3)
- errors.py      : Domain exception hierarchy (B1.4)
- db.py          : async SQLAlchemy engine + session factory (B1.5)
- security.py    : Argon2id hashing, cookie signing (phase 2)

Refs: PUKU_BACKEND_AGENT.md §3.1 (Architecture)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1)
"""