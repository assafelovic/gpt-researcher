variable "project_name" {
  description = "Name of the project (used in application configuration)"
  type        = string
  default     = "gpt-researcher"

  validation {
    condition     = length(var.project_name) > 0 && length(var.project_name) <= 100
    error_message = "Project name must be between 1 and 100 characters."
  }
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
