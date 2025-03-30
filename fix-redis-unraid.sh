#!/bin/bash
# Script to fix Redis disk persistence errors in Unraid

# Find the Redis container ID
REDIS_CONTAINER=$(docker ps -q --filter "name=redis")

if [ -z "$REDIS_CONTAINER" ]; then
  echo "Redis container not found. Make sure it's running."
  exit 1
fi

echo "Found Redis container: $REDIS_CONTAINER"

# Connect to Redis and disable stop-writes-on-bgsave-error
echo "Setting stop-writes-on-bgsave-error to no..."
docker exec -it $REDIS_CONTAINER redis-cli CONFIG SET stop-writes-on-bgsave-error no

# Verify the setting
echo "Verifying setting..."
docker exec -it $REDIS_CONTAINER redis-cli CONFIG GET stop-writes-on-bgsave-error

echo "Done! Redis should now accept writes even if disk persistence fails."
echo "To make this change persistent, you may want to update your Redis configuration."
