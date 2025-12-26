#!/bin/bash
# Deploy HappyKube v2 to Minikube

set -e  # Exit on error

echo "🚀 HappyKube v2 - Minikube Deployment Script"
echo "============================================="

# Check if minikube is running
if ! minikube status | grep -q "Running"; then
    echo "❌ Minikube is not running!"
    echo "   Start it with: minikube start"
    exit 1
fi

echo "✅ Minikube is running"

# Check if secrets file exists
if [ ! -f "deployment/overlays/minikube/secrets.yaml" ]; then
    echo "❌ Secrets file not found!"
    echo "   Copy secrets.yaml.example to secrets.yaml and fill in your values:"
    echo "   cp deployment/overlays/minikube/secrets.yaml.example deployment/overlays/minikube/secrets.yaml"
    exit 1
fi

echo "✅ Secrets file found"

# Build Docker images in Minikube's Docker daemon
echo ""
echo "🐳 Building Docker images..."
eval $(minikube docker-env)

docker build -f docker/Dockerfile.api -t emmekappa23/happykube-api:latest .
echo "✅ API image built"

docker build -f docker/Dockerfile.bot -t emmekappa23/happykube-bot:latest .
echo "✅ Bot image built"

# Apply Kubernetes manifests
echo ""
echo "☸️  Deploying to Kubernetes..."

kubectl apply -f deployment/overlays/minikube/

echo "✅ Manifests applied"

# Wait for deployments
echo ""
echo "⏳ Waiting for deployments to be ready..."

kubectl wait --for=condition=available --timeout=300s deployment/redis -n happykube
echo "✅ Redis is ready"

kubectl wait --for=condition=available --timeout=600s deployment/happykube-api -n happykube
echo "✅ API is ready"

kubectl wait --for=condition=available --timeout=600s deployment/happykube-bot -n happykube
echo "✅ Bot is ready"

# Show status
echo ""
echo "📊 Deployment Status:"
kubectl get pods -n happykube

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Check logs: kubectl logs -f deployment/happykube-bot -n happykube"
echo "   2. Port forward API: kubectl port-forward svc/happykube-api 5000:80 -n happykube"
echo "   3. Test API: curl -H 'X-API-Key: dev-key-12345' http://localhost:5000/healthz"
echo ""
