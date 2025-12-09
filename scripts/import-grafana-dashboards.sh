#!/bin/bash
# Import Grafana dashboards for all 19 industries

set -e

GRAFANA_NAMESPACE="monitoring"
GRAFANA_SERVICE="prometheus-grafana"
GRAFANA_USER="admin"
GRAFANA_PASSWORD="admin"

echo "📊 Importing Grafana dashboards..."
echo ""

# Wait for Grafana to be ready
echo "⏳ Waiting for Grafana to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n ${GRAFANA_NAMESPACE} --timeout=300s || true
sleep 10  # Give Grafana time to fully start

# Get Grafana URL
GRAFANA_URL=$(kubectl get svc ${GRAFANA_SERVICE} -n ${GRAFANA_NAMESPACE} -o jsonpath='{.spec.clusterIP}' 2>/dev/null || echo "")
if [ -z "$GRAFANA_URL" ]; then
    echo "❌ Could not find Grafana service"
    exit 1
fi

# Port forward Grafana
echo "🔗 Setting up port forward to Grafana..."
kubectl port-forward svc/${GRAFANA_SERVICE} -n ${GRAFANA_NAMESPACE} 3000:80 > /dev/null 2>&1 &
PORT_FORWARD_PID=$!
sleep 5

# Function to import dashboard
import_dashboard() {
    local dashboard_file=$1
    local dashboard_name=$(basename "$dashboard_file" .json)
    
    if [ ! -f "$dashboard_file" ]; then
        echo "⚠️  Dashboard file not found: $dashboard_file"
        return
    fi
    
    echo "  Importing: $dashboard_name"
    
    # Create dashboard payload
    DASHBOARD_JSON=$(cat "$dashboard_file")
    
    # Import via Grafana API
    RESPONSE=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Accept: application/json" \
        -u "${GRAFANA_USER}:${GRAFANA_PASSWORD}" \
        -d "{\"dashboard\":${DASHBOARD_JSON},\"overwrite\":true}" \
        "http://localhost:3000/api/dashboards/db" 2>/dev/null)
    
    if echo "$RESPONSE" | grep -q '"status":"success"'; then
        echo "    ✅ Imported successfully"
    else
        echo "    ⚠️  Import may have failed (check Grafana UI)"
    fi
}

# Import industry dashboards
INDUSTRIES=(
    "finance" "healthcare" "automotive" "retail" "logistics"
    "energy" "telecom" "banking" "insurance" "manufacturing"
    "gov" "education" "cloud" "media" "aiplatform"
    "semiconductor" "aicloud" "gpucloud" "socialmedia"
)

DASHBOARD_DIR="grafana/dashboards/generated"

# Generate dashboards if they don't exist
if [ ! -d "$DASHBOARD_DIR" ] || [ -z "$(ls -A $DASHBOARD_DIR 2>/dev/null)" ]; then
    echo "📝 Generating dashboards..."
    ./scripts/generate-dashboards.sh
fi

# Import each industry dashboard
for industry in "${INDUSTRIES[@]}"; do
    dashboard_file="${DASHBOARD_DIR}/${industry}-dashboard.json"
    import_dashboard "$dashboard_file"
done

# Import overview dashboard if it exists
if [ -f "${DASHBOARD_DIR}/overview-dashboard.json" ]; then
    echo "  Importing: Overview Dashboard"
    import_dashboard "${DASHBOARD_DIR}/overview-dashboard.json"
fi

# Cleanup port forward
kill $PORT_FORWARD_PID 2>/dev/null || true

echo ""
echo "✅ Dashboard import complete!"
echo ""
echo "Access Grafana at: http://localhost:3000 (admin/admin)"
echo "All 19 industry dashboards should now be available"
echo ""

