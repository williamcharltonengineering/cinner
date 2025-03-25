terraform {
  backend "s3" {
    bucket         = "presis-terraform-deployment-state"
    key            = "presis-prod/deployments/terraform.tfstate"
    region         = "us-east-2"
    encrypt        = true
    dynamodb_table = "presis-terraform-state-lock"
  }
}

resource "null_resource" "create_key_dir" {
  provisioner "local-exec" {
    command = "mkdir -p ${path.cwd}/keys"
  }
  lifecycle {
    create_before_destroy = true
  }
}

resource "tls_private_key" "ssh_key" {
  algorithm = "RSA"
  rsa_bits  = 4096
  lifecycle {
    create_before_destroy = true
  }
}

resource "local_file" "private_key" {
  content  = tls_private_key.ssh_key.private_key_openssh
  filename = "${path.cwd}/keys/id_rsa"
  file_permission = "0600"
}

resource "local_file" "public_key" {
  content  = tls_private_key.ssh_key.public_key_openssh
  filename = "${path.cwd}/keys/id_rsa.pub"
}

module "redis_instance" {
  source = "../modules/redis"
  ssh_private_key = tls_private_key.ssh_key.private_key_openssh
  ssh_public_key = tls_private_key.ssh_key.public_key_openssh
  environment = "prod"
  namecheap_api_key = var.namecheap_api_key
  namecheap_api_user = var.namecheap_api_user
}