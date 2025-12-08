#!/usr/bin/env bash
# Inject network latency into pods in a namespace

set -e

NAMESPACE=$1
LATENCY=${2:-100}  # Default 100ms

if [ -z "$NAMESPACE" ]; then
  echo "Usage: ./chaos-network-lag.sh <namespace> [latency_ms]"
  exit 1
fi

echo "🌐 Injecting network latency (${LATENCY}ms) into namespace $NAMESPACE..."
echo "   This requires network policies or sidecar injection"
echo "   For local testing, this is a placeholder"
echo ""
echo "⚠️  Full network chaos requires Istio/Linkerd or network policies"
echo "   For now, use pod kills or CPU stress for chaos testing"

