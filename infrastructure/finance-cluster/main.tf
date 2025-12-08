terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# EKS Cluster for Finance workloads
module "finance_eks" {
  source = "terraform-aws-modules/eks/aws"
  version = "~> 19.0"

  cluster_name    = "finance-cluster"
  cluster_version = "1.28"

  vpc_id     = var.vpc_id
  subnet_ids = var.private_subnet_ids

  # EKS Managed Node Groups
  eks_managed_node_groups = {
    general = {
      min_size     = 3
      max_size     = 10
      desired_size = 5

      instance_types = ["t3.medium", "t3.large"]
      capacity_type  = "ON_DEMAND"

      labels = {
        Environment = "testing"
        Cluster     = "finance"
        Workload    = "general"
      }
    }

    kafka = {
      min_size     = 2
      max_size     = 5
      desired_size = 3

      instance_types = ["t3.large", "t3.xlarge"]
      capacity_type  = "ON_DEMAND"

      labels = {
        Environment = "testing"
        Cluster     = "finance"
        Workload    = "kafka"
      }

      taints = [{
        key    = "workload"
        value  = "kafka"
        effect = "NO_SCHEDULE"
      }]
    }
  }

  # Enable IRSA
  enable_irsa = true

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  tags = {
    Environment = "testing"
    Cluster     = "finance"
    ManagedBy   = "Terraform"
  }
}

# RDS for Finance workloads
resource "aws_db_instance" "finance_postgres" {
  identifier     = "finance-postgres"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.medium"

  allocated_storage     = 100
  max_allocated_storage = 200
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "finance"
  username = "finance_admin"
  password = var.db_password # Use AWS Secrets Manager in production

  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.finance.name

  backup_retention_period = 7
  skip_final_snapshot    = true

  tags = {
    Name        = "finance-postgres"
    Environment = "testing"
    Cluster     = "finance"
  }
}

resource "aws_db_subnet_group" "finance" {
  name       = "finance-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "finance-db-subnet-group"
  }
}

resource "aws_security_group" "rds" {
  name_prefix = "finance-rds-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "finance-rds-sg"
  }
}

# ElastiCache Redis for Finance
resource "aws_elasticache_subnet_group" "finance" {
  name       = "finance-redis-subnet-group"
  subnet_ids = var.private_subnet_ids
}

resource "aws_elasticache_cluster" "finance_redis" {
  cluster_id           = "finance-redis"
  engine               = "redis"
  node_type            = "cache.t3.medium"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.finance.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = {
    Name        = "finance-redis"
    Environment = "testing"
    Cluster     = "finance"
  }
}

resource "aws_security_group" "redis" {
  name_prefix = "finance-redis-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "finance-redis-sg"
  }
}

# MSK (Kafka) for Finance
resource "aws_msk_cluster" "finance_kafka" {
  cluster_name           = "finance-kafka"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.t3.small"
    ebs_volume_size = 100
    client_subnets  = var.private_subnet_ids
    security_groups = [aws_security_group.kafka.id]
  }

  encryption_info {
    encryption_at_rest_kms_key_id = aws_kms_key.kafka.arn
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
  }

  tags = {
    Name        = "finance-kafka"
    Environment = "testing"
    Cluster     = "finance"
  }
}

resource "aws_kms_key" "kafka" {
  description = "KMS key for Finance Kafka encryption"
  
  tags = {
    Name = "finance-kafka-kms"
  }
}

resource "aws_security_group" "kafka" {
  name_prefix = "finance-kafka-"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 9092
    to_port     = 9092
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  ingress {
    from_port   = 9094
    to_port     = 9094
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "finance-kafka-sg"
  }
}

