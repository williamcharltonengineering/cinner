# Presis Test Suite

This directory contains tests for the Presis application, including unit tests and functional tests.

## Test Setup

The test suite uses pytest and includes tests for:
- User registration
- Payment processing with Stripe (using test cards)
- Account cancellation

## Running Tests

### Option 1: Using the provided script

The easiest way to run the tests is to use the provided script:

```bash
# Navigate to the project root
cd /path/to/presis

# Run all tests
./tests/run_tests.sh

# Run a specific test file
./tests/run_tests.sh tests/test_registration.py
```

This script:
1. Sets up the necessary environment variables for testing
2. Creates a test database directory
3. Sets the Python path
4. Runs the tests with pytest
5. Cleans up the test database after running

### Option 2: Manual test execution

You can also run the tests manually with pytest:

```bash
# Navigate to the project root
cd /path/to/presis

# Set up environment variables
export FLASK_ENV=testing
export FLASK_APP=app/app.py
export STRIPE_API_KEY="sk_test_51PPG9tBLvzmZ9ZyKG6q9dK9WQ7LG3fEF44OXckIWdlUg8O4oHMjFGJQ42WbXbTBIVlKoIUBciBP5xTZy09AJXON9001hnkOWO6"
export STRIPE_PUBLISHABLE_KEY="pk_test_51PPG9tBLvzmZ9ZyKFQz9JAngfqAuXQdAWYmufL2yeKu3oV239qbhUzYDbwBOBcUiWsh3qXMsl2mshJ3PwFfKSjtr00DBatgbdO"
export SECRET_KEY="test_secret_key"

# Create test database directory
mkdir -p instance/test

# Run tests
python -m pytest tests/ -v
```

## Stripe Testing

The tests use Stripe's test mode with test cards. No real payments are processed. The following test cards are used:

- **Success card**: 4242 4242 4242 4242
- **Requires authentication**: 4000 0025 0000 3155
- **Decline card**: 4000 0000 0000 0002

You can find more test cards in the [Stripe documentation](https://stripe.com/docs/testing).

## Test Structure

- `conftest.py`: Contains pytest fixtures and configuration
- `test_registration.py`: Tests for user registration and payment processing
- `test_timesheet.py`: Tests for timesheet functionality

## Adding New Tests

When adding new tests:
1. Create a new test file in the `tests/` directory
2. Import the application and required modules
3. Use the pytest fixtures from conftest.py where appropriate
4. Run the tests to ensure they pass
