terraform {
  required_providers {
    linode = {
        source  = "linode/linode"
        # version = "1.25.0" # Current latest version as of 2021-12-03
    }
    namecheap = {
      source = "namecheap/namecheap"
      version = ">= 2.0.0"
    }
    acme = {
      source = "vancluever/acme"
      version = "~> 2.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 3.0"
    }
  }
}