# Changelog

All notable changes to the Raspberry Pi Temperature Monitor project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-07-26

### Added
- Initial release of Raspberry Pi Temperature Monitor
- Real-time temperature monitoring for CPU, GPU, and storage devices
- Web-based interface with interactive charts
- Plugin-based external sensor system
- Support for multiple storage devices (NVME, SATA, eMMC)
- Database storage with configurable retention
- System service setup scripts
- Comprehensive documentation and setup guides

### Features
- **Core Monitoring**
  - CPU temperature reading from thermal zones
  - GPU temperature via vcgencmd
  - Multiple storage device temperature monitoring with sudo support
  - Configurable collection intervals (1-60 minutes)

- **Plugin System**
  - DS18B20 1-Wire temperature sensor plugin
  - DHT11/DHT22 temperature and humidity sensor plugin
  - Extensible plugin architecture for custom sensors

- **Web Interface**
  - Real-time temperature display with color-coded cards
  - Interactive charts with Chart.js
  - Time range selection (1 hour to 1 week)
  - Device name display for storage devices
  - Responsive design for mobile devices

- **Database Management**
  - SQLite database with optimized schema
  - Separate tables for different sensor types
  - Data retention and cleanup tools
  - Database status and statistics

- **System Integration**
  - Systemd service configuration
  - Automatic startup and restart capabilities
  - Comprehensive logging
  - Permission management for hardware access

- **Utilities and Scripts**
  - Storage device scanning and detection
  - System test and validation
  - Data cleaning and maintenance tools
  - Sudo permission setup for hardware access

### Configuration
- JSON-based configuration system
- Sensor enable/disable options
- Storage device list configuration
- External sensor plugin configuration
- Server and database settings

### Documentation
- Complete setup and installation guide
- Plugin development documentation
- Troubleshooting guide
- API documentation
- Contributing guidelines

### Requirements
- Raspberry Pi with Raspberry Pi OS
- Python 3.6+
- Optional: smartmontools for storage monitoring
- Optional: Sensor-specific libraries for external sensors

## [Unreleased]

### Planned Features
- Email/SMS notifications for temperature thresholds
- Data export functionality (CSV, JSON)
- Historical trend analysis
- Mobile app companion
- Docker containerization
- More sensor plugins (BME280, thermocouples, etc.)
- Multi-device monitoring dashboard
- REST API authentication
- Grafana integration support
