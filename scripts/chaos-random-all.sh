#!/usr/bin/env bash
# Randomly inject chaos across all 19 industries

set -e

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

CHAOS_TYPE=${1:-kill}  # kill, cpu, or both

echo "💥 Injecting random chaos across all 19 industries..."
echo "   Type: $CHAOS_TYPE"
echo ""

for ns in "${namespaces[@]}"; do
  # Randomly select ~30% of namespaces for chaos
  if [ $((RANDOM % 10)) -lt 3 ]; then
    case "$CHAOS_TYPE" in
      kill)
        echo "  💥 Killing random pod in: $ns"
        ./scripts/chaos-kill-random.sh "$ns" > /dev/null 2>&1 || true
        ;;
      cpu)
        echo "  🔥 CPU stress in: $ns"
        ./scripts/chaos-cpu-stress.sh "$ns" 30 > /dev/null 2>&1 || true
        ;;
      both)
        if [ $((RANDOM % 2)) -eq 0 ]; then
          echo "  💥 Killing random pod in: $ns"
          ./scripts/chaos-kill-random.sh "$ns" > /dev/null 2>&1 || true
        else
          echo "  🔥 CPU stress in: $ns"
          ./scripts/chaos-cpu-stress.sh "$ns" 30 > /dev/null 2>&1 || true
        fi
        ;;
    esac
    sleep 1
  fi
done

echo ""
echo "✅ Chaos injection complete!"

