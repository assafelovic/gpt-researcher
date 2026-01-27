variable "image_tag" {
  description = "Docker image tag to deploy for the application"
  type        = string
  default     = "v1.0.5"

  validation {
    condition     = can(regex("^[a-zA-Z0-9._-]+$", var.image_tag))
    error_message = "Image tag must contain only alphanumeric characters, dots, underscores, and hyphens."
  }
}

variable "ecr_repository_name" {
  description = "ECR repository name to pull image from (defaults to project_name)"
  type        = string
  default     = ""
}

variable "environment" {
  description = "Environment name (affects resource naming and tagging)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "desired_count" {
  description = "Number of service instances to run"
  type        = number
  default     = 1

  validation {
    condition     = var.desired_count >= 1 && var.desired_count <= 10
    error_message = "Desired count must be between 1 and 10."
  }
}

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"

  validation {
    condition     = can(regex("^[a-z]{2}-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "AWS region must be in valid format (e.g., us-east-1)."
  }
}

variable "force_new_deployment" {
  description = "Force a new deployment when updating the service"
  type        = bool
  default     = false
}

variable "enable_service_discovery" {
  description = "Enable CloudMap service discovery for the application"
  type        = bool
  default     = true
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring"
  type        = bool
  default     = false
}

variable "cpu" {
  description = "CPU units for the service task (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 2048

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "memory" {
  description = "Memory in MB for the service task (must be compatible with CPU)"
  type        = number
  default     = 10240

  validation {
    condition     = var.memory >= 512 && var.memory <= 30720
    error_message = "Memory must be between 512 MB and 30720 MB."
  }
}
variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}

  validation {
    condition     = alltrue([for k, v in var.additional_tags : can(regex("^[\\w\\s.-]+$", k))])
    error_message = "Tag keys must contain only alphanumeric characters, spaces, periods, and hyphens."
  }
}

variable "enable_gg_vpn_access" {
  description = "Allow access from GG VPN network (192.168.158.0/24)"
  type        = bool
  default     = true
}

variable "enable_internal_vpc_access" {
  description = "Allow access from internal VPC network (192.168.144.0/23)"
  type        = bool
  default     = true
}

variable "custom_access_cidr_blocks" {
  description = "Additional CIDR blocks to allow access from"
  type        = list(string)
  default     = []

  validation {
    condition     = alltrue([for cidr in var.custom_access_cidr_blocks : can(cidrhost(cidr, 0))])
    error_message = "All values must be valid CIDR blocks (e.g., 10.0.0.0/8)."
  }
}

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.log_retention_days)
    error_message = "Log retention days must be one of the valid CloudWatch values: 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653."
  }
}

variable "enable_container_insights" {
  description = "Enable CloudWatch Container Insights"
  type        = bool
  default     = false
}

variable "deployment_configuration" {
  description = "ECS service deployment configuration"
  type = object({
    maximum_percent         = optional(number, 200)
    minimum_healthy_percent = optional(number, 50)
  })
  default = {
    maximum_percent         = 200
    minimum_healthy_percent = 50
  }

  validation {
    condition = (
      var.deployment_configuration.maximum_percent >= 100 &&
      var.deployment_configuration.maximum_percent <= 200 &&
      var.deployment_configuration.minimum_healthy_percent >= 0 &&
      var.deployment_configuration.minimum_healthy_percent <= 100
    )
    error_message = "Maximum percent must be 100-200 and minimum healthy percent must be 0-100."
  }
}

variable "enable_execute_command" {
  description = "Enable ECS Exec for debugging service containers"
  type        = bool
  default     = false
}

# ==============================================================================
# 🔧 APPLICATION CONFIGURATION
# ==============================================================================

variable "project_name" {
  description = "Name of the project (used in application configuration)"
  type        = string
  default     = "gpt-researcher"

  validation {
    condition     = length(var.project_name) > 0 && length(var.project_name) <= 100
    error_message = "Project name must be between 1 and 100 characters."
  }
}

variable "cors_origins" {
  description = "CORS origins for the application"
  type        = string
  default     = ""
}

variable "access_token_expire_minutes" {
  description = "Access token expiration time in minutes"
  type        = string
  default     = "11520" # 8 days (60 * 24 * 8)

  validation {
    condition     = can(regex("^[0-9]+$", var.access_token_expire_minutes)) && tonumber(var.access_token_expire_minutes) > 0
    error_message = "Access token expiration must be a positive number."
  }
}

# ==============================================================================
# 📧 EMAIL CONFIGURATION (Optional)
# ==============================================================================

variable "smtp_host" {
  description = "SMTP host for email sending (optional)"
  type        = string
  default     = ""
}

variable "smtp_port" {
  description = "SMTP port for email sending"
  type        = string
  default     = "587"

  validation {
    condition     = can(regex("^[0-9]+$", var.smtp_port)) && tonumber(var.smtp_port) >= 1 && tonumber(var.smtp_port) <= 65535
    error_message = "SMTP port must be a valid port number (1-65535)."
  }
}

variable "smtp_tls" {
  description = "Enable TLS for SMTP"
  type        = string
  default     = "true"

  validation {
    condition     = contains(["true", "false"], var.smtp_tls)
    error_message = "SMTP TLS must be 'true' or 'false'."
  }
}

variable "smtp_ssl" {
  description = "Enable SSL for SMTP"
  type        = string
  default     = "false"

  validation {
    condition     = contains(["true", "false"], var.smtp_ssl)
    error_message = "SMTP SSL must be 'true' or 'false'."
  }
}

variable "smtp_user" {
  description = "SMTP username (optional)"
  type        = string
  default     = ""
}

variable "emails_from_name" {
  description = "Display name for outgoing emails"
  type        = string
  default     = ""
}

variable "email_reset_token_expire_hours" {
  description = "Password reset token expiration time in hours"
  type        = string
  default     = "48"

  validation {
    condition     = can(regex("^[0-9]+$", var.email_reset_token_expire_hours)) && tonumber(var.email_reset_token_expire_hours) > 0
    error_message = "Email reset token expiration must be a positive number."
  }
}

variable "email_test_user" {
  description = "Test email user for development"
  type        = string
  default     = "test@example.com"

  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.email_test_user))
    error_message = "Email test user must be a valid email address."
  }
}

variable "openwebui_secret_manager" {
  description = "Name of the secret manager existing in AWS Secrets Manager for OpenWebUI"
  type        = string
  default     = "arn:aws:secretsmanager:us-east-1:908027381725:secret:prod/openwebui/tools-bGKfLv"
}

variable "secret_manager_fargate_custom" {
  description = "Name of the secret manager existing in AWS Secrets Manager for Fargate custom"
  type        = string
  default     = "arn:aws:kms:us-east-1:908027381725:key/b4924fa6-0bee-430f-adec-5f81ac039291"
}

variable "ecs_service_environment" {
  description = "Environment for the ECS service"
  type        = string
  default     = "production"
}

variable "webui_pipieline_credentials" {
  description = "Credentials for the Excel Add-in environment was storaged in AWS Secrets Manager"
  type        = string
  default     = "arn:aws:secretsmanager:us-east-1:908027381725:secret:webUIpipelinesOpenAIApiKey-uUPw5T"
}

variable "cloudmap_service_name" {
  description = "CloudMap service name for service discovery (the part before .ggai)"
  type        = string
  default     = "gpt-researcher"
}
