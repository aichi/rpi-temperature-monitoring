# Raspberry Pi Temperature Monitor

[![GitHub Repository](https://img.shields.io/badge/GitHub-rpi--temperature--monitoring-blue?logo=github)](https://github.com/aichi/rpi-temperature-monitoring)

A web-based temperature monitoring system for Raspberry Pi that tracks CPU, GPU, multiple SSD/NVME devices, and pluggable external sensors with historical data visualization.

## Quick Installation

```bash
# Clone the repository
git clone https://github.com/aichi/rpi-temperature-monitoring.git
cd rpi-temperature-monitoring

# Setup permissions and test
./scripts/setup_sudo.sh
python3 scripts/test_system.py

# Start monitoring
./scripts/start.sh
```

## Features

- **Real-time Temperature Monitoring**: Track CPU, GPU, multiple storage devices, and external sensors
- **Plugin-based External Sensors**: Support for DS18B20, DHT11/DHT22, and custom sensor plugins
- **Multiple Storage Device Support**: Monitor multiple NVME/SSD devices with device names
- **Web Interface**: Clean, responsive web interface with real-time charts
- **Historical Data**: Store and visualize temperature data over time with configurable retention
- **Configurable Collection**: Set collection intervals from 1 minute to 1 hour
- **Time Range Selection**: View data for 1 hour, 6 hours, 24 hours, 3 days, or 1 week
- **Database Management**: Tools for cleaning and managing stored data
- **System Service**: Can be set up as a systemd service for automatic startup

## Project Structure

```
monitoring/
├── config/
│   └── config.json          # Configuration file
├── collector/
│   ├── plugins/             # External sensor plugins
│   │   ├── __init__.py      # Plugin base class
│   │   ├── ds18b20.py       # DS18B20 sensor plugin
│   │   └── dht.py           # DHT11/DHT22 sensor plugin
│   └── temperature_collector.py  # Data collection service
├── server/
│   └── web_server.py        # Web server and API
├── scripts/
│   ├── start.sh            # Start both services
│   ├── stop.sh             # Stop both services
│   ├── status.sh           # Check service status
│   ├── setup_service.sh    # Setup as systemd service
│   ├── setup_sudo.sh       # Configure sudo for smartctl
│   ├── scan_devices.py     # Scan for storage devices
│   └── clean_data.py       # Database cleaning utility
├── data/                   # Database and log files (created automatically)
├── docs/                   # Documentation
│   └── SSD_SETUP.md        # SSD setup guide
└── prompts/
    ├── 1.setup.md          # Original project requirements
    ├── 2.update_nvme.md    # NVME updates
    └── 3.refinement.md     # System refinements
```

## Quick Start

1. **Setup sudo permissions for SSD temperature monitoring:**
   ```bash
   ./scripts/setup_sudo.sh
   ```

2. **Scan for available storage devices (optional):**
   ```bash
   ./scripts/scan_devices.py
   ```

3. **Make scripts executable:**
   ```bash
   chmod +x scripts/*.sh
   ```

4. **Start the monitoring system:**
   ```bash
   ./scripts/start.sh
   ```

5. **Open the web interface:**
   - Open your browser and go to `http://[raspberry-pi-ip]:8080`
   - The IP address will be displayed when you start the services

6. **Check status:**
   ```bash
   ./scripts/status.sh
   ```

7. **Stop the services:**
   ```bash
   ./scripts/stop.sh
   ```

## Configuration

Edit `config/config.json` to customize the monitoring system:

### Collection Settings
- `interval_minutes`: How often to collect data (1-60 minutes)
- `sensors`: Enable/disable individual sensors (cpu_temp, gpu_temp, ssd_temp, external_sensors)
- `storage_devices`: List of storage devices to monitor for temperature (e.g., ["/dev/nvme0n1", "/dev/sda"])
- `external_sensors`: Configuration for external sensor plugins

### External Sensor Configuration
Each external sensor is defined with:
- `plugin`: Plugin type (ds18b20, dht11, dht22)
- Plugin-specific configuration (device_id for DS18B20, gpio_pin for DHT sensors)
- `description`: Human-readable description

Example:
```json
"external_sensors": {
  "outdoor_temp": {
    "plugin": "ds18b20",
    "device_id": "28-0000072431ab",
    "description": "Outdoor Temperature"
  },
  "room_temp": {
    "plugin": "dht22",
    "gpio_pin": 4,
    "sensor_type": "DHT22",
    "description": "Room Temperature & Humidity"
  }
}
```

### External Sensor (DS18B20)
- `type`: Sensor type (currently supports "ds18b20")
- `device_id`: Specific device ID (optional, uses first found if null)
- `pin`: GPIO pin (for reference, not used in 1-wire interface)

### Storage Settings
- `database_file`: SQLite database file path
- `retention_days`: How many days of data to keep

### Server Settings
- `host`: Server bind address (0.0.0.0 for all interfaces)
- `port`: Server port (default: 8080)
- `debug`: Enable debug mode

## System Service Setup

To run the monitoring system as a system service that starts automatically:

1. **Setup the service:**
   ```bash
   ./scripts/setup_service.sh
   ```

2. **Start the services:**
   ```bash
   sudo systemctl start pi-temp-collector pi-temp-server
   ```

3. **Check status:**
   ```bash
   sudo systemctl status pi-temp-collector
   sudo systemctl status pi-temp-server
   ```

4. **View logs:**
   ```bash
   sudo journalctl -u pi-temp-collector -f
   sudo journalctl -u pi-temp-server -f
   ```

## API Endpoints

The web server provides several API endpoints:

- `GET /` - Main web interface
- `GET /api/data?hours=24` - Get temperature data for specified hours
- `GET /api/latest` - Get latest temperature readings
- `GET /api/config` - Get sensor configuration

## Temperature Sensors

### CPU Temperature
- Read from `/sys/class/thermal/thermal_zone0/temp`
- Standard on all Raspberry Pi models

### GPU Temperature
- Read using `vcgencmd measure_temp`
- Requires vcgencmd utility (standard on Raspberry Pi OS)

### SSD Temperature
- Read using `smartctl` from smartmontools with sudo privileges
- Configurable list of storage devices in config.json
- Supports NVME, SATA, and eMMC devices
- Automatically detects temperature from SMART data
- Requires sudo access: run `./scripts/setup_sudo.sh` to configure

### External Sensors
- **Plugin-based system**: Support for multiple sensor types
- **DS18B20**: 1-Wire digital temperature sensors
- **DHT11/DHT22**: Digital temperature and humidity sensors
- **Automatic detection**: Sensors automatically discovered when possible
- **Custom plugins**: Easy to add support for new sensor types

To enable external sensors:
1. Set `"external_sensors": true` in config.json
2. Configure sensors in the `external_sensors` section
3. Install required libraries (see sensor-specific setup below)

#### DS18B20 Setup:
```bash
# Enable 1-wire interface
sudo raspi-config
# Interface Options > 1-Wire > Yes

# Check sensors detected
ls /sys/bus/w1/devices/
```

#### DHT11/DHT22 Setup:
```bash
# Install Adafruit DHT library
pip3 install Adafruit-DHT

# Or for alternative method
sudo apt install python3-pigpio
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

## Requirements

### Python Packages
- Standard library only (no external dependencies required)
- Python 3.6+ recommended

### System Tools
- `vcgencmd` (for GPU temperature, included in Raspberry Pi OS)
- `smartctl` (for SSD temperature, install with `sudo apt install smartmontools`)

### Hardware Setup for External Sensor
1. Connect DS18B20 sensor:
   - VCC to 3.3V
   - GND to Ground
   - Data to GPIO 4 (with 4.7kΩ pull-up resistor)
2. Enable 1-wire interface:
   ```bash
   sudo raspi-config
   ```
   Navigate to Interface Options > 1-Wire > Yes

## Data Management

The system includes tools for managing stored temperature data:

### Database Cleaning

```bash
# Show database status
python3 scripts/clean_data.py --status

# Delete all data (with confirmation)
python3 scripts/clean_data.py --clean-all

# Delete data older than 30 days
python3 scripts/clean_data.py --clean-old 30

# Force delete without confirmation (dangerous!)
python3 scripts/clean_data.py --clean-all --force
```

### Database Structure

The system uses SQLite with three main tables:
- `temperature_readings`: CPU and GPU temperatures
- `storage_temperatures`: Storage device temperatures with device names
- `external_temperatures`: External sensor readings with sensor names

This allows for:
- Multiple storage devices with preserved device information
- Multiple external sensors with configurable names
- Historical tracking even when hardware changes

## Troubleshooting

### Common Issues

1. **Permission denied for temperature files:**
   - Make sure the user has read access to `/sys/class/thermal/`
   - Run with appropriate permissions

2. **GPU temperature not available:**
   - Ensure `vcgencmd` is available: `which vcgencmd`
   - Add user to video group: `sudo usermod -a -G video $USER`

3. **SSD temperature not available:**
   - Install smartmontools: `sudo apt install smartmontools`
   - Setup sudo access: `./scripts/setup_sudo.sh`
   - Check supported devices: `./scripts/scan_devices.py`
   - Verify device exists: `ls /dev/nvme* /dev/sd* /dev/mmcblk*`

4. **External sensor not found:**
   - Check 1-wire interface is enabled: `ls /sys/bus/w1/devices/`
   - Verify wiring and pull-up resistor
   - Check kernel modules: `lsmod | grep w1`

5. **Web interface not accessible:**
   - Check if port 8080 is blocked by firewall
   - Verify server is running: `./scripts/status.sh`
   - Check server logs: `cat data/server.log`

### Log Files

- Collector logs: `data/collector.log`
- Server logs: `data/server.log`
- Database: `data/temperature_data.db`

## License

This project is open source and available under the MIT License.
