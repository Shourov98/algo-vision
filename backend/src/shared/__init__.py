"""Cross-feature utilities used by more than one module.

Contents (filled in later phase-1 commits):
- pagination.py    : limit/offset + cursor math, link headers
- filters.py       : typed filter base classes
- ids.py           : id generation helpers
- time.py          : UTC clock helpers

Anything in here must be domain-agnostic. If a helper references
"users" or "algorithms", it belongs in the feature module instead.

Refs: PUKU_BACKEND_AGENT.md §3.6 (DRY)
Refs: ALGOVISION_BACKEND_PLAN.md §7 (API design)
"""
