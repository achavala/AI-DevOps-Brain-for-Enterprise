# 🖥️ Day-to-Day Usage Guide

How to use your local AI DevOps Brain environment for daily work.

---

## 🚀 Quick Start (Every Time You Work)

### Morning: Start Everything

```bash
# One command to start everything
./scripts/start-local.sh
```

This will:
- ✅ Start Minikube
- ✅ Start all Docker services (PostgreSQL, Redis, Kafka, MinIO)
- ✅ Deploy platform components
- ✅ Run smoke tests
- ✅ Show you access URLs

**Time**: ~3-5 minutes

---

## 📊 Access Dashboards

### Minikube Dashboard
```bash
minikube dashboard
```
Opens Kubernetes dashboard in browser.

### Grafana
```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```
Then open: http://localhost:3000
- Username: `admin`
- Password: `prom-operator`

### ArgoCD
```bash
kubectl port-forward -n argocd svc/argocd-server 8080:443
```
Then open: https://localhost:8080
- Username: `admin`
- Password: `kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d`

### MinIO Console
Open: http://localhost:9001
- Username: `minioadmin`
- Password: `minioadmin`

---

## 🧪 Daily Workflow

### 1. Check Status
```bash
# Quick health check
./scripts/smoke-test-local.sh

# Or manually
kubectl get pods --all-namespaces
docker ps
```

### 2. Work on AI Models
```bash
cd ai-models
source venv/bin/activate

# Train models
python anomaly-detection/train_anomaly_detector.py --simulate

# Test RCA engine
python rca-engine/rca_engine.py data/sample_logs.csv ...

# Test auto-fix
python auto-fix/auto_fix_engine.py --local
```

### 3. Test Trading Integration
```bash
# Use local config
export APP_PROFILE=local

# Run your trading code
python your_trading_app.py

# All data goes to local PostgreSQL, Redis, Kafka
```

### 4. View Logs
```bash
# Kubernetes logs
kubectl logs -f -n finance deployment/payment-service

# Local data logs
tail -f local-data/logs/fluent-bit-*.log

# Docker service logs
docker logs -f postgres-finance
docker logs -f redis-finance
```

---

## 🛑 End of Day: Stop Everything

```bash
# Clean shutdown
./scripts/stop-local.sh
```

This stops:
- ✅ Minikube
- ✅ All Docker services

**Data is preserved** - you can start again tomorrow.

---

## ⚡ Lightweight Mode (For Everyday Use)

If the full stack is too heavy for your laptop:

```bash
# Start lightweight version (skips ArgoCD, full observability)
./scripts/setup-lightweight-local.sh
```

This includes:
- ✅ Essential services (PostgreSQL, Redis, Kafka, MinIO)
- ✅ Prometheus + Grafana
- ✅ FluentBit
- ❌ ArgoCD (skipped)
- ❌ Full observability stack (skipped)

**Resource usage**: ~4GB RAM, 2 CPUs

---

## 🧹 Clean Everything (When Needed)

```bash
# Delete everything (keeps data)
./scripts/clean-local.sh

# To also delete data
rm -rf local-data/
rm -rf ai-models/models/
```

---

## 📊 Resource Management

### Check Resource Usage
```bash
# Minikube resources
minikube ssh -- df -h

# Docker resources
docker stats

# Kubernetes resources
kubectl top nodes
kubectl top pods --all-namespaces
```

### Adjust Resources
```bash
# Stop current cluster
minikube stop

# Start with more resources
minikube start --driver=docker --cpus=6 --memory=12g

# Or less resources
minikube start --driver=docker --cpus=2 --memory=4g
```

---

## 🔧 Troubleshooting

### Services Not Starting
```bash
# Check Docker
docker ps

# Check Kubernetes
kubectl get nodes
kubectl get pods --all-namespaces

# Check logs
kubectl logs <pod-name> -n <namespace>
docker logs <container-name>
```

### Out of Resources
```bash
# Use lightweight mode
./scripts/setup-lightweight-local.sh

# Or increase Minikube resources
minikube stop
minikube start --driver=docker --cpus=6 --memory=12g
```

### Port Conflicts
```bash
# Check what's using ports
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :9092  # Kafka
lsof -i :9000  # MinIO

# Stop conflicting services or change ports in config
```

---

## 📋 Quick Reference

| Task | Command |
|------|---------|
| Start everything | `./scripts/start-local.sh` |
| Stop everything | `./scripts/stop-local.sh` |
| Health check | `./scripts/smoke-test-local.sh` |
| Clean everything | `./scripts/clean-local.sh` |
| Lightweight mode | `./scripts/setup-lightweight-local.sh` |
| View logs | `kubectl logs -f <pod>` |
| Access Grafana | `kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80` |
| Access MinIO | http://localhost:9001 |

---

## 🎯 Best Practices

1. **Start fresh each day**: Run `./scripts/start-local.sh`
2. **Check health**: Run `./scripts/smoke-test-local.sh` after starting
3. **Use lightweight mode**: If full stack is too heavy
4. **Stop when done**: Run `./scripts/stop-local.sh` to save resources
5. **Clean periodically**: Run `./scripts/clean-local.sh` weekly

---

## 💡 Pro Tips

- **Keep port-forwards running**: Use `tmux` or `screen` to keep port-forwards active
- **Monitor resources**: Use `docker stats` to watch resource usage
- **Backup data**: Copy `local-data/` and `ai-models/models/` before cleaning
- **Use aliases**: Add shortcuts to your `.zshrc`:
  ```bash
  alias ai-start='./scripts/start-local.sh'
  alias ai-stop='./scripts/stop-local.sh'
  alias ai-test='./scripts/smoke-test-local.sh'
  ```

---

**You're all set for daily development work! 🎉**

