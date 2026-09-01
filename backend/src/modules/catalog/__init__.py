"""Catalog feature module.

Read-mostly content surface: algorithm categories, topics, algorithms,
data structures, and versioned algorithm code per language. Emits
``ItemViewedEvent`` on detail fetch so progress/dashboard features can
track engagement without Catalog importing Progress.

Canonical layered structure:

    models.py               categories, topics, algorithms,
                            data_structures, algorithm_topics,
                            algorithm_code_versions
    schemas.py              request/response models
    repository.py           protocols + impls
    service.py              AlgorithmService, CategoryService, TopicService,
                            DataStructureService
    router.py               /algorithms, /data-structures,
                            /algorithms/categories
    events.py               ItemViewedEvent
    tests/

Refs: PUKU_BACKEND_AGENT.md §3.1, §3.2 (DIP — dispatch events, don't import)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 3)
Refs: DATABASE_DESIGN.md §3 (catalog tables)
"""
