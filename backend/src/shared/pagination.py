"""Pagination primitives shared across all list endpoints.

This module owns two things:

1. ``Pagination`` — a typed, immutable request-side handle
   (page / page_size / offset / limit). Routers construct it
   from query params; repositories consume it.
2. ``Page`` — a generic, immutable response-side envelope
   (items + page + page_size + total + total_pages). This is
   the shape every list endpoint returns, per
   ALGOVISION_BACKEND_PLAN §7.

Why this lives in shared/
-------------------------
Pagination math is the canonical DRY anchor listed in
PUKU_BACKEND_AGENT §3.6 — every list endpoint needs the same
``offset = (page - 1) * page_size`` calculation and the same
response shape. Repeating that math per module invites drift
(two endpoints disagreeing about what "page 0" means, or one
returning ``total_pages`` and the other not).

Bounds policy
-------------
- ``page >= 1``        : 1-indexed for human readability.
- ``1 <= page_size <= 100``: typical SaaS bounds. Large pages
  inflate server memory and slow JSON serialization; small
  pages increase request rate without UX benefit. The cap is
  configurable via ``MAX_PAGE_SIZE`` so a future admin-facing
  endpoint can request more.
- ``total_pages`` is ``ceil(total / page_size)`` but with a
  minimum of 1 (an empty result still has 1 page).

Refs: ALGOVISION_BACKEND_PLAN §7 (Pagination envelope)
Refs: PUKU_BACKEND_AGENT §3.6 (DRY — pagination math)
Refs: PUKU_BACKEND_AGENT §9 (Repository conventions)
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

MAX_PAGE_SIZE: int = 100
DEFAULT_PAGE_SIZE: int = 20


@dataclass(frozen=True, slots=True)
class Pagination:
    """Request-side pagination handle.

    Construct from query params via ``Pagination.from_query``
    (validates bounds) or directly (assumes already validated).
    """

    page: int
    page_size: int

    @classmethod
    def from_query(cls, page: int, page_size: int) -> Pagination:
        """Validate and normalize incoming query params.

        - ``page`` < 1 is clamped to 1 (rather than rejected)
          so a typo in the URL never returns an empty response.
        - ``page_size`` < 1 becomes ``DEFAULT_PAGE_SIZE``.
        - ``page_size`` > ``MAX_PAGE_SIZE`` is capped.
        """
        page = max(1, page)
        page_size = max(1, min(MAX_PAGE_SIZE, page_size))
        return cls(page=page, page_size=page_size)

    @property
    def offset(self) -> int:
        """0-indexed offset for SQL ``OFFSET``."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Row cap for SQL ``LIMIT``."""
        return self.page_size


@dataclass(frozen=True, slots=True)
class Page[T]:
    """Response-side pagination envelope.

    Immutable so it can't be mutated after the repository hands
    it to the router. Generic over the item type — the response
    schema layer (Pydantic) maps ORM rows to response DTOs, but
    this ``Page`` wraps whatever sequence the repository chose
    to return (usually ORM rows; the service layer is
    responsible for converting to Pydantic).
    """

    items: Sequence[T]
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        """Total number of pages, minimum 1 even when empty.

        An empty result is conventionally "page 1 of 1", not
        "page 1 of 0" — clients shouldn't have to special-case.
        """
        if self.total == 0:
            return 1
        return math.ceil(self.total / self.page_size)


__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "Page",
    "Pagination",
]
