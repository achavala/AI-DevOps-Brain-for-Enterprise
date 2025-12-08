#!/usr/bin/env bash
# Create all 19 industry namespaces

set -e

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

echo "🚀 Creating all 19 industry namespaces..."
echo ""

for ns in "${namespaces[@]}"; do
  kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -
  echo "  ✔ Namespace created: $ns"
done

echo ""
echo "✅ All 19 namespaces created!"
echo ""
echo "📊 Verification:"
kubectl get namespaces | grep -E "$(IFS='|'; echo "${namespaces[*]}")"

