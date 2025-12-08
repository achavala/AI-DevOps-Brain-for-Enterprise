#!/bin/bash
# Check which ports are in use and by what

echo "🔍 Checking port usage..."
echo ""

PORTS=(5432 6379 9092 9000 9001 2181)

for port in "${PORTS[@]}"; do
    echo -n "Port $port: "
    
    # Check Docker containers
    DOCKER_USAGE=$(docker ps --format "{{.Names}}: {{.Ports}}" 2>/dev/null | grep -o "0.0.0.0:$port" || echo "")
    
    # Check lsof
    LSOF_USAGE=$(lsof -i :$port 2>/dev/null | tail -n +2 | awk '{print $1, $2}' | head -1 || echo "")
    
    if [ -n "$DOCKER_USAGE" ]; then
        CONTAINER=$(docker ps --format "{{.Names}}\t{{.Ports}}" 2>/dev/null | grep ":$port" | awk '{print $1}' | head -1)
        echo -e "\033[0;33m⚠️  IN USE\033[0m by Docker container: $CONTAINER"
    elif [ -n "$LSOF_USAGE" ]; then
        echo -e "\033[0;33m⚠️  IN USE\033[0m by: $LSOF_USAGE"
    else
        echo -e "\033[0;32m✅ AVAILABLE\033[0m"
    fi
done

echo ""
echo "💡 If ports are in use, the setup script will use alternative ports automatically"

