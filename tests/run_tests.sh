#!/bin/bash
# Run test suite for the Presis application

# Set environment variables for testing
export FLASK_ENV=testing
export FLASK_APP=app/app.py
export STRIPE_API_KEY="sk_test_51PPG9tBLvzmZ9ZyKG6q9dK9WQ7LG3fEF44OXckIWdlUg8O4oHMjFGJQ42WbXbTBIVlKoIUBciBP5xTZy09AJXON9001hnkOWO6"
export STRIPE_PUBLISHABLE_KEY="pk_test_51PPG9tBLvzmZ9ZyKFQz9JAngfqAuXQdAWYmufL2yeKu3oV239qbhUzYDbwBOBcUiWsh3qXMsl2mshJ3PwFfKSjtr00DBatgbdO"
export SECRET_KEY="test_secret_key"

# Create directory for test database
mkdir -p instance/test

# Set PYTHONPATH to include the project root directory
export PYTHONPATH=$(pwd):$PYTHONPATH

# Check if specific test file was passed as an argument
if [ $# -eq 0 ]; then
    # Run all tests
    python -m pytest tests/ -v
else
    # Run specific test file
    python -m pytest "$@" -v
fi

# Clean up test databases
rm -f instance/test/*.db
