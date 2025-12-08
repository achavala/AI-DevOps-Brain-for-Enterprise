#!/usr/bin/env bash
# Deploy simulation services to all 19 industries

set -e

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

echo "🚀 Deploying simulation services to all 19 industries..."
echo ""

# First, ensure all namespaces exist
echo "📦 Ensuring namespaces exist..."
for ns in "${namespaces[@]}"; do
  kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f - > /dev/null
done

echo "✅ Namespaces ready"
echo ""

# Deploy deployments
echo "📋 Creating deployments..."
for ns in "${namespaces[@]}"; do
  cat <<EOF | kubectl apply -n "$ns" -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${ns}-sim
  labels:
    app: ${ns}-sim
    cluster: ${ns}
    workload: simulation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ${ns}-sim
  template:
    metadata:
      labels:
        app: ${ns}-sim
        cluster: ${ns}
        workload: simulation
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "80"
    spec:
      containers:
      - name: ${ns}-sim-container
        image: nginx:alpine
        ports:
        - containerPort: 80
          name: http
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 10
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 5
EOF
  echo "  ✔ Deployment created: ${ns}-sim"
done

echo ""
echo "✅ All 19 deployments created!"
echo ""
echo "⏳ Waiting for pods to be ready..."
sleep 5

echo ""
echo "📊 Status:"
for ns in "${namespaces[@]}"; do
  ready=$(kubectl get deployment ${ns}-sim -n "$ns" -o jsonpath='{.status.readyReplicas}' 2>/dev/null || echo "0")
  desired=$(kubectl get deployment ${ns}-sim -n "$ns" -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0")
  echo "  $ns: $ready/$desired pods ready"
done

echo ""
echo "✅ Deployment complete!"

