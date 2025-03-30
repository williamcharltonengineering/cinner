# Presis Infrastructure

This directory contains infrastructure as code and deployment scripts for the Presis application.

## Overview

The infrastructure is managed using Terraform and Docker. The deployment process involves:

1. Building a Docker image tagged with the Git tag
2. Pushing the image to the Docker registry (192.168.1.15:5000)
3. Deploying the application using Terraform with Consul backend (192.158.1.15:8500)

## Directory Structure

- `terraform/` - Terraform configurations
  - `backend.tf` - Configures Terraform to use Consul as a backend
  - `main.tf` - Main Terraform configuration file
  - `variables.tf` - Input variables for the infrastructure
  - `outputs.tf` - Output values after deployment
  - `modules/` - Reusable Terraform modules
    - `app/` - Module for deploying the Presis application as a Docker container

- `Dockerfile` - Container definition for the Presis application
- `build-image.sh` - Script to build and push the Docker image
- `deploy.sh` - Main deployment script
- `deploy-local.sh` - Alternative deployment script for local-only deployment
- `diagnose.sh` - Diagnostic script to troubleshoot deployment issues

## Deployment Requirements

- Docker (with access to 192.168.1.15:5000 Docker registry)
- Terraform v1.0.0 or newer
- Git
- Access to Consul running at 192.158.1.15:8500
- Environment variables (can be in a .env file in the root directory):
  - `STRIPE_API_KEY` - Your Stripe API key
  - `STRIPE_PUBLISHABLE_KEY` - Your Stripe publishable key
  - `SECRET_KEY` - Secret key for Flask sessions

## Deployment Options

### Standard Deployment

To deploy the application using the registry and Terraform backend:

```bash
# Navigate to project root
cd /path/to/presis

# Run the deployment script
./infra/deploy.sh
```

This will:
1. Look for the latest git tag to determine the image version
2. Build and push the Docker image to the registry with the tagged version
3. Apply the Terraform configuration to deploy the application

### Local Deployment (Without Registry)

If you're developing locally and want to test without the registry:

```bash
# Navigate to project root
cd /path/to/presis

# Run the local deployment script
./infra/deploy-local.sh
```

This will:
1. Build a Docker image with a "local" tag
2. Run a Docker container locally on port 5000
3. Mount the instance directory for database persistence

## Troubleshooting

If you encounter deployment issues:

```bash
# Run the diagnostic script
./infra/diagnose.sh
```

This will:
1. Check Docker configuration and connectivity
2. Test connectivity to the registry (192.168.1.15:5000)
3. Verify connectivity to Consul (192.158.1.15:8500)
4. Check Docker's insecure-registries configuration
5. Verify Git tag availability
6. Provide detailed recommendations for fixing issues

## Docker & Consul Requirements

### Docker Registry (192.168.1.15:5000)
This deployment requires access to a Docker registry at 192.168.1.15:5000 which will be used to store the built Docker images. Since this registry uses HTTP instead of HTTPS, you'll need to configure Docker to trust it:

1. For macOS/Windows:
   - Open Docker Desktop
   - Go to Settings/Preferences → Docker Engine
   - Add `"insecure-registries": ["192.168.1.15:5000"]` to the JSON configuration:
     ```json
     {
       "insecure-registries": ["192.168.1.15:5000"],
       ... other settings ...
     }
     ```
   - Click "Apply & Restart"

2. For Linux:
   - Edit `/etc/docker/daemon.json`
   - Add: `{"insecure-registries": ["192.168.1.15:5000"]}`
   - Restart Docker: `sudo systemctl restart docker`

### Unraid Docker Deployment
This infrastructure is configured to deploy Docker containers directly to your Unraid server at 192.168.1.15. The deployment process:

1. Generates a deployment shell script for your Unraid server
2. Attempts to use SSH to deploy the container directly to Unraid
3. If SSH fails, provides manual instructions for deployment

Requirements for Unraid deployment:
- Unraid server must be running at 192.168.1.15
- Docker must be enabled on your Unraid server
- SSH access to your Unraid server (ideally with key authentication set up)
- Network connectivity between your deployment machine and Unraid

#### SSH Setup for Automated Deployment

For the automated deployment to work seamlessly, you should set up passwordless SSH access to your Unraid server:

1. Generate an SSH key pair if you don't already have one:
   ```
   ssh-keygen -t rsa -b 4096
   ```

2. Copy your public key to the Unraid server:
   ```
   ssh-copy-id root@192.168.1.15
   ```

3. Test your SSH connection:
   ```
   ssh root@192.168.1.15 'echo "SSH connection successful"'
   ```

If SSH authentication fails during deployment, the Terraform output will provide clear instructions on how to deploy manually using the generated script.

### Consul Backend (192.168.1.15:8500)
This deployment uses Consul running at 192.168.1.15:8500 as the Terraform state backend. Ensure:

1. Consul is running and accessible from your machine
2. The Consul KV store is writable by your connection
3. Network connectivity allows reaching port 8500 on the host

The deployment will fail if Consul is not accessible, as this is a hard requirement.

## CI/CD Integration

The infrastructure is designed to be used in a CI/CD pipeline, where:

1. The build system creates a git tag for each release
2. The deploy script uses the git tag to version the Docker image
3. Terraform applies the new image to the infrastructure

## Customization

You can customize the deployment by:

1. Modifying `terraform.tfvars` (created by deploy.sh)
2. Editing environment variables in `.env`
3. Adding more resources to the Terraform configuration
