#!/bin/bash
# Test database connectivity for UI

set -e

echo "🔍 Testing database connectivity for UI..."
echo ""

# Check if PostgreSQL container is running
if ! docker ps | grep -q postgres-finance; then
    echo "❌ PostgreSQL container not running"
    echo "   Run: ./scripts/setup-local-services.sh"
    exit 1
fi

echo "✅ PostgreSQL container is running"
echo ""

# Test connection with SQLAlchemy pattern
python3 << 'EOF'
import os
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Use same env vars as UI
db_url = os.getenv(
    'DB_URL',
    f"postgresql+psycopg2://{os.getenv('POSTGRES_USER', 'postgres')}:"
    f"{os.getenv('POSTGRES_PASSWORD', 'finance123')}@"
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"
    f"{os.getenv('POSTGRES_PORT', '5433')}/"
    f"{os.getenv('POSTGRES_DB', 'devops_brain')}"
)

try:
    engine = create_engine(db_url, poolclass=NullPool, future=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Check if incidents table exists
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'incidents'
        """))
        table_exists = result.scalar() > 0
        
        if table_exists:
            print("✅ incidents table exists")
            
            # Count incidents
            result = conn.execute(text("SELECT COUNT(*) FROM incidents"))
            count = result.scalar()
            print(f"   📊 Total incidents: {count}")
        else:
            print("⚠️  incidents table does not exist")
            print("   Run: ./scripts/setup-db-for-ui.sh")
    
    engine.dispose()
    print("")
    print("✅ All database checks passed!")
    
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)
EOF

echo ""
echo "✅ Database connectivity test complete!"

