# 🚨 Alerts Configuration - Complete Guide

## ✅ What's Configured

### Alert Rules (Prometheus)

#### CPU Alerts
- **HighCPUUsage**: CPU > 80% for 5 minutes (Warning)
- **CriticalCPUUsage**: CPU > 95% for 2 minutes (Critical)
- **NodeCPUThrottling**: CPU throttling detected (Warning)

#### Memory Alerts
- **HighMemoryUsage**: Memory > 85% of limit for 5 minutes (Warning)
- **CriticalMemoryUsage**: Memory > 95% of limit for 2 minutes (Critical)
- **MemoryPressure**: Namespace memory > 90% for 10 minutes (Warning)

#### Pod Failure Alerts
- **PodCrashLooping**: Pod restarting continuously (Critical)
- **PodNotReady**: Pod not in Running state for 10 minutes (Warning)
- **PodFailed**: Pod in Failed state for 5 minutes (Critical)
- **ExcessivePodRestarts**: > 5 restarts in 1 hour (Warning)

#### Deployment Alerts
- **DeploymentReplicasMismatch**: Replica count mismatch for 10 minutes (Warning)

#### Node Alerts
- **NodeHighCPU**: Node CPU > 80% for 5 minutes (Warning)
- **NodeHighMemory**: Node memory > 85% for 5 minutes (Warning)

#### Application Alerts
- **HighErrorRate**: Error rate > 5% for 5 minutes (Warning)
- **HighLatency**: P95 latency > 1s for 5 minutes (Warning)

---

## 🚀 Quick Start

### 1. Deploy Alerts
```bash
./scripts/configure-alerts.sh
```

This will:
- Apply Prometheus alert rules
- Configure Alertmanager
- Restart Alertmanager to pick up config

### 2. View Alerts

**Prometheus UI**:
```bash
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
# Open: http://localhost:9090/alerts
```

**Alertmanager UI**:
```bash
kubectl port-forward svc/alertmanager-main -n monitoring 9093:9093
# Open: http://localhost:9093
```

### 3. Test Alerts

**Generate High CPU**:
```bash
# Generate traffic to trigger high CPU
./scripts/load-traffic-all.sh 600 1

# Or inject CPU stress
./scripts/chaos-cpu-stress.sh <namespace>
```

**Trigger Pod Failures**:
```bash
# Kill pods to trigger failure alerts
./scripts/chaos-random-all.sh kill
```

---

## ⚙️ Alert Configuration

### Alert Rules Location
`k8s/observability/prometheus-alerts.yaml`

### Alertmanager Config Location
`k8s/observability/alertmanager-config.yaml`

### Alert Routing

Alerts are routed based on:
- **Severity**: Critical vs Warning
- **Component**: CPU, Memory, Pod, etc.
- **Namespace**: Industry-specific

**Routing Rules**:
- **Critical alerts**: Immediate notification, 1h repeat
- **Warning alerts**: 30s group wait, 6h repeat
- **Component-specific**: Grouped by namespace and severity

### Alert Inhibition

Lower severity alerts are suppressed when higher severity fires:
- Warning CPU suppressed when Critical CPU fires
- Warning Memory suppressed when Critical Memory fires

---

## 📊 Alert Monitoring

### View Active Alerts

1. **Prometheus**:
   - Go to Alerts tab
   - See all configured alerts and their states
   - Click alert name for details

2. **Alertmanager**:
   - See grouped alerts
   - View alert history
   - Silence alerts if needed

3. **Grafana**:
   - Alerts visible in dashboards
   - Configure alert notifications

### Alert States

- **Inactive**: Alert condition not met
- **Pending**: Alert condition met, waiting for `for` duration
- **Firing**: Alert active and sending notifications
- **Resolved**: Alert condition no longer met

---

## 🔔 Notification Configuration

### Current Setup

Alerts are sent to:
- **AI Operator webhook**: `http://ai-operator.monitoring.svc.cluster.local:8080/alerts`
- **Default receiver**: All alerts

### Adding Slack Notifications

1. **Get Slack Webhook URL**:
   - Go to Slack App settings
   - Create Incoming Webhook
   - Copy webhook URL

2. **Update Alertmanager Config**:
   ```yaml
   # In k8s/observability/alertmanager-config.yaml
   global:
     slack_api_url: 'YOUR_SLACK_WEBHOOK_URL'
   
   receivers:
     - name: 'critical-alerts'
       slack_configs:
         - channel: '#alerts-critical'
           title: '🚨 Critical Alert'
           text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
   ```

3. **Apply Configuration**:
   ```bash
   kubectl apply -f k8s/observability/alertmanager-config.yaml
   kubectl rollout restart deployment/alertmanager-main -n monitoring
   ```

### Adding Email Notifications

1. **Update Alertmanager Config**:
   ```yaml
   global:
     smtp_smarthost: 'smtp.gmail.com:587'
     smtp_from: 'alerts@yourdomain.com'
     smtp_auth_username: 'your-email@gmail.com'
     smtp_auth_password: 'your-app-password'
   
   receivers:
     - name: 'critical-alerts'
       email_configs:
         - to: 'oncall@yourdomain.com'
           subject: '🚨 Critical Alert: {{ .GroupLabels.alertname }}'
   ```

### Adding PagerDuty

1. **Get PagerDuty Integration Key**
2. **Update Alertmanager Config**:
   ```yaml
   receivers:
     - name: 'critical-alerts'
       pagerduty_configs:
         - service_key: 'YOUR_PAGERDUTY_KEY'
   ```

---

## 🧪 Testing Alerts

### Test High CPU Alert

```bash
# Generate high CPU load
./scripts/load-traffic-all.sh 600 1

# Or stress specific namespace
./scripts/chaos-cpu-stress.sh finance

# Wait 2-5 minutes, then check alerts
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
# Open: http://localhost:9090/alerts
```

### Test Pod Failure Alert

```bash
# Kill pods to trigger failures
./scripts/chaos-random-all.sh kill

# Wait 5 minutes, then check alerts
kubectl port-forward svc/alertmanager-main -n monitoring 9093:9093
# Open: http://localhost:9093
```

### Test Memory Alert

```bash
# Generate memory pressure
# (Would need memory stress script or high-memory workload)
# Then check alerts after 5 minutes
```

---

## 📚 Runbook

Complete runbook with remediation procedures:
`docs/RUNBOOK.md`

Includes:
- Investigation steps for each alert
- Remediation procedures
- Prevention strategies
- Common causes and fixes

---

## 🔧 Customization

### Modifying Alert Thresholds

Edit `k8s/observability/prometheus-alerts.yaml`:

```yaml
- alert: HighCPUUsage
  expr: |
    sum(rate(container_cpu_usage_seconds_total{...}[5m])) > 0.8  # Change 0.8 to your threshold
  for: 5m  # Change duration
```

Then apply:
```bash
kubectl apply -f k8s/observability/prometheus-alerts.yaml
```

### Adding New Alerts

1. Add new rule to `prometheus-alerts.yaml`
2. Apply configuration
3. Update runbook with remediation steps

### Industry-Specific Alerts

To add alerts for specific industries, modify the namespace filter:

```yaml
expr: |
  sum(...) by (namespace, pod) > 0.8
  # Add: and namespace="finance" for finance-specific alerts
```

---

## ✅ Summary

**Status**: ✅ **Alerts Fully Configured**

You now have:
- ✅ 15+ alert rules covering CPU, Memory, Pod failures
- ✅ Alertmanager routing and grouping
- ✅ Alert inhibition rules
- ✅ Webhook integration with AI Operator
- ✅ Complete runbook for remediation
- ✅ Easy customization and testing

**Next Steps**:
1. Test alerts by generating load
2. Configure Slack/Email notifications (optional)
3. Review and adjust thresholds as needed
4. Train team on runbook procedures

---

**Files Created**:
- `k8s/observability/prometheus-alerts.yaml` - Alert rules
- `k8s/observability/alertmanager-config.yaml` - Alertmanager config
- `scripts/configure-alerts.sh` - Setup script
- `docs/RUNBOOK.md` - Complete runbook

