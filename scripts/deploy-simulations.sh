#!/bin/bash
# Deploy industry simulation workloads to local Kubernetes

set -e

echo "🚀 Deploying industry simulations..."
echo ""

# Create namespaces if they don't exist
echo "📦 Creating namespaces..."
kubectl create namespace finance --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace healthcare --dry-run=client -o yaml | kubectl apply -f -
kubectl create namespace automotive --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Namespaces ready"
echo ""

# Setup prerequisites
echo "🔧 Setting up prerequisites..."
./scripts/setup-simulation-prereqs.sh

echo ""
echo "📋 Deploying workloads..."

# Deploy simulations (using local versions with nginx placeholders)
kubectl apply -f simulations/finance/payment-service-local.yaml
kubectl apply -f simulations/healthcare/emr-api-local.yaml
kubectl apply -f simulations/automotive/telemetry-collector-local.yaml

echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=payment-service -n finance --timeout=60s || true
kubectl wait --for=condition=ready pod -l app=emr-api -n healthcare --timeout=60s || true
kubectl wait --for=condition=ready pod -l app=telemetry-collector -n automotive --timeout=60s || true

echo ""
echo "✅ Deployments complete!"
echo ""
echo "📊 Status:"
kubectl get pods -n finance
echo ""
kubectl get pods -n healthcare
echo ""
kubectl get pods -n automotive

