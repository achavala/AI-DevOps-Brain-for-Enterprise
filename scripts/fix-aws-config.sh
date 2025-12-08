#!/bin/bash
# Helper script to fix AWS configuration issues

set -e

echo "🔧 AWS Configuration Helper"
echo ""

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found"
    echo ""
    echo "Installing AWS CLI..."
    ./scripts/install-prerequisites.sh
    exit 0
fi

echo "✅ AWS CLI installed: $(aws --version)"
echo ""

# Check if credentials exist
if [ -f ~/.aws/credentials ]; then
    echo "✅ AWS credentials file exists"
    echo ""
    echo "Current configuration:"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    cat ~/.aws/credentials | grep -v "^#" | head -5
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # Test credentials
    echo "Testing AWS credentials..."
    if aws sts get-caller-identity &> /dev/null; then
        ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null)
        echo "✅ AWS credentials are valid!"
        echo "   Account ID: $ACCOUNT_ID"
        echo ""
        echo "You can now proceed with:"
        echo "  ./scripts/setup-aws.sh"
    else
        echo "❌ AWS credentials are invalid or expired"
        echo ""
        echo "Please reconfigure:"
        echo "  aws configure"
    fi
else
    echo "⚠️  AWS credentials file not found"
    echo ""
    echo "You need to configure AWS credentials first."
    echo ""
    echo "Run this command:"
    echo "  aws configure"
    echo ""
    echo "You'll need:"
    echo "  - AWS Access Key ID"
    echo "  - AWS Secret Access Key"
    echo "  - Default region (e.g., us-east-1)"
    echo "  - Default output format (json)"
    echo ""
    echo "Get credentials from:"
    echo "  AWS Console → IAM → Users → Your User → Security Credentials"
fi

echo ""

