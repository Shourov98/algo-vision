"""Problems SQLAlchemy 2.x models — package root.

Re-exports every mapped class so callers can write
``from src.modules.problems.models import Problem`` exactly as
they did when this was a flat ``models.py`` file.

Phase 4 ships incrementally (B4.1, B4.2, B4.3, ...). This
file is updated as each model lands:

- ``problem.py`` — Problem (problems) + DIFFICULTY_VALUES (B4.1)
- ``company.py`` — Company (companies) (B4.2)
- ``problem_topics.py``     — M:N to topics    (B4.3)
- ``problem_companies.py``  — M:N to companies (B4.3)

Refs: DATABASE_DESIGN.md §1 (ERD), §4 (constraints), §5 (indexes)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4 — Problems)
Refs: PUKU_BACKEND_AGENT.md §3.7 (file size rule: split by responsibility)
"""

from src.modules.problems.models.company import Company
from src.modules.problems.models.problem import DIFFICULTY_VALUES, Problem

__all__ = ["DIFFICULTY_VALUES", "Company", "Problem"]
