#!/usr/bin/env bash
# Randomly kill a pod in a namespace (chaos testing)

set -e

NAMESPACE=$1

if [ -z "$NAMESPACE" ]; then
  echo "Usage: ./chaos-kill-random.sh <namespace>"
  echo ""
  echo "Examples:"
  echo "  ./chaos-kill-random.sh semiconductor"
  echo "  ./chaos-kill-random.sh gpucloud"
  exit 1
fi

# Get a random pod
POD=$(kubectl get pods -n "$NAMESPACE" -o jsonpath='{.items[*].metadata.name}' | tr ' ' '\n' | shuf | head -1)

if [ -z "$POD" ]; then
  echo "❌ No pods found in namespace $NAMESPACE"
  exit 1
fi

echo "💥 Killing random pod in namespace $NAMESPACE..."
echo "   Pod: $POD"

kubectl delete pod "$POD" -n "$NAMESPACE" --grace-period=0 --force

echo "✅ Pod $POD deleted"
echo ""
echo "📊 Remaining pods:"
kubectl get pods -n "$NAMESPACE"

