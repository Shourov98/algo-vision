"""Health check service.

Pure business logic for the /health and /health/db endpoints.
The router maps these into HTTP responses; the service knows
nothing about HTTP.

Why a service for two trivial endpoints
---------------------------------------
The router pattern (router depends on service) is uniform across
modules. HealthService can be exercised in unit tests directly,
which is faster than spinning up a TestClient per assertion.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class HealthStatus:
    """Result of a health check."""

    healthy: bool
    components: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": "ok" if self.healthy else "degraded",
            "components": self.components,
        }


class HealthService:
    """Probes runtime health of the application.

    - check_liveness(): always-true fast path (no I/O). Used by
      orchestrators to decide whether the process is alive.
    - check_readiness(): pings the DB to confirm the service can
      actually serve traffic. Returns degraded if DB is down so
      orchestrators can route traffic elsewhere.

    Stateless; instances are cheap. The router holds a single
    instance via FastAPI Depends.
    """

    async def check_liveness(self) -> HealthStatus:
        """Fast liveness probe — no I/O, always healthy if reachable."""
        return HealthStatus(healthy=True, components={})

    async def check_readiness(
        self,
        session: AsyncSession | None = None,
    ) -> HealthStatus:
        """Readiness probe — pings the DB with SELECT 1.

        On success: components["database"] = {"status": "ok"}.
        On failure: components["database"] = {"status": "down",
        "error": "<type>: <message>"} and healthy=False.

        ``session=None`` means the engine isn't initialized. We
        treat this as a degradation, not an exception, so the
        orchestrator can distinguish "the service is up but its
        dependencies aren't ready" from "the service is broken".

        Never raises — failures are reported in the payload so the
        orchestrator can read both the status code and the JSON.
        """
        if session is None:
            return HealthStatus(
                healthy=False,
                components={
                    "database": {
                        "status": "down",
                        "error": "engine not initialized",
                    },
                },
            )
        try:
            result = (await session.execute(text("SELECT 1"))).scalar_one()
            assert result == 1
        except Exception as exc:  # noqa: BLE001 - report any failure
            return HealthStatus(
                healthy=False,
                components={
                    "database": {
                        "status": "down",
                        "error": f"{type(exc).__name__}: {exc}",
                    },
                },
            )
        return HealthStatus(
            healthy=True,
            components={"database": {"status": "ok"}},
        )