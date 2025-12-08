#!/bin/bash
# Install Chaos Mesh on Kubernetes cluster

set -e

echo "Installing Chaos Mesh..."

# Add Chaos Mesh Helm repo
helm repo add chaos-mesh https://charts.chaos-mesh.org
helm repo update

# Install Chaos Mesh
helm install chaos-mesh chaos-mesh/chaos-mesh \
  --namespace chaos-mesh \
  --create-namespace \
  --set chaosDaemon.runtime=containerd \
  --set chaosDaemon.socketPath=/run/containerd/containerd.sock \
  --set dashboard.create=true \
  --set dashboard.securityMode=false

echo "Waiting for Chaos Mesh to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=chaos-mesh \
  -n chaos-mesh --timeout=300s

echo "Chaos Mesh installed successfully!"
echo "Access dashboard at: kubectl port-forward -n chaos-mesh svc/chaos-mesh-dashboard 2333:2333"

