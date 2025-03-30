# Deployment Instructions

## Environment Setup

The application requires environment variables to be set for proper operation. This is now handled through a mounted `.env` file rather than building the variables into the Docker image.

### Using the .env File

1. Create a `.env` file in the root directory of the project with your configuration:

```
# Flask Configuration
SECRET_KEY=your_secure_secret_key

# Stripe Integration
STRIPE_API_KEY=your_stripe_api_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# Admin User (Optional - can also be set as environment variables)
ADMIN_EMAIL=your_admin_email@example.com
ADMIN_PASSWORD=your_secure_admin_password
```

2. This `.env` file should be mounted as a volume when running the container:

   - When using docker-compose (already configured in docker-compose.redis.yml):
     ```yaml
     volumes:
       - ./.env:/app/.env:ro  # Mount .env file as read-only
     ```

   - When running the Docker container directly:
     ```bash
     docker run -d \
       -p 3000:3000 \
       -v $(pwd)/.env:/app/.env:ro \
       --name presis-app \
       your-image-name:tag
     ```

   - When deploying to Unraid, add a path mapping in the Docker container configuration:
     - Container Path: `/app/.env`
     - Host Path: Path to your `.env` file on the Unraid server

## Security Notes

- The `.env` file is mounted as read-only (`ro`) to prevent modification from inside the container
- Keep your `.env` file secure and do not commit it to version control
- Different deployment environments should have different `.env` files with appropriate configurations

## Redis Persistence in Unraid

If you encounter Redis persistence errors when deploying to Unraid, follow the instructions in [UNRAID_REDIS_FIX.md](UNRAID_REDIS_FIX.md).
