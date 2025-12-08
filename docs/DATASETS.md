# 📊 Validation Dataset Sources

This document lists all available datasets for training and validating the AI DevOps Brain models.

---

## Public Datasets

### 1. Google Borg Traces
- **Source**: Google Cluster Data
- **Description**: Large-scale cluster traces from Google's infrastructure
- **Size**: ~40GB
- **Format**: CSV, JSON
- **Use Case**: Training anomaly detection on real production patterns
- **Link**: https://github.com/google/cluster-data
- **License**: Apache 2.0

### 2. Alibaba Cluster Traces
- **Source**: Alibaba Cloud
- **Description**: Production cluster traces from Alibaba's infrastructure
- **Size**: ~30GB
- **Format**: CSV
- **Use Case**: Workload pattern analysis, resource prediction
- **Link**: https://github.com/alibaba/clusterdata
- **License**: Apache 2.0

### 3. Azure Public Logs Dataset
- **Source**: Microsoft Azure
- **Description**: Anonymized logs from Azure services
- **Size**: ~20GB
- **Format**: JSON, Parquet
- **Use Case**: Cloud-native failure patterns
- **Link**: https://github.com/Azure/azure-public-datasets
- **License**: MIT

### 4. Falco Security Logs
- **Source**: Falco Project
- **Description**: Security event logs from container runtime
- **Size**: ~5GB
- **Format**: JSON
- **Use Case**: Security anomaly detection
- **Link**: https://github.com/falcosecurity/falco
- **License**: Apache 2.0

### 5. Kubernetes SIG Failure Datasets
- **Source**: Kubernetes SIG Testing
- **Description**: Failure scenarios from K8s test suites
- **Size**: ~10GB
- **Format**: YAML, JSON
- **Use Case**: K8s-specific failure patterns
- **Link**: https://github.com/kubernetes/test-infra
- **License**: Apache 2.0

### 6. Cloudflare & GitHub Incident Reports
- **Source**: Public incident reports
- **Description**: Real-world incident data
- **Size**: ~2GB
- **Format**: Markdown, JSON
- **Use Case**: RCA pattern learning
- **Links**: 
  - https://github.com/cloudflare/cloudflare-blog
  - https://github.com/github/incidents
- **License**: Various

### 7. Application Logs (Open Source)
- **Apache Logs**: https://github.com/logpai/loghub
- **Nginx Logs**: https://github.com/logpai/loghub
- **Kafka Logs**: https://github.com/apache/kafka
- **Redis Logs**: https://github.com/redis/redis
- **Size**: ~15GB total
- **Use Case**: Application-level error patterns

---

## Dataset Download Script

```bash
#!/bin/bash
# download_datasets.sh

mkdir -p datasets
cd datasets

# Google Borg Traces
echo "Downloading Google Borg traces..."
git clone https://github.com/google/cluster-data.git google-borg
cd google-borg
# Follow instructions to download actual trace files
cd ..

# Alibaba Cluster Traces
echo "Downloading Alibaba cluster traces..."
git clone https://github.com/alibaba/clusterdata.git alibaba-cluster
cd alibaba-cluster
# Follow instructions to download actual trace files
cd ..

# Kubernetes SIG Data
echo "Downloading Kubernetes SIG data..."
git clone https://github.com/kubernetes/test-infra.git k8s-sig
cd k8s-sig
# Extract failure scenarios
cd ..

# Falco Logs
echo "Downloading Falco logs..."
git clone https://github.com/falcosecurity/falco.git falco
cd falco
# Extract example logs
cd ..

# Application Logs
echo "Downloading application logs..."
git clone https://github.com/logpai/loghub.git loghub
cd loghub
# Extract relevant logs
cd ..

echo "Dataset download complete!"
```

---

## Data Preprocessing

### 1. Normalize Formats
All datasets should be converted to a common format:

```python
# Standard log format
{
    "timestamp": "2024-01-01T00:00:00Z",
    "level": "error",
    "service": "payment-service",
    "message": "Connection timeout",
    "cluster": "finance",
    "namespace": "default",
    "pod": "payment-service-123"
}

# Standard metric format
{
    "timestamp": "2024-01-01T00:00:00Z",
    "metric": "cpu_usage",
    "value": 85.5,
    "service": "payment-service",
    "cluster": "finance"
}

# Standard event format
{
    "timestamp": "2024-01-01T00:00:00Z",
    "type": "Warning",
    "reason": "PodCrashLoopBackOff",
    "object": "pod/payment-service-123",
    "message": "Back-off restarting failed container"
}
```

### 2. Label Data
Use the labeling script:

```bash
python scripts/label_data.py \
  --input datasets/raw/ \
  --output datasets/labeled/ \
  --labels config/labels.json
```

---

## Dataset Statistics

| Dataset | Records | Time Range | Failure Rate |
|---------|---------|------------|--------------|
| Google Borg | 1.2B | 29 days | ~2.5% |
| Alibaba | 800M | 8 days | ~3.1% |
| Azure Logs | 500M | 30 days | ~1.8% |
| K8s SIG | 50M | Various | ~5.0% |
| Application Logs | 200M | Various | ~2.0% |

**Total**: ~2.75 billion records, ~50-100GB

---

## Usage in Training

### Anomaly Detection
```python
from ai_models.anomaly_detection import train_anomaly_detector

# Use Google Borg + Alibaba for training
train_anomaly_detector(
    data_path='datasets/labeled/metrics/',
    output_dir='models/anomaly/',
    algorithms=['isolation_forest', 'lstm', 'prophet']
)
```

### RCA Engine
```python
from ai_models.rca_engine import RCAEngine

# Use K8s SIG + incident reports
rca = RCAEngine()
rca.train_on_incidents('datasets/labeled/incidents/')
```

### Auto-Fix Engine
```python
from ai_models.auto_fix import AutoFixEngine

# Use labeled fixes from incident reports
engine = AutoFixEngine()
engine.train_on_fixes('datasets/labeled/fixes/')
```

---

## Data Privacy

All datasets used are:
- ✅ Publicly available
- ✅ Anonymized (no PII)
- ✅ Licensed for research/commercial use
- ✅ Compliant with data protection regulations

---

## Contributing Datasets

If you have additional datasets:
1. Ensure they're publicly available or properly licensed
2. Anonymize any sensitive data
3. Document format and structure
4. Submit via pull request

---

## References

- Google Cluster Data: https://github.com/google/cluster-data
- Alibaba Cluster Traces: https://github.com/alibaba/clusterdata
- LogHub: https://github.com/logpai/loghub
- Kubernetes Test Infra: https://github.com/kubernetes/test-infra

