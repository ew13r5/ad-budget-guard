#!/bin/bash
set -e

echo "Waiting for web service to be healthy..."
until curl -sf http://web:8000/health > /dev/null 2>&1; do
    sleep 2
done
echo "Web service is healthy."

echo "Starting worker..."
exec "$@"
