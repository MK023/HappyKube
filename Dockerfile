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
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

# ================================
# Stage 2: Runtime
# ================================
FROM python:3.12-slim

WORKDIR /app

# Create non-root user with home directory
RUN groupadd -r appuser && useradd -g appuser -u 1000 -m -s /bin/bash appuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Copy Python wheels and set ownership
COPY --from=builder --chown=appuser:appuser /wheels /wheels

# Switch to non-root user before pip install
USER appuser

# Install Python wheels as non-root user (installs to ~/.local)
RUN pip install --no-cache-dir --user /wheels/*

# Add user site-packages to PATH for executables
ENV PATH="/home/appuser/.local/bin:${PATH}"

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/

# Copy wsgi.py to root
COPY --chown=appuser:appuser wsgi.py /app/wsgi.py

# Copy alembic config and migrations
COPY --chown=appuser:appuser alembic.ini /app/alembic.ini
COPY --chown=appuser:appuser alembic/ /app/alembic/

# Switch back to root for supervisor setup
USER root

# Clean up wheels directory
RUN rm -rf /wheels

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
