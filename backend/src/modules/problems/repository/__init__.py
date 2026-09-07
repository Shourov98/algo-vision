"""Problems module repository - package root.

Re-exports per-entity repository protocols + concrete impls
so callers can do
``from src.modules.problems.repository import ProblemRepository``.
"""

from __future__ import annotations

from src.modules.problems.repository.companies import (
    CompanyRepository,
    CompanyRepositoryProtocol,
)
from src.modules.problems.repository.problems import (
    ProblemRepository,
    ProblemRepositoryProtocol,
)

__all__ = [
    "CompanyRepository",
    "CompanyRepositoryProtocol",
    "ProblemRepository",
    "ProblemRepositoryProtocol",
]
