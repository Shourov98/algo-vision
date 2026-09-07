"""Unit tests for src.core.security (Argon2id password hashing).

Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 2 — B2.3)
Refs: AlgoVision_BACKEND.md §29 (Argon2id)
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from src.core.security import (
    hash_password,
    needs_rehash,
    verify_password,
)
from src.core.settings import Settings, get_settings

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_settings(**overrides: object) -> Settings:
    """Build a fresh, hermetic Settings instance.

    Pydantic Settings reads from the environment by default; we
    construct each test's Settings from kwargs via the model_dump
    / model_validate dance to avoid leaking the project's actual
    .env into our assertions. Each test gets its own instance, so
    the lru_cache on get_settings() does not interfere.
    """
    base: dict[str, object] = {
        "app_env": "test",
        "database_url": "postgresql+asyncpg://x:x@x/x",
        "database_url_sync": "postgresql+psycopg2://x:x@x/x",
        "secret_key": "x" * 64,
        # Lower the cost so tests run fast; correctness is what we
        # verify, not brute-force resistance.
        "argon2_time_cost": 1,
        "argon2_memory_cost": 8_192,
        "argon2_parallelism": 1,
    }
    base.update(overrides)
    return Settings.model_validate(base)


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> Iterator[None]:
    """Make sure no test sees a cached get_settings() instance."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    """Default test Settings with low-cost Argon2id params."""
    return _make_settings()


# ---------------------------------------------------------------------------
# hash_password
# ---------------------------------------------------------------------------


class TestHashPassword:
    def test_returns_nonempty_string(self, settings: Settings) -> None:
        h = hash_password("correct-horse-battery-staple", settings)
        assert isinstance(h, str)
        assert h

    def test_hash_is_argon2id(self, settings: Settings) -> None:
        """The encoded hash must declare Argon2id as its variant.
        argon2-cffi writes the variant tag in the prefix; we
        require id to prevent accidental downgrade to argon2i/d."""
        h = hash_password("password", settings)
        assert h.startswith("$argon2id$")

    def test_different_salts_per_call(self, settings: Settings) -> None:
        """Two hashes of the same password must differ — salt is
        random per call, otherwise identical passwords would be
        brute-forceable across the user table."""
        a = hash_password("same-password", settings)
        b = hash_password("same-password", settings)
        assert a != b

    def test_empty_password_rejected(self, settings: Settings) -> None:
        with pytest.raises(ValueError, match="password must not be empty"):
            hash_password("", settings)

    def test_long_password_accepted(self, settings: Settings) -> None:
        """Argon2id accepts arbitrary lengths; we don't impose a
        schema-level cap here. Pydantic schemas cap at 128 chars
        before this function is ever called."""
        h = hash_password("x" * 1024, settings)
        assert h


# ---------------------------------------------------------------------------
# verify_password
# ---------------------------------------------------------------------------


class TestVerifyPassword:
    def test_correct_password_returns_true(self, settings: Settings) -> None:
        h = hash_password("correct-horse-battery-staple", settings)
        assert verify_password("correct-horse-battery-staple", h, settings) is True

    def test_wrong_password_returns_false(self, settings: Settings) -> None:
        h = hash_password("correct-horse-battery-staple", settings)
        assert verify_password("wrong-password-here", h, settings) is False

    def test_empty_password_returns_false(self, settings: Settings) -> None:
        """An empty plaintext never matches — short-circuits before
        touching argon2 so we don't waste CPU on a known-bad input."""
        h = hash_password("anything", settings)
        assert verify_password("", h, settings) is False

    def test_malformed_hash_returns_false(self, settings: Settings) -> None:
        """A garbage hash must not raise — it must return False so
        callers can use one error path for 'wrong password' and
        'corrupted hash'."""
        assert verify_password("any", "not-a-real-hash", settings) is False

    def test_empty_hash_returns_false(self, settings: Settings) -> None:
        assert verify_password("any", "", settings) is False

    def test_hash_from_different_hasher_still_verifies(self) -> None:
        """Argon2id hashes are self-describing — a hash made with
        one parameter set verifies under another, as long as both
        are Argon2id. This is the migration property that lets
        us tune parameters over time without invalidating stored
        hashes."""
        weak = _make_settings(
            argon2_time_cost=1,
            argon2_memory_cost=8_192,
            argon2_parallelism=1,
        )
        strong = _make_settings(
            argon2_time_cost=3,
            argon2_memory_cost=65_536,
            argon2_parallelism=4,
        )
        h = hash_password("migrating", weak)
        # Strong settings can still verify the old hash.
        assert verify_password("migrating", h, strong) is True


# ---------------------------------------------------------------------------
# needs_rehash
# ---------------------------------------------------------------------------


class TestNeedsRehash:
    def test_returns_false_when_params_match(self, settings: Settings) -> None:
        h = hash_password("p", settings)
        assert needs_rehash(h, settings) is False

    def test_returns_true_when_params_increase(self) -> None:
        weak = _make_settings(
            argon2_time_cost=1,
            argon2_memory_cost=8_192,
            argon2_parallelism=1,
        )
        strong = _make_settings(
            argon2_time_cost=3,
            argon2_memory_cost=65_536,
            argon2_parallelism=4,
        )
        h = hash_password("p", weak)
        # Strong settings use higher cost -> needs rehash.
        assert needs_rehash(h, strong) is True

    def test_returns_true_when_any_param_differs(self) -> None:
        """argon2-cffi's check_needs_rehash is strict: any difference
        from target params triggers a rehash. This is the safe
        default — if the deployment ever tightens OR loosens params,
        rehash on next login."""
        weak = _make_settings(
            argon2_time_cost=1,
            argon2_memory_cost=8_192,
            argon2_parallelism=1,
        )
        weaker = _make_settings(
            argon2_time_cost=1,
            argon2_memory_cost=8_192,
            argon2_parallelism=1,
        )
        h = hash_password("p", weak)
        # Same params -> no rehash.
        assert needs_rehash(h, weak) is False
        # Even slightly different parallelism triggers rehash.
        slightly_off = _make_settings(
            argon2_time_cost=1,
            argon2_memory_cost=8_192,
            argon2_parallelism=2,
        )
        assert needs_rehash(h, slightly_off) is True
        # Reference the unused var so mypy doesn't complain.
        assert weaker is not None

    def test_malformed_hash_does_not_raise(self, settings: Settings) -> None:
        assert needs_rehash("garbage", settings) is False


# ---------------------------------------------------------------------------
# Hash structure
# ---------------------------------------------------------------------------


class TestHashStructure:
    def test_hash_format_is_well_formed(self, settings: Settings) -> None:
        """Argon2id's self-describing format: $argon2id$v=N$m=..,t=..,p=..$salt$digest."""
        h = hash_password("p", settings)
        # Split on '$' and validate the prefix components.
        parts = h.split("$")
        # ["", "argon2id", "v=19", "m=...,t=...,p=...", "salt", "digest"]
        assert parts[1] == "argon2id"
        assert parts[2].startswith("v=")
        assert "m=" in parts[3] and "t=" in parts[3] and "p=" in parts[3]
        # Salt and digest are base64-like, non-empty.
        assert parts[4]
        assert parts[5]
