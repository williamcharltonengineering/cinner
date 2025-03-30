#!/bin/bash
set -e

# Script to build and push the Presis Docker image that avoids HTTPS issues

# Color formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Get the tag from the command line argument or use the latest git tag
TAG=${1:-$(git describe --tags --abbrev=0 2>/dev/null || echo "v0.1.0")}
REPO_NAME="williamcharltonengineering/presis"

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

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

# Check Docker prerequisites
if ! command_exists docker; then
    error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    error "Docker is not running or not accessible. Please start Docker."
    echo ""
    echo "If Docker is installed but not running:"
    echo "- On macOS or Windows: Start Docker Desktop"
    echo "- On Linux: Run 'sudo systemctl start docker'"
    
    # Check if it's a permission issue
    if [[ $(uname) == "Linux" ]]; then
        if ! groups | grep -q docker; then
            echo ""
            echo "Your user might not be in the docker group. Try:"
            echo "sudo usermod -aG docker $USER"
            echo "Then log out and log back in, or run 'newgrp docker'"
        fi
    fi
    
    exit 1
fi

# Navigate to the project root directory
cd "$(dirname "$0")/.."

# Build the Docker image for multiple platforms (amd64 and arm64)
echo "Building multi-architecture Docker image: $REPO_NAME:$TAG"
echo "This will build for both AMD64 (standard PCs/servers) and ARM64 (Apple Silicon/newer ARM servers)"

# Check if buildx is available and set up
if ! docker buildx ls | grep -q "default.*running"; then
    echo "Setting up Docker Buildx..."
    docker buildx create --name multiarch --use || true
    docker buildx inspect --bootstrap
fi

# Build and push directly to Docker Hub with multi-platform support
if ! docker buildx build --platform linux/amd64,linux/arm64 \
    -t "$REPO_NAME:$TAG" \
    -t "$REPO_NAME:latest" \
    --push \
    -f infra/Dockerfile .; then
    
    # If multi-platform build fails, try a fallback single platform build
    warning "Multi-platform build failed. Falling back to single platform build..."
    if ! docker build --platform=linux/amd64 -t "$REPO_NAME:$TAG" -f infra/Dockerfile .; then
        error "Failed to build Docker image."
        exit 1
    fi
    success "Docker image built successfully (single platform)."
    
    # Continue with push as before (this will be a single platform image)
else
    success "Multi-architecture Docker image built and pushed successfully!"
    echo "Image is available for both AMD64 and ARM64 architectures."
    # Skip the manual push since buildx --push handled it
    exit 0
fi

# Check if logged in to Docker Hub
echo "Checking Docker Hub authentication..."
if ! docker info | grep -q "Username"; then
    warning "You are not logged in to Docker Hub."
    echo "Please log in to Docker Hub to push the image:"
    echo "docker login"
    
    # Ask for login if not already logged in
    if ! docker login; then
        error "Docker Hub login failed. Cannot push image."
        exit 1
    fi
fi

# Push the image to Docker Hub
echo "Pushing Docker image to Docker Hub..."
echo "Running: docker push $REPO_NAME:$TAG"

if ! docker push "$REPO_NAME:$TAG"; then
    error "Failed to push Docker image to Docker Hub."
    echo ""
    echo "Possible issues:"
    echo "1. Authentication problems with Docker Hub"
    echo "2. Network connectivity issues"
    echo "3. Insufficient permissions to push to this repository"
    echo ""
    exit 1
fi

success "Successfully built and pushed: $REPO_NAME:$TAG"

# Also create and push a 'latest' tag
echo "Tagging image as 'latest' as well..."
docker tag "$REPO_NAME:$TAG" "$REPO_NAME:latest"
if ! docker push "$REPO_NAME:latest"; then
    warning "Failed to push latest tag, but version tag was successful."
else
    success "Successfully pushed latest tag."
fi
