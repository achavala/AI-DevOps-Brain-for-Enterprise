#!/usr/bin/env bash
# Reduce resource requests for all pods to fit within Minikube limits

set -e

echo "🔧 Reducing resource requests to fit Minikube constraints..."
echo ""

namespaces=(
  aicloud
  gpucloud
  socialmedia
)

echo "📉 Reducing resource requests for remaining namespaces..."

for ns in "${namespaces[@]}"; do
  echo "  Updating $ns..."
  kubectl patch deployment ${ns}-sim -n "$ns" -p '{"spec":{"template":{"spec":{"containers":[{"name":"'${ns}'-sim-container","resources":{"requests":{"cpu":"50m","memory":"64Mi"},"limits":{"cpu":"200m","memory":"256Mi"}}}]}}}}'
done

echo ""
echo "⏳ Waiting for pods to restart..."
sleep 15

echo ""
echo "✅ Resource adjustments complete!"
echo ""
echo "📊 Updated Status:"
./scripts/status-all-industries.sh

