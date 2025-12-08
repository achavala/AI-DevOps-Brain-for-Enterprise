#!/bin/bash
# Smoke test for local environment - verifies all services are healthy

set -e

echo "🧪 Running smoke tests for local environment..."
echo ""

ERRORS=0
WARNINGS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

test_pass() {
    echo -e "${GREEN}✅${NC} $1"
}

test_fail() {
    echo -e "${RED}❌${NC} $1"
    ERRORS=$((ERRORS + 1))
}

test_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
    WARNINGS=$((WARNINGS + 1))
}

# Test 1: Docker is running
echo "1️⃣  Testing Docker..."
if docker info &> /dev/null; then
    test_pass "Docker is running"
else
    test_fail "Docker is not running"
    echo "   Start Docker Desktop and try again"
    exit 1
fi
echo ""

# Test 2: Kubernetes cluster is accessible
echo "2️⃣  Testing Kubernetes cluster..."
if kubectl cluster-info &> /dev/null; then
    CLUSTER=$(kubectl config current-context)
    test_pass "Kubernetes cluster accessible: $CLUSTER"
    
    # Check if nodes are ready
    READY_NODES=$(kubectl get nodes --no-headers 2>/dev/null | grep -c Ready || echo "0")
    if [ "$READY_NODES" -gt 0 ]; then
        test_pass "Cluster has $READY_NODES ready node(s)"
    else
        test_fail "No ready nodes in cluster"
    fi
else
    test_fail "Cannot connect to Kubernetes cluster"
    echo "   Run: minikube start (or kind create cluster)"
    exit 1
fi
echo ""

# Test 3: PostgreSQL connection
echo "3️⃣  Testing PostgreSQL..."
if docker ps | grep -q "postgres-finance"; then
    if docker exec postgres-finance pg_isready -U postgres &> /dev/null; then
        # Test actual connection
        if docker exec postgres-finance psql -U postgres -d finance -c "SELECT 1;" &> /dev/null; then
            test_pass "PostgreSQL is healthy and accessible"
        else
            test_warn "PostgreSQL is running but connection test failed"
        fi
    else
        test_fail "PostgreSQL container exists but not ready"
    fi
else
    test_fail "PostgreSQL container not running"
    echo "   Run: ./scripts/setup-local-services.sh"
fi
echo ""

# Test 4: Redis connection
echo "4️⃣  Testing Redis..."
if docker ps | grep -q "redis-finance"; then
    if docker exec redis-finance redis-cli ping &> /dev/null; then
        PONG=$(docker exec redis-finance redis-cli ping 2>/dev/null)
        if [ "$PONG" = "PONG" ]; then
            test_pass "Redis is healthy and responding"
        else
            test_warn "Redis responded but unexpected value: $PONG"
        fi
    else
        test_fail "Redis container exists but not responding"
    fi
else
    test_fail "Redis container not running"
    echo "   Run: ./scripts/setup-local-services.sh"
fi
echo ""

# Test 5: Kafka connection
echo "5️⃣  Testing Kafka..."
if docker ps | grep -q "kafka-finance"; then
    # Wait a bit for Kafka to be ready
    sleep 2
    if docker exec kafka-finance kafka-broker-api-versions --bootstrap-server localhost:9092 &> /dev/null; then
        test_pass "Kafka is healthy and accessible"
    else
        test_warn "Kafka container exists but may still be starting"
        echo "   Kafka can take 30-60 seconds to be fully ready"
    fi
else
    test_fail "Kafka container not running"
    echo "   Run: ./scripts/setup-local-services.sh"
fi
echo ""

# Test 6: MinIO connection
echo "6️⃣  Testing MinIO..."
if docker ps | grep -q "minio"; then
    if curl -s http://localhost:9000/minio/health/live &> /dev/null; then
        test_pass "MinIO is healthy and accessible"
        echo "   Console: http://localhost:9001"
    else
        test_warn "MinIO container exists but health check failed"
    fi
else
    test_fail "MinIO container not running"
    echo "   Run: ./scripts/setup-local-services.sh"
fi
echo ""

# Test 7: Kubernetes services
echo "7️⃣  Testing Kubernetes services..."
NAMESPACES=("argocd" "monitoring" "logging" "keda")
for ns in "${NAMESPACES[@]}"; do
    if kubectl get namespace "$ns" &> /dev/null; then
        READY_PODS=$(kubectl get pods -n "$ns" --no-headers 2>/dev/null | grep -c "Running\|Completed" || echo "0")
        TOTAL_PODS=$(kubectl get pods -n "$ns" --no-headers 2>/dev/null | wc -l | tr -d ' ')
        
        if [ "$TOTAL_PODS" -gt 0 ]; then
            if [ "$READY_PODS" -eq "$TOTAL_PODS" ]; then
                test_pass "Namespace $ns: All $READY_PODS pod(s) ready"
            else
                test_warn "Namespace $ns: $READY_PODS/$TOTAL_PODS pods ready"
            fi
        else
            test_warn "Namespace $ns: No pods found (may not be deployed yet)"
        fi
    else
        test_warn "Namespace $ns: Does not exist (may not be deployed yet)"
    fi
done
echo ""

# Test 8: Local data directories
echo "8️⃣  Testing local data directories..."
DIRS=("local-data/logs" "local-data/metrics" "local-data/events" "ai-models/models")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        test_pass "Directory exists: $dir"
    else
        test_warn "Directory missing: $dir (will be created on first use)"
        mkdir -p "$dir"
    fi
done
echo ""

# Test 9: Python environment
echo "9️⃣  Testing Python environment..."
if [ -d "ai-models/venv" ]; then
    if [ -f "ai-models/venv/bin/activate" ]; then
        source ai-models/venv/bin/activate
        if python -c "import pandas, numpy, sklearn" &> /dev/null; then
            test_pass "Python environment is set up correctly"
        else
            test_fail "Python packages missing"
        fi
        deactivate
    else
        test_fail "Python virtual environment incomplete"
    fi
else
    test_fail "Python virtual environment not found"
    echo "   Run: cd ai-models && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi
echo ""

# Test 10: Test Kafka produce/consume
echo "🔟 Testing Kafka produce/consume..."
if docker ps | grep -q "kafka-finance"; then
    sleep 3  # Give Kafka more time
    # Create test topic
    docker exec kafka-finance kafka-topics --create \
        --bootstrap-server localhost:9092 \
        --topic smoke-test \
        --partitions 1 \
        --replication-factor 1 \
        --if-not-exists &> /dev/null || true
    
    # Produce a test message
    echo "test-message-$(date +%s)" | docker exec -i kafka-finance kafka-console-producer \
        --bootstrap-server localhost:9092 \
        --topic smoke-test &> /dev/null
    
    sleep 2
    
    # Consume the message
    CONSUMED=$(timeout 5 docker exec kafka-finance kafka-console-consumer \
        --bootstrap-server localhost:9092 \
        --topic smoke-test \
        --from-beginning \
        --max-messages 1 \
        --timeout-ms 5000 2>/dev/null || echo "")
    
    if [ -n "$CONSUMED" ]; then
        test_pass "Kafka produce/consume working"
    else
        test_warn "Kafka produce/consume test inconclusive (may need more time)"
    fi
    
    # Clean up
    docker exec kafka-finance kafka-topics --delete \
        --bootstrap-server localhost:9092 \
        --topic smoke-test &> /dev/null || true
else
    test_warn "Kafka not running, skipping produce/consume test"
fi
echo ""

# Test 11: MinIO bucket access
echo "1️⃣1️⃣  Testing MinIO bucket access..."
if docker ps | grep -q "minio"; then
    # Check if we can list buckets (using curl or mc)
    if command -v mc &> /dev/null; then
        # Use MinIO client if available
        mc alias set local http://localhost:9000 minioadmin minioadmin &> /dev/null || true
        if mc ls local &> /dev/null; then
            test_pass "MinIO bucket access working"
        else
            test_warn "MinIO client configured but bucket access failed"
        fi
    else
        # Fallback: just check if MinIO is responding
        if curl -s http://localhost:9000 &> /dev/null; then
            test_pass "MinIO is responding (install 'mc' for full bucket test)"
        else
            test_warn "MinIO may not be fully ready"
        fi
    fi
else
    test_warn "MinIO not running, skipping bucket test"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Smoke Test Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Your local environment is healthy and ready to use."
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  Tests passed with $WARNINGS warning(s)${NC}"
    echo ""
    echo "Environment is functional but some services may need attention."
    exit 0
else
    echo -e "${RED}❌ Tests failed: $ERRORS error(s), $WARNINGS warning(s)${NC}"
    echo ""
    echo "Please fix the errors before proceeding."
    echo ""
    echo "Common fixes:"
    echo "  - Start services: ./scripts/setup-local-services.sh"
    echo "  - Deploy platform: ./scripts/deploy-platform-local.sh"
    echo "  - Check logs: kubectl logs <pod-name> -n <namespace>"
    exit 1
fi

