#!/usr/bin/env bash
# Generate Grafana dashboards for all 19 industries

set -e

namespaces=(
  finance healthcare automotive retail logistics energy telecom
  banking insurance manufacturing gov education cloud media aiplatform
  semiconductor aicloud gpucloud socialmedia
)

DASHBOARD_DIR="grafana/dashboards"
TEMPLATE_FILE="grafana/dashboards/industry-template.json"

echo "📊 Generating Grafana dashboards for all 19 industries..."
echo ""

mkdir -p "$DASHBOARD_DIR/generated"

for ns in "${namespaces[@]}"; do
  echo "  Generating dashboard for: $ns"
  
  # Simple template replacement (in production, use jq or proper templating)
  sed "s/{{INDUSTRY}}/$ns/g" "$TEMPLATE_FILE" > "$DASHBOARD_DIR/generated/${ns}-dashboard.json"
  
  echo "    ✅ Created: $DASHBOARD_DIR/generated/${ns}-dashboard.json"
done

echo ""
echo "✅ All dashboards generated!"
echo ""
echo "📁 Dashboards location: $DASHBOARD_DIR/generated/"
echo ""
echo "To import into Grafana:"
echo "  1. Open Grafana UI"
echo "  2. Go to Dashboards > Import"
echo "  3. Upload each JSON file from $DASHBOARD_DIR/generated/"

