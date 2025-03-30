output "container_name" {
  description = "Name of the Unraid container"
  value       = var.container_name
}

output "image" {
  description = "Docker image used for the container"
  value       = "${var.image_name}:${var.image_tag}"
}

output "deployment_script" {
  description = "Path to the generated deployment script"
  value       = local_file.unraid_script.filename
}

output "unraid_url" {
  description = "URL to access the Unraid Docker containers page"
  value       = "http://192.168.1.15/Docker"
}

output "app_url" {
  description = "URL to access the deployed application"
  value       = "http://192.168.1.15:${var.app_port}"
}

output "manual_deployment" {
  description = "Manual deployment commands (if SSH fails)"
  value       = <<-EOT
    # To manually deploy the container to Unraid:
    
    # 1. Copy the generated script to Unraid:
    scp ${local_file.unraid_script.filename} root@192.168.1.15:/tmp/
    
    # 2. Execute the script on Unraid:
    ssh root@192.168.1.15 'bash /tmp/${basename(local_file.unraid_script.filename)}'
  EOT
}
