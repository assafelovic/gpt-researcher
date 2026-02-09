output "github_actions_role_arn" {
  description = "ARN of the GitHub Actions IAM role - use this in repository secrets as AWS_ROLE_ARN"
  value       = module.github_actions_iam.role_arn
}

output "github_oidc_provider_arn" {
  description = "ARN of the GitHub OIDC provider"
  value       = module.github_actions_iam.oidc_provider_arn
}
