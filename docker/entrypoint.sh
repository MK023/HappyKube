#!/bin/bash
set -e

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
