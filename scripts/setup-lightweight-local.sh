#!/bin/bash
# Lightweight local setup - minimal services for everyday use
# Skips heavy components like ArgoCD, full observability stack

set -e

echo "⚡ Setting up lightweight local environment..."
echo ""

# Check Docker
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Start Minikube with fewer resources
if ! kubectl cluster-info &> /dev/null; then
    echo "📦 Starting Minikube (lightweight)..."
    minikube start --driver=docker --cpus=2 --memory=4g
    echo "✅ Minikube started"
else
    echo "✅ Minikube already running"
fi
echo ""

# Start only essential services
echo "🐳 Starting essential services..."
./scripts/setup-local-services.sh
echo ""

# Deploy only essential platform components
echo "☸️  Deploying essential platform components..."

# Create namespaces
kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Deploy only Prometheus (lightweight)
if ! kubectl get deployment prometheus-operator -n monitoring &> /dev/null; then
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    helm install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --set prometheus.prometheusSpec.retention=1d \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=5Gi \
        --set grafana.enabled=true
fi

# Deploy FluentBit (lightweight)
kubectl apply -f data-pipeline/fluentbit/fluentbit-config-local.yaml

echo ""
echo "✅ Lightweight environment ready"
echo ""
echo "This setup includes:"
echo "  ✅ PostgreSQL, Redis, Kafka, MinIO"
echo "  ✅ Prometheus + Grafana"
echo "  ✅ FluentBit"
echo "  ❌ ArgoCD (skipped)"
echo "  ❌ Full observability stack (skipped)"
echo ""
echo "For full setup: ./scripts/start-local.sh"
echo ""

