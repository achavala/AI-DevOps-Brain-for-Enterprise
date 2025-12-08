#!/bin/bash
# Stop all local dashboards

set -e

echo "🛑 Stopping local dashboards..."
echo ""

# Stop port-forwards
PORTS=("grafana" "prometheus" "argocd" "trading-dashboard" "docs-server")

for port in "${PORTS[@]}"; do
    if [ -f "/tmp/port-forward-$port.pid" ]; then
        PID=$(cat /tmp/port-forward-$port.pid)
        if ps -p $PID > /dev/null 2>&1; then
            kill $PID 2>/dev/null || true
            echo "  ✅ Stopped $port (PID: $PID)"
        fi
        rm -f /tmp/port-forward-$port.pid
    fi
done

# Stop Minikube dashboard
if [ -f "/tmp/minikube-dashboard.pid" ]; then
    PID=$(cat /tmp/minikube-dashboard.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null || true
        echo "  ✅ Stopped Minikube Dashboard (PID: $PID)"
    fi
    rm -f /tmp/minikube-dashboard.pid
fi

# Stop trading dashboard
if [ -f "/tmp/trading-dashboard.pid" ]; then
    PID=$(cat /tmp/trading-dashboard.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null || true
        echo "  ✅ Stopped Trading Dashboard (PID: $PID)"
    fi
    rm -f /tmp/trading-dashboard.pid
fi

# Stop docs server
if [ -f "/tmp/docs-server.pid" ]; then
    PID=$(cat /tmp/docs-server.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID 2>/dev/null || true
        echo "  ✅ Stopped Docs Server (PID: $PID)"
    fi
    rm -f /tmp/docs-server.pid
fi

# Kill any remaining port-forwards
pkill -f "kubectl port-forward" 2>/dev/null || true

echo ""
echo "✅ All dashboards stopped"
echo ""

