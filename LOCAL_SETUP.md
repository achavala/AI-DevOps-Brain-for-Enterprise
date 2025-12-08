# 🏠 Local Setup Guide - Zero AWS, Zero Cost

Complete guide to run AI DevOps Brain **entirely locally** without any AWS resources.

---

## ✅ Benefits of Local Setup

- 💰 **Zero cost** - No AWS charges
- 🔒 **Zero risk** - No accidental cloud costs
- ⚡ **Fast iteration** - Quick testing cycles
- 🧪 **Perfect for development** - Test everything before cloud
- 📦 **Self-contained** - Everything runs on your machine

---

## 📋 Prerequisites

### Required Tools:
- ✅ Docker Desktop (for Kubernetes)
- ✅ Minikube or Kind (local Kubernetes)
- ✅ kubectl (already installed ✅)
- ✅ Helm (install with `./scripts/install-prerequisites.sh`)
- ✅ Python 3.9+ (already installed ✅)

### Optional but Recommended:
- Docker Compose (for local services)
- LocalStack (AWS service emulation)

---

## 🚀 Quick Start (5 Steps)

### Step 1: Install Local Kubernetes

**Option A: Minikube (Recommended for macOS)**

```bash
# Install Minikube
brew install minikube

# Start Minikube
minikube start --driver=docker

# Verify
kubectl get nodes
```

**Option B: Kind (Kubernetes in Docker)**

```bash
# Install Kind
brew install kind

# Create cluster
kind create cluster --name ai-devops-brain

# Verify
kubectl get nodes
```

---

### Step 2: Install Helm (if not installed)

```bash
./scripts/install-prerequisites.sh
# Or manually:
brew install helm
```

---

### Step 3: Deploy Local Services

We'll use local alternatives for AWS services:

- **S3** → Local filesystem or MinIO
- **RDS** → PostgreSQL in Docker
- **Redis** → Redis in Docker
- **Kafka** → Kafka in Docker
- **S3** → MinIO (S3-compatible)

```bash
# Start local services
./scripts/setup-local-services.sh
```

---

### Step 4: Deploy Platform Components

```bash
# Deploy to local Kubernetes
./scripts/deploy-platform-local.sh
```

This deploys:
- ArgoCD
- Prometheus + Grafana
- Loki (log aggregation)
- FluentBit
- KEDA
- All platform components

---

### Step 5: Deploy Sample Workloads

```bash
# Deploy finance simulation
kubectl apply -f simulations/finance/payment-service.yaml

# Deploy healthcare simulation
kubectl apply -f simulations/healthcare/emr-api.yaml

# Deploy automotive simulation
kubectl apply -f simulations/automotive/telemetry-collector.yaml
```

---

## 📁 Local Data Storage

Instead of S3, we'll use:

1. **Local filesystem** for logs/metrics/events
2. **MinIO** (S3-compatible) for testing S3 integration
3. **Local PostgreSQL** for databases
4. **Local Redis** for caching

---

## 🔧 Configuration Changes for Local

### Data Pipeline (Local Version)

Instead of S3, logs/metrics go to:
- `./local-data/logs/`
- `./local-data/metrics/`
- `./local-data/events/`

### Database Connections

Instead of RDS endpoints, use:
- PostgreSQL: `postgresql://localhost:5432/finance`
- Redis: `redis://localhost:6379`
- Kafka: `localhost:9092`

---

## 🧪 Testing Locally

### 1. Test Anomaly Detection

```bash
cd ai-models
source venv/bin/activate
python anomaly-detection/train_anomaly_detector.py --simulate
```

### 2. Test RCA Engine

```bash
# Generate sample data
python scripts/generate-sample-data.py

# Run RCA analysis
python rca-engine/rca_engine.py \
  data/sample_logs.csv \
  data/sample_metrics.csv \
  data/sample_events.csv \
  data/sample_services.json
```

### 3. Test Auto-Fix Engine

```bash
# Test with local Kubernetes
python auto-fix/auto_fix_engine.py --local
```

---

## 📊 Local Architecture

```
┌─────────────────────────────────────────┐
│         Your Local Machine               │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────────────────────────┐   │
│  │   Minikube/Kind Cluster          │   │
│  │  ┌──────────┐  ┌──────────┐    │   │
│  │  │ Finance  │  │Healthcare│    │   │
│  │  │ Services │  │ Services │    │   │
│  │  └──────────┘  └──────────┘    │   │
│  │  ┌──────────┐  ┌──────────┐    │   │
│  │  │Prometheus│  │  Loki    │    │   │
│  │  │ Grafana  │  │FluentBit │    │   │
│  │  └──────────┘  └──────────┘    │   │
│  └──────────────────────────────────┘   │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │   Docker Services                 │   │
│  │  - PostgreSQL                     │   │
│  │  - Redis                          │   │
│  │  - Kafka                          │   │
│  │  - MinIO (S3-compatible)          │   │
│  └──────────────────────────────────┘   │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │   Local Data Storage              │   │
│  │  ./local-data/                    │   │
│  │    ├── logs/                      │   │
│  │    ├── metrics/                   │   │
│  │    └── events/                     │   │
│  └──────────────────────────────────┘   │
│                                         │
│  ┌──────────────────────────────────┐   │
│  │   AI Models (Python)              │   │
│  │  - Anomaly Detection              │   │
│  │  - RCA Engine                     │   │
│  │  - Auto-Fix Engine                │   │
│  └──────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

---

## 🎯 What You Can Test Locally

✅ **All AI Models**
- Anomaly detection
- RCA engine
- Auto-fix engine

✅ **Data Pipeline**
- Log collection
- Metric collection
- Event collection

✅ **Kubernetes Features**
- Pod failures
- Service mesh
- Autoscaling
- Chaos engineering

✅ **Industry Simulations**
- Finance workloads
- Healthcare workloads
- Automotive workloads

---

## 🚀 Next Steps

1. **Install Minikube/Kind**
2. **Run setup scripts** (I'll create these)
3. **Deploy everything locally**
4. **Test the full pipeline**
5. **When ready, migrate to AWS** (optional)

---

## 💡 Advantages Over AWS

| Feature | Local | AWS |
|---------|-------|-----|
| Cost | $0 | $35-120/day |
| Setup Time | 10 min | 30-45 min |
| Risk | Zero | High |
| Iteration Speed | Fast | Slower |
| Resource Limits | Your machine | Cloud limits |
| Best For | Development | Production |

---

**Let's set this up! I'll create all the local configuration files next.**

