#!/bin/bash
# Deploy platform components to a cluster

set -e

CLUSTER_NAME=${1:-finance-cluster}
NAMESPACE=${2:-default}

echo "Deploying platform components to $CLUSTER_NAME..."

# Check kubectl context
kubectl cluster-info

# Create namespaces
kubectl create namespace argocd --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace keda --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace logging --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

# Install ArgoCD
echo "Installing ArgoCD..."
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# Wait for ArgoCD to be ready
echo "Waiting for ArgoCD..."
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s

# Install KEDA
echo "Installing KEDA..."
helm repo add kedacore https://kedacore.github.io/charts
helm repo update
helm install keda kedacore/keda --namespace keda

# Install Prometheus
echo "Installing Prometheus..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install prometheus prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set prometheus.prometheusSpec.retention=30d

# Install Loki
echo "Installing Loki..."
helm repo add grafana https://grafana.github.io/helm-charts
helm install loki grafana/loki-stack \
  --namespace logging \
  --set loki.persistence.enabled=true \
  --set loki.persistence.size=100Gi

# Install FluentBit
echo "Installing FluentBit..."
kubectl apply -f ../data-pipeline/fluentbit/daemonset.yaml
kubectl apply -f ../data-pipeline/fluentbit/fluentbit-config.yaml

# Install Karpenter (if not already installed)
echo "Checking Karpenter..."
if ! kubectl get deployment karpenter -n karpenter &>/dev/null; then
    echo "Installing Karpenter..."
    helm repo add karpenter https://charts.karpenter.sh
    helm repo update
    helm install karpenter karpenter/karpenter \
      --namespace karpenter \
      --create-namespace \
      --set settings.clusterName=$CLUSTER_NAME
fi

# Install Istio (optional)
read -p "Install Istio service mesh? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Installing Istio..."
    istioctl install --set values.defaultRevision=default -y
    kubectl label namespace default istio-injection=enabled --overwrite
fi

echo "Platform components deployed successfully!"
echo ""
echo "Access ArgoCD: kubectl port-forward -n argocd svc/argocd-server 8080:443"
echo "ArgoCD admin password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d"

