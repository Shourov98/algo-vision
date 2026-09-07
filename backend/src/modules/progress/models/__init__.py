"""Progress SQLAlchemy 2.x models — package root.

Re-exports every mapped class so callers can write
``from src.modules.progress.models import UserAlgorithmProgress``
exactly as they did when this was a flat ``models.py`` file.

Phase 5 ships incrementally (B5.1, B5.2, B5.3, ...). This file
is updated as each model lands:

- ``user_algorithm_progress.py`` — UserAlgorithmProgress + STATUS_VALUES (B5.1)
- ``user_problem_progress.py`` — UserProblemProgress (B5.2)
- ``user_recent_items.py`` — UserRecentItem + ITEM_TYPE_VALUES (B5.3)

Why split per file (not one big module)
---------------------------------------
The progress module already has 3 tracked tables and may grow
later (per-topic mastery, etc.). Each table deserves its own
file so the package stays readable and the file size rule
(PUKU_BACKEND_AGENT §3.7) is easy to satisfy.

Refs: DATABASE_DESIGN.md §1 (ERD: progress tables), §4
       (constraints), §5 (indexes)
Refs: ALGOVISION_BACKEND_PLAN.md §5 (Phase 5 — Progress)
Refs: PUKU_BACKEND_AGENT.md §3.7 (file size: split by responsibility)
"""

from src.modules.progress.models.user_algorithm_progress import (
    STATUS_VALUES,
    UserAlgorithmProgress,
)
from src.modules.progress.models.user_problem_progress import (
    UserProblemProgress,
)
from src.modules.progress.models.user_recent_items import (
    ITEM_TYPE_VALUES,
    UserRecentItem,
)

__all__ = [
    "ITEM_TYPE_VALUES",
    "STATUS_VALUES",
    "UserAlgorithmProgress",
    "UserProblemProgress",
    "UserRecentItem",
]
