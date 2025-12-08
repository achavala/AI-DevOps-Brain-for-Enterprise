variable "vpc_id" {
  description = "VPC ID for the cluster"
  type        = string
}

variable "vpc_cidr" {
  description = "VPC CIDR block"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the cluster"
  type        = list(string)
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

