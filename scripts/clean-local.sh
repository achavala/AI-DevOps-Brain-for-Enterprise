#!/bin/bash
# Clean local environment - removes everything

set -e

echo "🧹 Cleaning local AI DevOps Brain environment..."
echo ""
read -p "This will delete Minikube cluster and all Docker containers. Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Delete Minikube
if kubectl cluster-info &> /dev/null; then
    echo "🗑️  Deleting Minikube cluster..."
    minikube delete
    echo "✅ Minikube deleted"
fi
echo ""

# Stop and remove Docker containers
echo "🐳 Removing Docker containers..."
SERVICES=("postgres-finance" "redis-finance" "kafka-finance" "zookeeper-finance" "minio")

for service in "${SERVICES[@]}"; do
    if docker ps -a | grep -q "$service"; then
        echo "  Removing $service..."
        docker stop "$service" &> /dev/null || true
        docker rm "$service" &> /dev/null || true
        echo "  ✅ $service removed"
    fi
done
echo ""

# Remove volumes (optional - uncomment if you want to delete data)
# echo "🗑️  Removing Docker volumes..."
# docker volume rm postgres-finance-data redis-finance-data 2>/dev/null || true
# echo "✅ Volumes removed"
# echo ""

echo "✅ Cleanup complete"
echo ""
echo "Note: Local data in ./local-data/ and ./ai-models/models/ is preserved"
echo "To remove data as well, manually delete those directories"
echo ""

