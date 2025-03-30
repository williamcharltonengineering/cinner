# Configure the Terraform backend to use Consul
terraform {
  backend "consul" {
    address = "192.168.1.15:8500"  # Fixed IP address 
    scheme  = "http"
    path    = "terraform/state/presis"
    gzip    = true
  }
}
