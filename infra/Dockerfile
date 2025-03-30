FROM python:3.12-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

# Copy the application code
COPY app/ ./app/
COPY presis/ ./presis/
COPY setup.py .
COPY pyproject.toml .
# .env file should be mounted as a volume, not copied into the image

# Make sure the instance directory exists for SQLite database
RUN mkdir -p instance

# Set environment variables
ENV FLASK_APP=app.app
ENV PYTHONPATH=/app
ENV APP_ROOT_DIR=/app

# Optional Redis configuration for no filesystem mode
ENV REDIS_HOST=redis
ENV REDIS_PORT=6379
ENV REDIS_DB=0
ENV REDIS_PASSWORD=

# Create a symlink for config.py in the root directory for proper importing
RUN ln -sf /app/app/config.py /app/config.py

# Copy the entrypoint script and make it executable
COPY app/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Expose the port
EXPOSE 3000

# Add default admin credentials that can be overridden
ENV ADMIN_EMAIL=admin@example.com
ENV ADMIN_PASSWORD=adminpassword

# Use the entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
