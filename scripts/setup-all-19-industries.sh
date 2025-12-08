#!/usr/bin/env bash
# Complete setup script for all 19 industries
# This is the master script that orchestrates everything

set -e

echo "🚀 AI DevOps Brain - Complete 19-Industry Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Create namespaces
echo "📦 Step 1: Creating all 19 namespaces..."
./scripts/create-all-namespaces.sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 2: Deploy all industries
echo "📋 Step 2: Deploying all 19 industry simulations..."
./scripts/deploy-all-industries.sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 3: Create services
echo "🔌 Step 3: Creating services for all industries..."
./scripts/create-services-all.sh

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 4: Wait for everything to be ready
echo "⏳ Step 4: Waiting for all pods to be ready..."
sleep 10

echo ""
echo "📊 Final Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

TOTAL_PODS=0
READY_PODS=0

for ns in "${namespaces[@]}"; do
  ready=$(kubectl get deployment ${ns}-sim -n "$ns" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
  desired=$(kubectl get deployment ${ns}-sim -n "$ns" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
  TOTAL_PODS=$((TOTAL_PODS + desired))
  READY_PODS=$((READY_PODS + ready))
  printf "  %-15s %2d/%2d pods ready\n" "$ns:" "$ready" "$desired"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Setup Complete!"
echo ""
echo "📈 Summary:"
echo "   • Namespaces: 19"
echo "   • Deployments: 19"
echo "   • Services: 19"
echo "   • Total Pods: $TOTAL_PODS"
echo "   • Ready Pods: $READY_PODS"
echo ""
echo "🎯 Next Steps:"
echo "   1. Generate traffic: ./scripts/load-traffic-all.sh"
echo "   2. Inject chaos: ./scripts/chaos-random-all.sh"
echo "   3. Check status: kubectl get pods -A | grep -E 'finance|healthcare|automotive|retail|logistics|energy|telecom|banking|insurance|manufacturing|gov|education|cloud|media|aiplatform|semiconductor|aicloud|gpucloud|socialmedia'"
echo "   4. View logs: kubectl logs -n <namespace> -l app=<namespace>-sim"
echo ""

