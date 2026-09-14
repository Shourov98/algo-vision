"""``algorithm_code_versions`` table — versioned source code.

Each algorithm can have many (language, version) rows. The
``is_current`` flag picks the row the catalog renders by default
for a given (algorithm_id, language). The table is append-only:
edits create a new version row, never mutate an existing one.

Why versioned source code
-------------------------
Two reasons (ALGOVISION_BACKEND_PLAN §5 / DATABASE_DESIGN §1):

1. Audit + rollback: every published code change has a
   versioned row. We can rewind a buggy release to the previous
   version without restoring from backup.
2. Frontend can ask for "show the v2 JavaScript" explicitly
   for comparison/learning views — current code is the default,
   prior versions are reachable.

Why ``is_current`` as a flag rather than a separate "current" table
-------------------------------------------------------------------
A separate ``algorithm_current_code`` table would require a join
on every read. With ``is_current`` and a partial unique index
emitted by the migration, we get the same guarantee — exactly
one row per (algorithm_id, language) is current — without a join.

Source code is TEXT
-------------------
No length cap; algorithms are short but multi-language samples
can include explanatory comments. Argon2-style text-vs-varchar
trade-off applies — TEXT to avoid future surprises.

CASCADE on the FK
-----------------
DATABASE_DESIGN §4.2: code versions are useless without the
parent algorithm. Deleting an algorithm should remove all its
code versions in one shot. RESTRICT would force the explicit
teardown that the catalog never needs.

Refs: DATABASE_DESIGN.md §1 (ERD: algorithm_code_versions),
       §4 (constraints), §5 (indexes), §6 (0006)
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class AlgorithmCodeVersion(Base):
    """Versioned source code for an algorithm in a given language."""

    __tablename__ = "algorithm_code_versions"

    # ----- Identity ---------------------------------------------------------
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # ----- FK ---------------------------------------------------------------
    algorithm_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        nullable=False,
    )

    # ----- Content ----------------------------------------------------------
    language: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    source_code: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ----- Versioning -------------------------------------------------------
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("FALSE"),
    )

    # ----- Timestamps -------------------------------------------------------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    def __repr__(self) -> str:
        return f"<AlgorithmCodeVersion id={self.id}>"

    def __eq__(self, other: object) -> bool:
        return self is other

    def __hash__(self) -> int:
        return id(self)
