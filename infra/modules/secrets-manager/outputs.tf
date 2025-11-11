output "arns" {
  value = { for k, s in aws_secretsmanager_secret.this : k => s.arn }
}
output "ids" {
  value = { for k, s in aws_secretsmanager_secret.this : k => s.id }
}
