locals {
  container_name = var.name
  env_list = [for k, v in var.container_env : { name = k, value = v }]
  secrets_list = [for k, v in var.container_secrets : { name = k, valueFrom = v }]
}

resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/${var.name}"
  retention_in_days = 14
  kms_key_id        = var.log_kms_key_arn
}

resource "aws_ecs_task_definition" "this" {
  family                   = var.name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = tostring(var.cpu)
  memory                   = tostring(var.memory)
  task_role_arn            = var.task_role_arn
  execution_role_arn       = var.exec_role_arn
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  container_definitions = jsonencode([
    {
      name      = local.container_name
      image     = var.container_image
      essential = true
      environment = local.env_list
      secrets     = local.secrets_list
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ])
}

data "aws_region" "current" {}

resource "aws_ecs_service" "this" {
  name            = var.name
  cluster         = var.cluster_arn
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  platform_version= "1.4.0"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = var.security_group_ids
    assign_public_ip = false
  }

  lifecycle {
    ignore_changes = [task_definition] # enable zero-downtime deploys by creating new revs
  }
}
