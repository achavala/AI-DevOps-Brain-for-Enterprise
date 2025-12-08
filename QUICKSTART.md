# ⚡ Quick Start Guide

Get the AI DevOps Brain testing architecture up and running in 30 minutes.

---

## Prerequisites Check

```bash
# Check all required tools
aws --version          # AWS CLI v2
terraform version      # >= 1.5
kubectl version        # >= 1.28
helm version           # >= 3.12
python3 --version      # >= 3.9
```

---

## 1. Clone and Setup (5 min)

```bash
# Navigate to project
cd "AI DevOps Brain for Enterprise"

# Setup Python environment
cd ai-models
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd ..
```

---

## 2. AWS Configuration (5 min)

```bash
# Configure AWS credentials
aws configure

# Create S3 bucket for Terraform state
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 mb s3://ai-devops-brain-terraform-state-$ACCOUNT_ID
aws s3api put-bucket-versioning \
  --bucket ai-devops-brain-terraform-state-$ACCOUNT_ID \
  --versioning-configuration Status=Enabled
```

---

## 3. Deploy Finance Cluster (15 min)

```bash
# Initialize Terraform
cd infrastructure
terraform init

# Create variables file
cat > terraform.tfvars <<EOF
aws_region = "us-east-1"
project_name = "ai-devops-brain"
environment = "testing"
EOF

# Deploy (this takes ~15 minutes)
terraform plan
terraform apply -auto-approve

# Configure kubectl
aws eks update-kubeconfig --name finance-cluster --region us-east-1
kubectl get nodes
```

---

## 4. Deploy Platform Components (5 min)

```bash
# Deploy ArgoCD, KEDA, Prometheus, etc.
./scripts/deploy-platform.sh finance-cluster

# Wait for ArgoCD
kubectl wait --for=condition=available deployment/argocd-server -n argocd --timeout=300s

# Get ArgoCD password
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

---

## 5. Setup Data Pipeline (5 min)

```bash
# Deploy FluentBit, Prometheus, event exporters
./scripts/setup-data-pipeline.sh finance-cluster

# Verify
kubectl get pods -n logging
kubectl get pods -n monitoring
```

---

## 6. Deploy Sample Workload (2 min)

```bash
# Deploy finance payment service
kubectl create namespace finance
kubectl apply -f simulations/finance/payment-service.yaml

# Check status
kubectl get pods -n finance
```

---

## 7. Install Chaos Mesh (3 min)

```bash
# Install chaos engineering
./chaos/chaos-mesh/install.sh

# Create a test chaos experiment
kubectl apply -f chaos/chaos-mesh/pod-kill-experiment.yaml

# Watch chaos in action
kubectl get chaos -n default
```

---

## 8. Train Initial Models (Optional)

```bash
cd ai-models
source venv/bin/activate

# Train anomaly detector (requires sample data)
python anomaly-detection/train_anomaly_detector.py \
  data/sample.csv \
  models/
```

---

## Verify Everything Works

```bash
# Check all components
kubectl get pods --all-namespaces | grep -E "Running|Completed"

# Check data flow
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws s3 ls s3://ai-devops-brain-logs-$ACCOUNT_ID/ | head -5

# Access dashboards
# ArgoCD: kubectl port-forward -n argocd svc/argocd-server 8080:443
# Grafana: kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

---

## Next Steps

1. **Deploy other clusters**: Repeat steps 3-7 for healthcare and automotive clusters
2. **Add more workloads**: Deploy additional microservices
3. **Run chaos experiments**: Test failure scenarios
4. **Train models**: Use collected data to train AI models
5. **Follow roadmap**: See `docs/ROADMAP.md` for 12-week plan

---

## Troubleshooting

### Issue: Terraform fails
```bash
# Check AWS credentials
aws sts get-caller-identity

# Check S3 bucket exists
aws s3 ls | grep terraform-state
```

### Issue: kubectl cannot connect
```bash
# Update kubeconfig
aws eks update-kubeconfig --name finance-cluster --region us-east-1

# Test connection
kubectl get nodes
```

### Issue: Pods not starting
```bash
# Check pod logs
kubectl logs <pod-name> -n <namespace>

# Check events
kubectl get events --sort-by='.lastTimestamp' | tail -20
```

---

## Cost Estimate

**Quick Start (Finance cluster only)**: ~$500-800/month
- EKS: $150
- EC2: $300-500
- S3: $50
- RDS: $100

**Full Setup (3 clusters)**: ~$1,500-2,500/month

---

## Cleanup

```bash
# Destroy infrastructure
cd infrastructure
terraform destroy

# Delete S3 buckets (after terraform destroy)
aws s3 rb s3://ai-devops-brain-logs-$ACCOUNT_ID --force
aws s3 rb s3://ai-devops-brain-metrics-$ACCOUNT_ID --force
aws s3 rb s3://ai-devops-brain-events-$ACCOUNT_ID --force
```

---

## Support

- **Documentation**: See `docs/` directory
- **Architecture**: `docs/ARCHITECTURE.md`
- **Deployment**: `docs/DEPLOYMENT.md`
- **Roadmap**: `docs/ROADMAP.md`

