#!/bin/bash
# Setup AWS configuration for AI DevOps Brain

set -e

echo "🔐 Setting up AWS configuration..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not found. Please install it first:"
    echo "   Run: ./scripts/install-prerequisites.sh"
    exit 1
fi

# Check if AWS is already configured
if aws sts get-caller-identity &> /dev/null; then
    echo "✅ AWS credentials already configured"
    ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    echo "   Account ID: $ACCOUNT_ID"
else
    echo "⚠️  AWS credentials not configured"
    echo "   Please run: aws configure"
    echo "   You'll need:"
    echo "   - AWS Access Key ID"
    echo "   - AWS Secret Access Key"
    echo "   - Default region (e.g., us-east-1)"
    echo "   - Default output format (json)"
    read -p "Press Enter after configuring AWS credentials..."
fi

# Get account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>/dev/null || echo "")

if [ -z "$ACCOUNT_ID" ]; then
    echo "❌ Could not get AWS account ID. Please configure AWS credentials first."
    exit 1
fi

echo ""
echo "📦 Creating S3 bucket for Terraform state..."

BUCKET_NAME="ai-devops-brain-terraform-state-$ACCOUNT_ID"

# Check if bucket exists
if aws s3 ls "s3://$BUCKET_NAME" 2>&1 | grep -q 'NoSuchBucket'; then
    # Create bucket
    if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
        echo "✅ Bucket $BUCKET_NAME already exists"
    else
        # Determine region
        REGION=$(aws configure get region || echo "us-east-1")
        
        if [ "$REGION" == "us-east-1" ]; then
            aws s3 mb "s3://$BUCKET_NAME"
        else
            aws s3 mb "s3://$BUCKET_NAME" --region "$REGION"
        fi
        echo "✅ Created bucket: $BUCKET_NAME"
    fi
    
    # Enable versioning
    aws s3api put-bucket-versioning \
        --bucket "$BUCKET_NAME" \
        --versioning-configuration Status=Enabled
    echo "✅ Enabled versioning on bucket"
    
    # Enable encryption
    aws s3api put-bucket-encryption \
        --bucket "$BUCKET_NAME" \
        --server-side-encryption-configuration '{
            "Rules": [{
                "ApplyServerSideEncryptionByDefault": {
                    "SSEAlgorithm": "AES256"
                }
            }]
        }'
    echo "✅ Enabled encryption on bucket"
else
    echo "✅ Bucket $BUCKET_NAME already exists"
fi

echo ""
echo "✅ AWS setup complete!"
echo ""
echo "Next steps:"
echo "1. Update infrastructure/main.tf with your S3 bucket name:"
echo "   bucket = \"$BUCKET_NAME\""
echo "2. Run: cd infrastructure && terraform init"
echo "3. Continue with QUICKSTART.md Step 3"

