#!/bin/bash

# Load environment variables from .env file
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
    echo "Environment variables loaded from .env file:"
    echo "GOOGLE_CLIENT_ID: $GOOGLE_CLIENT_ID"
    echo "SECRET_KEY: $SECRET_KEY"
else
    echo "Warning: .env file not found. Using default values."
    export GOOGLE_CLIENT_ID="698166460427-nh1pooookkaka1t0odc7jmck1fjpq4nf.apps.googleusercontent.com"
    export SECRET_KEY="recruitment-dashboard-secret-key-2024"
fi

# Start the application
echo "Starting recruitment dashboard..."
export FLASK_RUN_PORT=5006
python3 app.py
