# ECS Service Outputs
output "ecs_service_name" {
  description = "Name of the ECS service"
  value       = module.ecs_service.service_name
}

output "ecs_service_arn" {
  description = "ARN of the ECS service"
  value       = module.ecs_service.service_arn
}

output "ecs_cluster_arn" {
  description = "ARN of the ECS cluster"
  value       = module.ecs_service.cluster_arn
}

output "task_definition_arn" {
  description = "ARN of the task definition"
  value       = module.ecs_service.task_definition_arn
}

output "cloudmap_service_arn" {
  description = "ARN of the CloudMap service"
  value       = module.ecs_service.cloudmap_service_arn
}

output "service_discovery_endpoint" {
  description = "Service discovery endpoint for inter-service communication"
  value       = "${local.cloudmap_service_name}.${local.cloudmap_namespace}:${local.container_port}"
}

output "security_group_id" {
  description = "ID of the service security group"
  value       = module.ecs_service.security_group_id
}

output "log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = module.ecs_service.log_group_name
}

output "log_group_arn" {
  description = "ARN of the CloudWatch log group"
  value       = module.ecs_service.log_group_arn
}

output "deployment_summary" {
  description = "Summary of the deployed service"
  value = {
    service_name          = local.service_name
    cluster_name          = local.ecs_cluster_name
    container_port        = local.container_port
    service_discovery_url = "${local.cloudmap_service_name}.${local.cloudmap_namespace}:${local.container_port}"
    ecr_repository_url    = local.ecr_repository_url
    image_tag             = coalesce(var.image_tag, local.image_tag)
    environment           = local.environment
    cpu                   = module.ecs_service.cpu
    memory                = module.ecs_service.memory
    desired_count         = module.ecs_service.desired_count
  }
}
