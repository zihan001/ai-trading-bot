terraform {
  backend "s3" {
    bucket         = "tf-state-zihan-ca-central-1"   # <= your output
    key            = "ai-trading-bot/dev/terraform.tfstate"
    region         = "ca-central-1"
    dynamodb_table = "tf-locks"                       # <= your output
    encrypt        = true
  }
}
