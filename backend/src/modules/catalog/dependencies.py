"""FastAPI dependencies for the catalog module.

Wires the HTTP layer to the service layer:

- ``get_catalog_service``: builds a CatalogService from the
  request-scoped AsyncSession and a process-wide event
  dispatcher.
- ``get_optional_user``: extracts the authenticated user
  (or None) from the request without raising on anonymous
  callers — catalog endpoints are public-read so detail
  reads dispatch events only when a user is present.

Why a process-wide dispatcher
-----------------------------
The event dispatcher holds handler subscriptions, which
are added at startup. It must be a singleton per process so
handlers registered by other modules (progress, analytics)
are visible to catalog services. ``get_catalog_service``
pulls the dispatcher off ``app.state.dispatcher`` (set by
the wiring in B3.8 router registration).

Refs: ALGOVISION_BACKEND_PLAN.md §3.5 (B3.6 services),
      §6.7 (event dispatcher)
Refs: PUKU_BACKEND_AGENT.md §7 (Router Conventions)
"""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.core.errors import TokenInvalid
from src.core.settings import Settings, get_settings
from src.core.tokens import verify_access_token
from src.modules.catalog.repository import (
    AlgorithmCodeVersionRepository,
    AlgorithmRepository,
    CategoryRepository,
    DataStructureRepository,
    TopicRepository,
)
from src.modules.catalog.service import (
    CatalogService,
    CatalogServiceProtocol,
)
from src.modules.users.models import User
from src.modules.users.repository import UsersRepository
from src.shared.events import (
    EventDispatcherProtocol,
    NoopEventDispatcher,
)


def get_catalog_service(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> CatalogServiceProtocol:
    """Build a CatalogService bound to the request-scoped session.

    The dispatcher is read off ``app.state.dispatcher`` so a
    single process-wide subscription list is shared across
    every request. When the dispatcher hasn't been wired
    yet (tests, CLI), a ``NoopEventDispatcher`` is used so
    the service can still construct.
    """
    dispatcher: EventDispatcherProtocol = getattr(
        request.app.state, "dispatcher", NoopEventDispatcher()
    )
    return CatalogService(
        categories_repo=CategoryRepository(session),
        topics_repo=TopicRepository(session),
        algorithms_repo=AlgorithmRepository(session),
        code_versions_repo=AlgorithmCodeVersionRepository(session),
        data_structures_repo=DataStructureRepository(session),
        events=dispatcher,
    )


async def get_optional_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User | None:
    """Return the authenticated user, or None if anonymous.

    Catalog endpoints are public-read: they accept both
    anonymous and authenticated callers. When a user is
    present we attach it to ``ItemViewedEvent`` dispatches
    (so progress can attribute the view); when absent we
    skip dispatch.

    A bad token is treated as anonymous (return None) rather
    than a 401 — public endpoints must not be gated on
    optional auth. Real auth-required endpoints use the
    auth module's ``get_current_user`` which does raise 401.
    """
    cookie = request.cookies.get("access_token")
    token: str | None = None
    if cookie:
        token = cookie
    else:
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header[7:]

    if token is None:
        return None

    try:
        user_id = verify_access_token(token, settings)
    except TokenInvalid:
        return None

    repo = UsersRepository(session)
    user = await repo.get_by_id(user_id)
    if user is None or not user.is_active:
        return None
    return user


__all__ = [
    "get_catalog_service",
    "get_optional_user",
]
