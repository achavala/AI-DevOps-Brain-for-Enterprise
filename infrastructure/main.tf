terraform {
  required_version = ">= 1.5"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
  }

  backend "s3" {
    # Configure your S3 backend
    bucket = "ai-devops-brain-terraform-state"
    key    = "global/terraform.tfstate"
    region = "us-east-1"
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# VPC for all clusters
module "vpc" {
  source = "./modules/vpc"
  
  name                 = "ai-devops-brain-vpc"
  cidr                 = var.vpc_cidr
  availability_zones   = data.aws_availability_zones.available.names
  enable_nat_gateway   = true
  enable_vpn_gateway   = false
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = var.common_tags
}

# S3 buckets for data storage
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${data.aws_caller_identity.current.account_id}"
  
  tags = merge(var.common_tags, {
    Name        = "${var.project_name}-logs"
    Environment = var.environment
  })
}

resource "aws_s3_bucket" "metrics" {
  bucket = "${var.project_name}-metrics-${data.aws_caller_identity.current.account_id}"
  
  tags = merge(var.common_tags, {
    Name        = "${var.project_name}-metrics"
    Environment = var.environment
  })
}

resource "aws_s3_bucket" "events" {
  bucket = "${var.project_name}-events-${data.aws_caller_identity.current.account_id}"
  
  tags = merge(var.common_tags, {
    Name        = "${var.project_name}-events"
    Environment = var.environment
  })
}

# Enable versioning and encryption on S3 buckets
resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "metrics" {
  bucket = aws_s3_bucket.metrics.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "metrics" {
  bucket = aws_s3_bucket.metrics.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_versioning" "events" {
  bucket = aws_s3_bucket.events.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "events" {
  bucket = aws_s3_bucket.events.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# IAM role for data pipeline access
resource "aws_iam_role" "data_pipeline" {
  name = "${var.project_name}-data-pipeline-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.common_tags
}

resource "aws_iam_role_policy" "data_pipeline_s3" {
  name = "${var.project_name}-data-pipeline-s3-policy"
  role = aws_iam_role.data_pipeline.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.logs.arn,
          "${aws_s3_bucket.logs.arn}/*",
          aws_s3_bucket.metrics.arn,
          "${aws_s3_bucket.metrics.arn}/*",
          aws_s3_bucket.events.arn,
          "${aws_s3_bucket.events.arn}/*"
        ]
      }
    ]
  })
}

