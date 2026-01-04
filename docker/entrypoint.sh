#!/bin/bash
set -e

echo "🔄 Waiting for environment variables..."

# Wait for DATABASE_URL to be available (injected by Doppler/Render)
MAX_WAIT=30
COUNTER=0
while [ -z "$DATABASE_URL" ] && [ $COUNTER -lt $MAX_WAIT ]; do
    echo "⏳ Waiting for DATABASE_URL... ($COUNTER/$MAX_WAIT)"
    sleep 1
    COUNTER=$((COUNTER + 1))
done

if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL not set after ${MAX_WAIT}s. Cannot run migrations."
    exit 1
fi

echo "✅ DATABASE_URL available"
echo "🔄 Running database migrations..."
cd /app

# Run Alembic migrations
python -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Database migrations completed successfully"
else
    echo "❌ Database migrations failed"
    exit 1
fi

echo "🚀 Starting application services..."
exec "$@"
