#!/bin/bash
# Setup FinOps database schema

set -e

echo "🔧 Setting up FinOps database..."
echo ""

# Check if PostgreSQL container is running
if ! docker ps | grep -q postgres-finance; then
    echo "❌ PostgreSQL container not running"
    echo "   Run: ./scripts/setup-local-services.sh"
    exit 1
fi

echo "✅ PostgreSQL container is running"
echo ""

# Create database and schema
echo "📦 Creating FinOps database and schema..."
docker exec -i postgres-finance psql -U postgres < finops/db_schema.sql

echo ""
echo "✅ FinOps database setup complete!"
echo ""
echo "📊 Tables created:"
echo "  • cost_baselines"
echo "  • opportunities"
echo "  • cost_allocation"
echo "  • savings_reports"
echo "  • audit_log"

