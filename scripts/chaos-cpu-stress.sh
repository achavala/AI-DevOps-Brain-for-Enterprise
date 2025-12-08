#!/usr/bin/env bash
# Inject CPU stress into a random pod

set -e

NAMESPACE=$1
DURATION=${2:-60}  # Default 60 seconds

if [ -z "$NAMESPACE" ]; then
  echo "Usage: ./chaos-cpu-stress.sh <namespace> [duration_seconds]"
  exit 1
fi

# Get a random pod
POD=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | shuf | head -1)

if [ -z "$POD" ]; then
  echo "❌ No pods found in namespace $NAMESPACE"
  exit 1
fi

echo "🔥 Injecting CPU stress into pod $POD in namespace $NAMESPACE..."
echo "   Duration: ${DURATION}s"

# Create a temporary stress container
kubectl run stress-${POD}-$(date +%s) \
  --image=containerstack/cpustress \
  --restart=Never \
  --rm -i \
  --overrides="{\"spec\":{\"containers\":[{\"name\":\"stress\",\"image\":\"containerstack/cpustress\",\"command\":[\"sh\",\"-c\",\"stress --cpu 4 --timeout ${DURATION}s\"]}]}}" \
  -n "$NAMESPACE" || \
kubectl exec -n "$NAMESPACE" "$POD" -- sh -c "apk add --no-cache stress && stress --cpu 4 --timeout ${DURATION}s" 2>/dev/null || \
echo "⚠️  Could not inject CPU stress directly. Pod may not support it."

echo "✅ CPU stress injection complete"

