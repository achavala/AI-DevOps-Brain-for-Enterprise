#!/bin/bash
# Start local environment - one command to bring everything up

set -e

echo "🚀 Starting local AI DevOps Brain environment..."
echo ""

# Check Docker
if ! docker info &> /dev/null; then
    echo "❌ Docker is not running."
    echo ""
    echo "Please start Docker Desktop:"
    echo "  1. Open Docker Desktop application"
    echo "  2. Wait for it to fully start (whale icon in menu bar should be steady)"
    echo "  3. Then run this script again: ./scripts/start-local.sh"
    echo ""
    echo "To check Docker status: docker info"
    exit 1
fi

echo "✅ Docker is running"

# Check if Minikube is installed
if ! command -v minikube &> /dev/null; then
    echo "📦 Minikube not found. Installing..."
    echo ""
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v brew &> /dev/null; then
            brew install minikube
        else
            echo "❌ Homebrew not found. Please install Minikube manually:"
            echo "   brew install minikube"
            echo "   Or download from: https://minikube.sigs.k8s.io/docs/start/"
            exit 1
        fi
    else
        echo "❌ Please install Minikube manually:"
        echo "   See: https://minikube.sigs.k8s.io/docs/start/"
        exit 1
    fi
    
    echo "✅ Minikube installed"
    echo ""
fi

# Check if Minikube is running
if ! kubectl cluster-info &> /dev/null; then
    echo "📦 Starting Minikube..."
    
    # Try 6GB first (works for most Docker Desktop setups)
    # If that fails due to memory, fall back to 4GB
    if ! minikube start --driver=docker --cpus=3 --memory=6g 2>&1; then
        echo "   Retrying with less memory..."
        minikube start --driver=docker --cpus=2 --memory=4g
    fi
    
    echo "✅ Minikube started"
else
    echo "✅ Minikube already running"
fi
echo ""

# Start local services
echo "🐳 Starting local services..."
./scripts/setup-local-services.sh
echo ""

# Wait a bit for services
echo "⏳ Waiting for services to be ready..."
sleep 10
echo ""

# Deploy platform
echo "☸️  Deploying platform components..."
./scripts/deploy-platform-local.sh
echo ""

# Run smoke tests
echo "🧪 Running smoke tests..."
./scripts/smoke-test-local.sh
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Local environment is ready!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Quick access:"
echo "  📊 Minikube dashboard: minikube dashboard"
echo "  📈 Grafana: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
echo "  🔄 ArgoCD: kubectl port-forward -n argocd svc/argocd-server 8080:443"
echo "  📦 MinIO: http://localhost:9001 (minioadmin/minioadmin)"
echo ""
echo "Stop everything: ./scripts/stop-local.sh"
echo ""

