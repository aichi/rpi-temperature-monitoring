#!/usr/bin/env python3
"""
Storage device detection script for Raspberry Pi temperature monitoring.
This script helps identify available storage devices for temperature monitoring.
"""

import os
import subprocess
import json
import glob

def check_device_exists(device):
    """Check if a storage device exists."""
    return os.path.exists(device)

def test_smartctl_access(device):
    """Test if smartctl can access the device."""
    try:
        # Test with sudo
        result = subprocess.run(['sudo', 'smartctl', '-i', device], 
                              capture_output=True, text=True, check=True, timeout=5)
        return True, "sudo required"
    except subprocess.CalledProcessError:
        try:
            # Test without sudo
            result = subprocess.run(['smartctl', '-i', device], 
                                  capture_output=True, text=True, check=True, timeout=5)
            return True, "no sudo required"
        except subprocess.CalledProcessError:
            return False, "access denied"
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, f"error: {e}"

def get_device_info(device):
    """Get basic device information."""
    try:
        result = subprocess.run(['sudo', 'smartctl', '-i', device], 
                              capture_output=True, text=True, check=True, timeout=5)
        lines = result.stdout.split('\n')
        
        info = {}
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key in ['Device Model', 'Model Number', 'Product', 'Model Family']:
                    info['model'] = value
                elif key == 'Serial Number':
                    info['serial'] = value
                elif key == 'User Capacity':
                    info['capacity'] = value
                elif key in ['Form Factor', 'Rotation Rate']:
                    info['type'] = value
        
        return info
    except Exception:
        return {}

def test_temperature_reading(device):
    """Test if we can read temperature from the device."""
    try:
        # Try regular smartctl output
        result = subprocess.run(['sudo', 'smartctl', '-A', device], 
                              capture_output=True, text=True, check=True, timeout=10)
        lines = result.stdout.split('\n')
        
        temp_found = False
        temp_value = None
        
        for line in lines:
            if 'Temperature' in line and ('Celsius' in line or '°C' in line):
                parts = line.split()
                for part in parts:
                    if part.replace('.', '').isdigit():
                        temp_value = float(part)
                        if 20 <= temp_value <= 100:
                            temp_found = True
                            break
                if temp_found:
                    break
            elif 'Temperature_Celsius' in line:
                parts = line.split()
                if len(parts) >= 10 and parts[9].replace('.', '').isdigit():
                    temp_value = float(parts[9])
                    temp_found = True
                    break
        
        if temp_found:
            return True, f"{temp_value}°C"
        
        # Try JSON output for NVME
        try:
            result_json = subprocess.run(['sudo', 'smartctl', '-A', '-j', device], 
                                       capture_output=True, text=True, check=True, timeout=10)
            data = json.loads(result_json.stdout)
            
            if 'temperature' in data:
                temp = data['temperature']['current']
                return True, f"{temp}°C (JSON)"
            
            if 'ata_smart_attributes' in data:
                for attr in data['ata_smart_attributes']['table']:
                    if attr['name'] == 'Temperature_Celsius':
                        temp = attr['raw']['value']
                        return True, f"{temp}°C (JSON)"
        except:
            pass
        
        return False, "no temperature data found"
        
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, f"error: {e}"

def main():
    """Main function to scan and test storage devices."""
    print("Storage Device Scanner for Raspberry Pi Temperature Monitor")
    print("=" * 60)
    
    # Common storage device paths
    common_devices = [
        '/dev/nvme0n1',
        '/dev/nvme1n1', 
        '/dev/sda',
        '/dev/sdb',
        '/dev/sdc',
        '/dev/mmcblk0',
        '/dev/mmcblk1'
    ]
    
    # Find additional NVME devices
    nvme_devices = glob.glob('/dev/nvme*n1')
    for device in nvme_devices:
        if device not in common_devices:
            common_devices.append(device)
    
    # Find additional SATA devices
    sata_devices = glob.glob('/dev/sd[a-z]')
    for device in sata_devices:
        if device not in common_devices:
            common_devices.append(device)
    
    found_devices = []
    working_devices = []
    
    print("Scanning for storage devices...\n")
    
    for device in common_devices:
        if check_device_exists(device):
            found_devices.append(device)
            print(f"📀 Found device: {device}")
            
            # Get device info
            info = get_device_info(device)
            if info.get('model'):
                print(f"   Model: {info['model']}")
            if info.get('capacity'):
                print(f"   Capacity: {info['capacity']}")
            
            # Test smartctl access
            can_access, access_msg = test_smartctl_access(device)
            print(f"   Access: {access_msg}")
            
            if can_access:
                # Test temperature reading
                can_read_temp, temp_msg = test_temperature_reading(device)
                print(f"   Temperature: {temp_msg}")
                
                if can_read_temp:
                    working_devices.append(device)
                    print(f"   ✅ Device ready for temperature monitoring")
                else:
                    print(f"   ❌ Cannot read temperature")
            else:
                print(f"   ❌ Cannot access device")
            
            print()
    
    if not found_devices:
        print("No storage devices found.")
        return
    
    print("Summary")
    print("-" * 30)
    print(f"Total devices found: {len(found_devices)}")
    print(f"Devices with temperature support: {len(working_devices)}")
    
    if working_devices:
        print("\nRecommended configuration for config.json:")
        print('"storage_devices": [')
        for i, device in enumerate(working_devices):
            comma = "," if i < len(working_devices) - 1 else ""
            print(f'  "{device}"{comma}')
        print(']')
    else:
        print("\nNo devices found with temperature monitoring support.")
        print("This could be due to:")
        print("- Devices don't support SMART temperature monitoring")
        print("- sudo access not configured (run: ./scripts/setup_sudo.sh)")
        print("- smartmontools not installed (run: sudo apt install smartmontools)")

if __name__ == "__main__":
    main()
