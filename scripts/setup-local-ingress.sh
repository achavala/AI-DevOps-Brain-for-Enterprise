#!/bin/bash
# Setup local ingress for dashboards (trading.local, grafana.local, etc.)

set -e

echo "🌐 Setting up local ingress for dashboards..."
echo ""

# Check if Minikube is running
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not running"
    echo "   Run: ./scripts/start-local.sh first"
    exit 1
fi

# Enable Minikube ingress addon
echo "📦 Enabling Minikube ingress addon..."
minikube addons enable ingress
echo "✅ Ingress addon enabled"
echo ""

# Wait for ingress controller to be ready
echo "⏳ Waiting for ingress controller..."
kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=300s || echo "⚠️  Ingress controller may still be starting"
echo ""

# Get Minikube IP
MINIKUBE_IP=$(minikube ip)
echo "📍 Minikube IP: $MINIKUBE_IP"
echo ""

# Apply ingress configuration
echo "📋 Applying ingress configuration..."
kubectl apply -f k8s/local/ingress.yaml
echo "✅ Ingress configured"
echo ""

# Update /etc/hosts (requires sudo)
echo "📝 Updating /etc/hosts..."
echo ""
echo "Add these lines to /etc/hosts (requires sudo):"
echo ""
echo "$MINIKUBE_IP trading.local"
echo "$MINIKUBE_IP grafana.local"
echo "$MINIKUBE_IP prometheus.local"
echo "$MINIKUBE_IP argocd.local"
echo "$MINIKUBE_IP minio.local"
echo ""

read -p "Do you want to update /etc/hosts automatically? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup /etc/hosts
    sudo cp /etc/hosts /etc/hosts.backup.$(date +%Y%m%d_%H%M%S)
    
    # Remove old entries
    sudo sed -i '' '/trading.local\|grafana.local\|prometheus.local\|argocd.local\|minio.local/d' /etc/hosts
    
    # Add new entries
    echo "$MINIKUBE_IP trading.local" | sudo tee -a /etc/hosts
    echo "$MINIKUBE_IP grafana.local" | sudo tee -a /etc/hosts
    echo "$MINIKUBE_IP prometheus.local" | sudo tee -a /etc/hosts
    echo "$MINIKUBE_IP argocd.local" | sudo tee -a /etc/hosts
    echo "$MINIKUBE_IP minio.local" | sudo tee -a /etc/hosts
    
    echo "✅ /etc/hosts updated"
else
    echo "ℹ️  Please manually update /etc/hosts with the IPs above"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Local ingress setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Access dashboards at:"
echo "  💰 Trading:    http://trading.local"
echo "  📈 Grafana:   http://grafana.local"
echo "  📊 Prometheus: http://prometheus.local"
echo "  🔄 ArgoCD:    https://argocd.local"
echo "  📦 MinIO:     http://minio.local"
echo ""
echo "Note: You may need to accept self-signed certificates for HTTPS"
echo ""

