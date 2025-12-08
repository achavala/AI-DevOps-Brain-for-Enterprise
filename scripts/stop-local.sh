#!/bin/bash
# Stop local environment - clean shutdown

set -e

echo "🛑 Stopping local AI DevOps Brain environment..."
echo ""

# Stop Minikube
if kubectl cluster-info &> /dev/null; then
    echo "⏸️  Stopping Minikube..."
    minikube stop
    echo "✅ Minikube stopped"
else
    echo "ℹ️  Minikube not running"
fi
echo ""

# Stop Docker services
echo "🐳 Stopping Docker services..."
SERVICES=("postgres-finance" "redis-finance" "kafka-finance" "zookeeper-finance" "minio")

for service in "${SERVICES[@]}"; do
    if docker ps | grep -q "$service"; then
        echo "  Stopping $service..."
        docker stop "$service" &> /dev/null || true
        echo "  ✅ $service stopped"
    fi
done

echo ""
echo "✅ Local environment stopped"
echo ""
echo "To start again: ./scripts/start-local.sh"
echo "To delete everything: ./scripts/clean-local.sh"
echo ""

