output "state_bucket" {
  description = "Name of the created S3 state bucket"
  value       = aws_s3_bucket.tf_state.bucket
}

output "lock_table" {
  description = "Name of the created DynamoDB lock table"
  value       = aws_dynamodb_table.tf_locks.name
}
