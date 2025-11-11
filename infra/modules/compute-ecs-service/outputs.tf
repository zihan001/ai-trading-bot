output "service_arn"  { value = aws_ecs_service.this.id }
output "service_name" { value = aws_ecs_service.this.name }
output "taskdef_arn"  { value = aws_ecs_task_definition.this.arn }
output "log_group"    { value = aws_cloudwatch_log_group.app.name }
