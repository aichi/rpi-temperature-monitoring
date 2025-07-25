#!/bin/bash

# Setup sudo permissions for temperature monitoring
# This script configures sudo to allow smartctl to run without password

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CURRENT_USER=$(whoami)

echo "Setting up sudo permissions for temperature monitoring..."
echo "User: $CURRENT_USER"

# Create sudoers file for smartctl
SUDOERS_FILE="/etc/sudoers.d/pi-temp-monitor"

cat > /tmp/pi-temp-monitor-sudoers << EOF
# Allow temperature monitoring to run smartctl without password
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/sbin/smartctl
EOF

# Install the sudoers file
echo "Installing sudoers configuration..."
sudo cp /tmp/pi-temp-monitor-sudoers "$SUDOERS_FILE"
sudo chmod 440 "$SUDOERS_FILE"
sudo chown root:root "$SUDOERS_FILE"

# Clean up
rm /tmp/pi-temp-monitor-sudoers

# Verify the sudoers file
echo "Verifying sudoers configuration..."
if sudo visudo -cf "$SUDOERS_FILE"; then
    echo "✅ Sudoers configuration is valid"
else
    echo "❌ Sudoers configuration is invalid, removing..."
    sudo rm "$SUDOERS_FILE"
    exit 1
fi

# Test sudo access
echo "Testing sudo access for smartctl..."
if sudo -n smartctl --version >/dev/null 2>&1; then
    echo "✅ Sudo access for smartctl is working"
else
    echo "❌ Sudo access test failed"
    exit 1
fi

echo ""
echo "✅ Setup complete!"
echo "The temperature collector can now read SSD/NVME temperatures using sudo."
echo ""
echo "Note: This configuration allows the user '$CURRENT_USER' to run smartctl"
echo "with sudo without a password for temperature monitoring purposes."
