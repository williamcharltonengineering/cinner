#!/bin/bash
# Script to run the application locally

# Function to setup the environment
setup_environment() {
    # Create virtual environment if it doesn't exist
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment..."
        python -m venv .venv
    fi

    # Activate virtual environment
    source .venv/bin/activate

    # Install dependencies if not already installed
    if ! pip show flask &>/dev/null; then
        echo "Installing dependencies..."
        pip install -r requirements-app.txt
        pip install -e .
    fi

    # Create symlink for config.py if it doesn't exist
    if [ ! -f "config.py" ]; then
        echo "Creating config.py symlink..."
        ln -sf "$(pwd)/app/config.py" "$(pwd)/config.py"
    fi

    # Set environment variables
    export FLASK_APP=app.app
    export PYTHONPATH=$(pwd)
    export APP_ROOT_DIR=$(pwd)
    export ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
    export ADMIN_PASSWORD=${ADMIN_PASSWORD:-adminpassword}
    export SECRET_KEY=${SECRET_KEY:-development_secret_key}
    export SQLALCHEMY_DATABASE_URI=${SQLALCHEMY_DATABASE_URI:-"sqlite:///instance/users.db"}

    # Check for Redis mode
    if [ "$1" == "redis" ]; then
        echo "Setting up Redis mode..."
        export PRESIS_NO_FSDB=True
        export REDIS_HOST=${REDIS_HOST:-localhost}
        export REDIS_PORT=${REDIS_PORT:-6379}
        export REDIS_DB=${REDIS_DB:-0}
        export REDIS_PASSWORD=${REDIS_PASSWORD:-}
        
        # Check if Redis is running locally
        if ! nc -z localhost 6379 &>/dev/null; then
            echo "Warning: Redis doesn't appear to be running on localhost:6379"
            echo "If you have Docker, you can start Redis with:"
            echo "docker run -d -p 6379:6379 --name redis redis:alpine"
            read -p "Continue anyway? (y/N) " continue_without_redis
            if [[ ! "$continue_without_redis" =~ ^[Yy]$ ]]; then
                exit 1
            fi
        fi
    fi

    # Create admin user
    echo "Setting up admin user..."
    python app/create_admin.py
}

# Check if we're being sourced by another script
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
    # If --no-run is passed, just setup the environment
    if [[ "$1" == "--no-run" ]]; then
        setup_environment "$2"
    fi
else
    # Normal execution: setup and run
    setup_environment "$1"
    
    # Run the Flask application
    echo "Starting application on http://localhost:3000"
    flask run --host=0.0.0.0 --port=3000
fi
