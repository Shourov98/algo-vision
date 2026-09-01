"""Static validation tests for the catalog seed data.

The seed runner is exercised end-to-end by integration tests
(B3.11) against a real Postgres. These tests instead verify
the seed definitions in isolation — every row has the shape
the DB expects, every FK reference resolves to a real seed
row, no slug duplicates — so we don't need a database to
catch the common mistakes.

Why these tests exist
---------------------
A typo in a seed tuple (e.g. ``difficulty="Hard"`` instead of
``"hard"``) would surface only on the integration test, which
requires a live Postgres. Static validation catches it at
unit-test speed and gives the seed authors a fast feedback
loop.

What these tests don't cover
-----------------------------
- Actual DB constraints (CHECK on difficulty values, FKs to
  tables we don't seed). Those live in the migration tests +
  integration tests.
- Idempotency (ON CONFLICT semantics). Integration test.

Refs: DATABASE_DESIGN.md §7 (Seed Plan), §7.2 (Idempotency)
Refs: ALGOVISION_BACKEND_PLAN.md §3.10 (B3.10 seeds)
"""

from __future__ import annotations

import re
from typing import Final

import pytest
from src.modules.catalog.models.algorithm import DIFFICULTY_VALUES
from src.seeds.algorithm_code_versions_data import CODE_VERSIONS
from src.seeds.algorithms_data import ALGORITHMS
from src.seeds.categories import CATEGORIES
from src.seeds.data_structures import DATA_STRUCTURES
from src.seeds.topics import TOPICS

# ---------------------------------------------------------------------------
# Slug shape: lowercase kebab-case, max 96 chars
# ---------------------------------------------------------------------------

SLUG_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _is_valid_slug(slug: str, max_len: int = 96) -> bool:
    return bool(SLUG_RE.match(slug)) and len(slug) <= max_len


def test_category_slugs_are_valid() -> None:
    for c in CATEGORIES:
        assert _is_valid_slug(c.slug, max_len=64), c.slug


def test_topic_slugs_are_valid() -> None:
    for t in TOPICS:
        assert _is_valid_slug(t.slug, max_len=64), t.slug


def test_algorithm_slugs_are_valid() -> None:
    for a in ALGORITHMS:
        assert _is_valid_slug(a.slug), a.slug


def test_data_structure_slugs_are_valid() -> None:
    for d in DATA_STRUCTURES:
        assert _is_valid_slug(d.slug), d.slug


# ---------------------------------------------------------------------------
# Slug uniqueness within each entity
# ---------------------------------------------------------------------------


def test_category_slugs_are_unique() -> None:
    slugs = [c.slug for c in CATEGORIES]
    assert len(slugs) == len(set(slugs)), (
        f"duplicate category slugs: {slugs}"
    )


def test_topic_slugs_are_unique() -> None:
    slugs = [t.slug for t in TOPICS]
    assert len(slugs) == len(set(slugs))


def test_algorithm_slugs_are_unique() -> None:
    slugs = [a.slug for a in ALGORITHMS]
    assert len(slugs) == len(set(slugs))


def test_data_structure_slugs_are_unique() -> None:
    slugs = [d.slug for d in DATA_STRUCTURES]
    assert len(slugs) == len(set(slugs))


# ---------------------------------------------------------------------------
# Difficulty is the closed vocabulary
# ---------------------------------------------------------------------------


def test_algorithm_difficulty_is_in_vocabulary() -> None:
    for a in ALGORITHMS:
        assert a.difficulty in DIFFICULTY_VALUES, (
            f"{a.slug}: difficulty={a.difficulty!r} not in {DIFFICULTY_VALUES}"
        )


def test_data_structure_difficulty_is_in_vocabulary() -> None:
    for d in DATA_STRUCTURES:
        assert d.difficulty in DIFFICULTY_VALUES, (
            f"{d.slug}: difficulty={d.difficulty!r} not in {DIFFICULTY_VALUES}"
        )


# ---------------------------------------------------------------------------
# FK integrity — every algorithm references a real category
# ---------------------------------------------------------------------------


def test_every_algorithm_category_is_known() -> None:
    known = {c.slug for c in CATEGORIES}
    for a in ALGORITHMS:
        assert a.category_slug in known, (
            f"algorithm {a.slug!r} references unknown category "
            f"{a.category_slug!r}"
        )


# ---------------------------------------------------------------------------
# Topic M:N integrity — every topic reference is known
# ---------------------------------------------------------------------------


def test_every_algorithm_topic_is_known() -> None:
    known = {t.slug for t in TOPICS}
    for a in ALGORITHMS:
        for topic_slug in a.topic_slugs:
            assert topic_slug in known, (
                f"algorithm {a.slug!r} references unknown topic "
                f"{topic_slug!r}"
            )


def test_every_algorithm_topic_is_unique_within_algorithm() -> None:
    """An algorithm's topic list shouldn't list the same topic twice."""
    for a in ALGORITHMS:
        assert len(a.topic_slugs) == len(set(a.topic_slugs)), (
            f"algorithm {a.slug!r} has duplicate topic slugs: "
            f"{a.topic_slugs}"
        )


# ---------------------------------------------------------------------------
# Code versions
# ---------------------------------------------------------------------------


def test_every_code_version_targets_a_seeded_algorithm() -> None:
    known = {a.slug for a in ALGORITHMS}
    for cv in CODE_VERSIONS:
        assert cv.algorithm_slug in known, (
            f"code version for unknown algorithm {cv.algorithm_slug!r}"
        )


def test_code_versions_have_non_empty_source() -> None:
    for cv in CODE_VERSIONS:
        assert cv.source_code.strip(), (
            f"empty source code for {cv.algorithm_slug!r} in "
            f"{cv.language!r}"
        )


def test_code_version_language_is_short_token() -> None:
    """Language slugs are short (DB column is VARCHAR(32))."""
    for cv in CODE_VERSIONS:
        assert cv.language and len(cv.language) <= 32, (
            f"language {cv.language!r} for {cv.algorithm_slug!r} "
            "too long or empty"
        )


# ---------------------------------------------------------------------------
# Coverage sanity — every category is represented
# ---------------------------------------------------------------------------


def test_every_category_has_at_least_one_algorithm() -> None:
    """Coverage check: no category ships empty."""
    seen: dict[str, int] = {c.slug: 0 for c in CATEGORIES}
    for a in ALGORITHMS:
        seen[a.category_slug] += 1
    missing = [slug for slug, n in seen.items() if n == 0]
    assert not missing, f"categories with no algorithms: {missing}"


# ---------------------------------------------------------------------------
# Parametrize-driven detail checks
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "slug",
    [
        "bubble-sort",
        "quick-sort",
        "merge-sort",
        "binary-search",
        "dijkstra",
        "bfs",
        "dfs",
        "fibonacci",
        "knapsack-01",
        "activity-selection",
        "karatsuba",
        "kmp",
        "inorder-traversal",
    ],
)
def test_smoke_known_algorithms_are_seeded(slug: str) -> None:
    """Smoke: the algorithms called out in the catalog narrative are seeded.

    These are the algorithms the frontend will reference in the
    visual references (Quick Sort, Dijkstra, Linked List
    visualizations, etc.). If someone removes one of them in a
    future seed edit, this test fails loudly.
    """
    seeded = {a.slug for a in ALGORITHMS}
    assert slug in seeded


__all__: list[object] = []
