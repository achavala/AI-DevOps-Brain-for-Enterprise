#!/usr/bin/env bash
# Advanced chaos experiments for AI training

set -e

NAMESPACE=$1
EXPERIMENT_TYPE=${2:-cpu}

if [ -z "$NAMESPACE" ]; then
  echo "Usage: ./scripts/chaos-advanced.sh <namespace> [experiment_type]"
  echo ""
  echo "Experiment types:"
  echo "  cpu        - CPU saturation"
  echo "  memory     - Memory pressure"
  echo "  network    - Network latency/partition"
  echo "  errors     - Error injection"
  echo "  pod-kill   - Random pod kill"
  echo ""
  exit 1
fi

echo "💥 Running chaos experiment: $EXPERIMENT_TYPE in namespace $NAMESPACE"
echo ""

case "$EXPERIMENT_TYPE" in
  cpu)
    echo "🔥 Injecting CPU stress..."
    ./scripts/chaos-cpu-stress.sh "$NAMESPACE" 120
    ;;
  
  memory)
    echo "💾 Injecting memory pressure..."
    # Create a pod that consumes memory
    cat <<EOF | kubectl apply -n "$NAMESPACE" -f -
apiVersion: v1
kind: Pod
metadata:
  name: memory-stress-$(date +%s)
  namespace: $NAMESPACE
spec:
  containers:
  - name: stress
    image: polinux/stress
    command: ["stress", "--vm", "1", "--vm-bytes", "512M", "--timeout", "60s"]
    resources:
      requests:
        memory: 256Mi
      limits:
        memory: 1Gi
  restartPolicy: Never
EOF
    echo "✅ Memory stress pod created"
    ;;
  
  network)
    echo "🌐 Injecting network latency..."
    echo "⚠️  Network chaos requires Istio/Linkerd or network policies"
    echo "   For now, using pod network isolation simulation"
    # This would use Istio fault injection or network policies
    kubectl label pod -n "$NAMESPACE" -l app=${NAMESPACE}-sim network-chaos=enabled --overwrite || true
    ;;
  
  errors)
    echo "❌ Injecting error spikes..."
    # Scale down to cause errors, then scale back up
    echo "  Scaling down deployment..."
    kubectl scale deployment ${NAMESPACE}-sim --replicas=0 -n "$NAMESPACE"
    sleep 10
    echo "  Scaling back up..."
    kubectl scale deployment ${NAMESPACE}-sim --replicas=1 -n "$NAMESPACE"
    echo "✅ Error injection complete"
    ;;
  
  pod-kill)
    echo "💀 Killing random pod..."
    ./scripts/chaos-kill-random.sh "$NAMESPACE"
    ;;
  
  *)
    echo "❌ Unknown experiment type: $EXPERIMENT_TYPE"
    exit 1
    ;;
esac

echo ""
echo "✅ Chaos experiment complete!"

