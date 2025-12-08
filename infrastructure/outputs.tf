output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpc_cidr" {
  description = "VPC CIDR block"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "logs_bucket_name" {
  description = "S3 bucket for logs"
  value       = aws_s3_bucket.logs.id
}

output "metrics_bucket_name" {
  description = "S3 bucket for metrics"
  value       = aws_s3_bucket.metrics.id
}

output "events_bucket_name" {
  description = "S3 bucket for events"
  value       = aws_s3_bucket.events.id
}

output "data_pipeline_role_arn" {
  description = "IAM role ARN for data pipeline"
  value       = aws_iam_role.data_pipeline.arn
}

