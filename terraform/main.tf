# Remote state to pull ECR repository details managed in terraform/ecr-setup
data "terraform_remote_state" "ecr" {
  backend = "s3"

  config = {
    bucket         = "gg-ai-terraform-states"
    key            = "production/gpt-researcher/ecr.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-locks"
    encrypt        = true
  }
}
locals {
  # Remote ECR url is preferred; fall back to live lookup only when missing
  use_remote_ecr_url = try(data.terraform_remote_state.ecr.outputs.ecr_repository_url != "", false)
}
data "aws_ecr_repository" "app" {
  count = local.use_remote_ecr_url ? 0 : 1
  name  = var.ecr_repository_name != "" ? var.ecr_repository_name : var.project_name
}
data "aws_secretsmanager_secret" "openwebui_secret_manager" {
  name = var.openwebui_secret_manager
}
data "aws_secretsmanager_secret" "webui_pipieline_credentials" {
  name = var.webui_pipieline_credentials
}

# Common module for shared constants - NOW REMOTE
module "common" {
  source = "git::https://github.com/Gravity-Global/gg-ai-terraform-common.git//modules/common?ref=main"
}

# Local values for computed and reusable configurations
locals {
  # Service configuration
  service_name = var.project_name
  environment  = var.environment

  # ECR configuration
  ecr_repository_name = local.service_name
  image_tag           = var.image_tag
  # Prefer remote state output but fall back to querying the repository directly
  ecr_repository_url = try(
    data.terraform_remote_state.ecr.outputs.ecr_repository_url,
    data.aws_ecr_repository.app[0].repository_url,
  )

  # ECS configuration - using common module with validation
  ecs_cluster_name = module.common.available_clusters["general"]
  container_port   = 3535 # Gradio default port

  # CloudMap configuration
  cloudmap_namespace    = module.common.cloudmap_service_discovery_namespace # "ggai"
  cloudmap_service_name = var.cloudmap_service_name

  # Common tags
  common_tags = {
    Environment = local.environment
    Service     = local.service_name
    Purpose     = "gpt-researcher-service"
    CreatedBy   = "terraform"
  }

  # Health check configuration
  health_check = {
    command      = ["CMD-SHELL", "curl -f http://localhost:${local.container_port}/health || exit 1"]
    interval     = 30
    timeout      = 5
    retries      = 3
    start_period = 60
  }
}

# Data source to get VPC CIDR block
data "aws_vpc" "main" {
  id = module.common.vpc_id
}

# Security Group for EFS NFS access
resource "aws_security_group" "efs_nfs" {
  name        = "${var.project_name}-efs-nfs-sg"
  description = "Security group for EFS NFS access"
  vpc_id      = module.common.vpc_id

  ingress {
    description     = "NFS from VPC"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = ["sg-049461f6151961660"] # security group of ECS Pipeline for using
  }

  ingress {
    description     = "NFS from ECS Service"
    from_port       = 2049
    to_port         = 2049
    protocol        = "tcp"
    security_groups = [module.ecs_service.security_group_id]
  }

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    {
      Name = "${var.project_name}-efs-nfs-sg"
    }
  )
}

# IAM policy for secrets access - using base secret ARN instead of field-specific ARN
resource "aws_iam_role_policy" "website_content_agents_secrets_policy" {
  name = "${var.project_name}-secrets-access"
  role = module.ecs_service.execution_role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          "${data.aws_secretsmanager_secret.openwebui_secret_manager.arn}",
          "${data.aws_secretsmanager_secret.webui_pipieline_credentials.arn}",
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:GenerateDataKey"
        ]
        Resource = [
          "${var.secret_manager_fargate_custom}"
        ]
      }
    ]
  })
}

# ECS Service for Website Content Agents - NOW REMOTE
module "ecs_service" {
  source = "git::https://github.com/Gravity-Global/gg-ai-terraform-common.git//modules/ecs-service?ref=main"

  service_name    = local.service_name
  container_image = "${local.ecr_repository_url}:${var.image_tag}"

  container_port = local.container_port
  environment    = local.environment

  cpu           = var.cpu
  memory        = var.memory
  desired_count = var.desired_count

  cluster_name = local.ecs_cluster_name
  vpc_id       = module.common.vpc_id
  subnet_ids   = module.common.subnet_ids

  environment_variables = {
    PORT           = local.container_port
    AWS_REGION     = "us-east-1"
    DB_PATH        = "/pipelines/gravity-researcher/research_tasks.db"
    S3_ACCESS_URL  = "https://aigeneratedfiles-glondon.msappproxy.net/"
    S3_BUCKET      = "ggai-generated-files"
    S3_KEY_PREFIX  = "ai_generated_research_reports/"
    TEMP_DIRECTORY = "/pipelines/gravity-researcher/tmp"
  }

  secrets = {
    OPENAI_API_KEY         = "${data.aws_secretsmanager_secret.webui_pipieline_credentials.arn}"
    AWS_ACCESS_KEY         = "${data.aws_secretsmanager_secret.openwebui_secret_manager.arn}:AI_GENERATED_S3_AWS_ACCESS_KEY::"
    AWS_SECRET_KEY         = "${data.aws_secretsmanager_secret.openwebui_secret_manager.arn}:AI_GENERATED_S3_AWS_SECRET_KEY::"
    GOOGLE_API_KEY         = "${data.aws_secretsmanager_secret.openwebui_secret_manager.arn}:GOOGLE_PSE_API_KEY::"
    GOOGLE_CX_KEY          = "${data.aws_secretsmanager_secret.openwebui_secret_manager.arn}:GOOGLE_PSE_ENGINE_ID::"
    SEND_EMAIL_PASSWORD    = "${data.aws_secretsmanager_secret.openwebui_secret_manager.arn}:SENDING_EMAIL_PASSWORD::"
    SEND_EMAIL_USERNAME    = "${data.aws_secretsmanager_secret.openwebui_secret_manager.arn}:SENDING_EMAIL_USERNAME::"
    SEND_EMAIL_WEBHOOK_URL = "${data.aws_secretsmanager_secret.openwebui_secret_manager.arn}:SENDING_EMAIL_WEBHOOK_URL::"
  }

  # KMS key for secrets decryption
  secrets_kms_key_id = "arn:aws:kms:us-east-1:908027381725:key/b4924fa6-0bee-430f-adec-5f81ac039291"

  # Override IAM policy to use base secret ARN instead of field-specific ARN
  skip_iam_policy_creation = true

  create_efs                 = false
  efs_provisioned_throughput = 1 # Required for validation even when EFS is disabled
  efs_volumes = [
    {
      name            = "pipelines"
      file_system_id  = "fs-09c4afb9c80f325a1"
      access_point_id = "fsap-0c36252f7b9e45d71"
      mount_point     = "/pipelines"
    }
  ]

  custom_ingress_rules = [
    # {
    #   description     = "Access from n8n service"
    #   from_port       = local.container_port
    #   to_port         = local.container_port
    #   protocol        = "tcp"
    #   cidr_blocks     = null
    #   security_groups = [module.common.available_security_groups["ecs-n8n"]]
    # },
    {
      description     = "Access from Microsoft Entra App Proxy"
      from_port       = local.container_port
      to_port         = local.container_port
      protocol        = "tcp"
      cidr_blocks     = [module.common.network_access_patterns.microsoft_entra_app_proxy]
      security_groups = null
    }
  ]

  health_check = local.health_check

  enable_execute_command      = true
  service_discovery_namespace = local.cloudmap_namespace
  cloudmap_service_name       = local.cloudmap_service_name

  tags = {
    CloudMapServiceName = local.cloudmap_service_name
    CloudMapNamespace   = local.cloudmap_namespace
    CreatedBy           = "terraform"
    Project             = var.project_name
  }

  depends_on = [
    module.common
  ]
}
