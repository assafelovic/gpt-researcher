locals {
  # Service configuration
  service_name = var.project_name
  environment  = var.environment
  # ECR configuration
  ecr_repository_name = var.project_name
  # Common tags
  common_tags = {
    Environment = local.environment
    Service     = local.service_name
    Project     = var.project_name
    ManagedBy   = "terraform"
    Component   = "service"
  }
}

# ECR Repository for application images
module "ecr" {
  source = "git::https://github.com/Gravity-Global/gg-ai-terraform-common.git//modules/ecr?ref=main"

  repository_name      = local.ecr_repository_name
  image_tag_mutability = "IMMUTABLE"
  scan_on_push         = false

  # Production lifecycle policy
  lifecycle_policy = "production_policy"

  # Encryption configuration
  encryption_configuration = {
    encryption_type = "AES256"
  }

  tags = merge(local.common_tags, {
    Name = "ECR Repository - ${local.service_name}"
  })
}
