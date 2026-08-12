"""Problems feature module.

Curated interview problems with topic and company tags. Supports
filter by difficulty, topic, company, and (authenticated) personal
status. Emits ``ItemViewedEvent`` for progress tracking.

Canonical layered structure:

    models.py       problems, problem_topics, companies, problem_companies
    schemas.py      filters + request/response
    repository.py   ProblemRepository
    service.py      ProblemService
    router.py       /problems
    events.py       ItemViewedEvent (same shape as catalog; reused)
    tests/

Refs: PUKU_BACKEND_AGENT.md §3.1, §3.2
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 4)
Refs: DATABASE_DESIGN.md §3 (problems tables)
"""