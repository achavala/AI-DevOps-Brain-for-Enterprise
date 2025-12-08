#!/bin/bash
# Setup prerequisites for industry simulations

set -e

echo "🔧 Setting up simulation prerequisites..."
echo ""

# Create secrets for database connections
echo "📝 Creating database secrets..."

# Finance namespace
kubectl create secret generic finance-db-secret \
  --from-literal=url="postgresql://postgres:postgres@postgres-finance:5432/finance" \
  --namespace=finance \
  --dry-run=client -o yaml | kubectl apply -f -

# Healthcare namespace
kubectl create secret generic healthcare-db-secret \
  --from-literal=url="postgresql://postgres:postgres@postgres-finance:5432/healthcare" \
  --namespace=healthcare \
  --dry-run=client -o yaml | kubectl apply -f -

echo "✅ Secrets created"
echo ""

# Note: The actual deployments will fail if the Docker images don't exist
# For local testing, you can use simple placeholder images or build mock images
echo "⚠️  Note: Deployments reference custom images that may not exist:"
echo "   - payment-service:latest"
echo "   - emr-api:latest"
echo "   - telemetry-collector:latest"
echo ""
echo "For local testing, you may want to:"
echo "  1. Use placeholder images (nginx, httpd)"
echo "  2. Build mock images"
echo "  3. Use imagePullPolicy: IfNotPresent or Never"
echo ""

echo "✅ Prerequisites setup complete"

