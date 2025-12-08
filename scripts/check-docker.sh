#!/bin/bash
# Quick Docker status check

echo "🐳 Checking Docker status..."
echo ""

if docker info &> /dev/null; then
    echo "✅ Docker is running"
    echo ""
    
    # Show Docker version
    echo "Docker version:"
    docker --version
    echo ""
    
    # Show running containers
    echo "Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
    
    # Show Docker system info
    echo "Docker system info:"
    docker system df
    echo ""
    
    echo "✅ Docker is ready to use"
else
    echo "❌ Docker is NOT running"
    echo ""
    echo "To start Docker:"
    echo "  1. Open Docker Desktop application"
    echo "  2. Wait for it to start (whale icon in menu bar)"
    echo "  3. Verify with: docker info"
    echo ""
    echo "On macOS:"
    echo "  - Look for Docker Desktop in Applications"
    echo "  - Or search for 'Docker' in Spotlight"
    echo ""
    exit 1
fi

