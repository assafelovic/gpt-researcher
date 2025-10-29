#!/bin/bash

# Create necessary directories
mkdir -p outputs logs my-docs

# Set proper permissions
chmod 755 outputs logs my-docs

# Set environment variables for Chromium
export CHROME_BIN=/usr/bin/chromium
export CHROME_PATH=/usr/bin/chromium

# Start the application
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-1}
