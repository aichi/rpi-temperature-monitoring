# SSD/NVME Temperature Monitoring Setup

## Overview
The temperature monitoring system now supports reading SSD/NVME temperatures using `smartctl` with elevated permissions. This document covers the setup and troubleshooting for storage device temperature monitoring.

## Quick Setup

1. **Install smartmontools** (if not already installed):
   ```bash
   sudo apt update
   sudo apt install smartmontools
   ```

2. **Setup sudo permissions**:
   ```bash
   cd /home/pi/monitoring
   ./scripts/setup_sudo.sh
   ```

3. **Scan for available devices**:
   ```bash
   ./scripts/scan_devices.py
   ```

4. **Update configuration** with detected devices in `config/config.json`:
   ```json
   {
     "collection": {
       "storage_devices": ["/dev/nvme0n1"]
     }
   }
   ```

## What the sudo setup does

The `setup_sudo.sh` script creates a sudoers configuration that allows the monitoring user to run `smartctl` without a password prompt. This is necessary because:

- NVME and many SATA devices require elevated permissions to read SMART data
- The monitoring service runs continuously and cannot prompt for passwords
- The sudo configuration is limited to only the `smartctl` command for security

## Configuration Options

### Storage Devices List
In `config/config.json`, you can specify which devices to monitor:

```json
{
  "collection": {
    "storage_devices": [
      "/dev/nvme0n1",    # Primary NVME SSD
      "/dev/nvme1n1",    # Secondary NVME SSD  
      "/dev/sda",        # SATA drive
      "/dev/mmcblk0"     # SD card/eMMC
    ]
  }
}
```

The system will:
- Check each device in order
- Use the first device that provides valid temperature data
- Skip devices that don't exist or can't be accessed
- Log which device is being used for temperature readings

## Supported Device Types

### NVME SSDs
- Devices: `/dev/nvme0n1`, `/dev/nvme1n1`, etc.
- Temperature reading: Direct from NVME SMART attributes
- Usually requires sudo access
- Example: Lexar SSD NM710, Samsung 980 PRO, WD Black SN750

### SATA SSDs/HDDs  
- Devices: `/dev/sda`, `/dev/sdb`, etc.
- Temperature reading: From SMART attribute 194 (Temperature_Celsius)
- May or may not require sudo depending on system configuration
- Example: Samsung 860 EVO, WD Blue, Seagate Barracuda

### eMMC/SD Cards
- Devices: `/dev/mmcblk0`, `/dev/mmcblk1`, etc.
- Temperature reading: Limited SMART support
- Some devices don't support temperature monitoring
- Built-in storage on Raspberry Pi Compute Modules

## Troubleshooting

### "sudo access for smartctl not configured"
**Solution**: Run the sudo setup script:
```bash
./scripts/setup_sudo.sh
```

### "No SSD temperature found from any configured device"
**Possible causes**:
1. Device doesn't support temperature monitoring
2. Device path is incorrect
3. Permission issues

**Solutions**:
1. Check available devices: `./scripts/scan_devices.py`
2. Verify device exists: `ls -la /dev/nvme* /dev/sd* /dev/mmcblk*`
3. Test manual access: `sudo smartctl -A /dev/nvme0n1`

### "smartctl: command not found"
**Solution**: Install smartmontools:
```bash
sudo apt update
sudo apt install smartmontools
```

### "Permission denied" or "Operation not permitted"
**Possible causes**:
1. Sudo not configured
2. User not in correct groups
3. Device access restrictions

**Solutions**:
1. Run sudo setup: `./scripts/setup_sudo.sh`
2. Add user to disk group: `sudo usermod -a -G disk $USER`
3. Reboot after group changes: `sudo reboot`

### Temperature readings seem incorrect
**Checks**:
1. Verify readings manually: `sudo smartctl -A /dev/nvme0n1 | grep -i temp`
2. Check for multiple temperature sensors on device
3. Ensure device is actually generating heat (run disk activity)

### Service fails to start
**Debugging steps**:
1. Check service status: `./scripts/status.sh`
2. View logs: `cat data/collector.log`
3. Test collector manually: `python3 collector/temperature_collector.py`
4. Check sudo access: `sudo -n smartctl --version`

## Manual Testing

Test SSD temperature reading manually:
```bash
# Test with sudo
sudo smartctl -A /dev/nvme0n1 | grep -i temp

# Test JSON output (for NVME)
sudo smartctl -A -j /dev/nvme0n1 | grep -i temp

# Test without sudo (may fail)
smartctl -A /dev/nvme0n1 | grep -i temp
```

## Security Considerations

The sudo configuration created by `setup_sudo.sh`:
- Only allows running `smartctl` with sudo
- Does not allow running any other commands with elevated privileges
- Is limited to the specific user that ran the setup
- Can be removed by deleting `/etc/sudoers.d/pi-temp-monitor`

To remove the sudo configuration:
```bash
sudo rm /etc/sudoers.d/pi-temp-monitor
```

## Performance Impact

Reading SSD temperature:
- Typically takes 50-200ms per device
- Cached by system for short periods
- Does not significantly impact SSD performance or lifespan
- Reading frequency controlled by collection interval (default: 5 minutes)
