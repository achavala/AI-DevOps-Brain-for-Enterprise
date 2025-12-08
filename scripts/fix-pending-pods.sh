#!/usr/bin/env bash
# Fix pending pods by reducing replicas for resource-constrained namespaces

set -e

echo "🔧 Fixing pending pods by adjusting replica counts..."
echo ""

# Namespaces with pending pods (reduce to 1 replica)
problematic_namespaces=(
  semiconductor
  aicloud
  gpucloud
  socialmedia
  aiplatform
  media
)

echo "📉 Reducing replicas for resource-constrained namespaces..."

for ns in "${problematic_namespaces[@]}"; do
  current=$(kubectl get deployment ${ns}-sim -n "$ns" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
  if [ "$current" -gt 1 ]; then
    echo "  Scaling $ns: $current → 1 replica"
    kubectl scale deployment ${ns}-sim --replicas=1 -n "$ns"
  fi
done

echo ""
echo "⏳ Waiting for pods to stabilize..."
sleep 10

echo ""
echo "✅ Replica adjustments complete!"
echo ""
echo "📊 Updated Status:"
./scripts/status-all-industries.sh

