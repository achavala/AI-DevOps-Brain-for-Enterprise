#!/bin/bash
# Clean up all AI DevOps Brain containers

set -e

echo "🧹 Cleaning up AI DevOps Brain containers..."
echo ""

CONTAINERS=("postgres-finance" "redis-finance" "kafka-finance" "zookeeper-finance" "minio")

for container in "${CONTAINERS[@]}"; do
    if docker ps -a --format "{{.Names}}" | grep -q "^${container}$"; then
        echo "  Removing $container..."
        docker rm -f "$container" 2>/dev/null || true
        echo "  ✅ $container removed"
    fi
done

echo ""
echo "✅ Cleanup complete"
echo ""
echo "You can now run: ./scripts/setup-local-services.sh"

