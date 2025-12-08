#!/bin/bash
# Validate setup after completing QUICKSTART steps
# This script checks that everything is ready before proceeding

set -e

echo "🔍 Validating AI DevOps Brain Setup..."
echo ""

ERRORS=0
WARNINGS=0

# Check Python
echo "📦 Checking Python environment..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "   ✅ Python: $PYTHON_VERSION"
    
    # Check virtual environment
    if [ -d "ai-models/venv" ]; then
        echo "   ✅ Virtual environment exists"
        
        # Check if packages are installed
        if [ -f "ai-models/venv/bin/activate" ]; then
            source ai-models/venv/bin/activate
            if python -c "import pandas, numpy, sklearn, tensorflow" 2>/dev/null; then
                echo "   ✅ Key packages installed"
            else
                echo "   ❌ Key packages missing"
                ERRORS=$((ERRORS + 1))
            fi
            deactivate
        fi
    else
        echo "   ⚠️  Virtual environment not found"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "   ❌ Python 3 not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check AWS CLI
echo "☁️  Checking AWS CLI..."
if command -v aws &> /dev/null; then
    AWS_VERSION=$(aws --version)
    echo "   ✅ AWS CLI: $AWS_VERSION"
    
    # Check if configured
    if aws sts get-caller-identity &> /dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")
        echo "   ✅ AWS credentials configured (Account: $ACCOUNT_ID)"
    else
        echo "   ⚠️  AWS credentials not configured (run: aws configure)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "   ⚠️  AWS CLI not installed (run: ./scripts/install-prerequisites.sh)"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# Check Terraform
echo "🏗️  Checking Terraform..."
if command -v terraform &> /dev/null; then
    TERRAFORM_VERSION=$(terraform version -json | grep -o '"terraform_version":"[^"]*' | cut -d'"' -f4 || terraform version | head -1)
    echo "   ✅ Terraform: $TERRAFORM_VERSION"
    
    # Check if infrastructure is initialized
    if [ -d "infrastructure/.terraform" ]; then
        echo "   ✅ Infrastructure initialized"
    else
        echo "   ⚠️  Infrastructure not initialized (run: cd infrastructure && terraform init)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "   ⚠️  Terraform not installed (run: ./scripts/install-prerequisites.sh)"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# Check Helm
echo "⚓ Checking Helm..."
if command -v helm &> /dev/null; then
    HELM_VERSION=$(helm version --short)
    echo "   ✅ Helm: $HELM_VERSION"
else
    echo "   ⚠️  Helm not installed (run: ./scripts/install-prerequisites.sh)"
    WARNINGS=$((WARNINGS + 1))
fi

echo ""

# Check kubectl
echo "☸️  Checking kubectl..."
if command -v kubectl &> /dev/null; then
    KUBECTL_VERSION=$(kubectl version --client --short 2>/dev/null || echo "installed")
    echo "   ✅ kubectl: $KUBECTL_VERSION"
    
    # Check if connected to cluster
    if kubectl cluster-info &> /dev/null 2>&1; then
        echo "   ✅ Connected to Kubernetes cluster"
    else
        echo "   ⚠️  Not connected to cluster (this is OK for local testing)"
        WARNINGS=$((WARNINGS + 1))
    fi
else
    echo "   ❌ kubectl not found"
    ERRORS=$((ERRORS + 1))
fi

echo ""

# Check scripts
echo "📜 Checking helper scripts..."
SCRIPTS=("scripts/install-prerequisites.sh" "scripts/setup-aws.sh" "scripts/deploy-platform.sh" "scripts/setup-data-pipeline.sh")
for script in "${SCRIPTS[@]}"; do
    if [ -f "$script" ] && [ -x "$script" ]; then
        echo "   ✅ $(basename $script)"
    elif [ -f "$script" ]; then
        echo "   ⚠️  $(basename $script) exists but not executable"
        WARNINGS=$((WARNINGS + 1))
    else
        echo "   ❌ $(basename $script) missing"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# Check configuration files
echo "📋 Checking configuration files..."
CONFIGS=("infrastructure/main.tf" "infrastructure/variables.tf" "infrastructure/terraform.tfvars.example")
for config in "${CONFIGS[@]}"; do
    if [ -f "$config" ]; then
        echo "   ✅ $(basename $config)"
    else
        echo "   ❌ $(basename $config) missing"
        ERRORS=$((ERRORS + 1))
    fi
done

echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 Validation Summary"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ All checks passed! Ready to proceed."
    echo ""
    echo "Next steps:"
    echo "1. Run: python ai-models/anomaly-detection/train_anomaly_detector.py --simulate"
    echo "2. Review: QUICKSTART_VALIDATED.md"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Setup complete with $WARNINGS warning(s)"
    echo ""
    echo "Warnings are OK for local testing. Fix them before AWS deployment."
    echo ""
    echo "Next steps:"
    echo "1. Address warnings (optional for local testing)"
    echo "2. Run: python ai-models/anomaly-detection/train_anomaly_detector.py --simulate"
    exit 0
else
    echo "❌ Setup incomplete: $ERRORS error(s), $WARNINGS warning(s)"
    echo ""
    echo "Please fix errors before proceeding."
    echo ""
    echo "Common fixes:"
    echo "- Install missing tools: ./scripts/install-prerequisites.sh"
    echo "- Setup Python: cd ai-models && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

