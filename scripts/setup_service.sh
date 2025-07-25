#!/bin/bash

# Raspberry Pi Temperature Monitor - Setup Script
# This script sets up the monitoring system as a systemd service

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SERVICE_USER=$(whoami)

echo "Setting up Raspberry Pi Temperature Monitor as a system service..."
echo "Project directory: $PROJECT_DIR"
echo "Service user: $SERVICE_USER"

# Setup sudo permissions first
echo "Setting up sudo permissions for smartctl..."
"$PROJECT_DIR/scripts/setup_sudo.sh"

# Make scripts executable
chmod +x "$PROJECT_DIR/scripts/"*.sh
chmod +x "$PROJECT_DIR/collector/temperature_collector.py"
chmod +x "$PROJECT_DIR/server/web_server.py"

# Create systemd service file for collector
cat > /tmp/pi-temp-collector.service << EOF
[Unit]
Description=Raspberry Pi Temperature Collector
After=network.target
Wants=network.target

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $PROJECT_DIR/collector/temperature_collector.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service file for web server
cat > /tmp/pi-temp-server.service << EOF
[Unit]
Description=Raspberry Pi Temperature Monitor Web Server
After=network.target pi-temp-collector.service
Wants=network.target
Requires=pi-temp-collector.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 $PROJECT_DIR/server/web_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Install service files (requires sudo)
echo "Installing systemd service files..."
sudo cp /tmp/pi-temp-collector.service /etc/systemd/system/
sudo cp /tmp/pi-temp-server.service /etc/systemd/system/

# Clean up temporary files
rm /tmp/pi-temp-collector.service /tmp/pi-temp-server.service

# Reload systemd and enable services
echo "Enabling services..."
sudo systemctl daemon-reload
sudo systemctl enable pi-temp-collector.service
sudo systemctl enable pi-temp-server.service

echo ""
echo "✅ Setup complete!"
echo ""
echo "To start the services:"
echo "  sudo systemctl start pi-temp-collector"
echo "  sudo systemctl start pi-temp-server"
echo ""
echo "To start both services:"
echo "  sudo systemctl start pi-temp-collector pi-temp-server"
echo ""
echo "To check status:"
echo "  sudo systemctl status pi-temp-collector"
echo "  sudo systemctl status pi-temp-server"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u pi-temp-collector -f"
echo "  sudo journalctl -u pi-temp-server -f"
echo ""
echo "The web interface will be available at:"
echo "  http://$(hostname -I | awk '{print $1}'):8080"
