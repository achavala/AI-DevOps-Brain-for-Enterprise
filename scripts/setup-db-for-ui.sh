#!/bin/bash
# Setup database for UI (creates database and schema if needed)

set -e

echo "🔧 Setting up database for AI DevOps Brain UI..."
echo ""

# Check if PostgreSQL container is running
if ! docker ps | grep -q postgres-finance; then
    echo "❌ PostgreSQL container not running"
    echo "   Starting it..."
    ./scripts/setup-local-services.sh > /dev/null 2>&1
    sleep 5
fi

echo "✅ PostgreSQL container is running"
echo ""

# Create database via docker exec (bypasses password issues)
echo "📦 Creating devops_brain database..."
docker exec postgres-finance psql -U postgres -c "CREATE DATABASE devops_brain;" 2>/dev/null || echo "   (Database may already exist)"

echo "✅ Database created"
echo ""

# Create schema
echo "📋 Creating database schema..."
if [ -f "ai-operator/k8s/db-schema.sql" ]; then
    docker exec -i postgres-finance psql -U postgres -d devops_brain < ai-operator/k8s/db-schema.sql 2>/dev/null || echo "   (Schema may already exist)"
    echo "✅ Schema created"
else
    echo "⚠️  Schema file not found: ai-operator/k8s/db-schema.sql"
fi

echo ""
echo "✅ Database setup complete!"
echo ""
echo "You can now start the UI:"
echo "  ./scripts/start-ui.sh"

