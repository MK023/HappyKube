# HappyKube v2 - Quick Start Guide 🚀

## 5-Minute Deploy to Minikube

### Prerequisites
- ✅ Minikube installed
- ✅ Docker running
- ✅ kubectl installed

### Step 1: Start Minikube (30 seconds)
```bash
minikube start --cpus=4 --memory=8192
```

### Step 2: Deploy HappyKube (3-5 minutes)
```bash
cd /Users/marcobellingeri/Documents/GitHub/HappyKube/happykube-v2

# Deploy everything
./scripts/deploy_minikube.sh
```

That's it! ✅

### Step 3: Verify It's Working
```bash
# Check pods are running
kubectl get pods -n happykube

# Watch bot logs
kubectl logs -f deployment/happykube-bot -n happykube
```

### Step 4: Test Your Telegram Bot
1. Open Telegram
2. Search for your bot
3. Send: `/start`
4. Send: "Mi sento felice!"
5. Get instant emotion analysis! 🎉

---

## What Just Happened?

The deploy script:
1. ✅ Built optimized Docker images (with pre-loaded ML models)
2. ✅ Created K8s namespace `happykube`
3. ✅ Deployed Redis for caching
4. ✅ Deployed API (2 replicas)
5. ✅ Deployed Telegram Bot
6. ✅ Connected to your Neon database
7. ✅ Applied all secrets

---

## Secrets Already Configured

Your `deployment/overlays/minikube/secrets.yaml` contains:
- ✅ Neon PostgreSQL credentials
- ✅ Telegram bot token
- ✅ Encryption keys
- ✅ API keys

**🔒 This file is gitignored for security!**

---

## Common Commands

### View Logs
```bash
# Bot logs
kubectl logs -f deployment/happykube-bot -n happykube

# API logs
kubectl logs -f deployment/happykube-api -n happykube

# Redis logs
kubectl logs -f deployment/redis -n happykube
```

### Port Forward API (for testing)
```bash
kubectl port-forward svc/happykube-api 5000:80 -n happykube

# In another terminal:
curl http://localhost:5000/healthz
```

### Restart Deployments
```bash
kubectl rollout restart deployment/happykube-bot -n happykube
kubectl rollout restart deployment/happykube-api -n happykube
```

### Scale API
```bash
kubectl scale deployment/happykube-api --replicas=3 -n happykube
```

### Delete Everything
```bash
kubectl delete namespace happykube
```

---

## Troubleshooting

### Pods not starting?
```bash
kubectl describe pod -l app=happykube-api -n happykube
```

### Can't connect to database?
Check secrets:
```bash
kubectl get secret happykube-secrets -n happykube -o yaml
```

### Need to rebuild images?
```bash
eval $(minikube docker-env)
docker build -f docker/Dockerfile.api -t emmekappa23/happykube-api:latest .
docker build -f docker/Dockerfile.bot -t emmekappa23/happykube-bot:latest .
kubectl rollout restart deployment -n happykube
```

---

## Next Steps

1. **Migrate Old Data** (if you have v1 data):
   ```bash
   kubectl exec -it deployment/happykube-api -n happykube -- \
     python scripts/migrate_old_data.py
   ```

2. **Run Tests** (when ready):
   ```bash
   pytest
   ```

3. **Deploy to Production** (AWS/Oracle):
   - See `DEPLOYMENT_GUIDE.md`
   - Update overlays in `deployment/overlays/aws/` or `oracle/`

---

## Architecture at a Glance

```
Telegram Users
      ↓
 [Telegram Bot] ─────┐
      ↓              │
 [Redis Cache]       │
      ↓              ↓
   [API] ←─── [Neon PostgreSQL]
      ↓
 [ML Models]
  - Italian Emotion
  - English Emotion
  - Sentiment
```

**All running in Kubernetes! ☸️**

---

## Security Features Active

- ✅ AES-256 encryption for user text
- ✅ SHA-256 hashed user IDs
- ✅ API key authentication
- ✅ Rate limiting (100 req/min)
- ✅ Non-root containers
- ✅ Secrets in K8s Secrets (not in git!)

---

## Performance Features

- ✅ Redis caching (1-hour TTL)
- ✅ Connection pooling (10+20 connections)
- ✅ Pre-loaded ML models (no download at runtime)
- ✅ Horizontal Pod Autoscaling (2-5 replicas)
- ✅ Optimized Docker images (~40% smaller)

---

**You're all set! Enjoy your AI-powered emotion bot! 🤖😊**

For detailed information, see:
- [README.md](README.md) - Full documentation
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Detailed deployment
- [MIGRATION.md](MIGRATION.md) - Migrating from v1
