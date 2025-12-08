#!/bin/bash
# Setup local services (PostgreSQL, Redis, Kafka, MinIO) using Docker

set -e

echo "🐳 Setting up local services with Docker..."
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

echo "✅ Docker is running"
echo ""

# Check if docker-compose is available (preferred method)
if command -v docker-compose &> /dev/null || docker compose version &> /dev/null; then
    echo "📦 Using docker-compose for service orchestration..."
    echo ""
    
    # Create local data directories
    echo "📁 Creating local data directories..."
    mkdir -p local-data/{logs,metrics,events}
    mkdir -p local-data/minio
    echo "✅ Directories created"
    echo ""
    
    # Use docker-compose
    if docker compose version &> /dev/null; then
        docker compose -f docker-compose.local.yml up -d
    else
        docker-compose -f docker-compose.local.yml up -d
    fi
    
    echo ""
    echo "⏳ Waiting for services to be ready..."
    sleep 15
    
    echo ""
    echo "✅ Services started with docker-compose"
    echo ""
    echo "Services:"
    echo "  📊 PostgreSQL: localhost:5433"
    echo "  🔴 Redis: localhost:6379"
    echo "  📨 Kafka: localhost:9092"
    echo "  📦 MinIO: http://localhost:9000 (Console: http://localhost:9001)"
    echo ""
    exit 0
fi

# Fallback to individual docker run commands
echo "📦 Using individual Docker containers..."
echo ""

# Create local data directories
echo "📁 Creating local data directories..."
mkdir -p local-data/{logs,metrics,events}
mkdir -p local-data/minio
echo "✅ Directories created"
echo ""

# Start PostgreSQL
echo "🐘 Starting PostgreSQL..."
# Clean up any stopped containers with this name
docker rm -f postgres-finance 2>/dev/null || true

if ! docker ps | grep -q "postgres-finance"; then
    # Check if port 5432 is available
    if lsof -i :5432 &> /dev/null; then
        echo "⚠️  Port 5432 is already in use"
        echo "   Using alternative port 5433 instead"
        POSTGRES_PORT=5433
    else
        POSTGRES_PORT=5432
    fi
    
    docker run -d \
        --name postgres-finance \
        -e POSTGRES_PASSWORD=finance123 \
        -e POSTGRES_DB=finance \
        -p ${POSTGRES_PORT}:5432 \
        -v postgres-finance-data:/var/lib/postgresql/data \
        postgres:15-alpine
    
    if [ "$POSTGRES_PORT" != "5432" ]; then
        echo "✅ PostgreSQL started on port ${POSTGRES_PORT}"
        echo "   ⚠️  Note: Update config/local.yaml to use port ${POSTGRES_PORT}"
    else
        echo "✅ PostgreSQL started on port 5432"
    fi
else
    echo "✅ PostgreSQL already running"
fi
echo ""

# Start Redis
echo "🔴 Starting Redis..."
# Clean up any stopped containers
docker rm -f redis-finance 2>/dev/null || true

if ! docker ps | grep -q "redis-finance"; then
    # Check if port 6379 is available
    if lsof -i :6379 &> /dev/null; then
        echo "⚠️  Port 6379 is already in use, using alternative port 6380"
        REDIS_PORT=6380
    else
        REDIS_PORT=6379
    fi
    
    docker run -d \
        --name redis-finance \
        -p ${REDIS_PORT}:6379 \
        -v redis-finance-data:/data \
        redis:7-alpine redis-server --appendonly yes
    
    if [ "$REDIS_PORT" != "6379" ]; then
        echo "✅ Redis started on port ${REDIS_PORT}"
        echo "   ⚠️  Note: Update config/local.yaml to use port ${REDIS_PORT}"
    else
        echo "✅ Redis started on port 6379"
    fi
else
    echo "✅ Redis already running"
fi
echo ""

# Start Kafka (using Zookeeper + Kafka)
echo "📨 Starting Kafka..."
# Clean up any stopped containers
docker rm -f kafka-finance zookeeper-finance 2>/dev/null || true

if ! docker ps | grep -q "kafka-finance"; then
    # Check if port 9092 is available
    KAFKA_PORT=9092
    if lsof -i :9092 &> /dev/null; then
        echo "⚠️  Port 9092 is already in use, using alternative port 9093"
        KAFKA_PORT=9093
    fi
    
    # Start Zookeeper
    ZK_PORT=2181
    if lsof -i :2181 &> /dev/null; then
        ZK_PORT=2182
    fi
    
    echo "   Starting Zookeeper..."
    docker run -d \
        --name zookeeper-finance \
        -p ${ZK_PORT}:2181 \
        -e ZOOKEEPER_CLIENT_PORT=2181 \
        confluentinc/cp-zookeeper:7.4.0
    
    sleep 8
    
    # Start Kafka with proper environment variables
    echo "   Starting Kafka..."
    docker run -d \
        --name kafka-finance \
        -p ${KAFKA_PORT}:9092 \
        -e KAFKA_BROKER_ID=1 \
        -e KAFKA_ZOOKEEPER_CONNECT=zookeeper-finance:2181 \
        -e KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:${KAFKA_PORT} \
        -e KAFKA_LISTENER_SECURITY_PROTOCOL_MAP=PLAINTEXT:PLAINTEXT,PLAINTEXT_INTERNAL:PLAINTEXT \
        -e KAFKA_INTER_BROKER_LISTENER_NAME=PLAINTEXT_INTERNAL \
        -e KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR=1 \
        -e KAFKA_TRANSACTION_STATE_LOG_MIN_ISR=1 \
        -e KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR=1 \
        --link zookeeper-finance:zookeeper \
        confluentinc/cp-kafka:7.4.0
    
    echo "✅ Kafka started on port ${KAFKA_PORT}"
    if [ "$KAFKA_PORT" != "9092" ]; then
        echo "   ⚠️  Note: Update config/local.yaml to use port ${KAFKA_PORT}"
    fi
    echo "   Note: Wait 15-20 seconds for Kafka to be ready"
else
    echo "✅ Kafka already running"
fi
echo ""

# Start MinIO (S3-compatible)
echo "📦 Starting MinIO (S3-compatible)..."
# Clean up any stopped containers
docker rm -f minio 2>/dev/null || true

if ! docker ps | grep -q "^minio "; then
    # Check if ports are available
    MINIO_PORT=9000
    MINIO_CONSOLE_PORT=9001
    if lsof -i :9000 &> /dev/null || lsof -i :9001 &> /dev/null; then
        echo "⚠️  Ports 9000/9001 are already in use, using alternative ports 9010/9011"
        MINIO_PORT=9010
        MINIO_CONSOLE_PORT=9011
    fi
    
    docker run -d \
        --name minio \
        -p ${MINIO_PORT}:9000 \
        -p ${MINIO_CONSOLE_PORT}:9001 \
        -e MINIO_ROOT_USER=minioadmin \
        -e MINIO_ROOT_PASSWORD=minioadmin \
        -v "$(pwd)/local-data/minio:/data" \
        minio/minio server /data --console-address ":9001"
    echo "✅ MinIO started"
    echo "   Console: http://localhost:${MINIO_CONSOLE_PORT}"
    if [ "$MINIO_PORT" != "9000" ]; then
        echo "   ⚠️  Note: Update config/local.yaml to use ports ${MINIO_PORT}/${MINIO_CONSOLE_PORT}"
    fi
    echo "   Access Key: minioadmin"
    echo "   Secret Key: minioadmin"
else
    echo "✅ MinIO already running"
fi
echo ""

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Verify services
echo ""
echo "🔍 Verifying services..."
echo ""

# Check PostgreSQL
if docker exec postgres-finance pg_isready -U postgres &> /dev/null; then
    echo "✅ PostgreSQL is ready"
else
    echo "⚠️  PostgreSQL is starting..."
fi

# Check Redis
if docker exec redis-finance redis-cli ping &> /dev/null; then
    echo "✅ Redis is ready"
else
    echo "⚠️  Redis is starting..."
fi

# Check Kafka (wait a bit longer)
sleep 5
if docker exec kafka-finance kafka-broker-api-versions --bootstrap-server localhost:9092 &> /dev/null; then
    echo "✅ Kafka is ready"
else
    echo "⚠️  Kafka is starting (may take 30 seconds)..."
fi

# Check MinIO
if curl -s http://localhost:9000/minio/health/live &> /dev/null; then
    echo "✅ MinIO is ready"
else
    echo "⚠️  MinIO is starting..."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Local services setup complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Services running:"
echo "  📊 PostgreSQL: localhost:5432"
echo "     Database: finance"
echo "     Password: finance123"
echo ""
echo "  🔴 Redis: localhost:6379"
echo ""
echo "  📨 Kafka: localhost:9092"
echo ""
echo "  📦 MinIO: http://localhost:9000"
echo "     Console: http://localhost:9001"
echo "     Access: minioadmin / minioadmin"
echo ""
echo "Next steps:"
echo "  1. Start local Kubernetes: minikube start (or kind create cluster)"
echo "  2. Deploy platform: ./scripts/deploy-platform-local.sh"
echo ""

