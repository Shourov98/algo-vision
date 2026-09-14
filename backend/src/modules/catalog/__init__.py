"""Catalog feature module.

Read-mostly content surface: algorithm categories, topics, algorithms,
data structures, and versioned algorithm code per language. Emits
``ItemViewedEvent`` on detail fetch so progress/dashboard features can
track engagement without Catalog importing Progress.

Canonical layered structure:

    models/                 categories, topics, algorithms,
                            data_structures, algorithm_topics,
                            algorithm_code_versions
    schemas/                request/response models
    repository/             protocols + impls
    service/                CatalogService + ORM-to-response converters
    router/                 /algorithms, /data-structures,
                            /algorithms/categories, /topics
    filters/                query-parameter filter dataclasses
    dependencies.py         FastAPI DI factories
    exceptions.py           domain errors
    tests/

Refs: PUKU_BACKEND_AGENT.md §3.1, §3.2 (DIP — dispatch events, don't import)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 3)
Refs: DATABASE_DESIGN.md §3 (catalog tables)

Note: ``ItemViewedEvent`` is defined in ``src.shared.events`` —
not here — so the catalog/problems modules share one event
shape.
"""
