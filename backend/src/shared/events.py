"""Domain event dispatcher.

A minimal in-process pub/sub used to decouple side effects from
the service that emits them. Catalog and problems services
``dispatch(ItemViewedEvent(...))`` after a successful read;
progress (and any future analytics/recommendation) services
subscribe by registering a handler.

Why a hand-rolled dispatcher instead of an external bus
--------------------------------------------------------
This is in-process only (Postgres + Python) and runs in the
same request context as the read that triggered it. We do NOT
need durability across restarts — events are best-effort
side effects, not the source of truth. Adding Redis/Kafka is a
future cross-cutting decision.

Why a Protocol
--------------
Services depend on ``EventDispatcherProtocol`` so tests can
substitute a recording fake without monkey-patching global
state. The default ``NoopEventDispatcher`` is what gets wired
in when no module has registered a handler yet.

Handler error semantics
-----------------------
Handler errors are logged and swallowed. Event publishing is
best-effort; the read that produced the event has already
succeeded and must not be invalidated by a downstream failure.

Refs: ALGOVISION_BACKEND_PLAN.md §6.7 (Service Decoupling via
      Domain Events)
Refs: PUKU_BACKEND_AGENT.md §3.1 (DIP — dispatch, don't import),
      §10 (Service Conventions)
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Protocol
from uuid import UUID

from src.core.logging import log

# A handler may be sync or async — dispatch awaits the result
# only if it is awaitable.
Handler = Callable[[Any], Awaitable[None] | None]


# ---------------------------------------------------------------------------
# Concrete event payloads
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ItemViewedEvent:
    """Emitted when a user fetches a catalog/problems detail.

    Consumed by ProgressService to update ``user_recent_items``
    and bump view counters (Phase 5). The event is intentionally
    minimal — anything more belongs in the read detail, not
    in the event envelope.

    Fields
    ------
    user_id:
        The viewing user. ``None`` is reserved for future
        anonymous-view tracking (B5.x); current consumers
        should treat None as "do nothing".
    item_type:
        Discriminator: ``"algorithm" | "data_structure" | "problem"``.
        Plain string so cross-module handlers don't have to
        import a catalog/problem enum to switch on it.
    item_id:
        The UUID of the entity that was viewed.
    viewed_at:
        UTC timestamp. Set by the service, not the handler.
    """

    user_id: UUID | None
    item_type: str
    item_id: UUID
    viewed_at: datetime


# ---------------------------------------------------------------------------
# Dispatcher protocol
# ---------------------------------------------------------------------------


class EventDispatcherProtocol(Protocol):
    """Interface services depend on."""

    def register(
        self,
        event_type: type[Any],
        handler: Handler,
    ) -> None: ...

    async def dispatch(self, event: Any) -> None: ...


# ---------------------------------------------------------------------------
# Concrete in-process dispatcher
# ---------------------------------------------------------------------------


class InProcessEventDispatcher:
    """In-process dispatcher.

    The handler registry is a plain dict ``{event_type: [handler...]}``.
    Registration is intended to happen at startup, dispatch on
    every event. We snapshot the handler list under an asyncio
    lock at dispatch time so a handler may safely call
    ``register`` from inside itself (e.g. one-shot subscriptions).

    Handler errors are logged and skipped — see module docstring.
    """

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._handlers: dict[type[Any], list[Handler]] = {}

    def register(
        self,
        event_type: type[Any],
        handler: Handler,
    ) -> None:
        """Subscribe ``handler`` to all events of ``event_type``."""
        self._handlers.setdefault(event_type, []).append(handler)

    async def dispatch(self, event: Any) -> None:
        """Run every handler registered for ``type(event)``.

        A handler that raises is logged and skipped — the next
        handler still runs. This is deliberate: a flaky analytics
        sink must not break the request that dispatched the
        event.
        """
        event_type = type(event)
        # Snapshot under lock so a handler that calls
        # ``register`` doesn't invalidate iteration.
        async with self._lock:
            handlers = list(self._handlers.get(event_type, ()))

        for handler in handlers:
            try:
                result = handler(event)
                if inspect.isawaitable(result):
                    await result
            except Exception as exc:
                # Log event type + handler qualname so operators
                # can identify the failing consumer without
                # leaking payload content (which could contain
                # PII in future events).
                log.warning(
                    "event_handler_failed",
                    event_type=event_type.__name__,
                    handler=getattr(handler, "__qualname__", repr(handler)),
                    error=str(exc),
                )


# ---------------------------------------------------------------------------
# Noop dispatcher
# ---------------------------------------------------------------------------


class NoopEventDispatcher:
    """Dispatcher used when no module has wired any handlers.

    Lets catalog/problems services be constructed in tests and
    CLI scripts that don't care about progress tracking, without
    forcing a real dispatcher to be wired in.
    """

    def register(
        self,
        event_type: type[Any],
        handler: Handler,
    ) -> None:
        return

    async def dispatch(self, event: Any) -> None:
        return


__all__ = [
    "EventDispatcherProtocol",
    "Handler",
    "InProcessEventDispatcher",
    "ItemViewedEvent",
    "NoopEventDispatcher",
]
