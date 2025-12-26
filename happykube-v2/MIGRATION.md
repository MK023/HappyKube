# Migration Guide: HappyKube v1 → v2

Complete guide for migrating from the old HappyKube to the new v2 architecture.

## 🔄 What Changed

### Architecture
- **v1**: Monolithic Flask app with basic structure
- **v2**: Clean Architecture with Domain-Driven Design

### Security
- **v1**: ⚠️ Plaintext data, secrets in git
- **v2**: ✅ AES-256 encryption, secrets gitignored, API auth

### Database
- **v1**: Raw SQL queries, no migrations
- **v2**: SQLAlchemy 2.0 + Alembic migrations, encrypted fields

### Performance
- **v1**: No caching, single connection
- **v2**: Redis caching, connection pooling

## 📊 Data Migration

### Step 1: Backup Old Data

```sql
-- Connect to Neon database
psql "postgresql://neondb_owner:npg_2segulzP4cHW@ep-cold-brook-agz9f5sw-pooler.c-2.eu-central-1.aws.neon.tech/neondb?sslmode=require"

-- Create backup
CREATE TABLE emotions_backup AS SELECT * FROM emotions;

-- Rename old table
ALTER TABLE emotions RENAME TO emotions_old;
```

### Step 2: Run New Migrations

```bash
cd happykube-v2

# Install dependencies
pip install -r requirements/base.txt

# Set environment variables
export DB_HOST="ep-cold-brook-agz9f5sw-pooler.c-2.eu-central-1.aws.neon.tech"
export DB_NAME="neondb"
export DB_USER="neondb_owner"
export DB_PASSWORD="npg_2segulzP4cHW"
export ENCRYPTION_KEY="vF3K9mN7pQ2wX8yZ5tR6uE4hJ1kL0oM3nP6qS9tU2="
export TELEGRAM_BOT_TOKEN="8297870826:AAE1tYfM-Ms1bVcDN87YdHmWzS1CGysuj0c"
export API_KEYS="dev-key-12345"
export JWT_SECRET_KEY="dev-secret"

# Run migrations (creates new schema)
alembic upgrade head
```

### Step 3: Migrate Data

```bash
# Run migration script
python scripts/migrate_old_data.py
```

The script will:
1. Read from `emotions_old` table
2. Create users with hashed telegram_ids
3. Encrypt text fields
4. Insert into new `emotions` table with proper foreign keys
5. Preserve timestamps and scores

### Step 4: Verify Migration

```sql
-- Check new users table
SELECT COUNT(*) FROM users;

-- Check new emotions table
SELECT COUNT(*) FROM emotions;

-- Compare counts
SELECT COUNT(*) FROM emotions_old;

-- Verify encrypted data exists
SELECT id, user_id, emotion, score, created_at
FROM emotions
LIMIT 5;

-- Note: text_encrypted will be binary data
```

### Step 5: Archive Old Data

```sql
-- Once verified, rename old table
ALTER TABLE emotions_old RENAME TO emotions_archive;

-- Or delete if not needed (BE CAREFUL!)
-- DROP TABLE emotions_old;
```

## 🔑 Secrets Migration

### Old Secrets (v1)
```yaml
# deployment/api/secret.yaml (COMMITTED TO GIT! ⚠️)
data:
  telegram_token: ODI5Nzg3ODI2OkFBRTF0WWZNLU1zMWJWY0ROODdZZEhtV3pTMUNHeXN1ajBj
  db_user: bmVvbmRiX293bmVy
  db_password: bnBnXzJzZWd1bHpQNGNIVw==
  db_host: ZXAtY29sZC1icm9vay1hZ3o5ZjVzdy1wb29sZXIuYy0yLmV1LWNlbnRyYWwtMS5hd3MubmVvbi50ZWNo
```

### New Secrets (v2)
```yaml
# deployment/overlays/minikube/secrets.yaml (GITIGNORED! ✅)
stringData:
  telegram-token: "8297870826:AAE1tYfM-Ms1bVcDN87YdHmWzS1CGysuj0c"
  db-user: "neondb_owner"
  db-password: "npg_2segulzP4cHW"
  db-host: "ep-cold-brook-agz9f5sw-pooler.c-2.eu-central-1.aws.neon.tech"
  encryption-key: "vF3K9mN7pQ2wX8yZ5tR6uE4hJ1kL0oM3nP6qS9tU2="  # NEW!
  jwt-secret: "your-jwt-secret"  # NEW!
  api-keys: "dev-key-12345"  # NEW!
```

## 📝 Configuration Changes

### Environment Variables

**Added in v2:**
- `ENCRYPTION_KEY` - For PII encryption
- `JWT_SECRET_KEY` - For JWT tokens
- `API_KEYS` - For API authentication
- `REDIS_HOST/PORT` - For caching
- `RATE_LIMIT_*` - For rate limiting

**Renamed:**
- `TELEGRAM_TOKEN` → `TELEGRAM_BOT_TOKEN`
- `EMOTION_API_URL` → Not needed (bot now has direct DB access)

## 🐳 Docker Changes

### Old Dockerfile
```dockerfile
FROM python:3.10-slim
COPY src/ .
CMD ["python", "app.py"]
```

### New Dockerfile
```dockerfile
# Multi-stage with pre-loaded models
FROM python:3.12-slim AS model-downloader
# ... downloads ML models

FROM python:3.12-slim
USER appuser  # Non-root!
# ... optimized layers
```

## ☸️ Kubernetes Changes

### New Resources
- `HorizontalPodAutoscaler` for API
- `ConfigMap` for bot messages
- `redis` deployment
- Proper resource limits
- Better health checks

### Service Changes
- API service port: 5000 → 80 (external)
- Added readiness/liveness probes
- Resource requests/limits defined

## 🚀 Deployment Process

### Option 1: Clean Deploy (Recommended)

```bash
# 1. Deploy v2 alongside v1 (different namespace)
kubectl create namespace happykube-v2
kubectl apply -k deployment/overlays/minikube/ -n happykube-v2

# 2. Migrate data
kubectl exec -it deployment/happykube-api -n happykube-v2 -- python scripts/migrate_old_data.py

# 3. Test v2
# Send test messages to bot

# 4. Switch over
# Update bot token to point to v2 (or delete v1 namespace)

# 5. Delete v1
kubectl delete namespace happykube
kubectl create namespace happykube
kubectl apply -k deployment/overlays/minikube/
```

### Option 2: In-Place Upgrade

```bash
# 1. Scale down v1
kubectl scale deployment/happykube-api --replicas=0 -n happykube
kubectl scale deployment/happykube-bot --replicas=0 -n happykube

# 2. Migrate database
python scripts/migrate_old_data.py

# 3. Delete old deployments
kubectl delete deployment/happykube-api -n happykube
kubectl delete deployment/happykube-bot -n happykube

# 4. Deploy v2
kubectl apply -k deployment/overlays/minikube/
```

## ✅ Post-Migration Checklist

- [ ] All users migrated (check count)
- [ ] All emotions migrated (check count)
- [ ] Encrypted fields working (test insert)
- [ ] Bot responds to messages
- [ ] API endpoints working
- [ ] Redis caching functional
- [ ] Rate limiting active
- [ ] Logs are structured
- [ ] Metrics available
- [ ] Old data archived

## 🔧 Troubleshooting

### "Encryption key invalid"
Make sure `ENCRYPTION_KEY` is a valid Fernet key:
```bash
python scripts/generate_encryption_key.py
```

### "Migration script fails"
Check database connection:
```python
from src.infrastructure.database import health_check
print(health_check())
```

### "Bot not responding"
Check logs:
```bash
kubectl logs -f deployment/happykube-bot -n happykube
```

## 📞 Rollback Plan

If something goes wrong:

```sql
-- Restore old schema
DROP TABLE IF EXISTS emotions;
DROP TABLE IF EXISTS users;
ALTER TABLE emotions_archive RENAME TO emotions;
```

Then redeploy v1.

---

**⚠️ IMPORTANT**: Test migration in a staging environment first!
