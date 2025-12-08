#!/usr/bin/env bash
# Deploy all 19 industries with optimized replica counts for Minikube

set -e

echo "🚀 Deploying all 19 industries with optimized resource settings..."
echo ""

# Industry-specific replica counts (optimized for Minikube)
declare -A replicas=(
  [finance]=3
  [healthcare]=3
  [automotive]=3
  [retail]=3
  [logistics]=3
  [energy]=3
  [telecom]=3
  [banking]=3
  [insurance]=3
  [manufacturing]=3
  [gov]=3
  [education]=2
  [cloud]=2
  [media]=1
  [aiplatform]=1
  [semiconductor]=1
  [aicloud]=1
  [gpucloud]=1
  [socialmedia]=1
)

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

# Ensure all namespaces exist
echo "📦 Ensuring namespaces exist..."
for ns in "${namespaces[@]}"; do
  kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f - > /dev/null
done

echo "✅ Namespaces ready"
echo ""

# Deploy with optimized replica counts
echo "📋 Creating deployments with optimized replica counts..."
for ns in "${namespaces[@]}"; do
  replica_count=${replicas[$ns]:-1}
  
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
  replicas: ${replica_count}
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
  echo "  ✔ ${ns}: ${replica_count} replica(s)"
done

echo ""
echo "✅ All 19 deployments created with optimized settings!"
echo ""
echo "⏳ Waiting for pods to be ready..."
sleep 10

echo ""
echo "📊 Status:"
./scripts/status-all-industries.sh

