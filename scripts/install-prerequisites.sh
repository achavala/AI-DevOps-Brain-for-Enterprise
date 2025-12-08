#!/bin/bash
# Install missing prerequisites for AI DevOps Brain

set -e

echo "🔧 Installing prerequisites for AI DevOps Brain..."

# Detect OS
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

# Check for Homebrew (macOS) or apt (Linux)
if [[ "$OS" == "macos" ]]; then
    if ! command -v brew &> /dev/null; then
        echo "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    PACKAGE_MANAGER="brew"
elif [[ "$OS" == "linux" ]]; then
    if ! command -v apt-get &> /dev/null; then
        echo "apt-get not found. Please install manually."
        exit 1
    fi
    PACKAGE_MANAGER="apt"
fi

# Install AWS CLI
if ! command -v aws &> /dev/null; then
    echo "📦 Installing AWS CLI..."
    if [[ "$OS" == "macos" ]]; then
        brew install awscli
    else
        curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
        unzip awscliv2.zip
        sudo ./aws/install
        rm -rf aws awscliv2.zip
    fi
    echo "✅ AWS CLI installed"
else
    echo "✅ AWS CLI already installed: $(aws --version)"
fi

# Install Terraform
if ! command -v terraform &> /dev/null; then
    echo "📦 Installing Terraform..."
    if [[ "$OS" == "macos" ]]; then
        brew tap hashicorp/tap
        brew install hashicorp/tap/terraform
    else
        wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
        echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
        sudo apt update && sudo apt install terraform
    fi
    echo "✅ Terraform installed"
else
    echo "✅ Terraform already installed: $(terraform version | head -1)"
fi

# Install Helm
if ! command -v helm &> /dev/null; then
    echo "📦 Installing Helm..."
    if [[ "$OS" == "macos" ]]; then
        brew install helm
    else
        curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    fi
    echo "✅ Helm installed"
else
    echo "✅ Helm already installed: $(helm version --short)"
fi

# Verify kubectl
if ! command -v kubectl &> /dev/null; then
    echo "⚠️  kubectl not found. Please install kubectl:"
    echo "   macOS: brew install kubectl"
    echo "   Linux: https://kubernetes.io/docs/tasks/tools/"
else
    echo "✅ kubectl already installed: $(kubectl version --client --short)"
fi

# Install Minikube
if ! command -v minikube &> /dev/null; then
    echo "📦 Installing Minikube..."
    if [[ "$OS" == "macos" ]]; then
        brew install minikube
    else
        echo "⚠️  Minikube installation for Linux requires manual setup"
        echo "   See: https://minikube.sigs.k8s.io/docs/start/"
    fi
    echo "✅ Minikube installed"
else
    echo "✅ Minikube already installed: $(minikube version --short 2>/dev/null || minikube version | head -1)"
fi

# Verify Python
if ! command -v python3 &> /dev/null; then
    echo "⚠️  Python 3 not found. Please install Python 3.9+"
else
    echo "✅ Python already installed: $(python3 --version)"
fi

echo ""
echo "🎉 Prerequisites check complete!"
echo ""
echo "Next steps:"
echo "1. Configure AWS credentials: aws configure"
echo "2. Follow QUICKSTART.md for deployment"

