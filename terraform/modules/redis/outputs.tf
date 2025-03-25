output "server_ip_address" {
  description = "The IP address of the server running the premis app."
  value = linode_instance.server.ip_address
}
output "redis_client_ca_certificate_pem" {
  description = "The PEM-encoded certificate for the Redis Client CA."
  value       = tls_self_signed_cert.ca_cert.cert_pem
}
output "redis_cli_client_private_key" {
  description = "The PEM-encoded private key for the Redis CLI Client."
  value       = tls_private_key.redis_client_key.private_key_pem
  sensitive   = true
}
output "redis_cli_client_certificate_pem" {
  description = "The PEM-encoded certificate for the Redis CLI Client, signed by the CA."
  value       = tls_locally_signed_cert.redis_client_cert.cert_pem
}