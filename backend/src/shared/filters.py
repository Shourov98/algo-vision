"""Typed filter base classes shared across modules.

Per ALGOVISION_BACKEND_PLAN §7 and PUKU_BACKEND_AGENT §8.3,
filter parameters are parsed at the router into typed
``*Filters`` dataclasses. Repositories accept those dataclasses,
not raw query strings.

This module owns ``SortOrder`` (the small enum used by every
sortable catalog entity). Per-entity filters (e.g.
``AlgorithmFilters``, ``ProblemFilters``) live in their
respective feature modules so they can include fields specific
to that entity.

Why a base class is NOT used
----------------------------
We considered ``class FiltersBase`` and having each entity
filter inherit from it, but the fields diverge too much:

- CategoryFilters: sort_order, name
- AlgorithmFilters: difficulty, category, topic, search, sort
- DataStructureFilters: difficulty

A base class would force a generic ``extra: dict[str, Any]``
or a wide union of optional fields — both worse than the
alternative (each entity owns its filter class).

What lives here
---------------
- ``SortOrder`` : the only shared vocabulary (asc/desc).

Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering)
Refs: PUKU_BACKEND_AGENT §8.3 (Filters)
"""

from __future__ import annotations

from enum import StrEnum


class SortOrder(StrEnum):
    """Sort direction for list endpoints.

    StrEnum gives the right Pydantic/FastAPI serialization
    behavior without a manual ``str`` mixin (Python 3.11+).
    """

    ASC = "asc"
    DESC = "desc"


__all__ = ["SortOrder"]
