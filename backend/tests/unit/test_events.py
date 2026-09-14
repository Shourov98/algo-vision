"""Unit tests for the in-process event dispatcher.

These tests cover the dispatch + register contract that
catalog/problems services depend on:

- register + dispatch routes a payload to its handlers.
- Multiple handlers for one event all run.
- Sync and async handlers both work.
- Handler errors are logged and swallowed (next handler
  still runs; dispatch returns normally).
- The lock snapshot protects against handlers that
  re-register during iteration.

Refs: ALGOVISION_BACKEND_PLAN.md §6.7 (event dispatch)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from src.shared.events import (
    InProcessEventDispatcher,
    ItemViewedEvent,
    NoopEventDispatcher,
)


@dataclass(frozen=True, slots=True)
class _OtherEvent:
    """Test-local event class so we can verify type-routing."""

    payload: str


# ---------------------------------------------------------------------------
# register + dispatch
# ---------------------------------------------------------------------------


async def test_dispatch_routes_event_to_matching_handler() -> None:
    dispatcher = InProcessEventDispatcher()
    received: list[ItemViewedEvent] = []
    dispatcher.register(ItemViewedEvent, received.append)

    event = ItemViewedEvent(
        user_id=uuid4(),
        item_type="algorithm",
        item_id=uuid4(),
        viewed_at=datetime.now(UTC),
    )
    await dispatcher.dispatch(event)

    assert received == [event]


async def test_dispatch_does_not_route_to_unrelated_handler() -> None:
    dispatcher = InProcessEventDispatcher()
    received: list[_OtherEvent] = []
    dispatcher.register(_OtherEvent, received.append)

    await dispatcher.dispatch(
        ItemViewedEvent(
            user_id=uuid4(),
            item_type="algorithm",
            item_id=uuid4(),
            viewed_at=datetime.now(UTC),
        )
    )

    assert received == []


async def test_dispatch_runs_multiple_handlers_in_registration_order() -> None:
    dispatcher = InProcessEventDispatcher()
    calls: list[str] = []
    dispatcher.register(ItemViewedEvent, lambda _e: calls.append("first"))
    dispatcher.register(ItemViewedEvent, lambda _e: calls.append("second"))

    await dispatcher.dispatch(
        ItemViewedEvent(
            user_id=uuid4(),
            item_type="algorithm",
            item_id=uuid4(),
            viewed_at=datetime.now(UTC),
        )
    )

    assert calls == ["first", "second"]


# ---------------------------------------------------------------------------
# Async handlers
# ---------------------------------------------------------------------------


async def test_async_handler_is_awaited() -> None:
    dispatcher = InProcessEventDispatcher()
    received: list[UUID] = []

    async def handler(event: ItemViewedEvent) -> None:
        received.append(event.item_id)

    dispatcher.register(ItemViewedEvent, handler)

    expected_id = uuid4()
    await dispatcher.dispatch(
        ItemViewedEvent(
            user_id=None,
            item_type="algorithm",
            item_id=expected_id,
            viewed_at=datetime.now(UTC),
        )
    )

    assert received == [expected_id]


# ---------------------------------------------------------------------------
# Error handling — best-effort
# ---------------------------------------------------------------------------


async def test_handler_error_is_logged_and_swallowed() -> None:
    dispatcher = InProcessEventDispatcher()
    succeeded: list[int] = []

    def broken(_event: ItemViewedEvent) -> None:
        raise RuntimeError("boom")

    def after(_event: ItemViewedEvent) -> None:
        succeeded.append(1)

    dispatcher.register(ItemViewedEvent, broken)
    dispatcher.register(ItemViewedEvent, after)

    # Should NOT raise — handlers are best-effort.
    await dispatcher.dispatch(
        ItemViewedEvent(
            user_id=None,
            item_type="algorithm",
            item_id=uuid4(),
            viewed_at=datetime.now(UTC),
        )
    )

    assert succeeded == [1]


async def test_async_handler_error_is_swallowed() -> None:
    dispatcher = InProcessEventDispatcher()
    succeeded: list[int] = []

    async def broken(_event: ItemViewedEvent) -> None:
        raise RuntimeError("boom")

    def after(_event: ItemViewedEvent) -> None:
        succeeded.append(1)

    dispatcher.register(ItemViewedEvent, broken)
    dispatcher.register(ItemViewedEvent, after)

    await dispatcher.dispatch(
        ItemViewedEvent(
            user_id=None,
            item_type="algorithm",
            item_id=uuid4(),
            viewed_at=datetime.now(UTC),
        )
    )

    assert succeeded == [1]


# ---------------------------------------------------------------------------
# Re-entrant registration
# ---------------------------------------------------------------------------


async def test_handler_that_registers_during_dispatch_is_not_invoked() -> None:
    """The handler list is snapshotted before iteration so a handler
    that registers a NEW handler does NOT cause that new handler
    to run on the current dispatch (which would be a re-entrancy
    footgun)."""
    dispatcher = InProcessEventDispatcher()
    later_called: list[int] = []

    def later(_event: ItemViewedEvent) -> None:
        later_called.append(1)

    def reentrant(_event: ItemViewedEvent) -> None:
        dispatcher.register(ItemViewedEvent, later)

    dispatcher.register(ItemViewedEvent, reentrant)

    await dispatcher.dispatch(
        ItemViewedEvent(
            user_id=None,
            item_type="algorithm",
            item_id=uuid4(),
            viewed_at=datetime.now(UTC),
        )
    )

    assert later_called == []

    # But the handler IS available for the NEXT dispatch.
    await dispatcher.dispatch(
        ItemViewedEvent(
            user_id=None,
            item_type="algorithm",
            item_id=uuid4(),
            viewed_at=datetime.now(UTC),
        )
    )
    assert later_called == [1]


# ---------------------------------------------------------------------------
# Noop dispatcher
# ---------------------------------------------------------------------------


async def test_noop_dispatcher_swallows_events() -> None:
    dispatcher: Any = NoopEventDispatcher()
    # register is a no-op (no return value).
    assert dispatcher.register(_OtherEvent, lambda _e: None) is None
    # dispatch is a no-op (returns None without raising).
    assert (
        await dispatcher.dispatch(
            ItemViewedEvent(
                user_id=None,
                item_type="algorithm",
                item_id=uuid4(),
                viewed_at=datetime.now(UTC),
            )
        )
        is None
    )


# ---------------------------------------------------------------------------
# Protocol satisfaction
# ---------------------------------------------------------------------------


def test_dispatcher_satisfies_protocol() -> None:
    """Static sanity check: the concrete dispatcher exposes the
    protocol surface."""
    dispatcher = InProcessEventDispatcher()
    assert hasattr(dispatcher, "register")
    assert hasattr(dispatcher, "dispatch")
    assert callable(dispatcher.register)
    assert callable(dispatcher.dispatch)
