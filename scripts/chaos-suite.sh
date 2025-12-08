#!/usr/bin/env bash
# Run a suite of chaos experiments across all industries

set -e

DURATION=${1:-300}  # Default 5 minutes

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

experiments=("cpu" "memory" "errors" "pod-kill")

echo "💥 Running chaos suite across all 19 industries..."
echo "   Duration: ${DURATION}s"
echo ""

# Run random chaos experiments
for i in $(seq 1 $((DURATION / 60))); do
  echo "🔄 Chaos cycle $i..."
  
  # Select random namespace and experiment
  random_ns=${namespaces[$RANDOM % ${#namespaces[@]}]}
  random_exp=${experiments[$RANDOM % ${#experiments[@]}]}
  
  echo "  → $random_ns: $random_exp"
  ./scripts/chaos-advanced.sh "$random_ns" "$random_exp" > /dev/null 2>&1 || true
  
  sleep 60  # Wait 1 minute between experiments
done

echo ""
echo "✅ Chaos suite complete!"

