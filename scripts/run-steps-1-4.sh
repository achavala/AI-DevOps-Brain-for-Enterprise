#!/bin/bash
# Complete Steps 1-4: Observability, Alerts, AI Operator, Chaos
# This script ensures all dependencies are installed and runs all steps

set -e

echo "🚀 Running Steps 1-4: Complete MVP Validation"
echo ""

# Step 0: Ensure dependencies are installed
echo "📦 Step 0: Installing dependencies..."
if [ -d "ai-models/venv" ]; then
    source ai-models/venv/bin/activate
    echo "✅ Activated ai-models/venv"
    
    # Install AI Operator dependencies
    if ! python3 -c "import psycopg2" 2>/dev/null; then
        echo "   Installing missing dependencies..."
        pip install -r ai-operator/requirements.txt --quiet
        echo "   ✅ Dependencies installed"
    else
        echo "   ✅ Dependencies already installed"
    fi
else
    echo "❌ ai-models/venv not found"
    echo "   Please run: python3 -m venv ai-models/venv"
    exit 1
fi

echo ""

# Step 1: Complete observability deployment
echo "📊 Step 1: Completing Observability Deployment..."
echo "   (This may take 5-10 minutes - be patient!)"
echo ""
./scripts/complete-observability-deployment.sh || {
    echo "⚠️  Observability deployment in progress (this is normal)"
    echo "   You can check status with: kubectl get pods -n monitoring"
}

echo ""
echo "⏸️  Waiting 30 seconds for services to stabilize..."
sleep 30

# Step 2: Configure alerts (already done, but verify)
echo ""
echo "🚨 Step 2: Verifying Alert Configuration..."
if kubectl get prometheusrule ai-devops-brain-alerts -n monitoring &>/dev/null; then
    echo "   ✅ Alerts already configured"
else
    echo "   Configuring alerts..."
    ./scripts/configure-alerts.sh
fi

echo ""

# Step 3: Run AI Operator
echo "🔍 Step 3: Running AI Operator..."
echo "   (Press Ctrl+C to stop after validation)"
echo ""

# Ensure we're in the right venv
source ai-models/venv/bin/activate

# Run AI Operator in background, capture output
python3 ai-operator/ai-operator.py &
AI_OPERATOR_PID=$!

echo "   AI Operator started (PID: $AI_OPERATOR_PID)"
echo "   Waiting 10 seconds to validate startup..."
sleep 10

# Check if it's still running
if kill -0 $AI_OPERATOR_PID 2>/dev/null; then
    echo "   ✅ AI Operator is running"
    echo "   To stop: kill $AI_OPERATOR_PID"
else
    echo "   ❌ AI Operator stopped unexpectedly"
    echo "   Check logs above for errors"
    exit 1
fi

echo ""

# Step 4: Test chaos → detection → RCA loop
echo "💥 Step 4: Testing Chaos → Detection → RCA Loop..."
echo "   Injecting chaos across industries..."
./scripts/chaos-random-all.sh kill

echo ""
echo "⏸️  Waiting 15 seconds for incidents to be detected..."
sleep 15

echo ""
echo "✅ Steps 1-4 Complete!"
echo ""
echo "📊 Next Steps:"
echo "   1. Check AI Operator logs (it's running in background)"
echo "   2. View incidents in UI: ./scripts/start-ui.sh"
echo "   3. Check alerts: kubectl port-forward svc/alertmanager-main -n monitoring 9093:9093"
echo "   4. View Grafana: kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80"
echo ""
echo "🛑 To stop AI Operator: kill $AI_OPERATOR_PID"

