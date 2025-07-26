#!/bin/bash

# Raspberry Pi Temperature Monitor - Quick Setup Script
# This script performs initial setup for new installations

echo "🌡️  Raspberry Pi Temperature Monitor - Quick Setup"
echo "=================================================="
echo ""

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "   Some features may not work properly"
    echo ""
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python version: $PYTHON_VERSION"

if [ "$(echo "$PYTHON_VERSION < 3.6" | bc -l 2>/dev/null)" = "1" ] 2>/dev/null; then
    echo "❌ Python 3.6+ required, found $PYTHON_VERSION"
    exit 1
fi

# Update system packages
echo ""
echo "📦 Updating system packages..."
sudo apt update

# Install smartmontools for SSD monitoring
echo ""
echo "🔧 Installing smartmontools for SSD temperature monitoring..."
sudo apt install -y smartmontools

# Setup sudo permissions for smartctl
echo ""
echo "🔑 Setting up sudo permissions for SSD monitoring..."
if [ -f "scripts/setup_sudo.sh" ]; then
    ./scripts/setup_sudo.sh
else
    echo "❌ setup_sudo.sh not found. Please run from the project root directory."
    exit 1
fi

# Make all scripts executable
echo ""
echo "⚙️  Making scripts executable..."
chmod +x scripts/*.sh scripts/*.py
chmod +x collector/temperature_collector.py
chmod +x server/web_server.py

# Test the system
echo ""
echo "🧪 Testing the system..."
if python3 scripts/test_system.py; then
    echo ""
    echo "✅ System test completed successfully!"
else
    echo ""
    echo "⚠️  Some tests failed, but basic functionality should work"
fi

# Optional: Install external sensor libraries
echo ""
echo "📡 External Sensor Setup (Optional)"
echo "=================================="
echo ""
echo "For DS18B20 1-Wire sensors:"
echo "  1. Enable 1-Wire interface: sudo raspi-config -> Interface Options -> 1-Wire"
echo "  2. Connect sensor to GPIO 4 with 4.7kΩ pull-up resistor"
echo "  3. Reboot and check: ls /sys/bus/w1/devices/"
echo ""
echo "For DHT11/DHT22 sensors:"
echo "  Install Adafruit library: pip3 install Adafruit-DHT"
echo "  Or install pigpio: sudo apt install python3-pigpio"
echo ""

# Ask if user wants to set up as a service
echo "🚀 Service Setup"
echo "==============="
echo ""
read -p "Do you want to set up the monitor as a system service? (y/N): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Setting up system service..."
    ./scripts/setup_service.sh
    echo ""
    echo "Service setup complete! Use these commands:"
    echo "  Start:  sudo systemctl start pi-temp-collector pi-temp-server"
    echo "  Status: sudo systemctl status pi-temp-collector"
    echo "  Logs:   sudo journalctl -u pi-temp-collector -f"
else
    echo "Skipping service setup. You can run it later with: ./scripts/setup_service.sh"
fi

echo ""
echo "🎉 Setup Complete!"
echo "=================="
echo ""
echo "Quick Start Commands:"
echo "  Start monitoring:  ./scripts/start.sh"
echo "  Check status:      ./scripts/status.sh" 
echo "  Stop monitoring:   ./scripts/stop.sh"
echo "  Clean data:        python3 scripts/clean_data.py --status"
echo ""
echo "Web Interface:"
LOCAL_IP=$(hostname -I | awk '{print $1}')
if [ -n "$LOCAL_IP" ]; then
    echo "  http://$LOCAL_IP:8080"
else
    echo "  http://[your-pi-ip]:8080"
fi
echo ""
echo "Configuration:"
echo "  Edit config/config.json to customize sensors and settings"
echo ""
echo "Documentation:"
echo "  README.md         - Main documentation"
echo "  docs/API.md       - API reference"
echo "  docs/SSD_SETUP.md - SSD setup guide"
echo ""
echo "Need help? Check the documentation or visit:"
echo "  https://github.com/aichi/rpi-temperature-monitoring"
echo ""
echo "Happy monitoring! 🌡️"
