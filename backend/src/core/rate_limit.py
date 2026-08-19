"""Rate limiting for AlgoVision.

Single-responsibility module: expose per-route rate-limit
constants and a FastAPI dependency factory that enforces them.

Why a custom dependency rather than slowapi's ``@limiter.limit``
----------------------------------------------------------------
slowapi's decorator wraps the handler function with a closure
that reads ``request: Request`` and dispatches to a private
``_check_request_limit`` method. The wrapper's behavior is
fragile across FastAPI/Starlette versions — it relies on
internal slowapi state (``_route_limits``, ``_marked_for_limiting``)
that is keyed by function ``__qualname__``. We keep finding
ourselves working around slowapi's design rather than using it.

This module replaces that approach with a thin dependency that
uses slowapi's *storage* layer directly: every call increments a
keyed counter and raises ``RateLimitExceeded`` on overflow. We
get the same per-IP bucketing behavior without the wrapper.

The Limiter itself (with its default limits and key_func) is
still installed on ``app.state.limiter`` so any future slowapi
integration (e.g. via Starlette middleware) can find it.

Refs: ALGOVISION_BACKEND_PLAN.md §6 (Rate Limits)
Refs: AlgoVision_BACKEND.md §3 (Hard Rules)
Refs: PUKU_BACKEND_AGENT.md §3.4 (no silent rate-limit config)
"""

from __future__ import annotations

from fastapi import Depends, Request
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from slowapi.wrappers import Limit

# Per-endpoint override strings (ALGOVISION_BACKEND_PLAN.md §6).
# We keep them here so routers import a stable symbol rather than
# a magic string.
RATE_LIMIT_REGISTER = "5/hour"
RATE_LIMIT_LOGIN = "10/10 minute"
RATE_LIMIT_REFRESH = "60/hour"

# Fallback when Settings doesn't provide one. Used as a default
# argument to the Limiter constructor.
DEFAULT_RATE_LIMIT = "100/minute"


def build_limiter(default_limit: str = DEFAULT_RATE_LIMIT) -> Limiter:
    """Construct a slowapi Limiter keyed by remote IP.

    Why IP, not user
    ----------------
    Login/register happen BEFORE authentication, so we can't key
    by user id. The plan (§6) uses IP for those endpoints. After
    login, /auth/refresh is keyed by user via a custom key_func
    added in a later ticket if needed.

    The default limit applies to any route that does not specify
    its own. We deliberately set a high floor so the test suite
    isn't accidentally throttled.
    """
    return Limiter(
        key_func=get_remote_address,
        default_limits=[default_limit],
        headers_enabled=True,
    )


def _resolve_limiter(request: Request) -> Limiter:
    """Pull the slowapi Limiter from app.state for the current request."""
    return request.app.state.limiter


def make_rate_limit_dependency(limit_value: str):
    """Build a FastAPI dependency that enforces ``limit_value``.

    The dependency increments a per-route counter keyed by the
    client IP and the route's path. The counter window matches
    the rate string (e.g. ``5/hour`` means up to 5 calls per
    1-hour window). When the count exceeds the limit we raise
    slowapi's ``RateLimitExceeded``, which ``main.py`` maps to
    a ``RateLimited`` AppError envelope (HTTP 429).

    Implementation notes
    --------------------
    slowapi's storage backends are exposed on
    ``Limiter._storage``. We use the public ``incr`` method
    which atomically increments a key with a TTL and returns
    the new count. Parsing the rate string is delegated to
    ``limits.parse`` (the same parser slowapi uses internally).

    We build a ``slowapi.wrappers.Limit`` once at factory time
    so we can pass it to ``RateLimitExceeded`` on overflow —
    the exception's constructor expects the rich Limit object
    (with ``error_message`` and ``limit`` attrs), not a plain
    string.
    """
    import limits  # slowapi's rate-string parser
    from limits.limits import RateLimitItem

    # Parse the rate string once at factory time. slowapi's
    # internal ``Limit`` constructor accepts a RateLimitItem
    # (which is what ``limits.parse`` returns).
    parsed: RateLimitItem = limits.parse(limit_value)
    window: int = parsed.get_expiry()
    amount: int = parsed.amount

    # Build a slowapi ``Limit`` for the exception. Its
    # constructor accepts (limit, key_func, scope, per_method,
    # methods, error_message, exempt_when, cost, override_defaults).
    # We pass ``parsed`` (RateLimitItem) instead of the raw string
    # so mypy and runtime both accept it.
    def _dummy_key(*args: object, **kwargs: object) -> str:
        return ""

    limit_obj = Limit(
        parsed,
        _dummy_key,
        None,  # scope
        False,  # per_method
        None,  # methods
        None,  # error_message
        None,  # exempt_when
        1,  # cost
        True,  # override_defaults
    )

    async def _dep(
        request: Request,
        limiter: Limiter = Depends(_resolve_limiter),
    ) -> None:
        client_key = limiter._key_func(request)
        bucket = f"auth:{request.method}:{request.url.path}:{client_key}"
        # ``incr`` is the public storage interface. On the default
        # in-memory backend it returns an ``int`` synchronously;
        # async backends (Redis, etc.) return a coroutine.
        result = limiter._storage.incr(bucket, expiry=window, amount=1)
        if hasattr(result, "__await__"):
            result = await result
        if result is not None and result > amount:
            raise RateLimitExceeded(limit_obj)

    return _dep
