locals {
  # stable, friendly names
  secret_defs = { for k, v in var.secrets : k => {
    name = k
    value = v
  } }
}

resource "aws_secretsmanager_secret" "this" {
  for_each                = local.secret_defs
  name                    = each.value.name
  description             = "Managed by Terraform"
  kms_key_id              = var.kms_key_id
  recovery_window_in_days = var.recovery_window_in_days
}

# Optional initial versions (only create if value is not null and not empty)
resource "aws_secretsmanager_secret_version" "ver" {
  for_each      = { for k, v in local.secret_defs : k => v if v.value != null && v.value != "" }
  secret_id     = aws_secretsmanager_secret.this[each.key].id
  secret_string = each.value.value
}
