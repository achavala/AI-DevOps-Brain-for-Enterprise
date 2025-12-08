variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for resources"
  type        = string
  default     = "ai-devops-brain"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "testing"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "common_tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Project     = "AI-DevOps-Brain"
    ManagedBy   = "Terraform"
    Environment = "testing"
  }
}

variable "finance_cluster_config" {
  description = "Finance cluster configuration"
  type = object({
    name         = string
    region       = string
    node_groups  = map(object({
      instance_types = list(string)
      min_size      = number
      max_size      = number
      desired_size  = number
    }))
  })
  default = {
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
}

variable "healthcare_cluster_config" {
  description = "Healthcare cluster configuration"
  type = object({
    name         = string
    region       = string
    node_groups  = map(object({
      instance_types = list(string)
      min_size      = number
      max_size      = number
      desired_size  = number
    }))
  })
  default = {
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
}

variable "automotive_cluster_config" {
  description = "Automotive cluster configuration"
  type = object({
    name         = string
    region       = string
    node_groups  = map(object({
      instance_types = list(string)
      min_size      = number
      max_size      = number
      desired_size  = number
    }))
  })
  default = {
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
}

