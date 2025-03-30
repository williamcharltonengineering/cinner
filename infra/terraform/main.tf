terraform {
  required_providers {
    http = {
      source  = "hashicorp/http"
      version = "~> 3.0"
    }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4.0"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2.0"
    }
  }
  required_version = ">= 1.0.0"
}

# Use the app module to deploy the presis application
module "presis_app" {
  source = "./modules/app"

  image_name     = "williamcharltonengineering/presis"
  image_tag      = var.image_tag
  container_name = "presis-app"
  app_port       = 5000
  environment_vars = {
    FLASK_ENV                = var.environment
    STRIPE_API_KEY           = var.stripe_api_key
    STRIPE_PUBLISHABLE_KEY   = var.stripe_publishable_key
    SECRET_KEY               = var.secret_key
    SQLALCHEMY_DATABASE_URI  = var.database_uri
  }
}
