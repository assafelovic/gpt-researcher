output "ecr_repository_url" {
  description = "ECR repository URL for building and pushing images"
  value       = module.ecr.repository_url
}
