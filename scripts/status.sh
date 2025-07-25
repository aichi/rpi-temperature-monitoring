#!/bin/bash

# Raspberry Pi Temperature Monitor - Status Script
# This script checks the status of both services

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Raspberry Pi Temperature Monitor - Status"
echo "========================================"

cd "$PROJECT_DIR"

# Function to check process status
check_process() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "✅ $service_name is running (PID: $pid)"
            return 0
        else
            echo "❌ $service_name is not running (stale PID file)"
            rm -f "$pid_file"
            return 1
        fi
    else
        echo "❌ $service_name is not running (no PID file)"
        return 1
    fi
}

# Check collector status
check_process "Temperature Collector" "data/collector.pid"
collector_status=$?

# Check web server status
check_process "Web Server" "data/server.pid"
server_status=$?

echo ""

# Show additional information
if [ $server_status -eq 0 ]; then
    local_ip=$(hostname -I | awk '{print $1}')
    echo "🌐 Web interface: http://$local_ip:8080"
fi

# Check database
if [ -f "data/temperature_data.db" ]; then
    echo "📊 Database file exists: data/temperature_data.db"
    
    # Count records if sqlite3 is available
    if command -v sqlite3 &> /dev/null; then
        record_count=$(sqlite3 data/temperature_data.db "SELECT COUNT(*) FROM temperature_readings;" 2>/dev/null)
        if [ $? -eq 0 ]; then
            echo "📈 Total temperature records: $record_count"
        fi
    fi
else
    echo "⚠️  Database file not found"
fi

# Check log files
echo ""
echo "📋 Log files:"
if [ -f "data/collector.log" ]; then
    echo "   - Collector log: data/collector.log"
else
    echo "   - Collector log: Not found"
fi

if [ -f "data/server.log" ]; then
    echo "   - Server log: data/server.log"
else
    echo "   - Server log: Not found"
fi

echo ""

# Overall status
if [ $collector_status -eq 0 ] && [ $server_status -eq 0 ]; then
    echo "🟢 Overall Status: All services running"
    exit 0
elif [ $collector_status -eq 0 ] || [ $server_status -eq 0 ]; then
    echo "🟡 Overall Status: Some services running"
    exit 1
else
    echo "🔴 Overall Status: No services running"
    exit 2
fi
