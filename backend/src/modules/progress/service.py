"""ProgressService - write-side per-user progress orchestrator.

Owns the business rules for marking progress + the
subscription handler for ``ItemViewedEvent`` (the first
cross-module event in the codebase).

Single responsibility
---------------------
The service is the only layer that knows how progress
writes flow:

1. Validate the request payload (B5.4 schema does this
   at the router; the service trusts the typed DTO).
2. Delegate persistence to ``ProgressRepository`` via
   the protocol (Liskov substitution in tests).
3. Translate ORM rows to public responses via inline
   converters — ORM rows NEVER escape this layer
   (PUKU_BACKEND_AGENT §3.1).

Why the service also consumes ``ItemViewedEvent``
------------------------------------------------
Catalog services (Phase 3 / 4) emit ``ItemViewedEvent``
when a user reads an algorithm/problem/data_structure
detail. The progress service subscribes to the event via
``handle_item_viewed`` and appends to ``user_recent_items``
+ caps to 50.

This is the architectural moment called out in
``ALGOVISION_BACKEND_PLAN §6.7`` (DIP — services depend
on the event dispatcher protocol, not on each other
directly). Catalog services no longer import progress.

What this class does NOT own
----------------------------
- HTTP concerns (status codes, request parsing). Routers do.
- SQL. Repositories do.
- User identity. Routers extract via ``get_current_user``
  (Phase 2) and pass ``user_id`` as a method argument.

Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 - B5.6),
       §6.7 (Service Decoupling via Domain Events)
Refs: PUKU_BACKEND_AGENT.md §6, §10
Refs: AlgoVision_BACKEND.md §8
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from src.modules.progress.filters import (
    AlgorithmProgressFilters,
    ProblemProgressFilters,
)
from src.modules.progress.models import (
    UserAlgorithmProgress,
    UserProblemProgress,
    UserRecentItem,
)
from src.modules.progress.repository import ProgressRepositoryProtocol
from src.modules.progress.schemas import (
    ProgressOverviewCounts,
    ProgressOverviewResponse,
    RecentItemResponse,
    RecentsListResponse,
    UserAlgorithmProgressResponse,
    UserProblemProgressResponse,
)
from src.shared.events import ItemViewedEvent
from src.shared.pagination import Page

# ---------------------------------------------------------------------------
# Service protocol
# ---------------------------------------------------------------------------


class ProgressServiceProtocol(Protocol):
    """Interface the progress router depends on."""

    async def mark_algorithm(
        self,
        user_id: UUID,
        algorithm_id: UUID,
        status: str,
        completion_percentage: int,
    ) -> UserAlgorithmProgressResponse: ...

    async def mark_problem(
        self,
        user_id: UUID,
        problem_id: UUID,
        status: str,
        attempts: int,
    ) -> UserProblemProgressResponse: ...

    async def list_algorithm_progress(
        self,
        user_id: UUID,
        filters: AlgorithmProgressFilters,
    ) -> Page[UserAlgorithmProgressResponse]: ...

    async def list_problem_progress(
        self,
        user_id: UUID,
        filters: ProblemProgressFilters,
    ) -> Page[UserProblemProgressResponse]: ...

    async def get_overview(self, user_id: UUID) -> ProgressOverviewResponse: ...

    async def list_recents(
        self,
        user_id: UUID,
    ) -> RecentsListResponse: ...

    async def handle_item_viewed(self, event: ItemViewedEvent) -> None: ...


# ---------------------------------------------------------------------------
# ORM-row -> response converters
#
# Kept inline (not in a separate _converters.py) because
# the four conversions are tiny and live one-to-one with
# the service methods that call them. Splitting would
# multiply files for ~20 lines of total code.
# ---------------------------------------------------------------------------


def _alg_to_response(row: UserAlgorithmProgress) -> UserAlgorithmProgressResponse:
    return UserAlgorithmProgressResponse.model_validate(row)


def _prob_to_response(row: UserProblemProgress) -> UserProblemProgressResponse:
    return UserProblemProgressResponse.model_validate(row)


def _recent_to_response(row: UserRecentItem) -> RecentItemResponse:
    return RecentItemResponse.model_validate(row)


# ---------------------------------------------------------------------------
# Concrete service
# ---------------------------------------------------------------------------


class ProgressService:
    """Concrete progress service.

    Composition is constructor injection: the service is
    given the ``ProgressRepositoryProtocol``. Tests pass
    AsyncMock-backed fakes; the production wiring (B5.7
    dependency factory) passes the concrete repo with the
    request-scoped session.

    Why no EventDispatcher dependency here
    --------------------------------------
    The service consumes ``ItemViewedEvent`` via the
    ``handle_item_viewed`` method; that's enough — the
    wiring of "register this handler on the dispatcher"
    happens in the composition root (B5.7 / main.py) so
    the service itself stays free of dispatcher
    dependencies. The dependency direction is:

        dispatcher -> registers handler from -> service
        service   -> never imports        -> dispatcher
    """

    def __init__(
        self,
        repo: ProgressRepositoryProtocol,
    ) -> None:
        self._repo = repo

    # ------------------------------------------------------------------
    # Writes
    # ------------------------------------------------------------------

    async def mark_algorithm(
        self,
        user_id: UUID,
        algorithm_id: UUID,
        status: str,
        completion_percentage: int,
    ) -> UserAlgorithmProgressResponse:
        """Idempotent upsert of one algorithm-progress row.

        No event dispatch here — the view event fires when
        a user reads the algorithm detail (catalog
        service's job). This method only records explicit
        progress marks.
        """
        row = await self._repo.upsert_algorithm_progress(
            user_id=user_id,
            algorithm_id=algorithm_id,
            status=status,
            completion_percentage=completion_percentage,
        )
        return _alg_to_response(row)

    async def mark_problem(
        self,
        user_id: UUID,
        problem_id: UUID,
        status: str,
        attempts: int,
    ) -> UserProblemProgressResponse:
        """Idempotent upsert of one problem-progress row."""
        row = await self._repo.upsert_problem_progress(
            user_id=user_id,
            problem_id=problem_id,
            status=status,
            attempts=attempts,
        )
        return _prob_to_response(row)

    # ------------------------------------------------------------------
    # Reads
    # ------------------------------------------------------------------

    async def list_algorithm_progress(
        self,
        user_id: UUID,
        filters: AlgorithmProgressFilters,
    ) -> Page[UserAlgorithmProgressResponse]:
        page = await self._repo.list_algorithm_progress(user_id, filters)
        return Page(
            items=[_alg_to_response(r) for r in page.items],
            page=page.page,
            page_size=page.page_size,
            total=page.total,
        )

    async def list_problem_progress(
        self,
        user_id: UUID,
        filters: ProblemProgressFilters,
    ) -> Page[UserProblemProgressResponse]:
        page = await self._repo.list_problem_progress(user_id, filters)
        return Page(
            items=[_prob_to_response(r) for r in page.items],
            page=page.page,
            page_size=page.page_size,
            total=page.total,
        )

    async def get_overview(self, user_id: UUID) -> ProgressOverviewResponse:
        """Composite counts for the dashboard."""
        counts = await self._repo.get_overview(user_id)
        return ProgressOverviewResponse(
            algorithms=ProgressOverviewCounts(
                completed=counts["algorithms_completed"],
                in_progress=counts["algorithms_in_progress"],
                total=counts["algorithms_total"],
            ),
            problems=ProgressOverviewCounts(
                completed=counts["problems_completed"],
                in_progress=counts["problems_in_progress"],
                total=counts["problems_total"],
            ),
        )

    async def list_recents(
        self,
        user_id: UUID,
    ) -> RecentsListResponse:
        """Up to 50 most-recent views for the dashboard sidebar."""
        rows: Sequence[UserRecentItem] = await self._repo.list_recents(user_id)
        return RecentsListResponse(items=[_recent_to_response(r) for r in rows])

    # ------------------------------------------------------------------
    # Event handler (subscribed by the composition root)
    # ------------------------------------------------------------------

    async def handle_item_viewed(self, event: ItemViewedEvent) -> None:
        """ItemViewedEvent handler.

        Appends a row to ``user_recent_items`` (the cap-to-50
        is enforced inside ``record_view``). Anonymous views
        (user_id is None) are dropped — anonymous tracking is
        out of scope for v1.

        Why this is async
        -----------------
        The dispatcher (``shared/events.py``) awaits the
        handler result. Marking the method async keeps the
        dispatcher in its ``inspect.isawaitable`` happy path
        and lets us add real I/O later (e.g. analytics
        POST) without changing the signature.
        """
        if event.user_id is None:
            return
        await self._repo.record_view(
            user_id=event.user_id,
            item_type=event.item_type,
            item_id=event.item_id,
        )


__all__ = ["ProgressService", "ProgressServiceProtocol"]
