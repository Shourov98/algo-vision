"""Catalog SQLAlchemy 2.x models — package root.

Re-exports every mapped class so callers can still write
``from src.modules.catalog.models import Algorithm`` exactly as
they did when this was a flat ``models.py`` file.

The package split is per-entity:

- ``category.py``   — Category (algorithm_categories)
- ``topic.py``      — Topic (topics)
- ``algorithm.py``  — Algorithm (algorithms) + DIFFICULTY_VALUES
- ``data_structure.py`` — DataStructure (data_structures)
- ``code_version.py``   — AlgorithmCodeVersion
  (algorithm_code_versions)

Each file documents its own table and constraints. The shared
style rules (Mapped[], mapped_column, identity-only repr, no
field data in logs) are described in ``_base.py`` and inherited
implicitly by every model class.

Refs: DATABASE_DESIGN.md §1 (ERD), §4 (constraints), §5 (indexes)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 3 — Catalog)
Refs: PUKU_BACKEND_AGENT.md §3.7 (file size rule: split by responsibility)
"""

from src.modules.catalog.models.algorithm import DIFFICULTY_VALUES, Algorithm
from src.modules.catalog.models.algorithm_topics import algorithm_topics
from src.modules.catalog.models.category import Category
from src.modules.catalog.models.code_version import AlgorithmCodeVersion
from src.modules.catalog.models.data_structure import DataStructure
from src.modules.catalog.models.topic import Topic

__all__ = [
    "DIFFICULTY_VALUES",
    "Algorithm",
    "AlgorithmCodeVersion",
    "Category",
    "DataStructure",
    "Topic",
    "algorithm_topics",
]
