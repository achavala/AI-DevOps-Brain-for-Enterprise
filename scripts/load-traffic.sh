#!/usr/bin/env bash
# Generate traffic to a specific namespace service

set -e

NAMESPACE=$1
DURATION=${2:-60}  # Default 60 seconds
RATE=${3:-5}       # Default 5 requests per second

if [ -z "$NAMESPACE" ]; then
  echo "Usage: ./load-traffic.sh <namespace> [duration_seconds] [requests_per_second]"
  echo ""
  echo "Examples:"
  echo "  ./load-traffic.sh finance 60 5"
  echo "  ./load-traffic.sh aicloud 120 10"
  echo "  ./load-traffic.sh semiconductor"
  exit 1
fi

# Check if service exists
if ! kubectl get svc ${NAMESPACE}-service -n "$NAMESPACE" > /dev/null 2>&1; then
  echo "❌ Error: Service ${NAMESPACE}-service not found in namespace $NAMESPACE"
  exit 1
fi

# Get service URL (try minikube first, then port-forward)
if command -v minikube &> /dev/null && minikube status &> /dev/null; then
  SERVICE_URL=$(minikube service ${NAMESPACE}-service -n "$NAMESPACE" --url 2>/dev/null | head -1)
else
  # Fallback: use port-forward in background
  echo "⚠️  Minikube not available, using kubectl port-forward..."
  kubectl port-forward -n "$NAMESPACE" svc/${NAMESPACE}-service 8080:80 > /dev/null 2>&1 &
  PF_PID=$!
  sleep 2
  SERVICE_URL="http://localhost:8080"
fi

if [ -z "$SERVICE_URL" ]; then
  echo "❌ Error: Could not determine service URL"
  exit 1
fi

echo "📡 Sending traffic to ${SERVICE_URL}"
echo "   Namespace: $NAMESPACE"
echo "   Duration: ${DURATION}s"
echo "   Rate: ${RATE} req/s"
echo "   Press Ctrl+C to stop early"
echo ""

DELAY=$(echo "scale=3; 1/$RATE" | bc)
END_TIME=$(($(date +%s) + DURATION))
COUNT=0

trap 'echo ""; echo "✅ Traffic generation stopped. Total requests: $COUNT"; [ ! -z "$PF_PID" ] && kill $PF_PID 2>/dev/null; exit 0' INT TERM

while [ $(date +%s) -lt $END_TIME ]; do
  curl -s "$SERVICE_URL" > /dev/null 2>&1 && COUNT=$((COUNT + 1))
  sleep "$DELAY"
done

echo ""
echo "✅ Traffic generation complete!"
echo "   Total requests sent: $COUNT"
[ ! -z "$PF_PID" ] && kill $PF_PID 2>/dev/null

