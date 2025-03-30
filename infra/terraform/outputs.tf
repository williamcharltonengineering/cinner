output "app_container_name" {
  description = "Name of the Unraid container for Presis"
  value       = module.presis_app.container_name
}

output "app_image" {
  description = "Docker image used for Presis"
  value       = module.presis_app.image
}

output "app_deployment_script" {
  description = "Path to the generated deployment script"
  value       = module.presis_app.deployment_script
}

output "manual_deployment" {
  description = "Manual deployment commands (if SSH fails)"
  value       = module.presis_app.manual_deployment
}

output "unraid_url" {
  description = "URL to access the Unraid Docker containers page"
  value       = module.presis_app.unraid_url
}

output "app_url" {
  description = "URL to access the deployed Presis application"
  value       = module.presis_app.app_url
}
