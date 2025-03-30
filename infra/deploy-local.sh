#!/bin/bash
set -e

# Script to deploy the Presis application locally (without using the remote registry)
# This is useful for testing when the remote registry is unavailable

# Constants
LOCAL_TAG="local"
TERRAFORM_DIR="$(dirname "$0")/terraform-local"
LOCAL_ENV_FILE="/tmp/presis-local.env"

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

# Function to check if command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Check prerequisites
for cmd in git docker; do
    if ! command_exists "$cmd"; then
        error "$cmd command not found. Please install it."
        exit 1
    fi
done

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    error "Docker is not running or not accessible. Please start Docker."
    echo "Run './infra/diagnose.sh' for more detailed diagnostics."
    exit 1
fi

# Navigate to the project root directory
cd "$(dirname "$0")/.."

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "Loading environment variables from .env"
    source .env
fi

# Build the Docker image locally
echo "Building Presis Docker image locally with tag: $LOCAL_TAG"
docker build -t "presis:$LOCAL_TAG" -f infra/Dockerfile .
success "Docker image built successfully."

# Create local environment file
echo "Creating local environment file..."
cat << EOF > $LOCAL_ENV_FILE
FLASK_APP=app.app
PYTHONPATH=/app
FLASK_ENV=${FLASK_ENV:-production}
STRIPE_API_KEY=${STRIPE_API_KEY:-sk_test_dummy}
STRIPE_PUBLISHABLE_KEY=${STRIPE_PUBLISHABLE_KEY:-pk_test_dummy}
SECRET_KEY=${SECRET_KEY:-local_secret_key_for_testing}
EOF
success "Local environment file created at $LOCAL_ENV_FILE"

# Remove any existing presis container
if docker ps -a | grep -q "presis-local"; then
    echo "Removing existing presis-local container..."
    docker rm -f presis-local || true
fi

# Run the container locally
echo "Starting Presis container locally..."
docker run -d \
    --name presis-local \
    -p 5000:5000 \
    --env-file $LOCAL_ENV_FILE \
    -v "$(pwd)/instance:/app/instance" \
    presis:$LOCAL_TAG

success "Presis application deployed locally!"
echo "Application is running at: http://localhost:5000"
echo ""
echo "To view container logs: docker logs presis-local"
echo "To stop the container: docker stop presis-local"
echo "To start the container: docker start presis-local"
echo "To remove the container: docker rm -f presis-local"
