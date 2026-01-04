# Production Dockerfile - API + Bot unified service
# Optimized for Render.com deployment with Groq API

# ================================
# Stage 1: Build Dependencies
# ================================
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy pyproject.toml and src directory for building
COPY pyproject.toml .
COPY src/ ./src/
RUN pip wheel --no-cache-dir --no-warn-script-location --root-user-action=ignore --wheel-dir /wheels .

# ================================
# Stage 2: Runtime
# ================================
FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -u 1000 appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python wheels
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-warn-script-location --root-user-action=ignore /wheels/* && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/

# Copy wsgi.py to root
COPY --chown=appuser:appuser wsgi.py /app/wsgi.py

# Copy alembic config and migrations
COPY --chown=appuser:appuser alembic.ini /app/alembic.ini
COPY --chown=appuser:appuser alembic/ /app/alembic/

# Copy supervisor config
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
