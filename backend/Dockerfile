# =============================================================================
# AlgoVision backend — production Dockerfile
# =============================================================================
# Multi-stage build:
#   builder : install deps into a virtualenv
#   runtime : copy the venv + app code, run as non-root
#
# Targets: development (default) and production. Both bake the same code;
# production uses a slim runtime base and excludes test deps.
# =============================================================================

# ---- builder ----------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps needed to build asyncpg, psycopg2, argon2-cffi wheels.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libpq-dev \
        && rm -rf /var/lib/apt/lists/*

# Install Python deps into a virtualenv so we can COPY it into runtime.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only pyproject first to leverage Docker layer cache for deps.
COPY pyproject.toml ./
RUN pip install --upgrade pip \
    && pip install --no-cache-dir .

# ---- runtime ----------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Non-root user. UID 10001 is in the "users" range; no login shell needed.
RUN groupadd --system --gid 10001 algovision \
    && useradd --system --uid 10001 --gid algovision \
       --no-create-home --shell /sbin/nologin algovision

# Copy the venv from the builder stage.
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

# Copy application code.
COPY src ./src
COPY migrations ./migrations
COPY alembic.ini ./alembic.ini

# /app owned by algovision so the running process can read everything.
RUN chown -R algovision:algovision /app

USER algovision

EXPOSE 8000

# Default: 4 workers, single uvicorn process per container. Production
# scales horizontally via the orchestrator (k8s Deployment replicas).
CMD ["uvicorn", "src.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health').read()" \
    || exit 1