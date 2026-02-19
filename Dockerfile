# ── Stage 1: Build dependencies ──────────────────────────────────
FROM python:3.13-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project metadata and source for install
COPY pyproject.toml .
COPY src/ src/

# Install into a prefix we can copy later
RUN pip install --no-cache-dir --prefix=/install .

# ── Stage 2: Production runtime ─────────────────────────────────
FROM python:3.13-slim

LABEL maintainer="CronGuard <alerts@cronguard.dev>"
LABEL description="Dead man's switch monitoring for cron jobs"
LABEL org.opencontainers.image.source="https://github.com/arcangelileo/cron-guard"

# Copy installed packages from builder
COPY --from=builder /install /usr/local

WORKDIR /app

# Copy application code and Alembic config
COPY src/ src/
COPY alembic.ini .
COPY alembic/ alembic/

# Create non-root user and data directory
RUN groupadd -r cronguard && useradd -r -g cronguard -d /app -s /sbin/nologin cronguard \
    && mkdir -p /data && chown cronguard:cronguard /data

# Default environment
ENV CRONGUARD_DATABASE_URL="sqlite+aiosqlite:////data/cronguard.db" \
    CRONGUARD_SECRET_KEY="change-me-in-production" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

VOLUME ["/data"]

# Health check — hit the /health endpoint every 30s
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]

USER cronguard

# Use exec form for proper signal handling (PID 1)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
