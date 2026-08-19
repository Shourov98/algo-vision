"""Password hashing utilities (Argon2id).

Single-responsibility module: convert plaintext passwords to
hashes, and verify hashes against plaintexts. Nothing else.

Why Argon2id
------------
Argon2id (RFC 9106) is the OWASP-recommended password hashing
algorithm for new applications as of 2024. It defeats both GPU
brute-force (memory-hard) and side-channel attacks (hybrid
mode). bcrypt is acceptable but no longer preferred; PBKDF2 is
deprecated for new systems.

Why we wrap argon2-cffi
-----------------------
argon2-cffi is the canonical Python implementation. We expose two
functions, ``hash_password`` and ``verify_password``, so callers
never import the library directly. This means:
- The algorithm choice can change in one place (e.g. to argon2i or
  argon2d if Argon2id is ever found vulnerable).
- Test fixtures can patch our functions without monkey-patching
  the third-party library.
- The hashing policy (parameters from settings) lives next to the
  call site, not scattered across services.

Parameter choices
-----------------
The defaults baked into ``PasswordHasher`` come from argon2-cffi
which tracks the OWASP baseline. We further tune via settings
(``argon2_time_cost``, ``argon2_memory_cost``, ``argon2_parallelism``)
so deployment environments can dial up the cost if needed.

Security rules (PUKU_BACKEND_AGENT §3.4)
----------------------------------------
- Never log hashes or passwords. These functions take and return
  strings only — they never log anything.
- ``verify_password`` returns False (does NOT raise) on any
  verification failure, including malformed hashes. This is the
  standard pattern; callers distinguish "wrong password" from
  "user not found" by other means (so an attacker cannot probe
  user existence).
- ``hash_password`` raises ``ValueError`` on empty input — an
  empty password is almost certainly a bug, never a user choice.

Refs: ALGOVISION_BACKEND_PLAN.md §2 (Stack), §8 (Auth architecture)
Refs: AlgoVision_BACKEND.md §29 (Argon2id)
Refs: PUKU_BACKEND_AGENT.md §3.4 (no plaintext passwords, no logs of secrets)
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import (
    InvalidHashError,
    VerificationError,
)

from src.core.settings import Settings


def _build_hasher(settings: Settings) -> PasswordHasher:
    """Construct a PasswordHasher using the parameters from settings.

    Kept private — callers obtain a hasher via ``hash_password`` /
    ``verify_password`` and never need to know about parameter
    selection. Splitting it out also makes the parameter mapping
    explicit and unit-testable.
    """
    return PasswordHasher(
        time_cost=settings.argon2_time_cost,
        memory_cost=settings.argon2_memory_cost,
        parallelism=settings.argon2_parallelism,
    )


def hash_password(password: str, settings: Settings) -> str:
    """Hash a plaintext password using Argon2id.

    The returned string is the full encoded hash including salt,
    parameters, and version tag — everything needed to verify the
    password later without storing any additional metadata.

    Parameters are taken from ``settings.argon2_*`` so changing
    the cost in one environment does not require code changes.

    Raises:
        ValueError: if ``password`` is empty.
    """
    if not password:
        raise ValueError("password must not be empty")
    hasher = _build_hasher(settings)
    return hasher.hash(password)


def verify_password(password: str, encoded_hash: str, settings: Settings) -> bool:
    """Verify a plaintext password against an Argon2id hash.

    Returns True on match, False otherwise. Never raises on
    verification failure — the only exception that can bubble up
    is a programming error (e.g. ``encoded_hash`` is not a string),
    and that would already be a bug.

    Constant-time behavior is provided by argon2-cffi's ``verify``
    method. We do not add extra timing protection on top; any
    surrounding code (e.g. login lockout) handles timing
    defenses at the policy layer.
    """
    if not password:
        # An empty password is never the right answer. Returning
        # False here matches the documented contract and avoids
        # feeding empty input to argon2 (which would itself raise).
        return False
    hasher = _build_hasher(settings)
    try:
        hasher.verify(encoded_hash, password)
    except (VerificationError, InvalidHashError):
        return False
    return True


def needs_rehash(encoded_hash: str, settings: Settings) -> bool:
    """Return True if the hash was made with weaker parameters than
    the current settings.

    Callers (typically on successful login) use this to transparently
    upgrade hashes when the deployment's argon2 parameters are
    raised. Argon2id is self-describing — the encoded hash carries
    its own parameters — so this comparison is safe and exact.

    Returns False on a malformed hash (no rehash possible).
    """
    hasher = _build_hasher(settings)
    try:
        return hasher.check_needs_rehash(encoded_hash)
    except InvalidHashError:
        return False
