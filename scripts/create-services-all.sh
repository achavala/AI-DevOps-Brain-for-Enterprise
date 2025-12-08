#!/usr/bin/env bash
# Create services for all 19 industry deployments

set -e

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

echo "🚀 Creating services for all 19 industries..."
echo ""

for ns in "${namespaces[@]}"; do
  cat <<EOF | kubectl apply -n "$ns" -f -
apiVersion: v1
kind: Service
metadata:
  name: ${ns}-service
  labels:
    app: ${ns}-sim
    cluster: ${ns}
spec:
  type: ClusterIP
  selector:
    app: ${ns}-sim
  ports:
    - port: 80
      targetPort: 80
      protocol: TCP
      name: http
EOF
  echo "  ✔ Service created for: $ns"
done

echo ""
echo "✅ All 19 services created!"
echo ""
echo "📊 Verification:"
kubectl get svc -A | grep -E "$(IFS='|'; echo "${namespaces[*]}")" | grep -E "-service"

