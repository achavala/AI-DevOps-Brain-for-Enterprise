#!/bin/bash
# Clear incorrect AWS configuration so you can start fresh

echo "🧹 Clearing incorrect AWS configuration..."
echo ""

if [ -f ~/.aws/credentials ]; then
    echo "Current credentials file (showing first few lines):"
    head -5 ~/.aws/credentials
    echo ""
    read -p "Do you want to backup and clear this file? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Backup
        cp ~/.aws/credentials ~/.aws/credentials.backup.$(date +%Y%m%d_%H%M%S)
        echo "✅ Backed up to ~/.aws/credentials.backup.*"
        
        # Clear
        cat > ~/.aws/credentials << 'EOF'
[default]
# Add your credentials here or run: aws configure
aws_access_key_id = 
aws_secret_access_key = 
EOF
        echo "✅ Cleared credentials file"
        echo ""
        echo "Now run: aws configure"
        echo "And enter your REAL AWS credentials (not commands!)"
    else
        echo "Cancelled. File not changed."
    fi
else
    echo "No credentials file found. Run 'aws configure' to create one."
fi

echo ""

