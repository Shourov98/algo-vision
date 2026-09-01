"""Catalog service — orchestrator for catalog reads.

Single responsibility
---------------------
The service is the only layer that knows how catalog reads
flow:

1. Validate the request via the filter objects (constructed
   by the router — service does NOT parse query strings).
2. Delegate persistence to the per-entity repository.
3. Emit ``ItemViewedEvent`` for detail reads so progress /
   analytics services can subscribe (Dependency Inversion —
   we never import them).
4. Translate ORM rows to public responses via the schema
   converters (B3.7).

What this class does NOT own
----------------------------
- HTTP concerns (status codes, request parsing). Routers do.
- SQL. Repositories do.
- Cache headers / ETag (B3.9 router concern).
- View-event side effects beyond dispatching — handlers own
  their own transaction.

Why services depend on PROTOCOLS, not concrete repos
----------------------------------------------------
Liskov substitution: any class implementing
``AlgorithmRepositoryProtocol`` can stand in for the real
repo. Tests inject ``AsyncMock``-backed fakes. The router
constructs the concrete class from the request-scoped
session via the FastAPI dependency in B3.8.

Refs: ALGOVISION_BACKEND_PLAN.md §3.5, §6.7
Refs: PUKU_BACKEND_AGENT.md §6, §10
Refs: AlgoVision_BACKEND.md §8
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID

from src.modules.catalog.exceptions import (
    AlgorithmCodeVersionNotFound,
    AlgorithmNotFound,
    CategoryNotFound,
    DataStructureNotFound,
    NotPublished,
    TopicNotFound,
)
from src.modules.catalog.filters import (
    AlgorithmCodeVersionFilters,
    AlgorithmFilters,
    CategoryFilters,
    DataStructureFilters,
    TopicFilters,
)
from src.modules.catalog.models import (
    Algorithm,
    AlgorithmCodeVersion,
    Category,
    DataStructure,
    Topic,
)
from src.modules.catalog.repository import (
    AlgorithmCodeVersionRepositoryProtocol,
    AlgorithmRepositoryProtocol,
    CategoryRepositoryProtocol,
    DataStructureRepositoryProtocol,
    TopicRepositoryProtocol,
)
from src.shared.events import EventDispatcherProtocol, ItemViewedEvent
from src.shared.pagination import Page

# Item-type discriminator strings used by handlers to route
# ItemViewedEvent without importing the catalog enum. Plain
# strings are deliberate (ALGOVISION_BACKEND_PLAN §6.7).
_ITEM_TYPE_ALGORITHM = "algorithm"
_ITEM_TYPE_DATA_STRUCTURE = "data_structure"


# ---------------------------------------------------------------------------
# Service protocol — what routers depend on
# ---------------------------------------------------------------------------


class CatalogServiceProtocol(Protocol):
    """Read-side catalog operations.

    The protocol is intentionally minimal: each method maps to
    one router endpoint in B3.8. Adding a method here is a
    deliberate breaking change for callers — keep it stable.
    """

    async def list_categories(
        self, filters: CategoryFilters
    ) -> Page[Category]: ...

    async def get_category_by_slug(self, slug: str) -> Category: ...

    async def list_topics(self, filters: TopicFilters) -> Page[Topic]: ...

    async def get_topic_by_slug(self, slug: str) -> Topic: ...

    async def list_algorithms(
        self, filters: AlgorithmFilters
    ) -> Page[Algorithm]: ...

    async def get_algorithm_by_slug(
        self,
        slug: str,
        user_id: UUID | None = None,
        *,
        include_unpublished: bool = False,
    ) -> Algorithm: ...

    async def get_current_code(
        self,
        algorithm_id: UUID,
        language: str,
    ) -> AlgorithmCodeVersion: ...

    async def list_code_versions(
        self, filters: AlgorithmCodeVersionFilters
    ) -> Page[AlgorithmCodeVersion]: ...

    async def list_data_structures(
        self, filters: DataStructureFilters
    ) -> Page[DataStructure]: ...

    async def get_data_structure_by_slug(self, slug: str) -> DataStructure: ...


# ---------------------------------------------------------------------------
# Concrete service
# ---------------------------------------------------------------------------


class CatalogService:
    """Concrete catalog read service.

    Composition is constructor injection: the service is given
    the per-entity repositories and the event dispatcher. Tests
    pass AsyncMock-backed fakes; the production wiring
    (B3.8 dependency factory) passes the concrete repos with
    the request-scoped session.
    """

    def __init__(
        self,
        categories_repo: CategoryRepositoryProtocol,
        topics_repo: TopicRepositoryProtocol,
        algorithms_repo: AlgorithmRepositoryProtocol,
        code_versions_repo: AlgorithmCodeVersionRepositoryProtocol,
        data_structures_repo: DataStructureRepositoryProtocol,
        events: EventDispatcherProtocol,
    ) -> None:
        self._categories = categories_repo
        self._topics = topics_repo
        self._algorithms = algorithms_repo
        self._code_versions = code_versions_repo
        self._data_structures = data_structures_repo
        self._events = events

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    async def list_categories(
        self, filters: CategoryFilters
    ) -> Page[Category]:
        """List algorithm categories matching ``filters``."""
        return await self._categories.list(filters)

    async def get_category_by_slug(self, slug: str) -> Category:
        """Return the category with ``slug`` or raise 404."""
        category = await self._categories.get_by_slug(slug)
        if category is None:
            raise CategoryNotFound(
                f"No algorithm category with slug {slug!r}.",
            )
        return category

    # ------------------------------------------------------------------
    # Topics
    # ------------------------------------------------------------------

    async def list_topics(self, filters: TopicFilters) -> Page[Topic]:
        return await self._topics.list(filters)

    async def get_topic_by_slug(self, slug: str) -> Topic:
        topic = await self._topics.get_by_slug(slug)
        if topic is None:
            raise TopicNotFound(f"No topic with slug {slug!r}.")
        return topic

    # ------------------------------------------------------------------
    # Algorithms
    # ------------------------------------------------------------------

    async def list_algorithms(
        self, filters: AlgorithmFilters
    ) -> Page[Algorithm]:
        """List algorithms matching ``filters``.

        The default ``is_published=True`` filter is encoded in
        ``AlgorithmFilters``; callers that need to see drafts
        build a filters object with ``is_published=False``.
        """
        return await self._algorithms.list(filters)

    async def get_algorithm_by_slug(
        self,
        slug: str,
        user_id: UUID | None = None,
        *,
        include_unpublished: bool = False,
    ) -> Algorithm:
        """Return the algorithm with ``slug`` or raise 404.

        Public consumers only see ``is_published=True`` rows.
        Draft visibility is reserved for a future staff role
        (``include_unpublished=True``); the current implementation
        does not check roles because no staff role exists yet.
        When that lands, this method will branch on a role
        check.

        On success, dispatches ``ItemViewedEvent`` if ``user_id``
        is supplied — handlers (e.g. ProgressService.record_view
        in Phase 5) may update recent-items or counters. We
        do NOT await handler side effects: dispatch is
        fire-and-forget relative to the read.
        """
        algorithm = await self._algorithms.get_by_slug(slug)
        if algorithm is None:
            raise AlgorithmNotFound(f"No algorithm with slug {slug!r}.")
        if not algorithm.is_published and not include_unpublished:
            # ``NotPublished`` (403) is distinct from ``NotFound``
            # so the frontend can distinguish "exists but hidden"
            # from "never existed".
            raise NotPublished(
                f"Algorithm {slug!r} is not published.",
            )
        if user_id is not None:
            await self._events.dispatch(
                ItemViewedEvent(
                    user_id=user_id,
                    item_type=_ITEM_TYPE_ALGORITHM,
                    item_id=algorithm.id,
                    viewed_at=datetime.now(UTC),
                )
            )
        return algorithm

    async def get_current_code(
        self,
        algorithm_id: UUID,
        language: str,
    ) -> AlgorithmCodeVersion:
        """Return the current code row for (algorithm, language).

        Uses the partial UNIQUE index on
        ``(algorithm_id, language) WHERE is_current = TRUE`` for
        an O(1) lookup (DATABASE_DESIGN §5).

        Raises ``AlgorithmCodeVersionNotFound`` if no current
        code exists in ``language`` for the given algorithm.
        """
        version = await self._code_versions.get_current(
            algorithm_id, language
        )
        if version is None:
            raise AlgorithmCodeVersionNotFound(
                f"No current code for algorithm {algorithm_id} "
                f"in {language!r}.",
            )
        return version

    async def list_code_versions(
        self, filters: AlgorithmCodeVersionFilters
    ) -> Page[AlgorithmCodeVersion]:
        return await self._code_versions.list(filters)

    # ------------------------------------------------------------------
    # Data structures
    # ------------------------------------------------------------------

    async def list_data_structures(
        self, filters: DataStructureFilters
    ) -> Page[DataStructure]:
        return await self._data_structures.list(filters)

    async def get_data_structure_by_slug(
        self,
        slug: str,
        user_id: UUID | None = None,
    ) -> DataStructure:
        """Return the data structure with ``slug`` or raise 404.

        Dispatches ``ItemViewedEvent`` with ``item_type=
        "data_structure"`` when a user is supplied so the
        progress module can track engagement consistently
        across catalog entities.
        """
        ds = await self._data_structures.get_by_slug(slug)
        if ds is None:
            raise DataStructureNotFound(
                f"No data structure with slug {slug!r}.",
            )
        if user_id is not None:
            await self._events.dispatch(
                ItemViewedEvent(
                    user_id=user_id,
                    item_type=_ITEM_TYPE_DATA_STRUCTURE,
                    item_id=ds.id,
                    viewed_at=datetime.now(UTC),
                )
            )
        return ds


__all__ = [
    "CatalogService",
    "CatalogServiceProtocol",
]
