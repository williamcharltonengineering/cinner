variable "docker_host" {
  description = "The Docker host to connect to"
  type        = string
  default     = "unix:///var/run/docker.sock"
}

variable "image_tag" {
  description = "The tag for the presis Docker image (typically the git tag)"
  type        = string
}

variable "environment" {
  description = "The environment to deploy to (e.g., development, production)"
  type        = string
  default     = "production"
}

variable "stripe_api_key" {
  description = "The Stripe API key"
  type        = string
  sensitive   = true
}

variable "stripe_publishable_key" {
  description = "The Stripe publishable key"
  type        = string
}

variable "secret_key" {
  description = "The secret key for Flask sessions"
  type        = string
  sensitive   = true
}

variable "database_uri" {
  description = "The SQLAlchemy database URI"
  type        = string
  default     = "sqlite:///instance/users.db"
}
