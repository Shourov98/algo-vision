"""ETag helpers for the catalog module.

ETags let clients cache list responses cheaply: a 304
Not-Modified avoids the JSON serialization entirely. The
algorithm catalog is a read-heavy surface and updated_at
moves slowly, so an ETag keyed on the maximum updated_at
across the page set is a near-perfect cache key.

Why per-module, not in shared/
------------------------------
ETag is a transport concern (HTTP cache headers). The
algorithm is the only catalog entity with an ``updated_at``
column today; data structures and categories don't have
one. When those entities grow a cache key, the helper
moves next to them (not here). Keeping the helper next
to its consumer is the SOLID-segregation move.

Algorithm
---------
For the list endpoint, the ETag is computed from the
maximum ``updated_at`` across the returned page PLUS the
filter hash (so changing the filter changes the ETag).

For the detail endpoint, the ETag is the quoted
``updated_at`` of the single algorithm.

Why a quoted weak-validator format
----------------------------------
We use ``W/"<hash>"`` (RFC 7232 weak validator) because
the ETag is a derivative of the timestamp, not a
byte-identical representation of the response. Clients
that respect weak validators will treat the comparison
as semantic (any byte representation of the same logical
resource matches). Most clients treat weak/strong the
same way; weak is the safer choice here.

Refs: ALGOVISION_BACKEND_PLAN §3.9 (B3.9 ETag),
      §7 (Caching)
Refs: PUKU_BACKEND_AGENT §3.1 (no logic in routers — these
      are pure HTTP-shape helpers, no business rules)
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable
from datetime import datetime
from typing import Protocol


class _HasUpdatedAt(Protocol):
    """Structural type for response objects exposing ``updated_at``.

    Lets ``max_updated_at_from`` work on the algorithm response
    rows without importing the Pydantic class — duck typing
    on the one attribute the ETag algorithm reads.
    """

    updated_at: datetime


def max_updated_at_from(
    items: Iterable[_HasUpdatedAt],
) -> datetime | None:
    """Return the largest ``updated_at`` in ``items`` or None.

    Computed at the router boundary (HTTP transport concern —
    we need the value to derive an ETag, not to drive any
    business rule). Pages are bounded by ``page_size <= 100``
    so the scan is O(100) — negligible.
    """
    best: datetime | None = None
    for item in items:
        ts = item.updated_at
        if best is None or ts > best:
            best = ts
    return best


def etag_from_updated_at(
    updated_at: datetime,
    *,
    salt: str = "",
) -> str:
    """Return a weak ETag for a single resource.

    ``salt`` lets callers namespace the ETag so a single
    timestamp can't be reused across endpoints (e.g. the
    list endpoint and the detail endpoint should never
    share an ETag value).
    """
    raw = f"{salt}{updated_at.isoformat()}".encode()
    digest = hashlib.md5(raw, usedforsecurity=False).hexdigest()
    return f'W/"{digest[:16]}"'


def etag_from_filters_and_max_updated_at(
    *,
    filter_hash: str,
    max_updated_at: datetime | None,
) -> str:
    """Return a weak ETag for a paginated list.

    Combines the filter signature with the latest updated_at
    in the result set. An empty result uses the epoch so the
    ETag is stable for "no algorithms match" responses.

    Why ``max(updated_at)`` not the row count
    ------------------------------------------
    A new row added after the response was cached invalidates
    the ETag (the row's updated_at is later), even though the
    cached page is still on disk. This is the desired
    behavior — clients re-fetch the page and get the new
    count on the next request.
    """
    if max_updated_at is None:
        # Epoch (UTC) for the empty case. Using the epoch
        # makes the empty-page ETag stable across requests
        # AND distinguishable from a non-empty response.
        max_updated_at = datetime.fromtimestamp(0)
    raw = f"{filter_hash}{max_updated_at.isoformat()}".encode()
    digest = hashlib.md5(raw, usedforsecurity=False).hexdigest()
    return f'W/"{digest[:16]}"'


def filter_hash(filters: object) -> str:
    """Stable hash of a filters dataclass.

    Uses the dataclass ``__repr__`` (which the standard
    library generates deterministically for frozen dataclasses)
    so two semantically-equal filters produce the same hash.

    For dataclass instances we hash the tuple of values; for
    other objects we fall back to ``repr``.
    """
    try:
        import dataclasses

        if dataclasses.is_dataclass(filters):
            values = tuple(
                getattr(filters, f.name)
                for f in dataclasses.fields(filters)
            )
            # ``values`` may itself contain dataclasses
            # (Pagination); recurse via repr of the tuple.
            raw = repr(values).encode("utf-8")
        else:
            raw = repr(filters).encode("utf-8")
    except Exception:
        raw = repr(filters).encode("utf-8")
    return hashlib.md5(raw, usedforsecurity=False).hexdigest()


__all__ = [
    "etag_from_filters_and_max_updated_at",
    "etag_from_updated_at",
    "filter_hash",
    "max_updated_at_from",
]
