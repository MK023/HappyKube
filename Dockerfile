# Production Dockerfile - API + Bot unified service
# Optimized for Render.com deployment

# ================================
# Stage 1: Download ML Models
# ================================
FROM python:3.12-slim AS model-downloader

WORKDIR /models

RUN pip install --no-cache-dir transformers==4.46.3 torch==2.5.1 huggingface-hub==0.26.5

RUN python -c "from transformers import pipeline; \
    print('Downloading Italian emotion model...'); \
    pipeline('text-classification', model='MilaNLProc/feel-it-italian-emotion'); \
    print('Downloading English emotion model...'); \
    pipeline('text-classification', model='j-hartmann/emotion-english-distilroberta-base'); \
    print('Downloading sentiment model...'); \
    pipeline('text-classification', model='MilaNLProc/feel-it-italian-sentiment'); \
    print('All models downloaded!')"

# ================================
# Stage 2: Build Dependencies
# ================================
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

# ================================
# Stage 3: Runtime
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
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels

# Copy pre-downloaded models
COPY --from=model-downloader /root/.cache/huggingface /home/appuser/.cache/huggingface
RUN chown -R appuser:appuser /home/appuser/.cache

# Copy application code (with __init__.py files!)
# Cache bust v2025-12-29-02
COPY --chown=appuser:appuser src/ /app/

# Copy supervisor config
COPY --chown=root:root docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Create logs directory
RUN mkdir -p /var/log/supervisor && chown -R appuser:appuser /var/log/supervisor

# Set Python path
ENV PYTHONPATH=/app

# Expose API port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:5000/ping || exit 1

# Run supervisor as root (it will run processes as appuser)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
