#!/usr/bin/env python3
"""
Test script to verify the temperature monitoring system setup.
"""

import os
import sys
import json
import subprocess
import sqlite3
from pathlib import Path

def test_config():
    """Test configuration file."""
    print("Testing configuration...")
    
    config_path = "config/config.json"
    if not os.path.exists(config_path):
        print("❌ Config file not found")
        return False
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        print("✅ Config file is valid JSON")
        
        required_keys = ["collection", "storage", "server"]
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required config section: {key}")
                return False
        
        print("✅ Config file structure is valid")
        return True
    except json.JSONDecodeError:
        print("❌ Config file contains invalid JSON")
        return False

def test_temperature_sensors():
    """Test available temperature sensors."""
    print("\nTesting temperature sensors...")
    
    # Test CPU temperature
    try:
        with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
            temp = float(f.read().strip()) / 1000.0
        print(f"✅ CPU temperature: {temp:.1f}°C")
    except Exception as e:
        print(f"❌ CPU temperature: {e}")
    
    # Test GPU temperature
    try:
        result = subprocess.run(['vcgencmd', 'measure_temp'], 
                              capture_output=True, text=True, check=True)
        temp_str = result.stdout.strip()
        temp = float(temp_str.split('=')[1].split("'")[0])
        print(f"✅ GPU temperature: {temp:.1f}°C")
    except Exception as e:
        print(f"❌ GPU temperature: {e}")
    
    # Test for smartctl (SSD temperature)
    try:
        subprocess.run(['smartctl', '--version'], 
                      capture_output=True, text=True, check=True)
        print("✅ smartctl available for SSD temperature")
        
        # Test sudo access for smartctl
        try:
            result = subprocess.run(['sudo', '-n', 'smartctl', '--version'], 
                                  capture_output=True, text=True, check=True)
            print("✅ sudo access for smartctl configured")
        except subprocess.CalledProcessError:
            print("⚠️  sudo access for smartctl not configured (run: ./scripts/setup_sudo.sh)")
        
    except Exception as e:
        print("⚠️  smartctl not available (install with: sudo apt install smartmontools)")
    
    # Test for 1-wire sensors
    w1_devices = Path('/sys/bus/w1/devices')
    if w1_devices.exists():
        sensors = list(w1_devices.glob('28*'))
        if sensors:
            print(f"✅ Found {len(sensors)} DS18B20 sensor(s)")
        else:
            print("⚠️  No DS18B20 sensors found (check wiring and 1-wire interface)")
    else:
        print("⚠️  1-wire interface not available (enable with raspi-config)")

def test_collector():
    """Test the temperature collector."""
    print("\nTesting temperature collector...")
    
    sys.path.insert(0, 'collector')
    try:
        from temperature_collector import TemperatureCollector
        
        collector = TemperatureCollector()
        print("✅ Temperature collector module loaded")
        
        # Test database setup
        if os.path.exists(collector.db_path):
            print("✅ Database file exists")
        else:
            print("⚠️  Database will be created on first run")
        
        # Test collecting temperatures
        readings = collector.collect_temperatures()
        print(f"✅ Collected readings structure: {list(readings.keys())}")
        
        # Test basic temperatures
        basic = readings.get('basic', {})
        if basic:
            print(f"✅ Basic readings: {basic}")
        
        # Test storage temperatures
        storage = readings.get('storage', [])
        if storage:
            print(f"✅ Storage readings: {len(storage)} device(s)")
            for device in storage:
                print(f"   - {device['device_name']}: {device['temperature']}°C")
        else:
            print("⚠️  No storage temperature readings")
        
        # Test external sensors
        external = readings.get('external', [])
        if external:
            print(f"✅ External readings: {len(external)} sensor(s)")
            for sensor in external:
                print(f"   - {sensor['sensor_name']}: {sensor['temperature']}°C")
        else:
            print("⚠️  No external sensor readings (expected if not configured)")
        
        return True
    except Exception as e:
        print(f"❌ Temperature collector error: {e}")
        return False

def test_server():
    """Test the web server module."""
    print("\nTesting web server...")
    
    sys.path.insert(0, 'server')
    try:
        from web_server import TemperatureServer
        
        server = TemperatureServer()
        print("✅ Web server module loaded")
        
        # Test getting latest readings
        try:
            latest = server.get_latest_readings()
            if latest:
                print(f"✅ Latest readings available: {latest}")
            else:
                print("⚠️  No readings available yet (collector needs to run first)")
        except Exception as e:
            print(f"⚠️  Could not get latest readings: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Web server error: {e}")
        return False

def test_scripts():
    """Test that scripts are executable."""
    print("\nTesting scripts...")
    
    scripts = [
        'scripts/start.sh',
        'scripts/stop.sh',
        'scripts/status.sh',
        'scripts/setup_service.sh',
        'scripts/setup_sudo.sh',
        'scripts/scan_devices.py',
        'scripts/clean_data.py'
    ]
    
    all_good = True
    for script in scripts:
        if os.path.exists(script) and os.access(script, os.X_OK):
            print(f"✅ {script} is executable")
        else:
            print(f"❌ {script} is not executable")
            all_good = False
    
    return all_good

def test_plugins():
    """Test plugin system."""
    print("\nTesting plugin system...")
    
    try:
        sys.path.insert(0, 'collector')
        from plugins import TemperatureSensorPlugin, AVAILABLE_PLUGINS
        
        print("✅ Plugin base class loaded")
        print(f"✅ Available plugins: {list(AVAILABLE_PLUGINS.keys())}")
        
        # Test DS18B20 plugin
        try:
            from plugins.ds18b20 import DS18B20Plugin
            test_config = {'device_id': None}
            ds18b20 = DS18B20Plugin('test_ds18b20', test_config)
            print(f"✅ DS18B20 plugin loaded, available: {ds18b20.is_available()}")
        except Exception as e:
            print(f"⚠️  DS18B20 plugin error: {e}")
        
        # Test DHT plugin
        try:
            from plugins.dht import DHTPlugin
            test_config = {'gpio_pin': 4, 'sensor_type': 'DHT22'}
            dht = DHTPlugin('test_dht', test_config)
            print(f"✅ DHT plugin loaded, available: {dht.is_available()}")
        except Exception as e:
            print(f"⚠️  DHT plugin error: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Plugin system error: {e}")
        return False

def main():
    """Run all tests."""
    print("Raspberry Pi Temperature Monitor - System Test")
    print("=" * 50)
    
    # Change to project directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    os.chdir(project_dir)
    
    print(f"Testing in directory: {os.getcwd()}")
    
    tests = [
        test_config,
        test_temperature_sensors,
        test_scripts,
        test_plugins,
        test_collector,
        test_server
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n{'=' * 50}")
    print(f"Test Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! The system is ready to use.")
        print("\nTo start the monitoring system:")
        print("  ./scripts/start.sh")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
