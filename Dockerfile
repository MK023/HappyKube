# Production Dockerfile - API + Bot unified service
# Optimized for Render.com deployment with Groq API

# ================================
# Stage 1: Builder
# ================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only pyproject.toml first for better layer caching
COPY pyproject.toml .

# Install dependencies (cached if pyproject.toml doesn't change)
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Copy source code
COPY src/ ./src/

# Install project with all dependencies
RUN pip install --no-cache-dir .

# ================================
# Stage 2: Runtime
# ================================
FROM python:3.12-slim

WORKDIR /app

# Create non-root user with home directory
RUN groupadd -r appuser && useradd -g appuser -u 1000 -m -s /bin/bash appuser

# Install only runtime dependencies (no build-essential!)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    supervisor \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create dummy SSL certificate for PostgreSQL (libpq searches for it even with channel_binding=disable)
RUN mkdir -p /root/.postgresql && touch /root/.postgresql/postgresql.crt && chmod 600 /root/.postgresql/postgresql.crt

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Set PATH to use virtual environment
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser wsgi.py /app/wsgi.py

# Copy alembic config and migrations
COPY --chown=appuser:appuser alembic.ini /app/alembic.ini
COPY --chown=appuser:appuser alembic/ /app/alembic/

# Copy supervisor config (needs root ownership)
COPY --chown=root:root docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy entrypoint script
COPY --chown=root:root docker/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Create logs directory
RUN mkdir -p /var/log/supervisor && chown -R appuser:appuser /var/log/supervisor

# Set Python path to include src
ENV PYTHONPATH=/app/src:/app

# Expose API port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:5000/ping || exit 1

# Set entrypoint to run migrations before starting services
ENTRYPOINT ["/app/entrypoint.sh"]

# Run supervisor as root (it will run processes as appuser)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
