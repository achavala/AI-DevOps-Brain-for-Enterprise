#!/bin/bash
# Deploy platform components to local Kubernetes (Minikube/Kind)

set -e

CLUSTER_NAME=${1:-local-cluster}

echo "☸️  Deploying platform components to local Kubernetes..."
echo ""

# Check if kubectl can connect
if ! kubectl cluster-info &> /dev/null; then
    echo "❌ Cannot connect to Kubernetes cluster"
    echo ""
    echo "Please start a local cluster first:"
    echo "  Minikube: minikube start"
    echo "  Kind:     kind create cluster --name ai-devops-brain"
    exit 1
fi

echo "✅ Connected to cluster: $(kubectl config current-context)"
echo ""

# Create namespaces
echo "📦 Creating namespaces..."
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace keda --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
echo "✅ Namespaces created"
echo ""

# Install ArgoCD
echo "🔄 Installing ArgoCD..."
if ! kubectl get deployment argocd-server -n argocd &> /dev/null; then
    kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    echo "⏳ Waiting for ArgoCD to be ready..."
    kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s || true
    echo "✅ ArgoCD installed"
else
    echo "✅ ArgoCD already installed"
fi
echo ""

# Install KEDA
echo "📈 Installing KEDA..."
if ! kubectl get deployment keda-operator -n keda &> /dev/null; then
    helm repo add kedacore https://kedacore.github.io/charts
    helm repo update
    helm install keda kedacore/keda --namespace keda || helm upgrade keda kedacore/keda --namespace keda
    echo "✅ KEDA installed"
else
    echo "✅ KEDA already installed"
fi
echo ""

# Install Prometheus + Grafana
echo "📊 Installing Prometheus + Grafana..."
if ! kubectl get deployment prometheus-operator -n monitoring &> /dev/null; then
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    helm install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --set prometheus.prometheusSpec.retention=7d \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi || \
    helm upgrade prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --set prometheus.prometheusSpec.retention=7d \
        --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi
    echo "✅ Prometheus + Grafana installed"
else
    echo "✅ Prometheus + Grafana already installed"
fi
echo ""

# Install Loki
echo "📝 Installing Loki..."
if ! kubectl get deployment loki -n logging &> /dev/null; then
    helm repo add grafana https://grafana.github.io/helm-charts
    helm repo update
    helm install loki grafana/loki-stack \
        --namespace logging \
        --set loki.persistence.enabled=true \
        --set loki.persistence.size=10Gi || \
    helm upgrade loki grafana/loki-stack \
        --namespace logging \
        --set loki.persistence.enabled=true \
        --set loki.persistence.size=10Gi
    echo "✅ Loki installed"
else
    echo "✅ Loki already installed"
fi
echo ""

# Deploy FluentBit (local version - writes to local filesystem)
echo "📥 Deploying FluentBit (local version)..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config-local
  namespace: logging
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         1
        Log_Level     info
        Daemon        off
        Parsers_File  parsers.conf
        HTTP_Server   On
        HTTP_Listen   0.0.0.0
        HTTP_Port     2020

    [INPUT]
        Name              tail
        Path              /var/log/containers/*.log
        Parser            docker
        Tag               kube.*
        Refresh_Interval  5
        Mem_Buf_Limit     50MB

    [FILTER]
        Name                kubernetes
        Match               kube.*
        Kube_URL            https://kubernetes.default.svc:443
        Kube_CA_File        /var/run/secrets/kubernetes.io/serviceaccount/ca.crt
        Kube_Token_File     /var/run/secrets/kubernetes.io/serviceaccount/token
        Merge_Log           On
        Keep_Log            Off

    [FILTER]
        Name                modify
        Match               *
        Add                 cluster_name local
        Add                 environment local

    [OUTPUT]
        Name                file
        Match               *
        Path                /local-data/logs
        File                fluent-bit.log
        Format              json_lines

    [OUTPUT]
        Name                loki
        Match               *
        Url                 http://loki.logging.svc.cluster.local:3100
        Labels              job=fluent-bit,cluster=local
EOF

# Update FluentBit DaemonSet to use local storage
if ! kubectl get daemonset fluent-bit -n logging &> /dev/null; then
    # Use the existing daemonset but modify for local
    kubectl apply -f data-pipeline/fluentbit/daemonset.yaml
    
    # Patch to add local storage volume
    kubectl patch daemonset fluent-bit -n logging --type='json' -p='[
        {
            "op": "add",
            "path": "/spec/template/spec/volumes/-",
            "value": {
                "name": "local-data",
                "hostPath": {
                    "path": "'$(pwd)'/local-data",
                    "type": "DirectoryOrCreate"
                }
            }
        },
        {
            "op": "add",
            "path": "/spec/template/spec/containers/0/volumeMounts/-",
            "value": {
                "name": "local-data",
                "mountPath": "/local-data"
            }
        }
    ]' || echo "⚠️  Could not patch FluentBit (may need manual update)"
fi

echo "✅ FluentBit configured for local storage"
echo ""

# Wait for deployments
echo "⏳ Waiting for deployments to be ready..."
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s || true
kubectl wait --for=condition=available deployment/prometheus-operator -n monitoring --timeout=300s || true
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Platform components deployed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Access dashboards:"
echo ""
echo "  🔄 ArgoCD:"
echo "     kubectl port-forward -n argocd svc/argocd-server 8080:443"
echo "     Password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"
echo ""
echo "  📊 Grafana:"
echo "     kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80"
echo "     Username: admin"
echo "     Password: prom-operator"
echo ""
echo "  📦 MinIO Console:"
echo "     http://localhost:9001"
echo "     Access: minioadmin / minioadmin"
echo ""
echo "Data stored locally in: ./local-data/"
echo ""

