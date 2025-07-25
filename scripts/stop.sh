#!/bin/bash

# Raspberry Pi Temperature Monitor - Stop Script
# This script stops both the collector and web server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Stopping Raspberry Pi Temperature Monitor..."

cd "$PROJECT_DIR"

# Function to stop a process by PID file
stop_process() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "Stopping $service_name (PID: $pid)..."
            kill "$pid"
            
            # Wait for process to stop
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done
            
            if kill -0 "$pid" 2>/dev/null; then
                echo "Force stopping $service_name..."
                kill -9 "$pid"
            fi
            
            echo "$service_name stopped."
        else
            echo "$service_name is not running."
        fi
        rm -f "$pid_file"
    else
        echo "No PID file found for $service_name."
    fi
}

# Stop collector
stop_process "temperature collector" "data/collector.pid"

# Stop web server
stop_process "web server" "data/server.pid"

# Also try to kill any remaining Python processes with our scripts
pkill -f "temperature_collector.py"
pkill -f "web_server.py"

echo "All services stopped."
