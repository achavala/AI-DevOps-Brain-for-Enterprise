#!/bin/bash
# Fix missing dependencies for AI Operator and models

set -e

echo "🔧 Fixing dependencies..."
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Not in a virtual environment"
    echo "   Activating virtual environment..."
    
    if [ -d "ai-models/venv" ]; then
        source ai-models/venv/bin/activate
        echo "✅ Activated ai-models/venv"
    elif [ -d "venv" ]; then
        source venv/bin/activate
        echo "✅ Activated venv"
    else
        echo "❌ No virtual environment found"
        echo "   Creating one..."
        python3 -m venv venv
        source venv/bin/activate
        echo "✅ Created and activated venv"
    fi
fi

echo ""
echo "📦 Installing AI Operator dependencies..."
if [ -f "ai-operator/requirements.txt" ]; then
    pip install -r ai-operator/requirements.txt
else
    # Install core dependencies
    pip install kubernetes psycopg2-binary redis kafka-python
fi

echo ""
echo "📦 Installing AI Models dependencies..."
if [ -f "ai-models/requirements.txt" ]; then
    pip install -r ai-models/requirements.txt
fi

echo ""
echo "📦 Installing FinOps dependencies..."
if [ -f "finops/requirements.txt" ]; then
    pip install -r finops/requirements.txt
fi

echo ""
echo "✅ Dependencies installed!"
echo ""
echo "Verify installation:"
echo "  python3 -c 'import kubernetes; print(\"✅ kubernetes:\", kubernetes.__version__)'"
echo "  python3 -c 'import psycopg2; print(\"✅ psycopg2 installed\")'"
echo "  python3 -c 'import redis; print(\"✅ redis installed\")'"
echo ""

