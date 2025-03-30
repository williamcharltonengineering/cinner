#!/bin/bash
# Script to run the application locally with HTTPS support (downgraded to HTTP)

# Source the common setup from the regular script
source "./run_local.sh" --no-run

# Additional environment variable for HTTPS downgrade
export FLASK_RUN_CERT=adhoc

echo "Starting application with HTTPS downgrade on http://localhost:3000"
echo "This will accept HTTPS requests but serve HTTP content."
echo "To access the app, visit: https://localhost:3000"
echo "You may see a browser warning about an invalid certificate - this is expected in development mode."

# Run the Flask application with HTTPS support
flask run --host=0.0.0.0 --port=3000 --cert=adhoc
