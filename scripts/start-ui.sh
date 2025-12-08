#!/bin/bash
# Start the AI DevOps Brain Web UI

set -e

cd "$(dirname "$0")/.."

echo "🚀 Starting AI DevOps Brain Web UI..."
echo ""

# Check if PostgreSQL container is running
if ! docker ps | grep -q postgres-finance; then
    echo "⚠️  PostgreSQL container not running"
    echo "   Starting local services..."
    ./scripts/setup-local-services.sh > /dev/null 2>&1
    echo "   ⏳ Waiting for PostgreSQL to be ready..."
    sleep 5
fi

# Check database via docker exec (bypasses password authentication)
if docker exec postgres-finance psql -U postgres -c "SELECT 1" &> /dev/null; then
    echo "   ✅ Database accessible"
    
    # Ensure devops_brain database exists
    docker exec postgres-finance psql -U postgres -c "CREATE DATABASE devops_brain;" 2>/dev/null || true
    
    echo ""
else
    echo "   ⚠️  Database not accessible via container"
    echo "   Run: ./scripts/setup-db-for-ui.sh"
    echo ""
fi

# Start UI
cd ai-operator/ui
chmod +x run.sh

echo "🌐 UI will be available at: http://localhost:8504"
echo ""

./run.sh

