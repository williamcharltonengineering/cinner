#!/bin/bash
set -e

# Script to deploy the Presis application using Terraform

# Color formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Function to print error messages
error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
}

# Function to print success messages
success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

# Function to print warning messages
warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

# Constants
REGISTRY="192.168.1.15:5000"
REPO_NAME="presis"
TERRAFORM_DIR="$(dirname "$0")/terraform"

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    source .env
fi

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check prerequisites
for cmd in git docker terraform; do
    if ! command_exists "$cmd"; then
        echo "Error: $cmd command not found. Please install it."
        exit 1
    fi
done

# Get the latest git tag
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")
echo "Latest git tag: $LATEST_TAG"

# Build and push the Docker image
echo "Building and pushing Docker image $REGISTRY/$REPO_NAME:$LATEST_TAG"
./infra/build-image.sh "$LATEST_TAG"

# Create terraform.tfvars file
cat << EOF > $TERRAFORM_DIR/terraform.tfvars
image_tag = "$LATEST_TAG"
stripe_api_key = "${STRIPE_API_KEY}"
stripe_publishable_key = "${STRIPE_PUBLISHABLE_KEY}"
secret_key = "${SECRET_KEY}"
EOF

# Initialize and apply Terraform
cd $TERRAFORM_DIR
echo "Initializing Terraform..."

# Verify Consul connectivity
echo "Testing Consul connectivity..."
if ! curl -s --connect-timeout 5 http://192.168.1.15:8500/v1/status/leader > /dev/null; then
    error "Cannot connect to Consul at 192.168.1.15:8500. Please make sure Consul is running."
    echo "Consul backend is required for this deployment."
    exit 1
else
    success "Consul is accessible."
fi

# Initialize Terraform with Consul backend
if terraform init -migrate-state; then
    success "Terraform initialized successfully"
else
    error "Terraform initialization failed with Consul backend"
    echo "Please check the error messages above and fix the issues."
    exit 1
fi

echo "Planning Terraform deployment..."
if ! terraform plan -out=deployment.tfplan; then
    error "Terraform plan failed"
    echo "Running diagnostics to find the issue..."
    cd ..
    ./diagnose.sh
    exit 1
fi

echo "Applying Terraform deployment..."
if terraform apply deployment.tfplan; then
    success "Terraform apply succeeded!"
else
    error "Terraform apply failed"
    exit 1
fi

echo "Deployment complete!"
