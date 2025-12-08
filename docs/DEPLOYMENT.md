# 🚀 Deployment Guide

Complete guide for deploying the AI DevOps Brain testing architecture.

---

## Prerequisites

### Required Tools
- AWS CLI v2 (`aws --version`)
- Terraform >= 1.5 (`terraform version`)
- kubectl >= 1.28 (`kubectl version --client`)
- Helm 3 (`helm version`)
- Python 3.9+ (`python3 --version`)

### AWS Setup
1. Configure AWS credentials:
```bash
aws configure
```

2. Set up S3 backend for Terraform state:
```bash
aws s3 mb s3://ai-devops-brain-terraform-state
aws s3api put-bucket-versioning \
  --bucket ai-devops-brain-terraform-state \
  --versioning-configuration Status=Enabled
```

3. Create IAM roles and policies (see `infrastructure/iam/`)

---

## Step 1: Deploy Core Infrastructure

### 1.1 Initialize Terraform
```bash
cd infrastructure
terraform init
```

### 1.2 Create Terraform Variables File
```bash
cat > terraform.tfvars <<EOF
aws_region = "us-east-1"
project_name = "ai-devops-brain"
environment = "testing"

finance_cluster_config = {
  name   = "finance-cluster"
  region = "us-east-1"
  node_groups = {
    general = {
      instance_types = ["t3.medium", "t3.large"]
      min_size      = 3
      max_size      = 10
      desired_size  = 5
    }
  }
}

healthcare_cluster_config = {
  name   = "healthcare-cluster"
  region = "us-west-2"
  node_groups = {
    general = {
      instance_types = ["t3.medium", "t3.large"]
      min_size      = 3
      max_size      = 10
      desired_size  = 5
    }
  }
}

automotive_cluster_config = {
  name   = "automotive-cluster"
  region = "eu-west-1"
  node_groups = {
    general = {
      instance_types = ["t3.medium", "t3.large"]
      min_size      = 3
      max_size      = 10
      desired_size  = 5
    }
  }
}
EOF
```

### 1.3 Plan and Apply
```bash
terraform plan
terraform apply
```

This will create:
- VPC and networking
- 3 EKS clusters (Finance, Healthcare, Automotive)
- S3 buckets for data storage
- IAM roles and policies
- RDS, Redis, Kafka (for Finance cluster)

**Time**: ~30-45 minutes

---

## Step 2: Configure Kubernetes Access

### 2.1 Update kubeconfig for each cluster
```bash
# Finance cluster
aws eks update-kubeconfig --name finance-cluster --region us-east-1

# Healthcare cluster
aws eks update-kubeconfig --name healthcare-cluster --region us-west-2

# Automotive cluster
aws eks update-kubeconfig --name automotive-cluster --region eu-west-1
```

### 2.2 Verify access
```bash
kubectl get nodes
```

---

## Step 3: Deploy Platform Components

### 3.1 Deploy to Finance Cluster
```bash
export CLUSTER_NAME=finance-cluster
./scripts/deploy-platform.sh $CLUSTER_NAME
```

### 3.2 Deploy to Healthcare Cluster
```bash
export CLUSTER_NAME=healthcare-cluster
aws eks update-kubeconfig --name $CLUSTER_NAME --region us-west-2
./scripts/deploy-platform.sh $CLUSTER_NAME
```

### 3.3 Deploy to Automotive Cluster
```bash
export CLUSTER_NAME=automotive-cluster
aws eks update-kubeconfig --name $CLUSTER_NAME --region eu-west-1
./scripts/deploy-platform.sh $CLUSTER_NAME
```

This deploys:
- ArgoCD (GitOps)
- KEDA (Event-driven autoscaling)
- Prometheus + Grafana (Monitoring)
- Loki (Log aggregation)
- FluentBit (Log collection)
- Karpenter (Node autoscaling)

**Time**: ~20-30 minutes per cluster

---

## Step 4: Setup Data Pipeline

### 4.1 Deploy Data Collection
```bash
# Finance cluster
aws eks update-kubeconfig --name finance-cluster --region us-east-1
./scripts/setup-data-pipeline.sh finance-cluster

# Healthcare cluster
aws eks update-kubeconfig --name healthcare-cluster --region us-west-2
./scripts/setup-data-pipeline.sh healthcare-cluster

# Automotive cluster
aws eks update-kubeconfig --name automotive-cluster --region eu-west-1
./scripts/setup-data-pipeline.sh automotive-cluster
```

This sets up:
- FluentBit → S3 (logs)
- Prometheus → Thanos → S3 (metrics)
- K8s Event Exporter → S3 (events)

---

## Step 5: Deploy Chaos Engineering

### 5.1 Install Chaos Mesh
```bash
# On each cluster
./chaos/chaos-mesh/install.sh
```

### 5.2 Verify Installation
```bash
kubectl get pods -n chaos-mesh
```

### 5.3 Create Chaos Experiments
```bash
kubectl apply -f chaos/chaos-mesh/pod-kill-experiment.yaml
```

---

## Step 6: Deploy Industry Simulations

### 6.1 Finance Workloads
```bash
aws eks update-kubeconfig --name finance-cluster --region us-east-1
kubectl create namespace finance
kubectl apply -f simulations/finance/
```

### 6.2 Healthcare Workloads
```bash
aws eks update-kubeconfig --name healthcare-cluster --region us-west-2
kubectl create namespace healthcare
kubectl apply -f simulations/healthcare/
```

### 6.3 Automotive Workloads
```bash
aws eks update-kubeconfig --name automotive-cluster --region eu-west-1
kubectl create namespace automotive
kubectl apply -f simulations/automotive/
```

---

## Step 7: Train AI Models

### 7.1 Setup Python Environment
```bash
cd ai-models
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 7.2 Prepare Training Data
```bash
# Download validation datasets (see docs/DATASETS.md)
mkdir -p data
# Add your training data to data/
```

### 7.3 Train Models
```bash
# Train anomaly detection models
python anomaly-detection/train_anomaly_detector.py data/metrics.csv models/

# Test RCA engine
python rca-engine/rca_engine.py data/logs.csv data/metrics.csv data/events.csv data/services.json

# Test auto-fix engine
python auto-fix/auto_fix_engine.py
```

---

## Step 8: Verify Deployment

### 8.1 Check All Components
```bash
# Check pods
kubectl get pods --all-namespaces

# Check services
kubectl get svc --all-namespaces

# Check data flow
aws s3 ls s3://ai-devops-brain-logs-$(aws sts get-caller-identity --query Account --output text)/
```

### 8.2 Access Dashboards
```bash
# ArgoCD
kubectl port-forward -n argocd svc/argocd-server 8080:443

# Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Chaos Mesh
kubectl port-forward -n chaos-mesh svc/chaos-mesh-dashboard 2333:2333
```

---

## Troubleshooting

### Issue: Terraform fails with S3 backend error
**Solution**: Ensure S3 bucket exists and IAM permissions are correct.

### Issue: kubectl cannot connect to cluster
**Solution**: Run `aws eks update-kubeconfig` again with correct region.

### Issue: Pods in CrashLoopBackOff
**Solution**: Check logs: `kubectl logs <pod-name> -n <namespace>`

### Issue: FluentBit not sending logs to S3
**Solution**: 
1. Check IAM role permissions
2. Verify S3 bucket exists
3. Check FluentBit logs: `kubectl logs -n logging -l app=fluent-bit`

---

## Next Steps

1. **Week 1-2**: Follow this deployment guide
2. **Week 3-4**: Add failure injection and validate data pipeline
3. **Week 5-6**: Label data and train initial models
4. **Week 7-8**: Build auto-fix engine
5. **Week 9-10**: Test industry-specific scenarios
6. **Week 11-12**: Enterprise readiness testing

See `docs/ROADMAP.md` for detailed week-by-week plan.

---

## Cost Estimation

### Monthly Costs (Approximate)
- **EKS Clusters**: $150/cluster × 3 = $450
- **EC2 Instances**: ~$500-1000 (depending on instance types)
- **RDS**: ~$200 (Finance cluster)
- **S3 Storage**: ~$50-100 (depending on data volume)
- **Data Transfer**: ~$50-100
- **Total**: ~$1,250-1,800/month

**Note**: Use spot instances and reserved capacity to reduce costs.

---

## Security Best Practices

1. **Encryption**: All S3 buckets encrypted at rest
2. **Network**: VPC isolation between clusters
3. **IAM**: Least privilege access
4. **Secrets**: Use AWS Secrets Manager (not hardcoded)
5. **Audit**: Enable CloudTrail for all API calls

---

## Support

For issues or questions:
1. Check logs: `kubectl logs -n <namespace> <pod-name>`
2. Review documentation: `docs/`
3. Check GitHub issues (if public repo)

