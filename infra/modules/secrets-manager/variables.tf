variable "secrets" {
  description = "Map of secret_name => initial_plaintext ('' for placeholder)"
  type        = map(string)
}
variable "kms_key_id" {
  description = "Optional customer managed KMS key id/arn"
  type        = string
  default     = null
}
variable "recovery_window_in_days" {
  type    = number
  default = 7
}
