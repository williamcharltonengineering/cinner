# Redis Persistence Error Fix for Unraid

When deploying to Unraid, the Redis container may encounter disk persistence errors with the following message:

```
MISCONF Redis is configured to save RDB snapshots, but it's currently unable to persist to disk. 
Commands that may modify the data set are disabled, because this instance is configured to report 
errors during writes if RDB snapshotting fails (stop-writes-on-bgsave-error option).
Please check the Redis logs for details about the RDB error.
```

## Quick Fix

Run the included `fix-redis-unraid.sh` script to fix this issue temporarily:

```bash
./fix-redis-unraid.sh
```

This script connects to your Redis container and runs:
```
CONFIG SET stop-writes-on-bgsave-error no
```

## Permanent Fix

To fix this issue permanently, you need to update your Redis container configuration in Unraid:

### Option 1: Using the Unraid Web UI

1. Open the Unraid web interface
2. Go to the Docker tab
3. Click on the Redis container (or the container that provides Redis)
4. Click "Edit"
5. In the "Extra Parameters" field, add: `--stop-writes-on-bgsave-error no`
   - If you're using a different container image, you might need to add: `-e "REDIS_ARGS=--stop-writes-on-bgsave-error no"`
6. Apply the changes and restart the container

### Option 2: Using Docker Compose on Unraid

If you're deploying with docker-compose, update your docker-compose file to include:

```yaml
services:
  redis:
    image: redis:alpine
    # ... other settings ...
    command: redis-server --stop-writes-on-bgsave-error no
```

### Option 3: Add a Redis Configuration File

Create a custom redis.conf file and mount it in the container:

1. Create a file named `redis.conf` with the following content:
   ```
   stop-writes-on-bgsave-error no
   ```

2. Mount this file into your Redis container:
   - In Unraid UI: Add a path mapping from your redis.conf to /usr/local/etc/redis/redis.conf
   - In docker-compose: 
     ```yaml
     volumes:
       - ./redis.conf:/usr/local/etc/redis/redis.conf
     ```

## Why This Happens

This error occurs when Redis cannot write its snapshot to disk. This can happen due to:

1. Disk space issues on Unraid
2. Permission problems
3. Disk I/O errors

The parameter `stop-writes-on-bgsave-error` determines Redis behavior when it encounters these issues:
- When set to `yes` (default), Redis stops accepting writes to preserve data consistency
- When set to `no`, Redis continues to accept writes even if persistence is failing

Setting this to `no` allows your application to continue working, but be aware that if the Redis container restarts, data might be lost if the snapshots haven't been written successfully.

## Checking Disk Space

If you continue to have issues, check available disk space on your Unraid server:

```bash
df -h
```

And check if there are any I/O errors in the system logs:

```bash
dmesg | grep -i error
