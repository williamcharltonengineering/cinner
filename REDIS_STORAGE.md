# Redis Storage Configuration

The application can now be configured to use Redis as the backend storage solution for both user data and timesheets, eliminating the need for filesystem storage. This is ideal for containerized deployments or when you need to scale horizontally.

## How It Works

When the environment variable `PRESIS_NO_FSDB=True` is set, the application will:

1. Use Redis instead of SQLite for user data
2. Store timesheet data in Redis instead of JSON files
3. Store invitation data in Redis

This implementation maintains all the functionality of the original application while allowing for filesystem-less operation.

## Redis Data Structure

The Redis implementation uses the following key patterns:

- `user:{id}` - Stores user data as JSON
- `user_email:{email}` - Maps email addresses to user IDs
- `timesheet:user:{id}` - Stores timesheet data for a user as JSON
- `invitation:{token}` - Stores invitation data as JSON
- `next_user_id` - Stores the next available user ID

## Configuration

The following environment variables can be used to configure Redis:

- `PRESIS_NO_FSDB` - Set to `True` to enable Redis storage
- `REDIS_HOST` - Redis server hostname (default: `localhost`)
- `REDIS_PORT` - Redis server port (default: `6379`)
- `REDIS_DB` - Redis database number (default: `0`)
- `REDIS_PASSWORD` - Redis server password (default: none)

## Running with Docker Compose

A `docker-compose.redis.yml` file is provided to easily run the application with Redis:

```bash
# Build and start the services
docker-compose -f docker-compose.redis.yml up -d

# View logs
docker-compose -f docker-compose.redis.yml logs -f

# Stop the services
docker-compose -f docker-compose.redis.yml down
```

### Docker Compose Environment Variables

You should update the environment variables in the docker-compose.redis.yml file with your own values, especially:

- `SECRET_KEY` - Flask secret key
- `STRIPE_API_KEY` - Your Stripe API key
- `STRIPE_PUBLISHABLE_KEY` - Your Stripe publishable key
- `STRIPE_WEBHOOK_SECRET` - Your Stripe webhook secret
- `ADMIN_EMAIL` - Email for the default admin user
- `ADMIN_PASSWORD` - Password for the default admin user

## Running Without Docker

If you want to run the application without Docker but still use Redis:

1. Install and run Redis on your system
2. Set the appropriate environment variables:

```bash
export PRESIS_NO_FSDB=True
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=  # If required

# Then run the application
python -m flask run
```

## Data Persistence

When using the docker-compose setup, Redis data is persisted in a named volume (`redis-data`). This ensures that your data will survive container restarts.

If you need to backup your Redis data, you can use the Redis commands `SAVE` or `BGSAVE` to create a snapshot, or use Redis replication for more advanced backup strategies.

### Redis Write Error Handling

By default, Redis is configured with `stop-writes-on-bgsave-error yes`, which means it will stop accepting writes if it encounters an error when trying to save data to disk. This can happen if:

- The disk is full
- Redis doesn't have permission to write to the disk
- The disk is read-only
- There's an I/O error

The docker-compose.redis.yml configuration includes `--stop-writes-on-bgsave-error no` to prevent this from happening. This means Redis will continue to function even if it can't save to disk, which is useful for development and testing. 

For production environments, you may want to change this setting back to `yes` to ensure data durability, but make sure you have adequate disk space and permissions.

If you encounter this error when running Redis outside of the provided docker-compose setup:

```
MISCONF Redis is configured to save RDB snapshots, but it's currently unable to persist to disk.
```

You can fix it by running the following command in the Redis CLI:

```
CONFIG SET stop-writes-on-bgsave-error no
```

Or by modifying your redis.conf file.

## Updating Admin Password

If you need to update the administrator password, you have several options:

### For Docker Compose Deployments

1. Edit the `docker-compose.redis.yml` file and change the `ADMIN_PASSWORD` environment variable
2. Restart the containers:
   ```bash
   docker-compose -f docker-compose.redis.yml down
   docker-compose -f docker-compose.redis.yml up -d
   ```

### Using the update_admin_password.py Script

This repository includes a script to update the admin password directly in the database:

```bash
# For Redis backend:
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=new_secure_password \
PRESIS_NO_FSDB=True REDIS_HOST=localhost REDIS_PORT=6379 \
python update_admin_password.py

# For filesystem backend (SQLite):
ADMIN_EMAIL=admin@example.com ADMIN_PASSWORD=new_secure_password \
APP_ROOT_DIR=$(pwd) python update_admin_password.py
```

The script will look for a user with the specified email address, update their password, and ensure they have admin privileges.
