module "vpc" {
  source             = "../../modules/network-vpc"
  name               = "trading-dev"
  cidr_block         = "10.30.0.0/16"
  az_count           = 2
  enable_nat_gateway = true   # set false to avoid NAT cost while testing
}

module "kms" {
  source        = "../../modules/security-kms"
  alias         = "alias/trading-dev"
  deletion_days = 10
}

module "ecr" {
  source = "../../modules/ecr-repo"
  name   = "trading-bot"
}

module "ecs_cluster" {
  source = "../../modules/compute-ecs-cluster"
  name   = "trading-dev"
}

module "secrets" {
  source = "../../modules/secrets-manager"
  kms_key_id = module.kms.key_id
  secrets = {
    "paper_broker_api_key"    = ""   # leave empty; set real value later
    "paper_broker_api_secret" = ""
  }
}

# 2) IAM roles for the bot (least-privilege to read only those secrets)
module "bot_iam" {
  source        = "../../modules/security-iam-bot"
  name          = "trading-bot"
  secrets_arns  = [ for k, arn in module.secrets.arns : arn ]
  kms_key_arn   = module.kms.key_arn
}

# 3) ECS service (start at desired_count=0 until you have an image)
module "bot_service" {
  source              = "../../modules/compute-ecs-service"
  name                = "trading-bot"
  cluster_arn         = module.ecs_cluster.cluster_arn
  desired_count       = 0                 # flip to 1 when ready
  cpu                 = 256
  memory              = 512
  container_image     = "${module.ecr.repository_url}:latest"

  container_env = {
    APP_ENV = "dev"
    AWS_REGION = "ca-central-1"
  }

  # map ENV_VAR names to Secret ARNs
  container_secrets = {
    BROKER_API_KEY_ARN    = module.secrets.arns["paper_broker_api_key"]
    BROKER_API_SECRET_ARN = module.secrets.arns["paper_broker_api_secret"]
  }

  task_role_arn       = module.bot_iam.task_role_arn
  exec_role_arn       = module.bot_iam.exec_role_arn
  subnet_ids          = module.vpc.private_subnet_ids
  security_group_ids  = [module.vpc.default_sg_id]
  log_kms_key_arn     = module.kms.key_arn
}
