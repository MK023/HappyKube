# 🚀 Deploy Instructions for Render

## Build Command

In Render Dashboard → Settings → Build & Deploy, set the **Build Command** to:

```bash
pip install --no-cache-dir -r requirements.txt && alembic upgrade head
```

This will:
1. Install all dependencies
2. **Automatically run database migrations** (creates performance indexes)

## Start Command

Keep the existing start command or use:

```bash
python -m src.presentation.bot.telegram_bot &
python -m uvicorn src.presentation.api.app:app --host 0.0.0.0 --port $PORT
```

## Environment Variables

Ensure all these are set in Render:

### Required
- `DATABASE_URL` - PostgreSQL connection URL (NeonDB)
- `REDIS_URL` - Redis connection URL (Render Redis)
- `TELEGRAM_BOT_TOKEN` - Your Telegram bot token
- `GROQ_API_KEY` - Groq API key for Llama 3.3 70B
- `JWT_SECRET_KEY` - Secret for JWT tokens
- `ENCRYPTION_KEY` - Fernet key for PII encryption

### Optional
- `APP_ENV` - Default: `production`
- `LOG_LEVEL` - Default: `INFO`
- `SENTRY_DSN` - For error tracking (optional)

## Deployment Steps

1. **Merge PR to main branch**
   ```bash
   git checkout main
   git merge dev/newfeature
   git push origin main
   ```

2. **Render auto-deploys** when it detects push to `main`

3. **Migrations run automatically** during build

4. **Verify deployment:**
   - Check `/health` endpoint
   - Test bot with a message
   - Check logs for "Database migrations applied"

## Rollback

If you need to rollback the database migration:

```bash
alembic downgrade -1
```

This removes the performance indexes (safe operation).

## Notes

- ✅ Migrations are **idempotent** (safe to run multiple times)
- ✅ Indexes are added, no schema changes
- ✅ Zero downtime deployment
- ✅ Graceful shutdown implemented
