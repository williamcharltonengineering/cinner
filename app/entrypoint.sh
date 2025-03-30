#!/bin/bash
set -e

# Run the admin user creation script
echo "Setting up admin user if needed..."
cd /app
python ./app/create_admin.py

# Run the Flask application
echo "Starting Flask application..."
exec flask run --host=0.0.0.0 --port=3000
