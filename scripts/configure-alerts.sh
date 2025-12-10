#!/bin/bash
# Configure Prometheus alerts and Alertmanager

set -e

echo "🚨 Configuring Prometheus Alerts..."
echo ""

# Check if kubectl can connect
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    exit 1
fi

echo "✅ Connected to cluster: $(kubectl config current-context)"
echo ""

# Apply alert rules
echo "📋 Applying Prometheus alert rules..."
kubectl apply -f k8s/observability/prometheus-alerts.yaml
echo "✅ Alert rules applied"
echo ""

# Apply Alertmanager configuration
echo "⚙️  Configuring Alertmanager..."
kubectl apply -f k8s/observability/alertmanager-config.yaml

# Restart Alertmanager to pick up new config
if kubectl get deployment alertmanager-main -n monitoring &> /dev/null; then
    echo "🔄 Restarting Alertmanager..."
    kubectl rollout restart deployment/alertmanager-main -n monitoring
    kubectl rollout status deployment/alertmanager-main -n monitoring --timeout=60s
fi
echo "✅ Alertmanager configured"
echo ""

# Verify alert rules
echo "🔍 Verifying alert rules..."
kubectl get prometheusrule -n monitoring
echo ""

# Check Alertmanager config
echo "🔍 Checking Alertmanager configuration..."
kubectl get secret alertmanager-main -n monitoring -o jsonpath='{.data.alertmanager\.yaml}' | base64 -d | head -20
echo ""
echo ""

# Get Alertmanager URL
echo "🌐 Alertmanager URLs:"
echo ""
echo "Alertmanager UI:"
echo "  Port-forward: kubectl port-forward svc/alertmanager-main -n monitoring 9093:9093"
echo "  Then: http://localhost:9093"
echo ""

# Show active alerts
echo "📊 To view active alerts:"
echo "  1. Port-forward Alertmanager: kubectl port-forward svc/alertmanager-main -n monitoring 9093:9093"
echo "  2. Open: http://localhost:9093"
echo "  3. Or check Prometheus: kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090"
echo "  4. Then: http://localhost:9090/alerts"
echo ""

echo "✅ Alert configuration complete!"
echo ""
echo "Configured alerts:"
echo "  ✅ High CPU Usage (warning: >80%, critical: >95%)"
echo "  ✅ High Memory Usage (warning: >85%, critical: >95%)"
echo "  ✅ Pod Failures (crash looping, not ready, failed)"
echo "  ✅ Excessive Pod Restarts (>5 in 1 hour)"
echo "  ✅ Deployment Replica Mismatch"
echo "  ✅ Node Resource Alerts"
echo "  ✅ Application Error Rate & Latency"
echo ""
echo "Next steps:"
echo "  1. Test alerts by generating load: ./scripts/load-traffic-all.sh"
echo "  2. Trigger pod failures: ./scripts/chaos-random-all.sh kill"
echo "  3. Check alerts in Alertmanager UI"
echo ""

