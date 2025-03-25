variable "namecheap_api_key" {
  type        = string
  description = "API Key to Namecheap account for updating DNS records for Premis 'env' deployments. Use TF_VAR_namecheap_api_key=... terraform apply ..."
}
variable "namecheap_api_user" {
  type        = string
  description = "API User to Namecheap account for updating DNS records for Premis 'env' deployments. Use TF_VAR_namecheap_api_user=... terraform apply ..."
}