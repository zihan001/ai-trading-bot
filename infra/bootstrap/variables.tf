variable "region" {
  type        = string
  description = "AWS region, e.g. ca-central-1"
}

variable "state_bucket_name" {
  type        = string
  description = "Name for Terraform state S3 bucket (must be globally unique)"
}

variable "lock_table_name" {
  type        = string
  description = "Name for DynamoDB lock table"
}
