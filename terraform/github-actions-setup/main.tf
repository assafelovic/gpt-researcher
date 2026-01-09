locals {
  project_name = var.project_name
  environment  = var.environment
}

data "terraform_remote_state" "shared" {
  backend = "s3"
  config = {
    bucket = "gg-ai-terraform-states"
    key    = "shared-infrastructure/terraform.tfstate"
    region = "us-east-1"
  }
}

data "aws_secretsmanager_secret" "secret_manager_openwebui" {
  name = var.secret_manager_openwebui
}
data "aws_secretsmanager_secret" "webui_pipeline_secret_manager" {
  name = var.webui_pipeline_secret_manager
}

# Use the shared github-actions-iam module
module "github_actions_iam" {
  source = "git::https://github.com/Gravity-Global/gg-ai-terraform-common.git//modules/github-actions-iam?ref=main"

  # Service specific configuration
  service_name   = var.service_name
  github_org     = var.github_org
  github_repo    = var.github_repo
  aws_account_id = "908027381725"

  # Infrastructure defaults
  ecs_cluster_name                  = "general-cluster"
  aws_region                        = "us-east-1"
  additional_s3_resource_arns       = []
  additional_efs_resource_arns      = []
  additional_postgres_resource_arns = []
  additional_secrets_resource_arns  = ["${data.aws_secretsmanager_secret.webui_pipeline_secret_manager.arn}"]
  # Github OIDC Provider (from shared-infrastructure)
  github_oidc_provider_arn = data.terraform_remote_state.shared.outputs.github_oidc_provider_arn
  # Otional ECR repository
  # additional_ecr_repositories = ["shared-models"]
  # Secret Manager Access
  secrets_arns = [
    "${data.aws_secretsmanager_secret.secret_manager_openwebui.arn}"
  ]
}
