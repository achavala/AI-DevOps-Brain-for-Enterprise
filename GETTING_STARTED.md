# 🚀 Getting Started - Step by Step

Complete guide to get your local AI DevOps Brain environment running.

---

## ✅ Step 1: Start Docker Desktop

Docker is required for all local services (PostgreSQL, Redis, Kafka, MinIO).

### Option A: Automatic (Recommended)

```bash
./scripts/start-docker.sh
```

This will:
- ✅ Check if Docker is already running
- ✅ Try to start Docker Desktop automatically
- ✅ Wait for Docker to be ready
- ✅ Verify it's working

### Option B: Manual

1. **Open Docker Desktop**:
   - Press `Cmd+Space` (Spotlight)
   - Type "Docker"
   - Press Enter

2. **Wait for Docker to start**:
   - Look for whale icon in menu bar (top right)
   - Icon should be **steady** (not animated)
   - Takes 30-60 seconds

3. **Verify**:
   ```bash
   ./scripts/check-docker.sh
   ```

---

## ✅ Step 2: Start Local Environment

Once Docker is running:

```bash
./scripts/start-local.sh
```

This will:
- ✅ Check Docker is running
- ✅ Start Minikube (local Kubernetes)
- ✅ Start all services (PostgreSQL, Redis, Kafka, MinIO)
- ✅ Deploy platform components
- ✅ Run smoke tests

**Time**: ~5-10 minutes (first time)

---

## ✅ Step 3: Verify Everything Works

```bash
./scripts/trading-heartbeat.sh
```

You should see:
- ✅ PostgreSQL: OK
- ✅ Redis: OK
- ✅ Kafka: OK
- ✅ MinIO: OK
- ✅ Kubernetes: OK
- ✅ System Status: HEALTHY

---

## ✅ Step 4: Start Dashboards

```bash
./scripts/local-dashboard.sh
```

Access:
- 📊 Grafana: http://localhost:3000
- 📈 Prometheus: http://localhost:9090
- 🔄 ArgoCD: https://localhost:8080
- 📦 MinIO: http://localhost:9001

---

## 🎯 Complete Workflow

### Morning (Start Everything)
```bash
# 1. Start Docker
./scripts/start-docker.sh

# 2. Start environment
./scripts/start-local.sh

# 3. Check health
./scripts/trading-heartbeat.sh

# 4. Start dashboards
./scripts/local-dashboard.sh
```

### During Work
```bash
# Check status anytime
./scripts/trading-heartbeat.sh

# View logs
kubectl logs -f <pod-name> -n <namespace>
```

### Evening (Stop Everything)
```bash
# Stop dashboards
./scripts/stop-dashboards.sh

# Stop environment
./scripts/stop-local.sh

# (Docker can stay running)
```

---

## 🐛 Troubleshooting

### Docker Won't Start

1. **Check if Docker Desktop is installed**:
   ```bash
   ls /Applications/ | grep -i docker
   ```

2. **If not installed**:
   - Download: https://www.docker.com/products/docker-desktop
   - Install the .dmg
   - Move to Applications

3. **If installed but won't start**:
   - Quit Docker completely
   - Restart your Mac
   - Try again

### Services Not Starting

1. **Check Docker is running**:
   ```bash
   ./scripts/check-docker.sh
   ```

2. **Check Minikube**:
   ```bash
   minikube status
   ```

3. **View logs**:
   ```bash
   docker logs <container-name>
   kubectl logs <pod-name> -n <namespace>
   ```

### Out of Resources

If your Mac is slow:

1. **Use lightweight mode**:
   ```bash
   ./scripts/setup-lightweight-local.sh
   ```

2. **Increase Docker resources**:
   - Docker Desktop → Settings → Resources
   - Increase CPU and Memory

3. **Reduce Minikube resources**:
   ```bash
   minikube stop
   minikube start --driver=docker --cpus=2 --memory=4g
   ```

---

## 📋 Quick Reference

| Task | Command |
|------|---------|
| Start Docker | `./scripts/start-docker.sh` |
| Check Docker | `./scripts/check-docker.sh` |
| Start everything | `./scripts/start-local.sh` |
| Check health | `./scripts/trading-heartbeat.sh` |
| Start dashboards | `./scripts/local-dashboard.sh` |
| Stop dashboards | `./scripts/stop-dashboards.sh` |
| Stop everything | `./scripts/stop-local.sh` |

---

## ✅ Success Checklist

After completing all steps, you should have:

- [x] Docker Desktop running
- [x] Minikube cluster running
- [x] PostgreSQL, Redis, Kafka, MinIO running
- [x] Platform components deployed
- [x] All health checks passing
- [x] Dashboards accessible

---

## 🎉 You're Ready!

Once everything is running:

1. **Test AI models**:
   ```bash
   cd ai-models
   source venv/bin/activate
   python anomaly-detection/train_anomaly_detector.py --simulate
   ```

2. **Use mock broker**:
   ```python
   from integrations.mock_broker import MockBroker
   broker = MockBroker()
   ```

3. **Explore dashboards**:
   - Grafana for metrics
   - Prometheus for queries
   - MinIO for storage

---

**Start with: `./scripts/start-docker.sh` 🚀**

