#!/bin/bash
# Setup data ingestion pipeline

set -e

CLUSTER_NAME=${1:-finance-cluster}
NAMESPACE=${2:-logging}

echo "Setting up data pipeline for $CLUSTER_NAME..."

# Check kubectl context
kubectl cluster-info

# Create logging namespace
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Update FluentBit config with cluster name and account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
sed "s/CLUSTER_NAME/$CLUSTER_NAME/g; s/ACCOUNT_ID/$ACCOUNT_ID/g" \
  data-pipeline/fluentbit/fluentbit-config.yaml | kubectl apply -f -

# Deploy FluentBit
kubectl apply -f data-pipeline/fluentbit/daemonset.yaml

# Wait for FluentBit to be ready
echo "Waiting for FluentBit to be ready..."
kubectl wait --for=condition=ready pod -l app=fluent-bit -n $NAMESPACE --timeout=300s

# Deploy Prometheus
echo "Deploying Prometheus..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=30d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=100Gi

# Deploy Thanos for long-term storage
echo "Deploying Thanos..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm upgrade --install thanos bitnami/thanos \
  --namespace monitoring \
  --set objstoreConfig.type=s3 \
  --set objstoreConfig.config.bucket=ai-devops-brain-metrics-$ACCOUNT_ID \
  --set objstoreConfig.config.endpoint=s3.$AWS_DEFAULT_REGION.amazonaws.com

# Deploy K8s Event Exporter
echo "Deploying K8s Event Exporter..."
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: k8s-event-exporter
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: k8s-event-exporter
  template:
    metadata:
      labels:
        app: k8s-event-exporter
    spec:
      serviceAccountName: k8s-event-exporter
      containers:
      - name: exporter
        image: gcr.io/google-containers/event-exporter:v0.4.0
        env:
        - name: S3_BUCKET
          value: ai-devops-brain-events-$ACCOUNT_ID
        - name: AWS_REGION
          value: $AWS_DEFAULT_REGION
        volumeMounts:
        - name: config
          mountPath: /etc/config
      volumes:
      - name: config
        configMap:
          name: event-exporter-config
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: k8s-event-exporter
  namespace: $NAMESPACE
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: k8s-event-exporter
rules:
- apiGroups: [""]
  resources:
  - events
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: k8s-event-exporter
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: k8s-event-exporter
subjects:
- kind: ServiceAccount
  name: k8s-event-exporter
  namespace: $NAMESPACE
EOF

# Deploy CloudTrail Exporter (runs as Lambda or ECS task)
echo "CloudTrail exporter should be deployed separately as Lambda function"

# Verify deployments
echo "Verifying deployments..."
kubectl get pods -n $NAMESPACE
kubectl get pods -n monitoring

echo "Data pipeline setup complete!"
echo ""
echo "Data flows:"
echo "  - Logs: FluentBit → S3 (ai-devops-brain-logs-$ACCOUNT_ID)"
echo "  - Metrics: Prometheus → Thanos → S3 (ai-devops-brain-metrics-$ACCOUNT_ID)"
echo "  - Events: K8s Event Exporter → S3 (ai-devops-brain-events-$ACCOUNT_ID)"

