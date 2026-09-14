"""Unit tests for the catalog repositories (B3.5).

These tests verify *query construction* — the SQL the
repositories emit given a Filters object — without requiring
a live PostgreSQL. The pattern: instantiate the repo with a
mock ``AsyncSession``, call ``list()``, capture the statement
passed to ``session.execute``, and assert on its literal
SQL text.

End-to-end tests against a real database live in B3.11.

Why mock the session instead of using SQLite
---------------------------------------------
SQLite is forbidden (PUKU_BACKEND_AGENT §13.3) because it
doesn't support PG-specific features the catalog queries rely
on: partial UNIQUE indexes (B3.3), CITEXT, UUID default, etc.

The next-best approach is to assert that the query the repo
builds is syntactically what we expect. We use SQLAlchemy's
``literal_compile`` (PG dialect) to render the SQL string and
grep for the documented clauses. This catches regressions
where someone renames a column or drops a JOIN.

Refs: PUKU_BACKEND_AGENT §9 (Repository conventions), §13.3
      (no SQLite for tests)
Refs: ALGOVISION_BACKEND_PLAN §7 (Filtering & Pagination)
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

# Force PG dialect compilation so the literal SQL matches
# what alembic emits in CI.
from sqlalchemy.dialects import postgresql

from src.modules.catalog.filters import (
    AlgorithmCodeVersionFilters,
    AlgorithmFilters,
    CategoryFilters,
    DataStructureFilters,
    TopicFilters,
)
from src.modules.catalog.repository import (
    AlgorithmCodeVersionRepository,
    AlgorithmRepository,
    CategoryRepository,
    DataStructureRepository,
    TopicRepository,
)
from src.shared.filters import SortOrder
from src.shared.pagination import Pagination


def _compile(stmt) -> str:
    """Render a SQLAlchemy statement as a literal PostgreSQL string."""
    return str(stmt.compile(dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}))


def _session_with_scalar_returning(value: object) -> AsyncMock:
    """Return a mock AsyncSession whose execute().scalar_one() returns ``value``.

    Used to satisfy the count query path. The list-path result
    is also captured; tests inspect the *statement* passed to
    execute(), not the result.
    """
    session = AsyncMock()
    scalars_result = MagicMock()
    scalars_result.scalars.return_value.all.return_value = []
    scalars_result.scalar_one.return_value = value
    session.execute.side_effect = [scalars_result, scalars_result]
    return session


# ---------------------------------------------------------------------------
# CategoryRepository
# ---------------------------------------------------------------------------


def test_category_repository_list_emits_select_with_pagination() -> None:
    session = _session_with_scalar_returning(0)
    repo = CategoryRepository(session)

    import asyncio

    asyncio.run(
        repo.list(
            CategoryFilters(
                pagination=Pagination(page=2, page_size=10),
            )
        )
    )

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "algorithm_categories" in sql
    assert "LIMIT 10" in sql
    # Page 2, page_size 10 → offset 10.
    assert "OFFSET 10" in sql


def test_category_repository_list_search_uses_ilike() -> None:
    session = _session_with_scalar_returning(0)
    repo = CategoryRepository(session)

    import asyncio

    asyncio.run(
        repo.list(
            CategoryFilters(
                search="sort",
            )
        )
    )

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "ILIKE" in sql.upper() or "ilike" in sql
    assert "%sort%" in sql


def test_category_repository_list_sort_by_name_orders_by_name() -> None:
    from src.modules.catalog.filters import CategorySortField

    session = _session_with_scalar_returning(0)
    repo = CategoryRepository(session)

    import asyncio

    asyncio.run(
        repo.list(
            CategoryFilters(
                sort_by=CategorySortField.NAME,
                sort_order=SortOrder.DESC,
            )
        )
    )

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "ORDER BY" in sql.upper() or "order by" in sql.lower()
    assert "name" in sql
    assert "DESC" in sql.upper()


# ---------------------------------------------------------------------------
# TopicRepository
# ---------------------------------------------------------------------------


def test_topic_repository_list_filters_by_search() -> None:
    session = _session_with_scalar_returning(0)
    repo = TopicRepository(session)

    import asyncio

    asyncio.run(
        repo.list(
            TopicFilters(
                search="recursion",
            )
        )
    )

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "topics" in sql
    assert "%recursion%" in sql


# ---------------------------------------------------------------------------
# AlgorithmRepository
# ---------------------------------------------------------------------------


def test_algorithm_repository_list_filters_by_is_published() -> None:
    session = _session_with_scalar_returning(0)
    repo = AlgorithmRepository(session)

    import asyncio

    asyncio.run(repo.list(AlgorithmFilters(is_published=False)))

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "algorithms" in sql
    assert "is_published" in sql
    assert "false" in sql.lower()


def test_algorithm_repository_list_search_uses_ilike() -> None:
    session = _session_with_scalar_returning(0)
    repo = AlgorithmRepository(session)

    import asyncio

    asyncio.run(repo.list(AlgorithmFilters(search="quick")))

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "%quick%" in sql


def test_algorithm_repository_list_category_uses_subquery() -> None:
    """``filters.category`` should emit ``algorithm.category_id IN (SELECT id FROM categories WHERE slug = ...)``."""
    session = _session_with_scalar_returning(0)
    repo = AlgorithmRepository(session)

    import asyncio

    asyncio.run(repo.list(AlgorithmFilters(category="sorting")))

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "algorithm_categories" in sql
    assert "IN" in sql.upper()
    assert "sorting" in sql


def test_algorithm_repository_list_topic_uses_join() -> None:
    """``filters.topic`` should JOIN to algorithm_topics + topics."""
    session = _session_with_scalar_returning(0)
    repo = AlgorithmRepository(session)

    import asyncio

    asyncio.run(repo.list(AlgorithmFilters(topic="recursion")))

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "algorithm_topics" in sql
    assert "JOIN" in sql.upper()
    assert "topics" in sql
    assert "recursion" in sql
    # DISTINCT guards against double-counting.
    assert "DISTINCT" in sql.upper()


def test_algorithm_repository_list_pagination_applies_limit_offset() -> None:
    session = _session_with_scalar_returning(0)
    repo = AlgorithmRepository(session)

    import asyncio

    asyncio.run(
        repo.list(
            AlgorithmFilters(
                pagination=Pagination(page=3, page_size=25),
            )
        )
    )

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "LIMIT 25" in sql
    assert "OFFSET 50" in sql  # (3-1) * 25


# ---------------------------------------------------------------------------
# DataStructureRepository
# ---------------------------------------------------------------------------


def test_data_structure_repository_list_filters_by_difficulty() -> None:
    session = _session_with_scalar_returning(0)
    repo = DataStructureRepository(session)

    import asyncio

    asyncio.run(repo.list(DataStructureFilters(difficulty="easy")))

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert "data_structures" in sql
    assert "difficulty" in sql
    assert "easy" in sql


# ---------------------------------------------------------------------------
# AlgorithmCodeVersionRepository
# ---------------------------------------------------------------------------


def test_code_version_repository_get_current_emits_partial_filter() -> None:
    """get_current must filter on is_current = TRUE (uses partial UNIQUE)."""
    session = AsyncMock()
    scalars_result = MagicMock()
    scalars_result.scalar_one_or_none.return_value = None
    session.execute.return_value = scalars_result

    repo = AlgorithmCodeVersionRepository(session)

    algo_id = UUID("11111111-1111-1111-1111-111111111111")
    import asyncio

    asyncio.run(repo.get_current(algo_id, "python"))

    stmt = session.execute.call_args.args[0]
    sql = _compile(stmt)
    assert "algorithm_code_versions" in sql
    assert "algorithm_id" in sql
    assert "language" in sql
    assert "is_current" in sql
    assert "python" in sql


def test_code_version_repository_list_filters_by_algorithm_id() -> None:
    session = _session_with_scalar_returning(0)
    repo = AlgorithmCodeVersionRepository(session)

    algo_id_str = "11111111-1111-1111-1111-111111111111"

    import asyncio

    asyncio.run(
        repo.list(
            AlgorithmCodeVersionFilters(algorithm_id=algo_id_str),
        )
    )

    stmt = session.execute.call_args_list[0].args[0]
    sql = _compile(stmt)
    assert algo_id_str in sql


# ---------------------------------------------------------------------------
# Page envelope
# ---------------------------------------------------------------------------


def test_page_envelope_total_pages_min_is_one_for_empty() -> None:
    """An empty result must report total_pages == 1 (page 1 of 1)."""
    from src.shared.pagination import Page

    p: Page[object] = Page(items=[], page=1, page_size=20, total=0)
    assert p.total_pages == 1


def test_page_envelope_total_pages_rounds_up() -> None:
    from src.shared.pagination import Page

    p: Page[object] = Page(items=[], page=1, page_size=20, total=41)
    # 41 / 20 → ceil(2.05) = 3
    assert p.total_pages == 3


# ---------------------------------------------------------------------------
# Pagination normalization
# ---------------------------------------------------------------------------


def test_pagination_from_query_clamps_invalid_page() -> None:
    p = Pagination.from_query(page=0, page_size=20)
    assert p.page == 1


def test_pagination_from_query_caps_oversized_page_size() -> None:
    p = Pagination.from_query(page=1, page_size=10_000)
    assert p.page_size == 100  # MAX_PAGE_SIZE


def test_pagination_from_query_floors_undersized_page_size() -> None:
    p = Pagination.from_query(page=1, page_size=0)
    assert p.page_size == 1


def test_pagination_offset_is_zero_indexed() -> None:
    p = Pagination(page=1, page_size=20)
    assert p.offset == 0
    p = Pagination(page=2, page_size=20)
    assert p.offset == 20
