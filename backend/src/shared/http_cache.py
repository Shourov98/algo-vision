"""Small HTTP caching helpers shared by public read routers.

Refs: ALGOVISION_BACKEND_PLAN.md §7 (Caching)
"""

from __future__ import annotations

from fastapi import Response


def set_public_cache(response: Response, *, max_age: int) -> None:
    """Mark a public response cacheable for the supplied freshness period."""
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
