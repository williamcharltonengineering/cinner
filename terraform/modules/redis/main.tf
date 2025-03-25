# Generate a secure root password
resource "random_password" "root_password" {
  length  = 16
  special = true
}

resource "random_password" "redis_encryption_password" {
  length  = 16
  special = true
}

resource "linode_instance" "server" {
  depends_on = [ local_file.redis_server_cert_file ]
  label     = "presis-app-${var.environment}-us-ord"
  type      = "g6-nanode-1"
  region    = "us-ord"
  image     = "linode/debian11"
  authorized_keys = [trimspace(var.ssh_public_key)]
  root_pass = random_password.root_password.result
}

# Output the generated root password
output "linode_instance_root_password" {
  value       = random_password.root_password.result
  description = "The root password for the Linode instance"
  sensitive   = true
}

data "http" "my_ip_address" {
//   url = "https://ifconfig.me"
  url = "https://api.ipify.org"
}

# https://www.namecheap.com/support/api/intro/
provider "namecheap" {
  user_name = var.namecheap_api_user
  api_user = var.namecheap_api_user
  api_key = var.namecheap_api_key
  client_ip = data.http.my_ip_address.response_body
  use_sandbox = false
}

provider "acme" {
  server_url = "https://acme-staging-v02.api.letsencrypt.org/directory"
//   server_url = "https://acme-v02.api.letsencrypt.org/directory"
}

resource "namecheap_domain_records" "presis-pro" {
  depends_on = [ linode_instance.server ]
  domain = "presis.pro"
  mode = "MERGE"

  # ipv4
  record {
    hostname = "@" # root domain
    type = "A"
    address = linode_instance.server.ip_address
    ttl = 300
  }

  # ipv6
  record {
    hostname = "@" # root domain
    type = "AAAA"
    address = split("/", linode_instance.server.ipv6)[0] # split to remove subnet from address i.e. /128
    ttl = 300
  }

  # ipv4
  record {
    hostname = "app"
    type = "A"
    address = linode_instance.server.ip_address
    ttl = 300
  }

  # ipv6
  record {
    hostname = "app"
    type = "AAAA"
    address = split("/", linode_instance.server.ipv6)[0] # split to remove subnet from address i.e. /128
    ttl = 300
  }
}

resource "null_resource" "server_ssl" {
  provisioner "local-exec" {
    command = "mkdir -p ${path.cwd}/../${var.environment}/ssl"
  }
}
resource "tls_private_key" "ca_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}
resource "tls_self_signed_cert" "ca_cert" {
  private_key_pem = tls_private_key.ca_key.private_key_pem

  subject {
    common_name  = "Root CA"
    organization = "William Charlton Engineering"
  }

  is_ca_certificate = true
  validity_period_hours = 8760
  allowed_uses = [
    "cert_signing",
    "digital_signature",
    "key_encipherment",
  ]
}
resource "local_file" "ca_pem" {
  depends_on = [ null_resource.server_ssl ]
  content  = "${tls_self_signed_cert.ca_cert.cert_pem}"
  filename = "${path.cwd}/../${var.environment}/ssl/CA.pem"
}
resource "tls_private_key" "redis_server_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}
resource "local_file" "redis_server_key_file" {
  depends_on = [ null_resource.server_ssl ]
  content  = "${tls_private_key.redis_server_key.private_key_pem}"
  filename = "${path.cwd}/../${var.environment}/ssl/RedisServer.key"
}
resource "tls_cert_request" "redis_server_csr" {
  private_key_pem = tls_private_key.redis_server_key.private_key_pem

  subject {
    common_name  = "presis.pro"
  }
}
resource "tls_locally_signed_cert" "redis_server_cert" {
  cert_request_pem   = tls_cert_request.redis_server_csr.cert_request_pem
  ca_private_key_pem = tls_private_key.ca_key.private_key_pem
  ca_cert_pem        = tls_self_signed_cert.ca_cert.cert_pem

  validity_period_hours = 8760  # 1 year, adjust as needed
  set_subject_key_id    = true

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "client_auth",
    "server_auth",
  ]
}
resource "local_file" "redis_server_cert_file" {
  depends_on = [ null_resource.server_ssl ]
  content  = "${tls_locally_signed_cert.redis_server_cert.cert_pem}"
  filename = "${path.cwd}/../${var.environment}/ssl/RedisServer.pem"
}

resource "tls_private_key" "redis_client_key" {
  algorithm = "RSA"
  rsa_bits  = 2048
}
resource "local_file" "redis_client_key_file" {
  depends_on = [ null_resource.server_ssl ]
  content  = "${tls_private_key.redis_client_key.private_key_pem}"
  filename = "${path.cwd}/../${var.environment}/ssl/RedisClient.key"
}
resource "tls_cert_request" "redis_client_csr" {
  private_key_pem = tls_private_key.redis_client_key.private_key_pem

  subject {
    common_name  = "Redis Client"
  }
}
resource "tls_locally_signed_cert" "redis_client_cert" {
  cert_request_pem   = tls_cert_request.redis_client_csr.cert_request_pem
  ca_private_key_pem = tls_private_key.ca_key.private_key_pem
  ca_cert_pem        = tls_self_signed_cert.ca_cert.cert_pem

  validity_period_hours = 8760  # 1 year, adjust as needed
  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "client_auth",
  ]
}
resource "local_file" "redis_client_cert_file" {
  depends_on = [ null_resource.server_ssl ]
  content  = "${tls_locally_signed_cert.redis_client_cert.cert_pem}"
  filename = "${path.cwd}/../${var.environment}/ssl/RedisClient.pem"
}
# TODO: validate this can be removed and do so
resource "local_file" "ca_cert_chain" {
  depends_on = [ null_resource.server_ssl ]
  content  = "${tls_locally_signed_cert.redis_client_cert.cert_pem}${tls_self_signed_cert.ca_cert.cert_pem}"
  filename = "${path.cwd}/../${var.environment}/ssl/CACertChain.pem"
}

resource "null_resource" "machine_setup" {
  depends_on = [ linode_instance.server ]
  connection {
    type     = "ssh"
    user     = "root"
    private_key = var.ssh_private_key
    host     = linode_instance.server.ip_address
  }
  provisioner "file" {
    source = "${path.module}/machine-setup.sh"
    destination = "/tmp/machine-setup.sh"
  }
  provisioner "remote-exec" {
    inline = [
      "echo 'ENVIRONMENT=${var.environment}' >> /etc/environment",
      "chmod +x /tmp/machine-setup.sh",
      "/tmp/machine-setup.sh ${random_password.redis_encryption_password.result}",
      # "REDIS_SSH_PUBKEY=\"${var.ssh_public_key}\" /tmp/machine-setup.sh foofinheimer", # ${random_password.redis_encryption_password.result}",
      "reboot",
    ]
  }
  provisioner "local-exec" {
    command = <<-EOT
      echo "This loop should complete in approximately 2m20s."
      while ! nc -z ${linode_instance.server.ip_address} 22; do
        echo "Waiting for reboot..."
        sleep 5
      done
    EOT
  }
}

resource "null_resource" "sync_to_linode" {
  depends_on = [ local_file.redis_client_cert_file, local_file.redis_server_cert_file, null_resource.machine_setup, tls_locally_signed_cert.redis_client_cert ]
  connection {
    type     = "ssh"
    user     = "root"
    private_key = var.ssh_private_key
    host     = linode_instance.server.ip_address
  }
  provisioner "file" {
    source = "./ssl/RedisServer.key"
    destination = "/etc/ssl/redis.key"
  }
  provisioner "file" {
    source = "./ssl/RedisServer.pem"
    destination = "/etc/ssl/redis.crt"
  }
  provisioner "file" {
    source = "./ssl/CA.pem"
    destination = "/etc/ssl/redis-ca.crt"
  }
  provisioner "remote-exec" {
    inline = [
      "set -x",
      "echo '${tls_self_signed_cert.ca_cert.cert_pem}' | tee -a /etc/ssl/redis-ca.crt",
      "chown redis:redis /etc/ssl/redis.crt",
      "chown redis:redis /etc/ssl/redis.key",
      "chown redis:redis /etc/ssl/redis-ca.crt",
    ]
  }
  provisioner "file" {
    source = "${path.module}/conf/redis.conf"
    destination = "/etc/redis/redis.conf"
  }
  provisioner "remote-exec" {
    inline = [ 
      "chown redis:redis /etc/redis/redis.conf",
    ]
  }
  triggers = {
    always_run = "${timestamp()}"
  }
}

resource "null_resource" "remote_start" {
  depends_on = [null_resource.sync_to_linode]
  connection {
    type     = "ssh"
    user     = "root"
    private_key = var.ssh_private_key
    host     = linode_instance.server.ip_address
  }
  provisioner "remote-exec" {

    inline = [ 
      "set -x",
      "systemctl enable redis-server.service",
      "systemctl stop redis-server.service",
      "systemctl start redis-server.service",
      "systemctl status redis.service --no-pager",
    ]
  }
  triggers = {
    always_run = "${timestamp()}"
  }
}
resource "null_resource" "ping_redis" {
  depends_on = [null_resource.remote_start]
  provisioner "local-exec" {
    command = <<-EOT
      until echo PING | \
      redis-cli --tls \
                --cacert ./ssl/CA.pem \
                --cert ./ssl/RedisServer.pem \
                --key ./ssl/RedisServer.key \
                -h app.presis.pro \
                -p 6379 | grep -m 1 'PONG'; do
        echo "Waiting for Redis..."
        sleep 5
      done
      echo "Redis is up and running!"
    EOT
  }
  triggers = {
    always_run = "${timestamp()}"
  }
}
resource "null_resource" "load_data_to_redis" {
  depends_on = [null_resource.ping_redis]
  provisioner "local-exec" {
    command = "${path.module}/load-redis.sh"
  }
  triggers = {
    always_run = "${timestamp()}"
  }
}

