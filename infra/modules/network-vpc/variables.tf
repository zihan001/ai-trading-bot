variable "name" { type = string }
variable "cidr_block" {
  type    = string
  default = "10.30.0.0/16"
}
variable "az_count" {
  type    = number
  default = 2
}
variable "enable_nat_gateway" {
  type    = bool
  default = true
}
