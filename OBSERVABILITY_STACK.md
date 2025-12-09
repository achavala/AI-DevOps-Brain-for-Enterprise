# 📊 Observability Stack - Complete Deployment Guide

## ✅ What's Included

### Components
1. **Prometheus** - Metrics collection and storage
2. **Grafana** - Visualization and dashboards
3. **Loki** - Log aggregation
4. **FluentBit** - Log collection (DaemonSet)
5. **KEDA** - Kubernetes Event-Driven Autoscaling

### Features
- ✅ **19 Industry Dashboards** - One per industry
- ✅ **Overview Dashboard** - Cross-industry metrics
- ✅ **ServiceMonitors** - Auto-discovery of metrics
- ✅ **PodMonitors** - Pod-level metrics
- ✅ **Loki Integration** - Logs in Grafana
- ✅ **Local Storage** - All data stored locally

---

## 🚀 Quick Start

### 1. Deploy Observability Stack
```bash
./scripts/deploy-observability-stack.sh
```

This will:
- Create namespaces (monitoring, logging, keda)
- Install Prometheus + Grafana via Helm
- Install Loki via Helm
- Deploy FluentBit DaemonSet
- Install KEDA
- Configure Grafana datasources
- Import all 19 industry dashboards

### 2. Access Grafana
```bash
# Get Grafana URL
kubectl get svc prometheus-grafana -n monitoring

# Port forward
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80

# Or use Minikube service
minikube service prometheus-grafana -n monitoring
```

**Credentials:**
- Username: `admin`
- Password: `admin`

### 3. Access Prometheus
```bash
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
```

Then open: http://localhost:9090

### 4. Access Loki
```bash
kubectl port-forward svc/loki -n logging 3100:3100
```

Then open: http://localhost:3100

---

## 📊 Dashboards

### Industry Dashboards (19)
Each industry has its own dashboard with:
- Pod status
- CPU usage
- Memory usage
- Pod restarts
- Request rate
- Error rate

**Industries:**
- finance, healthcare, automotive, retail, logistics
- energy, telecom, banking, insurance, manufacturing
- gov, education, cloud, media, aiplatform
- semiconductor, aicloud, gpucloud, socialmedia

### Overview Dashboard
Cross-industry view showing:
- Total pods across all industries
- CPU usage by industry
- Memory usage by industry
- Pod restarts by industry
- Error rate by industry
- Request rate by industry

---

## 🔧 Configuration

### Prometheus
- **Retention**: 7 days
- **Storage**: 10Gi
- **Scrape Interval**: 30s
- **ServiceMonitors**: Auto-discover all services with `prometheus.io/scrape: "true"`

### Grafana
- **Storage**: 5Gi (persistent)
- **Datasources**: 
  - Prometheus (default)
  - Loki
- **Dashboards**: Auto-imported on deployment

### Loki
- **Retention**: 7 days (168h)
- **Storage**: 10Gi
- **Labels**: namespace, pod_name, container_name

### FluentBit
- **Collection**: All container logs
- **Output**: 
  - Local filesystem (`./local-data/logs`)
  - Loki (for querying in Grafana)
- **Labels**: namespace, pod, container

### KEDA
- **Purpose**: Event-driven autoscaling
- **Scalers**: CPU, Memory, Kafka, Prometheus metrics

---

## 📈 Metrics Collected

### Kubernetes Metrics
- Pod status and count
- Container CPU usage
- Container memory usage
- Pod restarts
- Node metrics

### Application Metrics
- HTTP request rate
- HTTP error rate
- Response latency
- Custom application metrics

### Logs
- All container logs
- System logs (kubelet)
- Application logs

---

## 🧪 Testing

### 1. Generate Traffic
```bash
./scripts/load-traffic-all.sh 300 2
```

### 2. Check Metrics in Prometheus
```bash
# Port forward Prometheus
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090

# Query examples:
# - Total pods: count(kube_pod_info)
# - CPU usage: sum(rate(container_cpu_usage_seconds_total[5m]))
# - Memory usage: sum(container_memory_working_set_bytes)
```

### 3. Check Logs in Loki
```bash
# Port forward Loki
kubectl port-forward svc/loki -n logging 3100:3100

# Query in Grafana:
# - All logs: {job="fluent-bit"}
# - By namespace: {job="fluent-bit", namespace="finance"}
# - By pod: {job="fluent-bit", pod="finance-sim-xxx"}
```

### 4. View Dashboards
1. Open Grafana: http://localhost:3000
2. Go to Dashboards
3. Select any industry dashboard
4. Verify metrics are showing

---

## 🔍 Troubleshooting

### Prometheus Not Scraping
```bash
# Check ServiceMonitors
kubectl get servicemonitors -n monitoring

# Check Prometheus targets
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
# Then: http://localhost:9090/targets
```

### FluentBit Not Collecting Logs
```bash
# Check FluentBit pods
kubectl get pods -n logging -l app=fluent-bit

# Check FluentBit logs
kubectl logs -n logging -l app=fluent-bit --tail=50

# Check config
kubectl get configmap fluent-bit-config-local -n logging -o yaml
```

### Grafana Not Showing Data
```bash
# Check Grafana datasources
kubectl port-forward svc/prometheus-grafana -n monitoring 3000:80
# Then: http://localhost:3000/datasources

# Check Prometheus connection
# Test query: up
```

### Loki Not Receiving Logs
```bash
# Check Loki pods
kubectl get pods -n logging -l app=loki

# Check Loki logs
kubectl logs -n logging -l app=loki --tail=50

# Check FluentBit output
kubectl logs -n logging -l app=fluent-bit | grep loki
```

---

## 📊 Resource Usage

### Expected Resource Consumption
- **Prometheus**: ~500Mi memory, ~500m CPU
- **Grafana**: ~200Mi memory, ~200m CPU
- **Loki**: ~300Mi memory, ~300m CPU
- **FluentBit**: ~100Mi memory per node, ~100m CPU per node
- **KEDA**: ~100Mi memory, ~100m CPU

**Total**: ~1.2Gi memory, ~1.2 CPU cores

---

## 🎯 Next Steps

### 1. Custom Dashboards
Create custom dashboards for specific use cases:
- Incident correlation
- Cost metrics
- Performance baselines

### 2. Alerts
Configure Prometheus alerts:
- High CPU usage
- High memory usage
- Pod failures
- Error rate spikes

### 3. Long-term Storage
For production, consider:
- Thanos (long-term metrics storage)
- S3 backend for Loki
- Metrics retention policies

---

## ✅ Summary

**Status**: ✅ **Observability Stack Complete**

You now have:
- ✅ Prometheus collecting metrics
- ✅ Grafana visualizing data
- ✅ Loki aggregating logs
- ✅ FluentBit collecting logs
- ✅ KEDA for autoscaling
- ✅ 19 industry dashboards
- ✅ Overview dashboard

**Access:**
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- Loki: http://localhost:3100

**Next**: Configure alerts and custom dashboards!

