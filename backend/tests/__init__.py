"""Test package.

Tests live next to the code they exercise:

    backend/
        src/
            modules/<feature>/tests/
        tests/
            conftest.py            # shared fixtures (db, client, factories)
            integration/           # cross-module integration
            unit/                   # pure helper tests

The pytest rootdir is backend/, with testpaths=["tests"]. asyncio_mode
is auto (configured in pyproject.toml).

Refs: PUKU_BACKEND_AGENT.md §2 (Tech Stack — pytest + httpx + real PG)
Refs: AlgoVision_BACKEND.md §3 (Hard Rules — meaningful tests)
"""