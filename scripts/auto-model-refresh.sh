#!/bin/bash
# Auto-refresh AI models when Python files change
# Watches model training files and retrains automatically

set -e

echo "🔄 Starting auto-model-refresh watcher..."
echo ""

# Check if Python environment is set up
if [ ! -d "ai-models/venv" ]; then
    echo "❌ Python virtual environment not found"
    echo "   Run: cd ai-models && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if watchman or fswatch is available
if command -v fswatch &> /dev/null; then
    WATCHER="fswatch"
elif command -v watchman &> /dev/null; then
    WATCHER="watchman"
else
    echo "⚠️  No file watcher found (fswatch or watchman)"
    echo "   Installing fswatch..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install fswatch
        WATCHER="fswatch"
    else
        echo "   Please install fswatch or watchman manually"
        exit 1
    fi
fi

echo "✅ Using $WATCHER for file watching"
echo ""

# Files to watch
WATCH_DIRS=(
    "ai-models/anomaly-detection"
    "ai-models/rca-engine"
    "ai-models/auto-fix"
)

# Training script
TRAIN_SCRIPT="ai-models/anomaly-detection/train_anomaly_detector.py"

echo "👀 Watching for changes in:"
for dir in "${WATCH_DIRS[@]}"; do
    echo "  - $dir"
done
echo ""

echo "🔄 Auto-refresh enabled. Press Ctrl+C to stop."
echo ""

# Function to train models
train_models() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔄 Model files changed - retraining..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    cd ai-models
    source venv/bin/activate
    
    # Train with simulation data
    python anomaly-detection/train_anomaly_detector.py --simulate
    
    deactivate
    cd ..
    
    echo ""
    echo "✅ Models retrained successfully"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}

# Watch files
if [ "$WATCHER" = "fswatch" ]; then
    fswatch -o "${WATCH_DIRS[@]}" | while read f; do
        train_models
    done
elif [ "$WATCHER" = "watchman" ]; then
    watchman watch "${WATCH_DIRS[@]}"
    watchman -- trigger "${WATCH_DIRS[@]}" train-models '*.py' -- train_models
fi

