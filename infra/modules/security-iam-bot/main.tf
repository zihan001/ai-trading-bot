# Execution role: pulls image, writes logs, reads secrets at runtime
resource "aws_iam_role" "exec" {
  name               = "${var.name}-exec-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

data "aws_iam_policy_document" "ecs_tasks_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# Base execution policy (AWS managed)
resource "aws_iam_role_policy_attachment" "exec_base" {
  role       = aws_iam_role.exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# Allow decrypt for customer KMS key (always created since we always use KMS)
resource "aws_iam_policy" "exec_kms" {
  name  = "${var.name}-exec-kms"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = ["kms:Decrypt", "kms:DescribeKey"],
      Resource = var.kms_key_arn
    }]
  })
}

resource "aws_iam_role_policy_attachment" "exec_kms_attach" {
  role       = aws_iam_role.exec.name
  policy_arn = aws_iam_policy.exec_kms.arn
}

# Task role: app's own permissions (read specific secrets only)
resource "aws_iam_role" "task" {
  name               = "${var.name}-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_tasks_assume.json
}

resource "aws_iam_policy" "task_secrets" {
  name   = "${var.name}-read-secrets"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = concat(
      length(var.secrets_arns) == 0 ? [] : [{
        Effect   = "Allow",
        Action   = ["secretsmanager:GetSecretValue", "secretsmanager:DescribeSecret"],
        Resource = var.secrets_arns
      }],
      var.kms_key_arn == null ? [] : [{
        Effect   = "Allow",
        Action   = ["kms:Decrypt","kms:DescribeKey"],
        Resource = var.kms_key_arn
      }]
    )
  })
}

resource "aws_iam_role_policy_attachment" "task_secrets_attach" {
  role       = aws_iam_role.task.name
  policy_arn = aws_iam_policy.task_secrets.arn
}
