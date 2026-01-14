#!/bin/bash
set -e

echo "🔄 Validating environment variables..."

# Define required environment variables based on APP_ENV
REQUIRED_VARS=()
OPTIONAL_VARS=()
MISSING_VARS=()
WARNING_VARS=()

# Always required variables
REQUIRED_VARS+=("TELEGRAM_BOT_TOKEN")
REQUIRED_VARS+=("GROQ_API_KEY")
REQUIRED_VARS+=("INTERNAL_API_KEY")

# Database validation (DATABASE_URL OR individual DB fields)
if [ -z "$DATABASE_URL" ]; then
    REQUIRED_VARS+=("DB_HOST" "DB_NAME" "DB_USER" "DB_PASSWORD")
fi

# Redis validation (REDIS_URL OR REDIS_HOST)
if [ -z "$REDIS_URL" ] && [ -z "$REDIS_HOST" ]; then
    REQUIRED_VARS+=("REDIS_HOST")
fi

# Production-specific requirements
if [ "$APP_ENV" = "production" ]; then
    REQUIRED_VARS+=("ENCRYPTION_KEY")
    OPTIONAL_VARS+=("SENTRY_DSN" "AXIOM_API_TOKEN" "AXIOM_ORG_ID")
fi

# Check required variables
echo "🔍 Checking required environment variables..."
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
        echo "  ❌ $var is NOT set"
    else
        # Mask sensitive values in logs
        if [[ "$var" == *"TOKEN"* ]] || [[ "$var" == *"KEY"* ]] || [[ "$var" == *"PASSWORD"* ]]; then
            echo "  ✅ $var is set (***masked***)"
        else
            echo "  ✅ $var is set"
        fi
    fi
done

# Check optional variables (warnings only)
if [ ${#OPTIONAL_VARS[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  Checking optional environment variables..."
    for var in "${OPTIONAL_VARS[@]}"; do
        if [ -z "${!var}" ]; then
            WARNING_VARS+=("$var")
            echo "  ⚠️  $var is NOT set (optional)"
        else
            echo "  ✅ $var is set"
        fi
    done
fi

# Exit if any required variable is missing
if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo ""
    echo "❌ FATAL: The following required environment variables are missing:"
    printf '   - %s\n' "${MISSING_VARS[@]}"
    echo ""
    echo "💡 Please set these variables in Doppler or your .env file"
    exit 1
fi

# Show warnings but continue
if [ ${#WARNING_VARS[@]} -gt 0 ]; then
    echo ""
    echo "⚠️  WARNING: The following optional variables are not set:"
    printf '   - %s\n' "${WARNING_VARS[@]}"
    echo "💡 The application will continue but some features may be disabled"
fi

echo ""
echo "✅ All required environment variables are properly configured!"
echo ""

# Wait for DATABASE_URL to be available (injected by Doppler/Render)
if [ -n "$DATABASE_URL" ]; then
    echo "🔄 Waiting for DATABASE_URL to be fully available..."
    MAX_WAIT=30
    COUNTER=0

    # Give a moment for the database service to be ready
    while [ $COUNTER -lt $MAX_WAIT ]; do
        if [ -n "$DATABASE_URL" ]; then
            echo "✅ DATABASE_URL is available"
            break
        fi
        echo "⏳ Waiting for DATABASE_URL... ($COUNTER/$MAX_WAIT)"
        sleep 1
        COUNTER=$((COUNTER + 1))
    done
fi

echo ""
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

echo ""
echo "🔑 Bootstrapping API keys..."

# Bootstrap API key if INTERNAL_API_KEY is set and database is empty
if [ -n "$INTERNAL_API_KEY" ]; then
    python -c "
import sys
sys.path.insert(0, '/app/src')
from infrastructure.database import get_engine
from infrastructure.repositories import APIKeyRepository

engine = get_engine()
repo = APIKeyRepository(engine)

# Check if any API keys exist
existing_keys = repo.list_keys(include_inactive=True)

if not existing_keys:
    import os
    api_key = os.environ.get('INTERNAL_API_KEY')
    print(f'📝 Creating initial API key from INTERNAL_API_KEY...')
    repo.create_key(
        api_key=api_key,
        name='Bootstrap API Key',
        rate_limit_per_minute=1000
    )
    print('✅ Initial API key created successfully')
else:
    print(f'ℹ️  Found {len(existing_keys)} existing API key(s) - skipping bootstrap')
"
    if [ $? -eq 0 ]; then
        echo "✅ API key bootstrap completed"
    else
        echo "⚠️  API key bootstrap failed (non-fatal)"
    fi
else
    echo "ℹ️  INTERNAL_API_KEY not set - skipping API key bootstrap"
fi

echo ""
echo "🚀 Starting application services..."
echo "   📡 API will be available on port ${API_PORT:-5000}"
echo "   🤖 Telegram bot will start shortly"
echo ""
exec "$@"
