variable "secret_manager_openwebui" {
  description = "Value of the secret manager openwebui"
  type        = string
  default     = "arn:aws:secretsmanager:us-east-1:908027381725:secret:prod/openwebui/tools-bGKfLv"
}

variable "project_name" {
  description = "Name of the project for resource lookups"
  type        = string
  default     = "gpt-researcher"
}

variable "environment" {
  description = "Deployment environment suffix for resource lookups"
  type        = string
  default     = "prod"
}

variable "webui_pipeline_secret_manager" {
  description = "OAth client credentials for GPT Researcher"
  type        = string
  default     = "arn:aws:secretsmanager:us-east-1:908027381725:secret:webUIpipelinesOpenAIApiKey-uUPw5T"
}

variable "service_name" {
  description = "The name for creating github actions role"
  type        = string
  default     = "gpt-researcher"
}

variable "github_org" {
  description = "Owner of this repository"
  type        = string
  default     = "Gravity-Global"
}

variable "github_repo" {
  description = "The name of this repository"
  type        = string
  default     = "gpt-researcher"
}
