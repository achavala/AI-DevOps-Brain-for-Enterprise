#!/bin/bash
# Run the Streamlit UI

set -e

cd "$(dirname "$0")"

echo "🚀 Starting AI DevOps Brain Web UI..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Set environment variables
export POSTGRES_HOST=${POSTGRES_HOST:-localhost}
export POSTGRES_PORT=${POSTGRES_PORT:-5433}
export POSTGRES_DB=${POSTGRES_DB:-devops_brain}
export POSTGRES_USER=${POSTGRES_USER:-postgres}
# Use password from docker-compose if not set
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-finance123}

# Optional: Set DB_URL directly (overrides individual vars if set)
export DB_URL=${DB_URL:-"postgresql+psycopg2://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}"}

# Run Streamlit
echo ""
echo "🌐 Starting Streamlit server..."
echo "   URL: http://localhost:8504"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run app.py --server.port 8504 --server.address localhost

