# 🌐 AI DevOps Brain - Web UI Guide

## Overview

The AI DevOps Brain Web UI is a fully functional Streamlit-based dashboard that provides real-time monitoring, incident management, and RCA visualization for all 19 industries.

## 🚀 Quick Start

### Local Development

```bash
# Start the UI
./scripts/start-ui.sh

# Or manually
cd ai-operator/ui
./run.sh
```

The UI will be available at: **http://localhost:8504**

### Kubernetes Deployment

```bash
# Build and deploy
docker build -t ai-operator-ui:latest -f ai-operator/ui/Dockerfile ai-operator/ui/
kubectl apply -f ai-operator/ui/k8s/deployment.yaml

# Port forward
kubectl port-forward svc/ai-operator-ui 8504:8504
```

## 📊 Features

### 1. Real-Time Dashboard

- **Top Metrics**: Total incidents, last 24h, high severity, open incidents, average confidence
- **Interactive Charts**: 
  - Incidents by severity (pie chart)
  - Incidents by namespace (bar chart)
- **Auto-refresh**: Data updates automatically

### 2. Incident Management

- **Table View**: Sortable, filterable incident table
- **Card View**: Visual incident cards with color-coded severity
- **Detailed View**: Full incident details with structured data

### 3. Filters & Search

- **Namespace Filter**: Filter by any of 19 industries
- **Severity Filter**: High, medium, low
- **Status Filter**: Open, resolved, investigating
- **Limit Control**: Adjust number of incidents displayed

### 4. Incident Details

- **Basic Information**: ID, namespace, service, severity, type, status
- **Structured Data**: JSON view of confidence, signals, patterns, actions
- **Root Cause Analysis**: Human-readable RCA summary
- **Remediation**: Suggested remediation actions
- **Suggested Actions**: Structured action list with confidence scores

### 5. Visualizations

- **Severity Distribution**: Pie chart showing incident severity breakdown
- **Namespace Heatmap**: Bar chart showing incidents per namespace
- **Confidence Scores**: Color-coded confidence indicators

## 🎨 UI Components

### Header
- Main title: "🧠 AI DevOps Brain - Enterprise Dashboard"
- Professional styling with custom CSS

### Sidebar
- Filters (namespace, severity, status)
- Refresh button
- Quick links to Grafana, Minikube, Kubernetes API

### Main Area
- Top metrics row (5 key metrics)
- Charts row (2 visualizations)
- Incidents table/cards
- Detailed incident view

## 📱 Usage Examples

### View All Incidents

1. Open http://localhost:8504
2. All incidents are displayed by default
3. Use filters to narrow down

### Filter by Namespace

1. Select namespace from sidebar dropdown
2. Table updates automatically
3. Charts reflect filtered data

### View Incident Details

1. Select an incident from the dropdown
2. View basic information, structured data, RCA, and remediation
3. Expand suggested actions to see full details

### Monitor Real-Time

1. Keep UI open
2. Click "🔄 Refresh Data" to update
3. Or wait for auto-refresh (Streamlit auto-refreshes on file changes)

## 🔧 Configuration

### Environment Variables

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5433
export POSTGRES_DB=devops_brain
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=postgres
```

### Customization

Edit `ai-operator/ui/app.py` to:
- Change color schemes
- Add new visualizations
- Modify filters
- Add new metrics

## 🐳 Docker Deployment

### Build Image

```bash
docker build -t ai-operator-ui:latest -f ai-operator/ui/Dockerfile ai-operator/ui/
```

### Run Container

```bash
docker run -d \
  -p 8504:8504 \
  -e POSTGRES_HOST=host.docker.internal \
  -e POSTGRES_PORT=5433 \
  -e POSTGRES_DB=devops_brain \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  ai-operator-ui:latest
```

## ☸️ Kubernetes Deployment

### Deploy

```bash
kubectl apply -f ai-operator/ui/k8s/deployment.yaml
```

### Access

```bash
# Port forward
kubectl port-forward svc/ai-operator-ui 8504:8504

# Or via ingress (if configured)
# http://ai-operator-ui.local
```

## 📊 Data Flow

```
PostgreSQL Database
    ↓
Streamlit App (app.py)
    ↓
UI Components
    ├── Metrics
    ├── Charts
    ├── Incident Table
    └── Detail View
```

## 🎯 Integration Points

### With AI Operator

- Reads from same PostgreSQL database
- Shows incidents created by operator
- Displays structured data from operator

### With Grafana

- Quick link in sidebar
- Can embed Grafana panels (future enhancement)
- Complementary visualization tool

### With Demo Scenario

- Run `./scripts/run-demo-scenario.sh`
- UI automatically shows new incidents
- Real-time validation of end-to-end flow

## 🔍 Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Test connection
psql -h localhost -p 5433 -U postgres -d devops_brain -c "SELECT 1"
```

### No Incidents Showing

```bash
# Generate incidents
./scripts/run-demo-scenario.sh

# Or manually
./scripts/chaos-advanced.sh finance cpu
```

### UI Not Loading

```bash
# Check Streamlit is running
ps aux | grep streamlit

# Check port
lsof -i :8504

# Restart
./scripts/start-ui.sh
```

## 🚀 Next Steps

### Enhancements

1. **Real-time Updates**: WebSocket for live incident streaming
2. **Alerting**: Visual alerts for high-severity incidents
3. **Export**: Export incidents to CSV/JSON
4. **Search**: Full-text search across incidents
5. **Timeline**: Visual timeline of incident events
6. **Grafana Embedding**: Embed Grafana panels directly
7. **Multi-user**: Authentication and user management
8. **Mobile**: Responsive design for mobile devices

## 📚 Files

- `ai-operator/ui/app.py` - Main Streamlit application
- `ai-operator/ui/requirements.txt` - Python dependencies
- `ai-operator/ui/run.sh` - Local run script
- `ai-operator/ui/Dockerfile` - Docker image
- `ai-operator/ui/k8s/deployment.yaml` - Kubernetes deployment
- `scripts/start-ui.sh` - Quick start script

## 🎊 Summary

The Web UI provides:
- ✅ Real-time incident monitoring
- ✅ Interactive visualizations
- ✅ Detailed incident analysis
- ✅ Structured data viewing
- ✅ Professional enterprise-grade interface

**Status**: 🚀 **PRODUCTION-READY**

