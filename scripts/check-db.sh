#!/bin/bash
# Check database connectivity and setup

set -e

echo "🔍 Checking database connectivity..."
echo ""

# Check if PostgreSQL container is running
if ! docker ps | grep -q postgres-finance; then
    echo "❌ PostgreSQL container not running"
    echo ""
    echo "To start it:"
    echo "  ./scripts/setup-local-services.sh"
    exit 1
fi

echo "✅ PostgreSQL container is running"
echo ""

# Check database connection
export PGPASSWORD=postgres

if psql -h localhost -p 5433 -U postgres -d postgres -c "SELECT 1" &> /dev/null; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check container: docker ps | grep postgres"
    echo "  2. Check logs: docker logs postgres-finance"
    echo "  3. Check port: lsof -i :5433"
    unset PGPASSWORD
    exit 1
fi

# Check if devops_brain database exists
if psql -h localhost -p 5433 -U postgres -d devops_brain -c "SELECT 1" &> /dev/null; then
    echo "✅ devops_brain database exists"
    
    # Check if incidents table exists
    if psql -h localhost -p 5433 -U postgres -d devops_brain -c "\dt incidents" &> /dev/null; then
        echo "✅ incidents table exists"
        
        # Count incidents
        COUNT=$(psql -h localhost -p 5433 -U postgres -d devops_brain -t -c "SELECT COUNT(*) FROM incidents;" 2>/dev/null | tr -d ' ')
        echo "   📊 Total incidents: $COUNT"
    else
        echo "⚠️  incidents table does not exist"
        echo "   Run: psql -h localhost -p 5433 -U postgres -f ai-operator/k8s/db-schema.sql"
    fi
else
    echo "⚠️  devops_brain database does not exist"
    echo "   Creating it..."
    psql -h localhost -p 5433 -U postgres -d postgres -c "CREATE DATABASE devops_brain;" 2>/dev/null || true
    echo "   ✅ Database created"
    echo "   Now run: psql -h localhost -p 5433 -U postgres -f ai-operator/k8s/db-schema.sql"
fi

unset PGPASSWORD

echo ""
echo "✅ Database check complete!"

