variable "environment" {
  type = string
  description = "Specify the deployment environment (e.g. local, dev, etc.) which much be the name of a directory under infra/environments."
  default = "prod"
}
variable "ssh_private_key" {
  type        = string
  description = "The SSH Private Key for the machine running the premis app."
}
variable "ssh_public_key" {
  type        = string
  description = "The SSH Public Key for the machine running the premis app."
}
variable "namecheap_api_key" {
  type        = string
  description = "API Key to Namecheap account for updating DNS records for Premis 'env' deployments. Use TF_VAR_namecheap_api_key=... terraform apply ..."
}
variable "namecheap_api_user" {
  type        = string
  description = "API User to Namecheap account for updating DNS records for Premis 'env' deployments. Use TF_VAR_namecheap_api_user=... terraform apply ..."
}
