"""FastAPI dependencies for the progress module.

Two responsibilities:

- ``get_progress_service``: per-request factory that builds
  a ``ProgressService`` from the request-scoped
  ``AsyncSession`` (Liskov substitution; tests pass fakes).

- ``register_progress_handlers``: one-time startup hook that
  subscribes a session-factory-aware closure to
  ``ItemViewedEvent`` on the process-wide dispatcher.
  Called from ``main.py`` after the dispatcher is created.

Why the handler opens its own session
-------------------------------------
The dispatcher is process-wide, not request-scoped. The
handler it invokes cannot inherit the request's session
(the request may be long over by the time a future event
reaches it; the handler is best-effort). The closure opens
a fresh session via ``get_session_factory()`` so its
writes are independent of the request that triggered the
event. View-tracking failures never cascade into the
request that caused them — the dispatcher's per-handler
try/except also swallows errors, but the session
isolation makes the design clean.

Why we don't pass a per-request ProgressService
-----------------------------------------------
Each request creates its own service bound to its own
session. The dispatcher must hold *one* subscription
that lives for the life of the process. Re-registering
on every request would create unbounded duplicate
subscriptions and a memory leak. The handler closure
is built once and uses its own session lifecycle.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 - B5.7),
       §6.7 (event dispatcher)
Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session, get_session_factory
from src.modules.progress.repository import (
    ProgressRepository,
    ProgressRepositoryProtocol,
)
from src.modules.progress.service import (
    ProgressService,
    ProgressServiceProtocol,
)
from src.shared.events import EventDispatcherProtocol, ItemViewedEvent


def get_progress_service(
    session: AsyncSession = Depends(get_session),
) -> ProgressServiceProtocol:
    """Build a per-request ProgressService bound to the session.

    Used by the routers for the user-driven
    list/mark/overview/recents operations.
    """
    return ProgressService(repo=ProgressRepository(session))


def register_progress_handlers(
    dispatcher: EventDispatcherProtocol,
) -> None:
    """Subscribe ``ProgressService.handle_item_viewed`` to ItemViewedEvent.

    The handler closure is a long-lived subscription whose
    repository opens its own session per call via
    ``get_session_factory()``. The handler is best-effort:
    errors are logged and swallowed by the dispatcher
    (see ``shared/events.py``).
    """
    factory = get_session_factory()

    async def _on_item_viewed(event: ItemViewedEvent) -> None:
        if event.user_id is None:
            # Anonymous tracking is out of scope for v1.
            return
        async with factory() as session:
            repo: ProgressRepositoryProtocol = ProgressRepository(session)
            await repo.record_view(
                user_id=event.user_id,
                item_type=event.item_type,
                item_id=event.item_id,
            )

    dispatcher.register(ItemViewedEvent, _on_item_viewed)


__all__ = [
    "get_progress_service",
    "register_progress_handlers",
]
