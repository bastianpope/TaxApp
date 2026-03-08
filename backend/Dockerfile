# ── Build stage ────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# System deps for cryptography / argon2
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libffi-dev libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install production deps into an isolated prefix
COPY pyproject.toml .
RUN pip install --upgrade pip \
    && pip install --prefix=/install . --no-deps \
    && pip install --prefix=/install .

# ── Runtime stage ───────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages
COPY --from=builder /install /usr/local

# Copy source
COPY . .

# Non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
