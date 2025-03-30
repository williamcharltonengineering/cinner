# Running the Application Locally

This guide will help you set up and run the application locally without Docker for development purposes.

## Prerequisites

- Python 3.x installed
- Redis server (only needed if you want to use Redis storage)
- pip (Python package manager)
- netcat (nc) command for Redis connectivity check (optional)

## Quick Start

The easiest way to run the application locally is to use the provided script:

```bash
# Run with filesystem storage (default)
./run_local.sh

# OR run with Redis storage
./run_local.sh redis
```

This script will:
- Create a virtual environment if needed
- Install dependencies
- Set up the admin user
- Run the application

## Manual Setup

If you prefer to set things up manually, follow these steps:

1. **Clone the repository** (assuming you've already done this)

2. **Create and activate a virtual environment** (recommended):

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate
```

3. **Install dependencies**:

```bash
pip install -r requirements-app.txt
pip install -e .  # Install the package in development mode
```

4. **Set up environment variables**:

Create a `.env` file in the root directory of the project with the following variables (adjust as needed):

```
SECRET_KEY=your_secret_key_here
STRIPE_API_KEY=your_stripe_api_key
STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret

# Email settings (optional, for invitation functionality)
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_username
MAIL_PASSWORD=your_password

# Default admin user (will be created on first run)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=adminpassword
```

## Running with Filesystem Storage (Default)

This is the default mode, which uses SQLite for user data and JSON files for timesheets.

```bash
./run_local.sh
```

The application will be available at http://localhost:3000

If you prefer to set things up manually instead of using the script:

1. **Create the config.py symlink**:

```bash
ln -sf "$(pwd)/app/config.py" "$(pwd)/config.py"
```

2. **Set the required environment variables**:

```bash
export FLASK_APP=app.app
export PYTHONPATH=$(pwd)
export APP_ROOT_DIR=$(pwd)
export SECRET_KEY=your_development_secret_key
export SQLALCHEMY_DATABASE_URI=sqlite:///instance/users.db
```

3. **Create the admin user**:

```bash
python app/create_admin.py
```

4. **Run the application**:

```bash
flask run --host=0.0.0.0 --port=3000
```

## Running with Redis Storage

First, start a Redis server if you don't have one running:

```bash
# Using Docker to run Redis
docker run -d -p 6379:6379 --name redis redis:alpine
```

Then run the application with Redis storage:

```bash
./run_local.sh redis
```

The application will be available at http://localhost:3000

For manual setup:

1. **Create the config.py symlink**:

```bash
ln -sf "$(pwd)/app/config.py" "$(pwd)/config.py"
```

2. **Set Redis environment variables**:

```bash
export FLASK_APP=app.app
export PYTHONPATH=$(pwd)
export APP_ROOT_DIR=$(pwd)
export SECRET_KEY=your_development_secret_key
export PRESIS_NO_FSDB=True
export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_DB=0
export REDIS_PASSWORD=  # Set this if your Redis server requires a password
```

3. **Create the admin user**:

```bash
python app/create_admin.py
```

4. **Run the application**:

```bash
flask run --host=0.0.0.0 --port=3000
```

## Running with HTTPS Support

The application can also be run with HTTPS support, which is useful for testing secure connections or when working with third-party services that require HTTPS.

```bash
# Run with HTTPS support
./run_https_local.sh

# Run with HTTPS support and Redis
./run_https_local.sh redis
```

This will generate a self-signed certificate and run Flask with HTTPS support. Your browser will show a security warning, which is expected in development mode. You access the application at https://localhost:3000.

### How it Works

This setup uses Flask's built-in support for running with adhoc SSL certificates. It accepts HTTPS requests but serves regular HTTP content. This is useful for development purposes but not recommended for production use.

## Development Tips

- To enable Flask's debug mode (auto-reload on code changes), set `export FLASK_DEBUG=1` before running the application.
- The application creates an SQLite database at `instance/users.db` in filesystem mode.
- Timesheet data is stored in `instance/time_data/` in filesystem mode.
- All data is stored in Redis in Redis mode.

## Testing the Application

```bash
# Run tests
pytest
```

## Troubleshooting

### Import Error with 'config.Config'

If you see an error like:
```
ModuleNotFoundError: No module named 'config'
```

Make sure you have created the config.py symlink and set the PYTHONPATH:
```bash
ln -sf "$(pwd)/app/config.py" "$(pwd)/config.py"
export PYTHONPATH=$(pwd)
```

### SQLite Error "no such column: is_admin"

The application will automatically try to add the missing column. If you encounter this error in create_admin.py, the script has been updated to handle this case.

### Redis Connection Issues

If you see errors connecting to Redis:
1. Ensure Redis is running and accessible
2. Check the connection details (host, port, password) 
3. For Docker users, verify the container is running:
   ```bash
   docker ps | grep redis
   ```

### Filesystem-related Errors

- If you see "Read-only file system" errors, make sure you've set the `APP_ROOT_DIR` environment variable correctly to a location where you have write permissions.
- For path-related issues, ensure you're running the application from the root directory of the project.

### General Troubleshooting

- Enable Flask debug mode: `export FLASK_DEBUG=1`
- Check the app logs for detailed error messages 
- Verify your virtual environment is activated and dependencies are installed
