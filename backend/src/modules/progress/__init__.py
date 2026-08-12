"""Progress feature module.

Tracks per-user engagement: marks (favorite, completed, in-progress),
overview counters, recent items, and consumes ``ItemViewedEvent`` to
update ``user_recent_items``.

Canonical layered structure:

    models.py       user_algorithm_progress, user_problem_progress,
                    user_recent_items
    schemas.py      request/response
    repository.py   ProgressRepository
    service.py      ProgressService: mark_*, get_overview, list_*,
                    record_view, handle_item_viewed
    router.py       /progress/*
    events.py       consumed events + local helpers
    tests/

Refs: PUKU_BACKEND_AGENT.md §3.1 (DIP — ProgressService is invoked by
       event dispatcher, not directly by catalog/problems)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 5)
Refs: DATABASE_DESIGN.md §3 (progress tables)
"""