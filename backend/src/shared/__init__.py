"""Cross-feature utilities used by more than one module.

Contents:
- pagination.py    : limit/offset + page envelope (Page[T])
- filters.py       : SortOrder enum shared by entity filters
- events.py        : EventDispatcherProtocol, InProcessEventDispatcher,
                     NoopEventDispatcher, ItemViewedEvent

Anything in here must be domain-agnostic. If a helper references
"users" or "algorithms", it belongs in the feature module instead.

Refs: PUKU_BACKEND_AGENT.md §3.6 (DRY)
Refs: ALGOVISION_BACKEND_PLAN.md §7 (API design)
"""
