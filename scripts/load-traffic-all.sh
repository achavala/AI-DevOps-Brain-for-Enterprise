#!/usr/bin/env bash
# Generate traffic to all 19 industries in parallel

set -e

DURATION=${1:-300}  # Default 5 minutes
RATE=${2:-2}        # Default 2 requests per second per namespace

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

echo "🚀 Starting traffic generation for all 19 industries..."
echo "   Duration: ${DURATION}s per namespace"
echo "   Rate: ${RATE} req/s per namespace"
echo "   Total rate: ~$((RATE * ${#namespaces[@]})) req/s"
echo ""

PIDS=()

for ns in "${namespaces[@]}"; do
  echo "  Starting traffic for: $ns"
  ./scripts/load-traffic.sh "$ns" "$DURATION" "$RATE" > /tmp/traffic-${ns}.log 2>&1 &
  PIDS+=($!)
  sleep 1  # Stagger starts
done

echo ""
echo "✅ All traffic generators started (${#PIDS[@]} processes)"
echo "   Logs: /tmp/traffic-*.log"
echo ""
echo "Press Ctrl+C to stop all traffic generators..."

trap 'echo ""; echo "🛑 Stopping all traffic generators..."; for pid in "${PIDS[@]}"; do kill $pid 2>/dev/null || true; done; echo "✅ All stopped"; exit 0' INT TERM

# Wait for all background processes
wait

