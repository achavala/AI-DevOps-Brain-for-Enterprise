#!/bin/bash
# Trading system heartbeat - shows status of all components

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "💓 Trading System Heartbeat"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check Trading Engine
echo -n "💰 Trading Engine:     "
if pgrep -f "trading.*engine\|your_trading_app" > /dev/null; then
    echo -e "${GREEN}RUNNING${NC}"
else
    echo -e "${YELLOW}IDLE${NC}"
fi

# Check Replay Engine
echo -n "🔄 Replay Engine:      "
if pgrep -f "replay.*engine\|weekend.*test" > /dev/null; then
    echo -e "${GREEN}RUNNING${NC}"
else
    echo -e "${YELLOW}IDLE${NC}"
fi

echo ""

# Check PostgreSQL
echo -n "🐘 PostgreSQL:         "
if ! docker info &> /dev/null; then
    echo -e "${RED}DOCKER NOT RUNNING${NC}"
elif docker ps | grep -q "postgres-finance"; then
    if docker exec postgres-finance pg_isready -U postgres &> /dev/null; then
        # Test connection
        if docker exec postgres-finance psql -U postgres -d finance -c "SELECT 1;" &> /dev/null; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${YELLOW}CONNECTING...${NC}"
        fi
    else
        echo -e "${RED}NOT READY${NC}"
    fi
else
    echo -e "${RED}NOT RUNNING${NC}"
fi

# Check Redis
echo -n "🔴 Redis:              "
if ! docker info &> /dev/null; then
    echo -e "${RED}DOCKER NOT RUNNING${NC}"
elif docker ps | grep -q "redis-finance"; then
    if docker exec redis-finance redis-cli ping &> /dev/null; then
        PONG=$(docker exec redis-finance redis-cli ping 2>/dev/null)
        if [ "$PONG" = "PONG" ]; then
            echo -e "${GREEN}OK${NC}"
        else
            echo -e "${YELLOW}CONNECTING...${NC}"
        fi
    else
        echo -e "${RED}NOT READY${NC}"
    fi
else
    echo -e "${RED}NOT RUNNING${NC}"
fi

# Check Kafka
echo -n "📨 Kafka:              "
if ! docker info &> /dev/null; then
    echo -e "${RED}DOCKER NOT RUNNING${NC}"
elif docker ps | grep -q "kafka-finance"; then
    if docker exec kafka-finance kafka-broker-api-versions --bootstrap-server localhost:9092 &> /dev/null; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}STARTING...${NC}"
    fi
else
    echo -e "${RED}NOT RUNNING${NC}"
fi

# Check MinIO
echo -n "📦 MinIO:              "
if ! docker info &> /dev/null; then
    echo -e "${RED}DOCKER NOT RUNNING${NC}"
elif docker ps | grep -q "minio"; then
    if curl -s http://localhost:9000/minio/health/live &> /dev/null; then
        echo -e "${GREEN}OK${NC}"
    else
        echo -e "${YELLOW}STARTING...${NC}"
    fi
else
    echo -e "${RED}NOT RUNNING${NC}"
fi

echo ""

# Check Kubernetes
echo -n "☸️  Kubernetes:         "
if kubectl cluster-info &> /dev/null; then
    READY_NODES=$(kubectl get nodes --no-headers 2>/dev/null | grep -c Ready || echo "0")
    if [ "$READY_NODES" -gt 0 ]; then
        echo -e "${GREEN}OK (${READY_NODES} node(s))${NC}"
    else
        echo -e "${YELLOW}NO READY NODES${NC}"
    fi
else
    echo -e "${RED}NOT CONNECTED${NC}"
fi

# Check AI Models
echo -n "🧠 AI Models:          "
if [ -d "ai-models/models" ] && [ "$(ls -A ai-models/models 2>/dev/null)" ]; then
    MODEL_COUNT=$(find ai-models/models -name "*.pkl" -o -name "*.h5" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$MODEL_COUNT" -gt 0 ]; then
        echo -e "${GREEN}OK (${MODEL_COUNT} model(s))${NC}"
    else
        echo -e "${YELLOW}NO MODELS${NC}"
    fi
else
    echo -e "${YELLOW}NOT TRAINED${NC}"
fi

echo ""

# Check Data Directories
echo -n "📁 Local Data:         "
if [ -d "local-data" ]; then
    LOG_COUNT=$(find local-data/logs -type f 2>/dev/null | wc -l | tr -d ' ')
    METRIC_COUNT=$(find local-data/metrics -type f 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}OK (${LOG_COUNT} logs, ${METRIC_COUNT} metrics)${NC}"
else
    echo -e "${YELLOW}EMPTY${NC}"
fi

echo ""

# Quick stats
echo "📊 Quick Stats:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Database stats (if accessible)
if docker info &> /dev/null && docker ps | grep -q "postgres-finance"; then
    if docker exec postgres-finance pg_isready -U postgres &> /dev/null; then
        # Count tables
        TABLE_COUNT=$(docker exec postgres-finance psql -U postgres -d finance -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ' || echo "0")
        if [ "$TABLE_COUNT" -gt 0 ]; then
            echo "  📊 Database tables: $TABLE_COUNT"
        fi
    fi
fi

# Kafka topics (if accessible)
if docker info &> /dev/null && docker ps | grep -q "kafka-finance"; then
    if docker exec kafka-finance kafka-broker-api-versions --bootstrap-server localhost:9092 &> /dev/null; then
        TOPIC_COUNT=$(docker exec kafka-finance kafka-topics --list --bootstrap-server localhost:9092 2>/dev/null | wc -l | tr -d ' ' || echo "0")
        if [ "$TOPIC_COUNT" -gt 0 ]; then
            echo "  📨 Kafka topics: $TOPIC_COUNT"
        fi
    fi
fi

# Kubernetes pods
if kubectl cluster-info &> /dev/null; then
    RUNNING_PODS=$(kubectl get pods --all-namespaces --no-headers 2>/dev/null | grep -c "Running\|Completed" || echo "0")
    TOTAL_PODS=$(kubectl get pods --all-namespaces --no-headers 2>/dev/null | wc -l | tr -d ' ')
    if [ "$TOTAL_PODS" -gt 0 ]; then
        echo "  ☸️  Kubernetes pods: $RUNNING_PODS/$TOTAL_PODS running"
    fi
fi

echo ""

# System resources
echo "💻 System Resources:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Docker containers
if docker info &> /dev/null; then
    DOCKER_COUNT=$(docker ps --format '{{.Names}}' 2>/dev/null | wc -l | tr -d ' ')
    echo "  🐳 Docker containers: $DOCKER_COUNT running"
    
    # Memory usage (if available)
    if [ "$DOCKER_COUNT" -gt 0 ]; then
        MEM_USAGE=$(docker stats --no-stream --format "{{.MemUsage}}" 2>/dev/null | head -1 || echo "N/A")
        if [ "$MEM_USAGE" != "N/A" ]; then
            echo "  💾 Memory usage: $MEM_USAGE"
        fi
    fi
else
    echo "  🐳 Docker: NOT RUNNING"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Status summary
ALL_OK=true
DOCKER_RUNNING=false

# Check Docker first
if docker info &> /dev/null; then
    DOCKER_RUNNING=true
    if ! docker ps | grep -q "postgres-finance"; then ALL_OK=false; fi
    if ! docker ps | grep -q "redis-finance"; then ALL_OK=false; fi
    if ! docker ps | grep -q "kafka-finance"; then ALL_OK=false; fi
else
    ALL_OK=false
fi

if ! kubectl cluster-info &> /dev/null; then ALL_OK=false; fi

if [ "$ALL_OK" = true ]; then
    echo -e "${GREEN}✅ System Status: HEALTHY${NC}"
elif [ "$DOCKER_RUNNING" = false ]; then
    echo -e "${RED}❌ System Status: DOCKER NOT RUNNING${NC}"
    echo ""
    echo "Please start Docker Desktop first:"
    echo "  1. Open Docker Desktop application"
    echo "  2. Wait for it to start (whale icon in menu bar)"
    echo "  3. Then run: ./scripts/start-local.sh"
else
    echo -e "${YELLOW}⚠️  System Status: SOME SERVICES OFFLINE${NC}"
    echo ""
    echo "To start everything: ./scripts/start-local.sh"
fi

echo ""

