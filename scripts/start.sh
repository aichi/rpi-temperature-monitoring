#!/bin/bash

# Raspberry Pi Temperature Monitor - Start Script
# This script starts both the collector and web server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Starting Raspberry Pi Temperature Monitor..."
echo "Project directory: $PROJECT_DIR"

cd "$PROJECT_DIR"

# Check if Python3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python3 is not installed or not in PATH"
    exit 1
fi

# Check if smartctl sudo access is configured
if ! sudo -n smartctl --version >/dev/null 2>&1; then
    echo "Warning: sudo access for smartctl not configured"
    echo "SSD temperature readings may not work properly"
    echo "Run './scripts/setup_sudo.sh' to configure sudo access"
fi

# Check if required directories exist
if [ ! -d "data" ]; then
    echo "Creating data directory..."
    mkdir -p data
fi

# Start the temperature collector in the background
echo "Starting temperature collector..."
python3 collector/temperature_collector.py &
COLLECTOR_PID=$!
echo "Temperature collector started with PID: $COLLECTOR_PID"

# Wait a moment for the collector to initialize
sleep 2

# Start the web server
echo "Starting web server..."
echo "Web interface will be available at: http://$(hostname -I | awk '{print $1}'):8080"
python3 server/web_server.py &
SERVER_PID=$!
echo "Web server started with PID: $SERVER_PID"

# Create a PID file for easy management
echo "$COLLECTOR_PID" > data/collector.pid
echo "$SERVER_PID" > data/server.pid

echo "Both services are now running!"
echo "To stop the services, run: ./scripts/stop.sh"
echo "To check status, run: ./scripts/status.sh"

# Keep the script running and handle signals
trap 'echo "Stopping services..."; kill $COLLECTOR_PID $SERVER_PID; exit' INT TERM

# Wait for both processes
wait
