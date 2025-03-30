#!/bin/bash
set -e

# Script to diagnose issues with Docker and registry connectivity

REGISTRY="192.168.1.15:5000"
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo "=== Presis Deployment Diagnostics ==="
echo ""

# Function to print error messages
error() {
    echo -e "${RED}ERROR: $1${NC}"
}

# Function to print success messages
success() {
    echo -e "${GREEN}SUCCESS: $1${NC}"
}

# Function to print warning messages
warning() {
    echo -e "${YELLOW}WARNING: $1${NC}"
}

# Function to print info messages
info() {
    echo -e "INFO: $1"
}

# Function to print heading
heading() {
    echo -e "\n${GREEN}=== $1 ===${NC}"
}

# Check if docker command exists
if ! command -v docker &> /dev/null; then
    error "Docker command not found. Please install Docker."
    exit 1
fi

# Check if Docker is running
echo "Checking if Docker daemon is running..."
if ! docker info &> /dev/null; then
    error "Docker daemon is not running."
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Start Docker Desktop if you're using macOS or Windows"
    echo "2. On Linux, run: sudo systemctl start docker"
    echo "3. Check Docker logs for errors:"
    echo "   macOS/Windows: Check Docker Desktop logs"
    echo "   Linux: sudo journalctl -u docker.service"
    exit 1
else
    success "Docker daemon is running."
fi

# Check local Docker functionality
echo ""
echo "Testing basic Docker functionality..."
echo "Creating test container..."
if ! docker run --rm hello-world &> /dev/null; then
    error "Failed to run a test container."
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check Docker permission issues"
    echo "2. Check system resources (disk space, memory)"
    echo "3. Try restarting Docker"
    exit 1
else
    success "Local Docker is working correctly."
fi

# Check Unraid connectivity
heading "Unraid Server Connectivity"
echo "Checking connectivity to Unraid server at 192.168.1.15:80..."

# Test TCP connection to Unraid web UI port
if ! nc -z -w5 192.168.1.15 80 &> /dev/null; then
    error "Cannot connect to Unraid web UI at 192.168.1.15:80"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Ensure Unraid server is running"
    echo "2. Check if the web UI is accessible"
    echo "3. Verify any firewall rules aren't blocking port 80"
else
    success "Unraid web UI port is accessible."
    
    # Try connecting to the Unraid API
    echo "Testing Unraid API connection..."
    if curl -s --connect-timeout 5 "http://192.168.1.15/api/v1/docker/containers" > /dev/null; then
        success "Successfully connected to Unraid Docker API!"
        echo "Listing current Unraid Docker containers:"
        curl -s "http://192.168.1.15/api/v1/docker/containers" | python -m json.tool || echo "Could not format response, but connection is working"
    else
        warning "Cannot connect to Unraid Docker API."
        echo ""
        echo "Troubleshooting steps:"
        echo "1. Ensure Docker is enabled in Unraid"
        echo "2. Verify API access is enabled in Unraid settings"
        echo "3. Check if Unraid requires authentication for API access"
    fi
fi

# Check registry connectivity
echo ""
echo "Testing connectivity to registry at $REGISTRY..."
if ! ping -c 1 192.168.1.15 &> /dev/null; then
    error "Cannot reach registry host at 192.168.1.15"
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Check network connectivity to the host"
    echo "2. Ensure the host is online"
    echo "3. Verify there are no firewall rules blocking traffic"
    exit 1
else
    success "Registry host is reachable."
fi

# Check registry port
echo ""
echo "Testing registry port connectivity..."
if ! nc -z -w5 192.168.1.15 5000 &> /dev/null; then
    warning "Cannot connect to registry port 5000."
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Ensure registry is running on the host"
    echo "2. Check if firewall is blocking port 5000"
    echo "3. Verify registry configuration"
else
    success "Registry port is accessible."
fi

# Check registry access through Docker
echo ""
echo "Testing Docker registry access..."

# Try to list registry catalog
echo "Querying registry catalog API..."
if ! curl -s -f http://192.168.1.15:5000/v2/_catalog &> /dev/null; then
    error "Cannot access registry API. Registry may not be running or has connectivity issues."
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Verify registry is running on the host with: ssh user@192.168.1.15 'docker ps | grep registry'"
    echo "2. Check if firewall is blocking access to port 5000"
    echo "3. Ensure registry is configured to accept non-TLS connections"
else
    success "Registry API is accessible."
    
    # Display the available repositories
    echo ""
    echo "Available repositories in registry:"
    curl -s http://192.168.1.15:5000/v2/_catalog | python -m json.tool
fi

# Test consul connectivity
heading "Consul Backend Connectivity"
echo "Testing Consul connectivity (for Terraform backend)..."
echo "Sending request to: http://192.168.1.15:8500/v1/status/leader"

# Try with a timeout to prevent hanging
if ! curl -s --connect-timeout 5 http://192.168.1.15:8500/v1/status/leader &> /dev/null; then
    error "Cannot access Consul API at 192.168.1.15:8500."
    echo ""
    echo "Checking network connectivity to Consul host..."
    if ! ping -c 1 -W 2 192.168.1.15 &> /dev/null; then
        error "Cannot reach Consul host at 192.168.1.15 (ping failed)"
        echo "This may indicate a network connectivity issue or the host is down."
    else
        warning "Host is reachable but Consul service may not be running or is blocked."
    fi
    
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Verify Consul is running with: ssh user@192.168.1.15 'consul members'"
    echo "2. Check if firewall is blocking access to port 8500"
    echo "3. Ensure Consul is configured to accept external connections"
    echo ""
    echo "You can also modify infra/terraform/backend.tf to use a local backend temporarily:"
    echo "terraform {"
    echo "  backend \"local\" {}"
    echo "}"
else
    success "Consul API is accessible."
    echo "Checking Consul KV storage..."
    curl -s http://192.168.1.15:8500/v1/kv/?recurse=true | python -m json.tool || echo "No KV data found (this is normal for new setups)"
fi

# Check if we need to configure Docker for insecure registries
heading "Docker Insecure Registry Configuration"
if ! docker info | grep -q "192.168.1.15:5000"; then
    warning "Registry not found in Docker's insecure-registries configuration."
    echo ""
    echo "This will cause 'HTTP response to HTTPS client' errors when pushing images."
    echo ""
    
    # Create a temporary file with daemon.json example
    DAEMON_JSON_EXAMPLE=$(cat <<EOF
{
  "insecure-registries": ["192.168.1.15:5000"]
}
EOF
)
    
    echo "For macOS/Windows:"
    echo "1. Open Docker Desktop"
    echo "2. Go to Settings/Preferences → Docker Engine"
    echo "3. Add or modify the JSON configuration to include:"
    echo "-------------------------------------------------"
    echo "$DAEMON_JSON_EXAMPLE"
    echo "-------------------------------------------------"
    echo "4. Click 'Apply & Restart'"
    echo ""
    echo "For Linux:"
    echo "1. Create or edit /etc/docker/daemon.json:"
    echo "   sudo nano /etc/docker/daemon.json"
    echo "2. Add the following content:"
    echo "-------------------------------------------------"
    echo "$DAEMON_JSON_EXAMPLE"
    echo "-------------------------------------------------"
    echo "3. Save and restart Docker: sudo systemctl restart docker"
    echo ""
    error "IMPORTANT: You must add the registry to insecure-registries to proceed!"
    echo "Push operations will fail without this configuration."
else
    success "Docker is correctly configured for insecure registry at 192.168.1.15:5000"
fi

# Try to test with a direct Docker push (to diagnose HTTP/HTTPS issues)
heading "Testing Docker Registry Push"
echo "Creating a small test image to check push capabilities..."
docker tag hello-world 192.168.1.15:5000/test-image:latest 2>/dev/null || docker pull hello-world >/dev/null && docker tag hello-world 192.168.1.15:5000/test-image:latest

# Try pushing to check for common errors
echo "Attempting test push to registry..."
if ! docker push 192.168.1.15:5000/test-image:latest 2>/tmp/docker_test_push.log; then
    warning "Test push failed."
    
    # Check for common error patterns
    if grep -q "server gave HTTP response to HTTPS client" /tmp/docker_test_push.log; then
        error "HTTPS ERROR: Your Docker client is trying to use HTTPS with an HTTP registry."
        echo "This confirms you need to configure the insecure-registries setting as described above."
    elif grep -q "no basic auth credentials" /tmp/docker_test_push.log; then
        warning "AUTHENTICATION ERROR: Registry requires authentication."
        echo "You may need to log in with 'docker login 192.168.1.15:5000' before pushing."
    elif grep -q "connection refused" /tmp/docker_test_push.log; then
        error "CONNECTION ERROR: Could not connect to the registry."
        echo "Make sure the registry is running and accessible."
    else
        error "Push failed with an unknown error:"
        cat /tmp/docker_test_push.log
    fi
else
    success "Test push successful! Docker registry is fully operational."
    echo "Cleaning up test image..."
    docker rmi 192.168.1.15:5000/test-image:latest >/dev/null 2>&1 || true
fi

# Check Git tag access
echo ""
echo "Checking Git tag access..."
if ! git describe --tags --abbrev=0 &> /dev/null; then
    warning "No Git tags found in the repository."
    echo ""
    echo "If you want to use Git tags for versioning, create a tag with:"
    echo "git tag -a v1.0.0 -m \"Version 1.0.0\""
else
    success "Git tags are accessible."
fi

echo ""
echo "=== Diagnostics complete ==="
echo ""
echo "For further troubleshooting:"
echo "1. Check if the registry is running: ssh user@192.168.1.15 'docker ps | grep registry'"
echo "2. Check registry logs: ssh user@192.168.1.15 'docker logs registry'"
echo "3. Temporarily test with a public registry like Docker Hub"
echo "4. Modify deploy.sh to add '--insecure-registry' flags if needed"
