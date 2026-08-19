"""Health check feature module.

Exposes /health (and /health/db) endpoints for liveness/readiness
probes used by orchestrators (k8s, ECS, load balancers).

This module follows the canonical layered-per-feature layout but is
unusually thin:
- router.py       defines GET /health and GET /health/db
- service.py      HealthService performs the DB ping
- tests/          integration tests for both endpoints

Refs: PUKU_BACKEND_AGENT.md §3.1 (routers own no logic)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.8)
"""