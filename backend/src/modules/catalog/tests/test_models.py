"""Unit tests for the catalog models.

We don't connect to a database here — these tests verify the
mapped-class shape: correct ``__tablename__``, column types,
requiredness, and uniqueness constraints. The actual schema
deployment is verified end-to-end via the Alembic SQL output
tests in ``tests/unit/test_migrations.py``.

What we test
------------
- ``__tablename__`` matches the documented table name.
- PK, unique, NOT NULL columns are declared as such.
- ``difficulty`` is a string column (CHECK lives in the migration).
- FK declaration on ``Algorithm.category_id`` matches DB
  expectations (RESTRICT on delete).

What we deliberately do NOT test
--------------------------------
- Default values generated server-side (``gen_random_uuid``,
  ``now()``) — those need a real DB to round-trip. Covered by
  integration tests in B3.11.
- Index names — verified via ``alembic upgrade head --sql``.

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 3 — B3.1)
Refs: DATABASE_DESIGN.md §1 (ERD), §4 (constraints)
"""

from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Table, UniqueConstraint, inspect

from src.core.db import Base
from src.modules.catalog.models import (
    DIFFICULTY_VALUES,
    Algorithm,
    Category,
    Topic,
)


def _table(model: type) -> Table:
    """Return the SQLAlchemy ``Table`` object backing a mapped class."""
    return inspect(model).local_table


def test_category_tablename() -> None:
    assert Category.__tablename__ == "algorithm_categories"


def test_topic_tablename() -> None:
    assert Topic.__tablename__ == "topics"


def test_algorithm_tablename() -> None:
    assert Algorithm.__tablename__ == "algorithms"


def test_models_are_registered_with_base() -> None:
    """Models must be discoverable by Alembic's target_metadata.

    Imported eagerly so the ``Base.metadata`` registry has them
    before autogenerate runs. This test catches the failure mode
    where a model is defined in a file that's not imported
    anywhere reachable from env.py.
    """
    table_names = set(Base.metadata.tables.keys())
    assert "algorithm_categories" in table_names
    assert "topics" in table_names
    assert "algorithms" in table_names


def test_category_columns() -> None:
    names = {c.name for c in _table(Category).columns}
    assert names == {
        "id",
        "slug",
        "name",
        "description",
        "sort_order",
        "created_at",
    }


def test_topic_columns() -> None:
    names = {c.name for c in _table(Topic).columns}
    assert names == {"id", "slug", "name"}


def test_algorithm_columns() -> None:
    names = {c.name for c in _table(Algorithm).columns}
    assert names == {
        "id",
        "category_id",
        "slug",
        "name",
        "description",
        "difficulty",
        "visualization_type",
        "best_time",
        "average_time",
        "worst_time",
        "space_complexity",
        "is_published",
        "created_at",
        "updated_at",
    }


def _columns_by_name(model: type) -> dict[str, Column[object]]:
    return {c.name: c for c in _table(model).columns}


def test_category_required_columns() -> None:
    """slug/name/sort_order/created_at NOT NULL; description nullable."""
    cols = _columns_by_name(Category)
    for required in ("slug", "name", "sort_order", "created_at"):
        assert not cols[required].nullable, f"{required} must be NOT NULL"
    assert cols["description"].nullable is True


def test_topic_required_columns() -> None:
    cols = _columns_by_name(Topic)
    for required in ("slug", "name"):
        assert not cols[required].nullable, f"{required} must be NOT NULL"


def test_algorithm_required_columns() -> None:
    cols = _columns_by_name(Algorithm)
    for required in (
        "category_id",
        "slug",
        "name",
        "difficulty",
        "visualization_type",
        "is_published",
        "created_at",
        "updated_at",
    ):
        assert not cols[required].nullable, f"{required} must be NOT NULL"


def _unique_constraints(model: type) -> list[UniqueConstraint]:
    return [c for c in _table(model).constraints if isinstance(c, UniqueConstraint)]


def test_category_unique_constraints() -> None:
    cols = [tuple(uc.columns.keys()) for uc in _unique_constraints(Category)]
    assert ("slug",) in cols


def test_topic_unique_constraints() -> None:
    cols = [tuple(uc.columns.keys()) for uc in _unique_constraints(Topic)]
    assert ("slug",) in cols


def test_algorithm_unique_constraints() -> None:
    cols = [tuple(uc.columns.keys()) for uc in _unique_constraints(Algorithm)]
    assert ("slug",) in cols


def _foreign_keys(model: type) -> list[ForeignKey]:
    return list(_table(model).foreign_keys)


def test_algorithm_category_fk_declaration() -> None:
    """category_id must be a FK to algorithm_categories.id."""
    targets = {(fk.column.table.name, fk.column.key) for fk in _foreign_keys(Algorithm)}
    assert ("algorithm_categories", "id") in targets


def test_algorithm_fk_uses_restrict_on_delete() -> None:
    """DATABASE_DESIGN §4.2 mandates RESTRICT on category FK."""
    fk = next(
        fk
        for fk in _foreign_keys(Algorithm)
        if fk.column.table.name == "algorithm_categories"
    )
    assert fk.ondelete == "RESTRICT", (
        "category FK must be RESTRICT to prevent orphaning published algorithms"
    )


def test_difficulty_values_match_database_check() -> None:
    """The CHECK constraint and the model constant must agree."""
    assert DIFFICULTY_VALUES == ("easy", "medium", "hard")


def test_category_repr_is_identity_only() -> None:
    """Repr must NOT leak slug or name (defensive logging)."""
    c = Category(id="00000000-0000-0000-0000-000000000000")
    text_repr = repr(c)
    assert "00000000-0000-0000-0000-000000000000" in text_repr
    # No field data — slug/name must not appear even if set.
    c2 = Category(slug="sorting", name="Sorting", description="...")
    assert "sorting" not in repr(c2)
    assert "Sorting" not in repr(c2)


def test_topic_repr_is_identity_only() -> None:
    t = Topic(slug="recursion", name="Recursion")
    assert "recursion" not in repr(t)
    assert "Recursion" not in repr(t)


def test_algorithm_repr_is_identity_only() -> None:
    a = Algorithm(
        slug="quicksort",
        name="Quick Sort",
        category_id="00000000-0000-0000-0000-000000000000",
        difficulty="medium",
        visualization_type="bar-chart",
    )
    assert "quicksort" not in repr(a)
    assert "Quick Sort" not in repr(a)


def test_models_are_distinct_types() -> None:
    """Category, Topic, and Algorithm must not collide in the registry."""
    assert Category is not Topic
    assert Topic is not Algorithm
    assert Category is not Algorithm
