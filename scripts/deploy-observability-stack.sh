#!/bin/bash
# Deploy complete observability stack: Prometheus, Grafana, Loki, FluentBit, KEDA
# Optimized for local Minikube environment

set -e

echo "📊 Deploying Observability Stack..."
echo ""

# Check if kubectl can connect
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    echo ""
    echo "Please start a local cluster first:"
    echo "  Minikube: minikube start"
    exit 1
fi

echo "✅ Connected to cluster: $(kubectl config current-context)"
echo ""

# Create namespaces
echo "📦 Creating namespaces..."
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace keda --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Namespaces created"
echo ""

# Check if Helm is installed
if ! command -v helm &> /dev/null; then
    echo "❌ Helm is not installed"
    echo "Install with: brew install helm (macOS) or visit https://helm.sh/docs/intro/install/"
    exit 1
fi

# Add Helm repos
echo "📚 Adding Helm repositories..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
echo "✅ Helm repos updated"
echo ""

# Install Prometheus + Grafana Stack
echo "📊 Installing Prometheus + Grafana..."
echo "   (This may take 10-15 minutes on Minikube - be patient!)"
echo ""

# Check if release exists
if helm list -n monitoring | grep -q prometheus; then
    echo "⚠️  Prometheus release exists, upgrading..."
    UPGRADE_MODE="upgrade"
else
    echo "📦 Installing new Prometheus release..."
    UPGRADE_MODE="install"
fi

# For Minikube/local: disable Grafana persistence to avoid PVC issues
# This is fine for local dev - Grafana will work without persistence
helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
    --namespace monitoring \
    --create-namespace \
    --set prometheus.prometheusSpec.retention=7d \
    --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi \
    --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
    --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
    --set grafana.enabled=true \
    --set grafana.adminPassword=admin \
    --set grafana.persistence.enabled=false \
    --set grafana.service.type=NodePort \
    --set grafana.service.nodePort=30080 \
    --timeout=20m \
    --wait || {
    echo "⚠️  Helm deployment in progress (timeout is normal for large charts)"
    echo "   Checking status..."
}

# Wait for critical pods (with longer timeout)
echo ""
echo "⏳ Waiting for critical pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus-operator -n monitoring --timeout=300s || echo "⚠️  Prometheus operator still starting..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s || echo "⚠️  Grafana still starting..."

echo "✅ Prometheus + Grafana deployment initiated"
echo ""

# Install Loki
echo "📝 Installing Loki..."
echo "   (For local dev, disabling persistence to avoid storage issues)"
echo ""

# For Minikube: disable persistence (logs will be ephemeral but that's OK for local)
helm upgrade --install loki grafana/loki-stack \
    --namespace logging \
    --create-namespace \
    --set loki.persistence.enabled=false \
    --set loki.config.limits_config.retention_period=24h \
    --set promtail.enabled=true \
    --set grafana.enabled=false \
    --timeout=15m \
    --wait || {
    echo "⚠️  Loki deployment in progress..."
}

echo "✅ Loki deployment initiated"
echo ""

# Configure Grafana to use Loki
echo "🔗 Configuring Grafana to use Loki..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  namespace: monitoring
data:
  datasources.yaml: |
    apiVersion: 1
    datasources:
      - name: Prometheus
        type: prometheus
        access: proxy
        url: http://prometheus-kube-prometheus-prometheus.monitoring.svc.cluster.local:9090
        isDefault: true
      - name: Loki
        type: loki
        access: proxy
        url: http://loki.logging.svc.cluster.local:3100
EOF

# Restart Grafana to pick up datasource config
kubectl rollout restart deployment/prometheus-grafana -n monitoring || true
echo "✅ Grafana configured with Prometheus and Loki"
echo ""

# Deploy FluentBit Daemonset
echo "📥 Deploying FluentBit..."
kubectl apply -f data-pipeline/fluentbit/fluentbit-config-local.yaml
kubectl apply -f data-pipeline/fluentbit/daemonset.yaml
echo "✅ FluentBit deployed"
echo ""

# Install KEDA
echo "📈 Installing KEDA..."
helm upgrade --install keda kedacore/keda \
    --namespace keda \
    --create-namespace \
    --timeout=10m \
    --wait || {
    echo "⚠️  KEDA deployment in progress..."
}

echo "✅ KEDA deployment initiated"
echo ""

# Wait for all pods to be ready
echo "⏳ Waiting for all pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n monitoring --timeout=300s || true
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n monitoring --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=loki -n logging --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=fluent-bit -n logging --timeout=300s || true
kubectl wait --for=condition=ready pod -l app=keda-operator -n keda --timeout=300s || true
echo ""

# Import Grafana dashboards
echo "📊 Importing Grafana dashboards..."
./scripts/import-grafana-dashboards.sh
echo ""

# Configure alerts
echo "🚨 Configuring Prometheus alerts..."
./scripts/configure-alerts.sh
echo ""

# Get service URLs
echo "🌐 Service URLs:"
echo ""
echo "Grafana:"
GRAFANA_PORT=$(kubectl get svc prometheus-grafana -n monitoring -o jsonpath='{.spec.ports[?(@.name=="service")].nodePort}' 2>/dev/null || echo "30080")
echo "  Local: http://localhost:${GRAFANA_PORT}"
echo "  Minikube: $(minikube service prometheus-grafana -n monitoring --url 2>/dev/null | head -1 || echo "N/A")"
echo "  Username: admin"
echo "  Password: admin"
echo ""

echo "Prometheus:"
PROM_PORT=$(kubectl get svc prometheus-kube-prometheus-prometheus -n monitoring -o jsonpath='{.spec.ports[?(@.name=="http-web")].port}' 2>/dev/null || echo "9090")
echo "  Port-forward: kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring ${PROM_PORT}:9090"
echo "  Then: http://localhost:9090"
echo ""

echo "Loki:"
echo "  Port-forward: kubectl port-forward svc/loki -n logging 3100:3100"
echo "  Then: http://localhost:3100"
echo ""

# Check pod status
echo "📊 Pod Status:"
echo ""
echo "Monitoring namespace:"
kubectl get pods -n monitoring
echo ""
echo "Logging namespace:"
kubectl get pods -n logging
echo ""
echo "KEDA namespace:"
kubectl get pods -n keda
echo ""

echo "✅ Observability stack deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Access Grafana: http://localhost:${GRAFANA_PORT} (admin/admin)"
echo "  2. Check dashboards: All 19 industry dashboards should be available"
echo "  3. Test metrics: Generate traffic with ./scripts/load-traffic-all.sh"
echo "  4. Test logs: Check Loki datasource in Grafana"
echo ""

