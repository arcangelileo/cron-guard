FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml .
COPY src/ src/
COPY alembic.ini .
COPY alembic/ alembic/

# Install Python dependencies
RUN pip install --no-cache-dir .

# Create data directory for SQLite
RUN mkdir -p /data

ENV CRONGUARD_DATABASE_URL="sqlite+aiosqlite:////data/cronguard.db"
ENV CRONGUARD_SECRET_KEY="change-me-in-production"

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
