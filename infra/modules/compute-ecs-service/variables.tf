variable "name" { type = string }
variable "cluster_arn" { type = string }
variable "desired_count" {
  type    = number
  default = 0     # start at 0 = safe
}
variable "cpu" {
  type    = number
  default = 256
}
variable "memory" {
  type    = number
  default = 512
}
variable "container_image" { type = string }                 # e.g. <acct>.dkr.ecr...:tag
variable "container_env" {
  type    = map(string)
  default = {}
}
variable "container_secrets" {
  type    = map(string)
  default = {}
} # ENV_NAME => secret ARN
variable "subnet_ids" { type = list(string) }
variable "security_group_ids" { type = list(string) }
variable "task_role_arn" { type = string }
variable "exec_role_arn" { type = string }
variable "log_kms_key_arn" {
  type    = string
  default = null
}
