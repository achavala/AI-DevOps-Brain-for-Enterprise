#!/bin/bash
# Attempt to start Docker Desktop on macOS

echo "🐳 Attempting to start Docker Desktop..."
echo ""

# Check if Docker is already running
if docker info &> /dev/null; then
    echo "✅ Docker is already running!"
    docker --version
    exit 0
fi

# Check OS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script is for macOS only"
    echo "   Please start Docker Desktop manually"
    exit 1
fi

# Try to start Docker Desktop
echo "🚀 Starting Docker Desktop..."
echo ""

# Method 1: Try to open Docker Desktop app
if [ -d "/Applications/Docker.app" ]; then
    echo "Found Docker Desktop in Applications"
    open -a Docker
    echo "✅ Docker Desktop launch command sent"
elif [ -d "/Applications/Docker Desktop.app" ]; then
    echo "Found Docker Desktop in Applications"
    open -a "Docker Desktop"
    echo "✅ Docker Desktop launch command sent"
else
    echo "⚠️  Docker Desktop not found in Applications"
    echo ""
    echo "Please install Docker Desktop:"
    echo "  1. Download from: https://www.docker.com/products/docker-desktop"
    echo "  2. Install the .dmg file"
    echo "  3. Move Docker to Applications"
    echo "  4. Run this script again"
    exit 1
fi

echo ""
echo "⏳ Waiting for Docker to start..."
echo "   (This can take 30-60 seconds)"
echo ""

# Wait for Docker to be ready (max 2 minutes)
TIMEOUT=120
ELAPSED=0
INTERVAL=5

while [ $ELAPSED -lt $TIMEOUT ]; do
    if docker info &> /dev/null; then
        echo ""
        echo "✅ Docker is now running!"
        echo ""
        docker --version
        echo ""
        echo "You can now run: ./scripts/start-local.sh"
        exit 0
    fi
    
    echo -n "."
    sleep $INTERVAL
    ELAPSED=$((ELAPSED + INTERVAL))
done

echo ""
echo ""
echo "⚠️  Docker Desktop is starting but not ready yet"
echo ""
echo "Please wait a bit longer and check:"
echo "  1. Look for Docker whale icon in menu bar (top right)"
echo "  2. Wait for icon to be steady (not animated)"
echo "  3. Then run: ./scripts/check-docker.sh"
echo ""
echo "Or check Docker Desktop window for any errors"
echo ""

