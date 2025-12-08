#!/bin/bash
# Install Minikube for local Kubernetes

set -e

echo "📦 Installing Minikube..."
echo ""

# Check OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo "Detected macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo "Detected Linux"
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

# Check if already installed
if command -v minikube &> /dev/null; then
    echo "✅ Minikube already installed: $(minikube version --short 2>/dev/null || minikube version | head -1)"
    exit 0
fi

# Install based on OS
if [[ "$OS" == "macos" ]]; then
    # Check for Homebrew
    if ! command -v brew &> /dev/null; then
        echo "❌ Homebrew not found"
        echo ""
        echo "Installing Homebrew first..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    echo "Installing Minikube via Homebrew..."
    brew install minikube
    
elif [[ "$OS" == "linux" ]]; then
    echo "Installing Minikube for Linux..."
    
    # Download Minikube binary
    curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
    sudo install minikube-linux-amd64 /usr/local/bin/minikube
    rm minikube-linux-amd64
    
    # Make executable
    sudo chmod +x /usr/local/bin/minikube
fi

# Verify installation
if command -v minikube &> /dev/null; then
    echo ""
    echo "✅ Minikube installed successfully!"
    echo ""
    minikube version
    echo ""
    echo "Next steps:"
    echo "  1. Make sure Docker is running: ./scripts/check-docker.sh"
    echo "  2. Start Minikube: minikube start --driver=docker"
    echo "  3. Or start everything: ./scripts/start-local.sh"
else
    echo "❌ Minikube installation failed"
    exit 1
fi

