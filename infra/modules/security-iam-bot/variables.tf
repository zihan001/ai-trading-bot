variable "name" { type = string }
variable "secrets_arns" {
  type    = list(string)
  default = []   # secrets the task may read
}
variable "kms_key_arn" {
  type    = string
  default = null # KMS used by Secrets (optional)
}
