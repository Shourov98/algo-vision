"""CatalogService — data structures tests.

Covers the data-structure read paths and their event-dispatch
behavior. Mirrors the algorithm-detail test shape.

Refs: ALGOVISION_BACKEND_PLAN.md §3.5, §6.7
Refs: PUKU_BACKEND_AGENT.md §13
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from src.modules.catalog.exceptions import DataStructureNotFound
from src.modules.catalog.schemas import DataStructureResponse
from src.shared.events import ItemViewedEvent

from tests.unit._catalog_conftest import (
    empty_page,
    make_data_structure,
    make_service,
)

# ---------------------------------------------------------------------------
# list_data_structures
# ---------------------------------------------------------------------------


async def test_list_data_structures_delegates_to_repo() -> None:
    svc, repos, _ = make_service()
    repos["ds"].list.return_value = empty_page(
        [make_data_structure("stack")]
    )
    page = await svc.list_data_structures(filters=object())  # type: ignore[arg-type]
    repos["ds"].list.assert_awaited_once()
    assert len(page.items) == 1
    assert isinstance(page.items[0], DataStructureResponse)
    assert page.items[0].slug == "stack"


# ---------------------------------------------------------------------------
# get_data_structure_by_slug
# ---------------------------------------------------------------------------


async def test_get_data_structure_by_slug_returns_response_when_present() -> None:
    svc, repos, _ = make_service()
    repos["ds"].get_by_slug.return_value = make_data_structure("stack")
    result = await svc.get_data_structure_by_slug("stack")
    assert isinstance(result, DataStructureResponse)
    assert result.slug == "stack"


async def test_get_data_structure_by_slug_raises_when_missing() -> None:
    svc, repos, _ = make_service()
    repos["ds"].get_by_slug.return_value = None
    with pytest.raises(DataStructureNotFound):
        await svc.get_data_structure_by_slug("nope")


async def test_get_data_structure_by_slug_skips_event_when_anonymous() -> None:
    svc, repos, dispatcher = make_service()
    repos["ds"].get_by_slug.return_value = make_data_structure("stack")
    await svc.get_data_structure_by_slug("stack")
    assert dispatcher.events == []


async def test_get_data_structure_by_slug_dispatches_item_viewed_event() -> None:
    svc, repos, dispatcher = make_service()
    ds = make_data_structure("stack")
    repos["ds"].get_by_slug.return_value = ds
    user_id = uuid4()
    before = datetime.now(UTC)
    await svc.get_data_structure_by_slug("stack", user_id=user_id)
    after = datetime.now(UTC)

    assert len(dispatcher.events) == 1
    event = dispatcher.events[0]
    assert isinstance(event, ItemViewedEvent)
    assert event.user_id == user_id
    assert event.item_type == "data_structure"
    assert event.item_id == ds.id
    assert before <= event.viewed_at <= after
