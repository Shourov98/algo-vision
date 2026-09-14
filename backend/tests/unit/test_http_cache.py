"""Unit tests for public HTTP cache policies.

Refs: ALGOVISION_BACKEND_PLAN.md §7 (Caching)
"""

from __future__ import annotations

from fastapi import Response
from src.shared.http_cache import set_public_cache


def test_set_public_cache_sets_configured_freshness() -> None:
    response = Response()

    set_public_cache(response, max_age=300)

    assert response.headers["Cache-Control"] == "public, max-age=300"
