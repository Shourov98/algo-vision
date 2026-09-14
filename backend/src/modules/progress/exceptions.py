"""Progress-specific domain exceptions.

Most progress operations are idempotent upserts (B5.5), so
a "not found" is rare. The cases that do raise are:

- Explicit delete operations (not in v1).
- Cross-entity lookups where the parent must exist (e.g. a
  progress row referencing an algorithm that was deleted
  while the request was in flight — the FK CASCADE would
  have removed the row, so the not-found is the only
  honest answer).

Why one file
------------
Keeping the exceptions next to the module that owns them
(``progress``) lets the import graph flow in one direction
— progress → core, never the other way — and avoids
fanning out exception modules for one or two classes.

Refs: PUKU_BACKEND_AGENT.md §6 (services raise domain errors)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5)
"""

from __future__ import annotations

from src.core.errors import NotFound


class ProgressNotFound(NotFound):
    """Raised when a progress lookup misses.

    Status code: 404.
    Code: ``progress.not_found``.
    """

    code = "progress.not_found"


__all__ = ["ProgressNotFound"]
