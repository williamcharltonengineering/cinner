output "linode_ip" {
  value = module.redis_instance.server_ip_address
}
output "redis_client_ca_certificate_pem" {
  description = "The PEM-encoded certificate for the Redis Client CA."
  value       = module.redis_instance.redis_client_ca_certificate_pem
}
output "redis_cli_client_private_key" {
  description = "The PEM-encoded private key for the Redis CLI Client."
  value       = module.redis_instance.redis_cli_client_private_key
  sensitive   = true
}
output "redis_cli_client_certificate_pem" {
  description = "The PEM-encoded certificate for the Redis CLI Client, signed by the CA."
  value       = module.redis_instance.redis_cli_client_certificate_pem
}