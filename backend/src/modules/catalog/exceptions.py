"""Catalog-specific domain exceptions.

These are the typed errors catalog services raise when the
public catalog contract is violated (entity not found, item
hidden from public view, etc.). The exception handler in
``main.py`` turns them into JSON envelopes with stable codes.

Why one file
------------
Catalog entities share the same 404/403 patterns. Keeping
them in one module prevents the ``exceptions.py`` per
service file split from creating churn every time a new
catalog entity is added.

Refs: PUKU_BACKEND_AGENT.md §6 (services raise domain errors)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 3)
"""

from __future__ import annotations

from src.core.errors import Forbidden, NotFound


class AlgorithmNotFound(NotFound):
    """Raised when an algorithm lookup misses (by slug or id)."""

    code = "catalog.algorithm_not_found"


class CategoryNotFound(NotFound):
    """Raised when an algorithm category lookup misses."""

    code = "catalog.category_not_found"


class TopicNotFound(NotFound):
    """Raised when a topic lookup misses."""

    code = "catalog.topic_not_found"


class DataStructureNotFound(NotFound):
    """Raised when a data-structure lookup misses."""

    code = "catalog.data_structure_not_found"


class AlgorithmCodeVersionNotFound(NotFound):
    """Raised when no current code version exists for a
    given (algorithm, language) pair.
    """

    code = "catalog.algorithm_code_version_not_found"


class NotPublished(Forbidden):
    """Raised when a caller asks for an unpublished algorithm
    without staff privileges.
    """

    code = "catalog.not_published"


__all__ = [
    "AlgorithmCodeVersionNotFound",
    "AlgorithmNotFound",
    "CategoryNotFound",
    "DataStructureNotFound",
    "NotPublished",
    "TopicNotFound",
]
