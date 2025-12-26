# HappyKube v2 - Deployment Guide 🚀

Complete guide for deploying HappyKube v2 on Minikube.

## Prerequisites ✅

- [x] Docker installed and running
- [x] Minikube installed
- [x] kubectl installed
- [x] Python 3.12+
- [x] Neon PostgreSQL database (already set up)
- [x] Telegram Bot Token

## Step-by-Step Deployment

### 1. Start Minikube

```bash
# Start Minikube with sufficient resources
minikube start --cpus=4 --memory=8192 --driver=docker

# Verify Minikube is running
minikube status

# Enable metrics server (optional, for HPA)
minikube addons enable metrics-server
```

### 2. Prepare Secrets

The secrets file is already created at `deployment/overlays/minikube/secrets.yaml` with your Neon credentials.

**⚠️ IMPORTANT**: This file contains sensitive data and is gitignored!

Current configuration:
- Database: Neon PostgreSQL (ep-cold-brook-agz9f5sw-pooler...)
- Telegram Token: Your existing bot token
- Encryption: Pre-generated Fernet key
- API Keys: `dev-key-12345` and `minikube-test-key`

### 3. Deploy to Minikube

```bash
# Navigate to project root
cd /Users/marcobellingeri/Documents/GitHub/HappyKube/happykube-v2

# Make deployment script executable
chmod +x scripts/deploy_minikube.sh

# Run deployment script
./scripts/deploy_minikube.sh
```

The script will:
1. ✅ Check Minikube is running
2. ✅ Build Docker images (API & Bot)
3. ✅ Apply Kubernetes manifests
4. ✅ Wait for all pods to be ready
5. ✅ Show deployment status

### 4. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n happykube

# Expected output:
# NAME                             READY   STATUS    RESTARTS   AGE
# redis-xxx                        1/1     Running   0          2m
# happykube-api-xxx                1/1     Running   0          2m
# happykube-bot-xxx                1/1     Running   0          2m

# Check logs
kubectl logs -f deployment/happykube-api -n happykube
kubectl logs -f deployment/happykube-bot -n happykube
```

### 5. Test the API (Optional)

```bash
# Port forward API service
kubectl port-forward svc/happykube-api 5000:80 -n happykube

# In another terminal, test health check
curl http://localhost:5000/healthz

# Test readiness (checks DB + Redis)
curl http://localhost:5000/readyz

# Test emotion analysis
curl -X POST http://localhost:5000/api/v1/emotion \
  -H "Content-Type: application/json" \
  -H "X-API-Key: dev-key-12345" \
  -d '{"user_id": "123456789", "text": "Oggi mi sento molto felice!"}'

# Expected response:
{
  "emotion": "joy",
  "sentiment": "positive",
  "score": 0.95,
  "confidence": "95%",
  "model_type": "italian_emotion"
}
```

### 6. Test the Telegram Bot

1. Open Telegram and search for your bot
2. Send `/start` - you should get a welcome message
3. Send any emotion text like "Mi sento triste"
4. Bot should analyze and respond with emotion + confidence

### 7. Monitor Logs

```bash
# Watch all logs in namespace
kubectl logs -f -l app=happykube-api -n happykube --tail=50

# Watch bot logs
kubectl logs -f -l app=happykube-bot -n happykube --tail=50

# Watch Redis logs
kubectl logs -f -l app=redis -n happykube --tail=50
```

## Database Migrations

### Run Initial Migration

```bash
# Port forward to API pod
kubectl port-forward deployment/happykube-api 5000:5000 -n happykube

# In another terminal, exec into the pod
kubectl exec -it deployment/happykube-api -n happykube -- /bin/bash

# Inside pod, run migrations
alembic upgrade head

# Exit pod
exit
```

### Migrate Old Data (If Needed)

If you have data from v1:

```bash
# Exec into API pod
kubectl exec -it deployment/happykube-api -n happykube -- /bin/bash

# Run migration script
python scripts/migrate_old_data.py

# Check logs for migration status
```

## Troubleshooting

### Pods Not Starting

```bash
# Describe pod to see errors
kubectl describe pod -l app=happykube-api -n happykube

# Check events
kubectl get events -n happykube --sort-by='.lastTimestamp'
```

### Database Connection Issues

```bash
# Check if secrets are correct
kubectl get secret happykube-secrets -n happykube -o yaml

# Test connection from pod
kubectl exec -it deployment/happykube-api -n happykube -- python -c "
from src.infrastructure.database import health_check
print('DB Health:', health_check())
"
```

### Redis Connection Issues

```bash
# Check Redis is running
kubectl get pods -l app=redis -n happykube

# Test Redis from API pod
kubectl exec -it deployment/happykube-api -n happykube -- python -c "
from src.infrastructure.cache import get_cache
cache = get_cache()
print('Redis Health:', cache.health_check())
"
```

### Image Pull Errors

If you see ImagePullBackOff:

```bash
# Rebuild images in Minikube's Docker daemon
eval $(minikube docker-env)

# Rebuild
docker build -f docker/Dockerfile.api -t emmekappa23/happykube-api:latest .
docker build -f docker/Dockerfile.bot -t emmekappa23/happykube-bot:latest .

# Restart deployments
kubectl rollout restart deployment/happykube-api -n happykube
kubectl rollout restart deployment/happykube-bot -n happykube
```

## Scaling

```bash
# Scale API replicas
kubectl scale deployment/happykube-api --replicas=3 -n happykube

# Bot should stay at 1 replica (Telegram limitation)

# Check HPA (if metrics-server is enabled)
kubectl get hpa -n happykube
```

## Cleanup

```bash
# Delete entire namespace
kubectl delete namespace happykube

# Stop Minikube
minikube stop

# Delete Minikube cluster (removes all data)
minikube delete
```

## Next Steps

### For Production Deployment:

1. **Rotate Secrets**:
   ```bash
   python scripts/generate_encryption_key.py
   ```
   Update secrets with new key

2. **Use Sealed Secrets**:
   Install sealed-secrets controller for production

3. **Setup Ingress**:
   Configure ingress for external API access

4. **Enable TLS**:
   Use cert-manager for HTTPS

5. **Configure Monitoring**:
   - Prometheus for metrics
   - Grafana for dashboards
   - Loki for log aggregation

6. **Setup Backups**:
   Configure database backups (Neon has automatic backups)

### For AWS/Oracle Deployment:

See `deployment/overlays/aws/` or `deployment/overlays/oracle/` for cloud-specific configurations.

---

**Good luck with your deployment! 🚀**
