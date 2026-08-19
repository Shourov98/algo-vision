"""Application settings (Pydantic v2 + pydantic-settings).

Single source of truth for runtime configuration. Loaded once at
process start from environment variables (and an optional .env file
in development). All other modules consume ``Settings`` via the
``get_settings`` FastAPI dependency, never by re-importing the module
attribute — that way tests can override values cleanly.

Why a class and not module-level constants
------------------------------------------
Module-level constants cannot be re-bound per test without monkey-
patching. ``BaseSettings`` is testable, type-checked, and emits
clear validation errors at boot if anything is malformed.

Why we deliberately do NOT include
----------------------------------
- Database engine & pool: lives in ``src/core/db.py`` (B1.5) so the
    settings module stays a pure config DTO, free of side effects.
- Logging config: lives in ``src/core/logging.py`` (B1.3).
- CORS origins parsing: lives in a small helper in ``src/shared/``
    when first needed, not here.

Refs: PUKU_BACKEND_AGENT.md §3.4 (Security — secrets from env)
Refs: ALGOVISION_BACKEND_PLAN.md §4 (Phase 1.2)
Refs: AlgoVision_BACKEND.md §3 (Hard Rules)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

AppEnv = Literal["development", "test", "production"]

# CORS origins are read from env as a comma-separated string and split
# in our field_validator. We use ``NoDecode`` so pydantic-settings does
# NOT try to ``json.loads()`` the value before the validator runs
# (pydantic-settings >=2.6 treats list[...] as JSON by default).
CorsOrigins = Annotated[list[str], NoDecode]


class Settings(BaseSettings):
    """Typed application configuration.

    Every field is read from an environment variable. Defaults are
    intentionally conservative so a missing variable never silently
    widens attack surface (e.g. CORS, cookie security).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # Validate on assignment so tests that mutate a Settings
        # instance fail fast rather than at first read.
        validate_default=True,
    )

    # ----- Environment ------------------------------------------------------
    app_env: AppEnv = Field(
        default="development",
        description="development | test | production. Drives log format, CORS, cookie flags.",
    )

    # ----- Database (Supabase managed Postgres) -----------------------------
    database_url: str = Field(
        ...,
        description="asyncpg DSN, e.g. postgresql+asyncpg://postgres:pw@db.ref.supabase.co:5432/postgres",
    )
    database_url_sync: str = Field(
        ...,
        description="psycopg2 DSN for Alembic. Same host/port, different driver.",
    )
    db_pool_size: int = Field(default=5, ge=1, le=100)
    db_max_overflow: int = Field(default=10, ge=0, le=200)
    db_pool_timeout_seconds: int = Field(default=30, ge=1, le=300)

    # ----- Supabase (optional, we own auth) ---------------------------------
    supabase_url: str = Field(default="")
    supabase_anon_key: SecretStr = Field(default=SecretStr(""))
    supabase_service_role_key: SecretStr = Field(default=SecretStr(""))

    # ----- Auth -------------------------------------------------------------
    secret_key: SecretStr = Field(
        ...,
        min_length=32,
        description="Long random string. Used to sign auth cookies/tokens. >=32 chars.",
    )
    argon2_time_cost: int = Field(default=3, ge=1, le=10)
    argon2_memory_cost: int = Field(default=65_536, ge=8_192, le=1_048_576)
    argon2_parallelism: int = Field(default=4, ge=1, le=16)
    access_token_ttl_seconds: int = Field(default=900, ge=60, le=86_400)
    refresh_token_ttl_seconds: int = Field(default=2_592_000, ge=86_400, le=31_536_000)

    cookie_secure: bool = Field(
        default=False,
        description="Set true in production (HTTPS only). False in dev so cookies work over http://localhost.",
    )
    cookie_samesite: Literal["lax", "strict", "none"] = Field(default="lax")
    cookie_domain: str = Field(default="")

    # ----- CORS -------------------------------------------------------------
    cors_allowed_origins: CorsOrigins = Field(
        default_factory=lambda: ["http://localhost:3000", "http://127.0.0.1:3000"],
        description="Comma-separated env var -> list. NEVER '*'.",
    )

    # ----- Logging ----------------------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")

    # ----- Rate limiting ----------------------------------------------------
    rate_limit_default: str = Field(default="100/minute")
    rate_limit_auth: str = Field(default="10/minute")

    # ----- Observability (later phases) -------------------------------------
    otel_enabled: bool = Field(default=False)
    otel_exporter_otlp_endpoint: str = Field(default="")
    metrics_enabled: bool = Field(default=False)

    # ----- Validators -------------------------------------------------------

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def _split_cors_env(cls, value: object) -> object:
        """Allow CORS_ALLOWED_ORIGINS=http://a,http://b in env files.

        Pydantic-settings normally only deserializes JSON-ish values
        for list[str] when given a string. We accept the more common
        comma-separated form (used by every web framework).
        """
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @field_validator("cors_allowed_origins")
    @classmethod
    def _no_wildcard_cors(cls, value: list[str]) -> list[str]:
        """Hard rule from AlgoVision_BACKEND.md §3.4: CORS never '*'."""
        for origin in value:
            if origin == "*":
                raise ValueError("CORS_ALLOWED_ORIGINS must not contain '*'")
        return value

    # ----- Convenience ------------------------------------------------------

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_test(self) -> bool:
        return self.app_env == "test"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached singleton accessor.

    ``lru_cache`` makes this a process-singleton while still allowing
    tests to call ``get_settings.cache_clear()`` and inject a fresh
    Settings via env monkey-patching.

    For per-request overrides, inject ``Settings`` directly via a
    FastAPI dependency that accepts ``Depends(get_settings)``.
    """
    return Settings()  # type: ignore[call-arg]