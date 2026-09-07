"""Problems-specific domain exceptions.

These are the typed errors problems services raise when
the public problems contract is violated (entity not
found, item hidden from public view, etc.). The exception
handler in ``main.py`` turns them into JSON envelopes
with stable codes.

Why one file
------------
Problems and companies share the same 404 pattern. Keeping
them in one module prevents the ``exceptions.py`` per
service file split from creating churn every time a new
problems entity is added.

Refs: PUKU_BACKEND_AGENT.md §6 (services raise domain errors)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4)
"""

from __future__ import annotations

from src.core.errors import NotFound


class ProblemNotFound(NotFound):
    """Raised when a problem lookup misses (by slug or id)."""

    code = "problems.problem_not_found"


class CompanyNotFound(NotFound):
    """Raised when a company lookup misses."""

    code = "problems.company_not_found"


__all__ = [
    "CompanyNotFound",
    "ProblemNotFound",
]
