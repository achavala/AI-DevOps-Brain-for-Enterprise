#!/usr/bin/env bash
# Show status of all 19 industries

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

echo "📊 AI DevOps Brain - 19 Industry Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

TOTAL_READY=0
TOTAL_DESIRED=0

for ns in "${namespaces[@]}"; do
  ready=$(kubectl get deployment ${ns}-sim -n "$ns" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
  desired=$(kubectl get deployment ${ns}-sim -n "$ns" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
  
  # Ensure we have numeric values
  ready=${ready:-0}
  desired=${desired:-0}
  
  TOTAL_READY=$((TOTAL_READY + ready))
  TOTAL_DESIRED=$((TOTAL_DESIRED + desired))
  
  if [ "$ready" -eq "$desired" ] && [ "$desired" -gt 0 ]; then
    status="✅"
  elif [ "$ready" -gt 0 ]; then
    status="⚠️ "
  else
    status="❌"
  fi
  
  printf "  %s %-15s %2d/%2d pods\n" "$status" "$ns:" "$ready" "$desired"
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📈 Summary:"
echo "   • Total Pods: $TOTAL_DESIRED"
echo "   • Ready Pods: $TOTAL_READY"
echo "   • Health: $((TOTAL_READY * 100 / TOTAL_DESIRED))%"
echo ""

