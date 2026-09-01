"""Problems module repository — package root.

Re-exports per-entity repository protocols + concrete impls
so callers can do
``from src.modules.problems.repository import ProblemRepository``.
"""

from __future__ import annotations

from src.modules.problems.repository.problems import (
    ProblemRepository,
    ProblemRepositoryProtocol,
)

__all__ = ["ProblemRepository", "ProblemRepositoryProtocol"]
