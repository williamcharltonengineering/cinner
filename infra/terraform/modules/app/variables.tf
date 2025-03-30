variable "image_name" {
  description = "The name of the Docker image"
  type        = string
}

variable "image_tag" {
  description = "The tag for the Docker image"
  type        = string
}

variable "container_name" {
  description = "The name of the Docker container"
  type        = string
}

variable "app_port" {
  description = "The port the app will run on"
  type        = number
  default     = 5000
}

variable "environment_vars" {
  description = "Environment variables to set in the container"
  type        = map(string)
  default     = {}
}
