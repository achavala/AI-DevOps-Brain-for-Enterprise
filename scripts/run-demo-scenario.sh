#!/usr/bin/env bash
# Complete demo scenario: traffic → chaos → AI detection → incidents
# This validates the entire end-to-end flow

set -e

echo "🎬 AI DevOps Brain - Complete Demo Scenario"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check prerequisites
echo "📋 Step 1: Checking prerequisites..."
echo ""

# Check if Kubernetes is running
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Kubernetes cluster not accessible"
    echo "   Run: minikube start"
    exit 1
fi
echo "  ✅ Kubernetes cluster accessible"

# Check if local services are running
if ! docker ps | grep -q postgres-finance; then
    echo "  ⚠️  Local services not running. Starting them..."
    ./scripts/setup-local-services.sh > /dev/null 2>&1
    sleep 5
fi
echo "  ✅ Local services running"

# Check if 19 industries are deployed
INDUSTRY_COUNT=$(kubectl get deployments -A | grep "\-sim" | wc -l | tr -d ' ')
if [ "$INDUSTRY_COUNT" -lt 19 ]; then
    echo "  ⚠️  Not all industries deployed. Deploying..."
    ./scripts/setup-all-19-industries.sh > /dev/null 2>&1
    sleep 10
fi
echo "  ✅ All 19 industries deployed ($INDUSTRY_COUNT deployments)"
echo ""

# Step 2: Setup database schema
echo "📦 Step 2: Setting up database schema..."
if psql -h localhost -p 5433 -U postgres -d devops_brain -c "SELECT 1" &> /dev/null; then
    echo "  ✅ Database accessible"
    if ! psql -h localhost -p 5433 -U postgres -d devops_brain -c "\dt incidents" &> /dev/null; then
        echo "  📝 Creating schema..."
        psql -h localhost -p 5433 -U postgres -f ai-operator/k8s/db-schema.sql > /dev/null 2>&1 || true
    fi
    echo "  ✅ Database schema ready"
else
    echo "  ⚠️  Database not accessible - will continue without DB storage"
fi
echo ""

# Step 3: Deploy AI Operator
echo "🤖 Step 3: Deploying AI Operator..."
if kubectl get deployment ai-operator &> /dev/null; then
    echo "  ✅ AI Operator already deployed"
else
    echo "  📝 Deploying AI Operator..."
    kubectl apply -f ai-operator/k8s/deployment.yaml > /dev/null 2>&1
    echo "  ⏳ Waiting for operator to be ready..."
    sleep 10
    kubectl wait --for=condition=ready pod -l app=ai-operator --timeout=60s > /dev/null 2>&1 || true
fi

OPERATOR_POD=$(kubectl get pod -l app=ai-operator -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || echo "")
if [ -n "$OPERATOR_POD" ]; then
    echo "  ✅ AI Operator running: $OPERATOR_POD"
else
    echo "  ⚠️  AI Operator pod not found - check deployment"
fi
echo ""

# Step 4: Start observability pipeline (in background)
echo "📊 Step 4: Starting observability pipeline..."
if pgrep -f "observability/pipeline.py" > /dev/null; then
    echo "  ✅ Observability pipeline already running"
else
    echo "  🚀 Starting pipeline in background..."
    python3 observability/pipeline.py > /tmp/observability.log 2>&1 &
    OBS_PID=$!
    echo "  ✅ Pipeline started (PID: $OBS_PID)"
fi
echo ""

# Step 5: Generate baseline traffic
echo "📡 Step 5: Generating baseline traffic..."
echo "  🚀 Starting traffic generation (60 seconds, 2 req/s per namespace)..."
./scripts/load-traffic-all.sh 60 2 > /tmp/traffic.log 2>&1 &
TRAFFIC_PID=$!
echo "  ✅ Traffic generation started (PID: $TRAFFIC_PID)"
echo ""

# Step 6: Wait for baseline
echo "⏳ Step 6: Establishing baseline (30 seconds)..."
sleep 30
echo "  ✅ Baseline established"
echo ""

# Step 7: Trigger chaos events
echo "💥 Step 7: Triggering chaos events..."
echo ""

CHAOS_EVENTS=(
    "finance:cpu"
    "semiconductor:memory"
    "aicloud:pod-kill"
    "gpucloud:errors"
    "socialmedia:cpu"
)

for event in "${CHAOS_EVENTS[@]}"; do
    IFS=':' read -r namespace experiment <<< "$event"
    echo "  💥 $namespace: $experiment"
    ./scripts/chaos-advanced.sh "$namespace" "$experiment" > /dev/null 2>&1 || true
    sleep 5
done

echo ""
echo "  ✅ Chaos events triggered"
echo ""

# Step 8: Wait for detection
echo "⏳ Step 8: Waiting for AI detection (60 seconds)..."
sleep 60
echo "  ✅ Detection window complete"
echo ""

# Step 9: Show results
echo "📊 Step 9: Demo Results"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Show operator logs
if [ -n "$OPERATOR_POD" ]; then
    echo -e "${BLUE}🤖 AI Operator Logs (last 20 lines):${NC}"
    echo ""
    kubectl logs "$OPERATOR_POD" --tail=20 2>/dev/null | grep -E "(Incident|Anomaly|RCA|Remediation)" || echo "  (No incidents detected yet - check operator logs)"
    echo ""
fi

# Show database incidents
if psql -h localhost -p 5433 -U postgres -d devops_brain -c "SELECT 1" &> /dev/null; then
    echo -e "${GREEN}📋 Recent Incidents (from database):${NC}"
    echo ""
    psql -h localhost -p 5433 -U postgres -d devops_brain -c "
        SELECT 
            id, 
            namespace, 
            severity, 
            anomaly_type, 
            detected_at,
            status
        FROM incidents 
        ORDER BY detected_at DESC 
        LIMIT 10;
    " 2>/dev/null || echo "  (No incidents in database yet)"
    echo ""
fi

# Show pod status
echo -e "${YELLOW}☸️  Pod Status (affected namespaces):${NC}"
echo ""
for ns in finance semiconductor aicloud gpucloud socialmedia; do
    READY=$(kubectl get deployment ${ns}-sim -n "$ns" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
    DESIRED=$(kubectl get deployment ${ns}-sim -n "$ns" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
    if [ "$READY" -lt "$DESIRED" ]; then
        echo "  ⚠️  $ns: $READY/$DESIRED pods (issues detected)"
    else
        echo "  ✅ $ns: $READY/$DESIRED pods"
    fi
done
echo ""

# Show dashboard URLs
echo -e "${BLUE}📊 Dashboard URLs:${NC}"
echo ""
echo "  Grafana: http://localhost:3000 (if running)"
echo "  Minikube Dashboard: minikube dashboard"
echo ""

# Show next steps
echo -e "${GREEN}🎯 Next Steps:${NC}"
echo ""
echo "  1. View operator logs:"
echo "     kubectl logs -l app=ai-operator -f"
echo ""
echo "  2. Query incidents:"
echo "     psql -h localhost -p 5433 -U postgres -d devops_brain -c \"SELECT * FROM incidents;\""
echo ""
echo "  3. View recent incidents:"
echo "     python3 ai-operator/tools/print_recent_incidents.py"
echo ""
echo "  4. Check observability pipeline:"
echo "     tail -f /tmp/observability.log"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}✅ Demo scenario complete!${NC}"
echo ""

