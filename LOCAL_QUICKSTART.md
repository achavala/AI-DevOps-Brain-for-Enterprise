# 🏠 Local Quick Start - Complete Setup in 10 Minutes

Run AI DevOps Brain **entirely locally** - no AWS needed!

---

## ✅ Prerequisites Check

```bash
# Check Docker
docker --version

# Check kubectl
kubectl version --client

# Check Python (already done ✅)
python3 --version
```

---

## 🚀 Setup Steps

### Step 1: Install Local Kubernetes (2 min)

**Option A: Minikube (Recommended)**

```bash
# Install
brew install minikube

# Start
minikube start --driver=docker

# Verify
kubectl get nodes
```

**Option B: Kind**

```bash
# Install
brew install kind

# Create cluster
kind create cluster --name ai-devops-brain

# Verify
kubectl get nodes
```

---

### Step 2: Install Helm (1 min)

```bash
brew install helm
# Or run:
./scripts/install-prerequisites.sh
```

---

### Step 3: Start Local Services (2 min)

```bash
./scripts/setup-local-services.sh
```

This starts:
- ✅ PostgreSQL (port 5432)
- ✅ Redis (port 6379)
- ✅ Kafka (port 9092)
- ✅ MinIO/S3 (ports 9000, 9001)

**Wait 30 seconds** for services to be ready.

---

### Step 4: Deploy Platform Components (3 min)

```bash
./scripts/deploy-platform-local.sh
```

This deploys:
- ✅ ArgoCD
- ✅ Prometheus + Grafana
- ✅ Loki
- ✅ FluentBit
- ✅ KEDA

**Wait 2-3 minutes** for everything to start.

---

### Step 5: Deploy Sample Workloads (1 min)

```bash
# Create namespaces
kubectl create namespace finance
kubectl create namespace healthcare
kubectl create namespace automotive

# Deploy workloads
kubectl apply -f simulations/finance/payment-service.yaml
kubectl apply -f simulations/healthcare/emr-api.yaml
kubectl apply -f simulations/automotive/telemetry-collector.yaml
```

---

### Step 6: Test AI Models (1 min)

```bash
cd ai-models
source venv/bin/activate

# Test anomaly detection
python anomaly-detection/train_anomaly_detector.py --simulate
```

---

## 🎉 You're Done!

### Access Dashboards

**ArgoCD**:
```bash
kubectl port-forward -n argocd svc/argocd-server 8080:443
# Open: https://localhost:8080
# Password: kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
```

**Grafana**:
```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Open: http://localhost:3000
# Login: admin / prom-operator
```

**MinIO Console**:
```bash
# Open: http://localhost:9001
# Login: minioadmin / minioadmin
```

---

## 📊 Check Status

```bash
# Check all pods
kubectl get pods --all-namespaces

# Check services
kubectl get svc --all-namespaces

# Check local data
ls -lh local-data/
```

---

## 🧪 Test Everything

### 1. Generate Logs
```bash
# Watch logs
kubectl logs -f -n finance deployment/payment-service
```

### 2. Check Data Collection
```bash
# Check FluentBit logs
ls -lh local-data/logs/

# Check metrics
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Open: http://localhost:9090
```

### 3. Test Anomaly Detection
```bash
cd ai-models
source venv/bin/activate
python anomaly-detection/train_anomaly_detector.py --simulate
```

---

## 🛑 Stop Everything

```bash
# Stop Kubernetes
minikube stop
# Or: kind delete cluster --name ai-devops-brain

# Stop Docker services
docker stop postgres-finance redis-finance kafka-finance zookeeper-finance minio
```

---

## 💰 Cost

**Total Cost: $0** ✅

Everything runs locally on your machine!

---

## 📁 Data Location

All data is stored locally:
- Logs: `./local-data/logs/`
- Metrics: `./local-data/metrics/`
- Events: `./local-data/events/`
- Models: `./ai-models/models/`

---

## 🎯 Next Steps

1. ✅ **Test anomaly detection** with real cluster data
2. ✅ **Run chaos experiments** (Chaos Mesh)
3. ✅ **Test RCA engine** with collected data
4. ✅ **Validate auto-fix** engine
5. ✅ **When ready, migrate to AWS** (optional)

---

**You now have a complete local AI DevOps Brain setup! 🎉**

