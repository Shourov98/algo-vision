"""FastAPI dependencies for the problems module.

Wires the HTTP layer to the service layer:

- ``get_problems_service``: builds a ProblemsService from
  the request-scoped AsyncSession.

The catalog has an event dispatcher dependency (for
ItemViewedEvent on public reads). The problems API is
staff-only in v1 (ALGOVISION_BACKEND_PLAN §4), so there is
no view-event dispatch and no ``get_optional_user``
dependency. The catalog's ``get_optional_user`` is reused
if a future read endpoint needs it.

Why no event dispatcher here
----------------------------
The catalog dispatches ``ItemViewedEvent`` on detail reads
so progress / analytics services can attribute views. The
problems API has no public read surface; the analytics
flow lands when the public endpoint exists. Adding an
unused dispatcher dependency now would couple this
module to a process-wide singleton it never uses.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 - Problems, B4.8)
Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.modules.problems.repository import (
    CompanyRepository,
    ProblemRepository,
)
from src.modules.problems.service import (
    ProblemsService,
    ProblemsServiceProtocol,
)
from src.shared.events import (
    EventDispatcherProtocol,
    NoopEventDispatcher,
)


def get_problems_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ProblemsServiceProtocol:
    """Build a ProblemsService bound to the request-scoped session.

    Phase 5 (B5.8): problems API now dispatches
    ``ItemViewedEvent`` on detail reads so the progress
    module can attribute views. The dispatcher is pulled
    off ``app.state.dispatcher`` (set by the wiring in
    main.py); when it hasn't been wired yet (tests, CLI),
    a ``NoopEventDispatcher`` keeps the service
    constructible.
    """
    dispatcher: EventDispatcherProtocol = getattr(
        request.app.state, "dispatcher", NoopEventDispatcher()
    )
    return ProblemsService(
        problems_repo=ProblemRepository(session),
        companies_repo=CompanyRepository(session),
        events=dispatcher,
    )


__all__ = ["get_problems_service"]
