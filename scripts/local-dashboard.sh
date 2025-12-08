#!/bin/bash
# Start all local dashboards and UIs in one command

set -e

echo "📊 Starting local dashboards..."
echo ""

# Check if services are running
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not running"
    echo "   Run: ./scripts/start-local.sh first"
    exit 1
fi

# Function to start port-forward in background
start_port_forward() {
    local name=$1
    local namespace=$2
    local service=$3
    local local_port=$4
    local remote_port=$5
    
    if kubectl get svc "$service" -n "$namespace" &> /dev/null; then
        kubectl port-forward -n "$namespace" "svc/$service" "$local_port:$remote_port" &> /tmp/port-forward-$name.log &
        PF_PID=$!
        sleep 2
        if ps -p $PF_PID > /dev/null; then
            echo "  ✅ $name: http://localhost:$local_port (PID: $PF_PID)"
            echo $PF_PID > /tmp/port-forward-$name.pid
        else
            echo "  ⚠️  $name: Failed to start (check logs: /tmp/port-forward-$name.log)"
        fi
    else
        echo "  ⚠️  $name: Service not found (may not be deployed)"
    fi
}

# Start Minikube dashboard
echo "🖥️  Starting Minikube Dashboard..."
minikube dashboard --url &> /tmp/minikube-dashboard.log &
DASHBOARD_PID=$!
sleep 3
if ps -p $DASHBOARD_PID > /dev/null; then
    DASHBOARD_URL=$(grep -o 'http://[^ ]*' /tmp/minikube-dashboard.log | head -1 || echo "http://127.0.0.1:8001")
    echo "  ✅ Minikube Dashboard: $DASHBOARD_URL (PID: $DASHBOARD_PID)"
    echo $DASHBOARD_PID > /tmp/minikube-dashboard.pid
else
    echo "  ⚠️  Minikube Dashboard: Failed to start"
fi
echo ""

# Start Grafana
echo "📈 Starting Grafana..."
start_port_forward "grafana" "monitoring" "prometheus-grafana" "3000" "80"
echo ""

# Start Prometheus
echo "📊 Starting Prometheus..."
start_port_forward "prometheus" "monitoring" "prometheus" "9090" "9090"
echo ""

# Start ArgoCD (if deployed)
echo "🔄 Starting ArgoCD..."
start_port_forward "argocd" "argocd" "argocd-server" "8080" "443"
echo ""

# MinIO Console (already running on port 9001)
echo "📦 MinIO Console..."
if docker ps | grep -q "minio"; then
    echo "  ✅ MinIO Console: http://localhost:9001"
    echo "     Access: minioadmin / minioadmin"
else
    echo "  ⚠️  MinIO not running"
fi
echo ""

# Local Trading Dashboard (if exists)
echo "💰 Trading Dashboard..."
if [ -f "integrations/trading-dashboard.html" ] || [ -d "integrations/dashboard" ]; then
    # Start simple HTTP server for trading dashboard
    cd integrations/dashboard 2>/dev/null || cd integrations
    python3 -m http.server 8081 &> /tmp/trading-dashboard.log &
    TRADING_PID=$!
    sleep 1
    if ps -p $TRADING_PID > /dev/null; then
        echo "  ✅ Trading Dashboard: http://localhost:8081 (PID: $TRADING_PID)"
        echo $TRADING_PID > /tmp/trading-dashboard.pid
        cd - &> /dev/null
    else
        echo "  ⚠️  Trading Dashboard: Not available"
        cd - &> /dev/null
    fi
else
    echo "  ℹ️  Trading Dashboard: Not configured (create integrations/dashboard/)"
fi
echo ""

# Docs viewer (optional)
echo "📚 Documentation..."
if command -v python3 &> /dev/null; then
    cd docs
    python3 -m http.server 8082 &> /tmp/docs-server.log &
    DOCS_PID=$!
    sleep 1
    if ps -p $DOCS_PID > /dev/null; then
        echo "  ✅ Docs Viewer: http://localhost:8082 (PID: $DOCS_PID)"
        echo $DOCS_PID > /tmp/docs-server.pid
        cd - &> /dev/null
    else
        cd - &> /dev/null
    fi
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ All dashboards started!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Available Dashboards:"
echo ""
echo "  🖥️  Minikube Dashboard: $DASHBOARD_URL"
echo "  📈 Grafana:            http://localhost:3000 (admin/prom-operator)"
echo "  📊 Prometheus:         http://localhost:9090"
echo "  🔄 ArgoCD:             https://localhost:8080"
echo "  📦 MinIO Console:      http://localhost:9001 (minioadmin/minioadmin)"
echo "  💰 Trading Dashboard:  http://localhost:8081"
echo "  📚 Documentation:      http://localhost:8082"
echo ""
echo "To stop all dashboards: ./scripts/stop-dashboards.sh"
echo ""

