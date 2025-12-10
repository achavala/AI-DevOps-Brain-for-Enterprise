#!/bin/bash
# Complete observability deployment - handles partial installations

set -e

echo "📊 Completing Observability Stack Deployment..."
echo ""

# Check if kubectl can connect
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    echo "Please start a local cluster first: minikube start"
    exit 1
fi

echo "✅ Connected to cluster: $(kubectl config current-context)"
echo ""

# Check current Prometheus status
if helm list -n monitoring | grep -q prometheus; then
    echo "⚠️  Prometheus release exists but may be incomplete"
    echo "   Attempting to complete installation..."
    echo ""
    
    # Try to upgrade/install
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --set prometheus.prometheusSpec.retention=7d \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi \
        --set grafana.enabled=true \
        --set grafana.persistence.enabled=false \
        --set grafana.adminPassword=admin \
        --wait --timeout=10m || {
        echo "⚠️  Helm upgrade timed out or failed"
        echo "   This is normal for large charts. Checking status..."
    }
else
    echo "📊 Installing Prometheus + Grafana..."
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --set prometheus.prometheusSpec.retention=7d \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi \
        --set grafana.enabled=true \
        --set grafana.persistence.enabled=false \
        --set grafana.adminPassword=admin \
        --wait --timeout=10m || {
        echo "⚠️  Installation may take longer. Checking status..."
    }
fi

echo ""
echo "⏳ Waiting for pods to be ready (this may take 2-3 minutes)..."
sleep 30

# Check pod status
echo ""
echo "📊 Pod Status:"
kubectl get pods -n monitoring | grep -E "NAME|prometheus|grafana|alertmanager" || true

echo ""
echo "✅ Observability stack deployment initiated!"
echo ""
echo "📝 Note: Full deployment may take 5-10 minutes"
echo "   Check status with: kubectl get pods -n monitoring"
echo ""
echo "🌐 Access URLs (after pods are ready):"
echo "  Grafana: kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80"
echo "  Prometheus: kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090"
echo "  Alertmanager: kubectl port-forward svc/alertmanager-main -n monitoring 9093:9093"

