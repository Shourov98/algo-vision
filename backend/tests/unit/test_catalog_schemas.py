"""Unit tests for catalog Pydantic schemas.

These tests verify the wire-format shapes — what the frontend
will see — and the schema validators. They don't touch the
DB; ORM conversion is exercised by the integration tests in
B3.11.

Refs: ALGOVISION_BACKEND_PLAN.md §3.7 (B3.7 schemas)
Refs: PUKU_BACKEND_AGENT.md §8
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError
from src.modules.catalog.schemas import (
    AlgorithmCodeResponse,
    AlgorithmDetailResponse,
    AlgorithmSummaryResponse,
    CategoryListResponse,
    CategoryResponse,
    DataStructureListResponse,
    DataStructureResponse,
    TopicListResponse,
    TopicResponse,
)

# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------


def test_category_response_accepts_known_fields() -> None:
    now = datetime.now(UTC)
    cat = CategoryResponse(
        id=uuid4(),
        slug="sorting",
        name="Sorting",
        description="Sorting algorithms",
        sort_order=1,
        created_at=now,
    )
    assert cat.slug == "sorting"
    assert cat.sort_order == 1
    assert cat.created_at == now


def test_category_response_description_is_optional() -> None:
    cat = CategoryResponse(
        id=uuid4(),
        slug="graphs",
        name="Graphs",
        sort_order=2,
        created_at=datetime.now(UTC),
    )
    assert cat.description is None


def test_category_response_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        CategoryResponse(
            id=uuid4(),
            slug="sorting",
            name="Sorting",
            sort_order=1,
            created_at=datetime.now(UTC),
            bogus="field",  # type: ignore[call-arg]
        )


def test_category_list_response_envelope_shape() -> None:
    now = datetime.now(UTC)
    items = [
        CategoryResponse(
            id=uuid4(),
            slug="sorting",
            name="Sorting",
            sort_order=1,
            created_at=now,
        )
    ]
    envelope = CategoryListResponse(
        items=items,
        page=1,
        page_size=20,
        total=1,
        total_pages=1,
    )
    assert envelope.items[0].slug == "sorting"
    assert envelope.total == 1


def test_category_list_response_rejects_zero_page() -> None:
    with pytest.raises(ValidationError):
        CategoryListResponse(items=[], page=0, page_size=20, total=0, total_pages=1)


# ---------------------------------------------------------------------------
# Topic
# ---------------------------------------------------------------------------


def test_topic_response_minimal_shape() -> None:
    topic = TopicResponse(id=uuid4(), slug="dp", name="Dynamic Programming")
    assert topic.slug == "dp"
    assert topic.name == "Dynamic Programming"


def test_topic_list_response_envelope() -> None:
    envelope = TopicListResponse(
        items=[TopicResponse(id=uuid4(), slug="dp", name="DP")],
        page=1,
        page_size=20,
        total=1,
        total_pages=1,
    )
    assert envelope.items[0].slug == "dp"


# ---------------------------------------------------------------------------
# Data structure
# ---------------------------------------------------------------------------


def test_data_structure_response_difficulty_literal() -> None:
    now = datetime.now(UTC)
    ds = DataStructureResponse(
        id=uuid4(),
        slug="stack",
        name="Stack",
        difficulty="easy",
        visualization_type="linear",
        created_at=now,
    )
    assert ds.difficulty == "easy"


def test_data_structure_response_rejects_unknown_difficulty() -> None:
    with pytest.raises(ValidationError):
        DataStructureResponse(
            id=uuid4(),
            slug="stack",
            name="Stack",
            difficulty="impossible",  # type: ignore[arg-type]
            visualization_type="linear",
            created_at=datetime.now(UTC),
        )


def test_data_structure_list_response_envelope() -> None:
    envelope = DataStructureListResponse(
        items=[],
        page=1,
        page_size=20,
        total=0,
        total_pages=1,
    )
    assert envelope.total_pages == 1


# ---------------------------------------------------------------------------
# Algorithm
# ---------------------------------------------------------------------------


def _make_algorithm_summary_dict(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": uuid4(),
        "slug": "quick-sort",
        "name": "Quick Sort",
        "difficulty": "medium",
        "visualization_type": "array",
        "category_id": uuid4(),
        "is_published": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    base.update(overrides)
    return base


def test_algorithm_summary_response_accepts_valid_payload() -> None:
    summary = AlgorithmSummaryResponse(**_make_algorithm_summary_dict())  # type: ignore[arg-type]
    assert summary.slug == "quick-sort"
    assert summary.difficulty == "medium"


def test_algorithm_summary_response_rejects_unknown_difficulty() -> None:
    with pytest.raises(ValidationError):
        AlgorithmSummaryResponse(
            **_make_algorithm_summary_dict(difficulty="nuclear")  # type: ignore[arg-type]
        )


def test_algorithm_detail_response_with_category_and_topics() -> None:
    alg_id = uuid4()
    cat_id = uuid4()
    payload = _make_algorithm_summary_dict(id=alg_id, category_id=cat_id)
    payload.pop("category_id")  # detail schema uses `category` not category_id
    payload.update(
        description="An algorithm.",
        best_time="O(n log n)",
        average_time="O(n log n)",
        worst_time="O(n^2)",
        space_complexity="O(log n)",
        category={"id": cat_id, "slug": "sorting", "name": "Sorting"},
        topics=[{"id": uuid4(), "slug": "in-place", "name": "In-place"}],
        current_code=None,
    )
    detail = AlgorithmDetailResponse(**payload)  # type: ignore[arg-type]
    assert detail.category.slug == "sorting"
    assert len(detail.topics) == 1
    assert detail.current_code is None


def test_algorithm_detail_response_defaults_for_missing_lists() -> None:
    """When ``topics`` and ``current_code`` are absent the
    schema must default to empty list / None rather than
    rejecting the payload (the detail endpoint may be hit
    before topics are wired in)."""
    payload = _make_algorithm_summary_dict()
    payload.pop("category_id", None)
    payload.update(
        category={"id": uuid4(), "slug": "x", "name": "X"},
    )
    detail = AlgorithmDetailResponse(**payload)  # type: ignore[arg-type]
    assert detail.topics == []
    assert detail.current_code is None


def test_algorithm_code_response_accepts_payload() -> None:
    alg_id = uuid4()
    cv = AlgorithmCodeResponse(
        id=uuid4(),
        algorithm_id=alg_id,
        language="python",
        version=1,
        source_code="def f(): pass",
        is_current=True,
        created_at=datetime.now(UTC),
    )
    assert cv.language == "python"
    assert cv.version == 1


def test_algorithm_code_response_rejects_zero_version() -> None:
    with pytest.raises(ValidationError):
        AlgorithmCodeResponse(
            id=uuid4(),
            algorithm_id=uuid4(),
            language="python",
            version=0,  # ge=1
            source_code="",
            is_current=True,
            created_at=datetime.now(UTC),
        )


def test_algorithm_code_response_rejects_empty_language() -> None:
    with pytest.raises(ValidationError):
        AlgorithmCodeResponse(
            id=uuid4(),
            algorithm_id=uuid4(),
            language="",
            version=1,
            source_code="",
            is_current=True,
            created_at=datetime.now(UTC),
        )
