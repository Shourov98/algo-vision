"""Catalog repositories — package root.

Re-exports every repository + its Protocol so callers can write
``from src.modules.catalog.repository import CategoryRepository``
as they would with a flat module.

Each per-entity file declares:

- One ``<Entity>RepositoryProtocol`` (LSP-substitutable in
  tests via ``Protocol``).
- One ``<Entity>Repository`` concrete async-SQLAlchemy impl.

Repositories do NOT contain business rules — see
PUKU_BACKEND_AGENT §3.1 and §9. They do:

- ``list(filters) -> Page[Entity]``
- ``get_by_slug(slug) -> Entity | None``
- ``get_by_id(id) -> Entity | None``

Special cases:

- ``AlgorithmRepository`` joins ``algorithm_topics`` to support
  topic-slug filtering.
- ``AlgorithmCodeVersionRepository`` exposes
  ``get_current(algorithm_id, language)`` for the catalog
  detail endpoint.

Refs: PUKU_BACKEND_AGENT §9 (Repository conventions), §3.1
      (no business rules)
Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering & Pagination)
Refs: DATABASE_DESIGN.md §8.1 (Q1: published-algorithms query)
"""

from src.modules.catalog.repository.algorithms import (
    AlgorithmRepository,
    AlgorithmRepositoryProtocol,
)
from src.modules.catalog.repository.categories import (
    CategoryRepository,
    CategoryRepositoryProtocol,
)
from src.modules.catalog.repository.code_versions import (
    AlgorithmCodeVersionRepository,
    AlgorithmCodeVersionRepositoryProtocol,
)
from src.modules.catalog.repository.data_structures import (
    DataStructureRepository,
    DataStructureRepositoryProtocol,
)
from src.modules.catalog.repository.topics import (
    TopicRepository,
    TopicRepositoryProtocol,
)

__all__ = [
    "AlgorithmCodeVersionRepository",
    "AlgorithmCodeVersionRepositoryProtocol",
    "AlgorithmRepository",
    "AlgorithmRepositoryProtocol",
    "CategoryRepository",
    "CategoryRepositoryProtocol",
    "DataStructureRepository",
    "DataStructureRepositoryProtocol",
    "TopicRepository",
    "TopicRepositoryProtocol",
]
