# 🔧 Quick Fixes - Common Issues

## Issue 1: Permission Denied on Scripts

**Error**: `zsh: permission denied: ./scripts/configure-alerts.sh`

**Fix**:
```bash
chmod +x scripts/*.sh
```

**Or run**:
```bash
./scripts/fix-dependencies.sh
```

---

## Issue 2: Missing Kubernetes Module

**Error**: `ModuleNotFoundError: No module named 'kubernetes'`

**Fix**:
```bash
# Activate virtual environment
source ai-models/venv/bin/activate  # or source venv/bin/activate

# Install dependencies
pip install kubernetes psycopg2-binary redis kafka-python

# Or use the fix script
./scripts/fix-dependencies.sh
```

---

## Issue 3: Helm Installation Cancelled

**Error**: `Release prometheus has been cancelled`

**Fix**:
```bash
# Retry the deployment
./scripts/deploy-observability-stack.sh

# If it fails, check what's already installed
kubectl get pods -n monitoring
kubectl get pods -n logging

# Clean up if needed
helm uninstall prometheus -n monitoring
helm uninstall loki -n logging
```

---

## Issue 4: Prometheus/Grafana Not Starting

**Check**:
```bash
# Check pod status
kubectl get pods -n monitoring
kubectl describe pod <pod-name> -n monitoring

# Check logs
kubectl logs <pod-name> -n monitoring

# Check resources
kubectl top nodes
kubectl top pods -n monitoring
```

**Common causes**:
- Insufficient memory (Minikube needs at least 8GB)
- Port conflicts
- Storage issues

**Fix**:
```bash
# Increase Minikube memory
minikube stop
minikube start --memory=8192 --cpus=4

# Or reduce resource requests in Helm values
```

---

## Issue 5: FluentBit Not Collecting Logs

**Check**:
```bash
kubectl get pods -n logging -l app=fluent-bit
kubectl logs -n logging -l app=fluent-bit --tail=50
```

**Fix**:
```bash
# Restart FluentBit
kubectl rollout restart daemonset/fluent-bit -n logging

# Check config
kubectl get configmap fluent-bit-config-local -n logging -o yaml
```

---

## Issue 6: Alerts Not Firing

**Check**:
```bash
# Check Prometheus rules
kubectl get prometheusrule -n monitoring

# Check Alertmanager
kubectl get pods -n monitoring -l app=alertmanager
kubectl logs -n monitoring -l app=alertmanager

# Port forward and check UI
kubectl port-forward svc/prometheus-kube-prometheus-prometheus -n monitoring 9090:9090
# Open: http://localhost:9090/alerts
```

**Fix**:
```bash
# Re-apply alert rules
kubectl apply -f k8s/observability/prometheus-alerts.yaml

# Restart Prometheus
kubectl rollout restart deployment/prometheus-operator -n monitoring
```

---

## Issue 7: AI Operator Not Starting

**Error**: `ModuleNotFoundError: No module named 'kubernetes'`

**Fix**:
```bash
# Install in correct virtual environment
cd ai-operator
source ../ai-models/venv/bin/activate  # or your venv
pip install -r requirements.txt

# Or use fix script
./scripts/fix-dependencies.sh
```

---

## Issue 8: Database Connection Errors

**Error**: `connection refused` or `password authentication failed`

**Check**:
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check port
docker ps | grep postgres | grep -o '0.0.0.0:[0-9]*'

# Test connection
psql -h localhost -p 5433 -U postgres -d devops_brain
```

**Fix**:
```bash
# Restart PostgreSQL
./scripts/setup-local-services.sh

# Or check config
cat config/local.yaml | grep -A 5 database
```

---

## Issue 9: Port Conflicts

**Error**: `port already in use`

**Check**:
```bash
# Check what's using the port
lsof -i :8504  # For Streamlit UI
lsof -i :9090  # For Prometheus
lsof -i :3000  # For Grafana
```

**Fix**:
```bash
# Kill the process
kill -9 <PID>

# Or use different port
export STREAMLIT_PORT=8505
```

---

## Issue 10: Minikube Resource Issues

**Error**: `Insufficient memory` or pods pending

**Fix**:
```bash
# Check Minikube resources
minikube status

# Increase resources
minikube stop
minikube start --memory=8192 --cpus=4

# Or reduce workload
./scripts/optimize-for-minikube.sh
```

---

## 🚀 Quick Fix Script

Run this to fix common issues:

```bash
./scripts/fix-dependencies.sh
```

This will:
- Fix script permissions
- Install missing Python packages
- Verify installations

---

## 📞 Still Having Issues?

1. **Check logs**:
   ```bash
   kubectl logs <pod-name> -n <namespace>
   ```

2. **Check events**:
   ```bash
   kubectl get events -n <namespace> --sort-by='.lastTimestamp'
   ```

3. **Check resource usage**:
   ```bash
   kubectl top nodes
   kubectl top pods -A
   ```

4. **Restart services**:
   ```bash
   ./scripts/stop-local.sh
   ./scripts/start-local.sh
   ```

---

**Last Updated**: December 8, 2024

