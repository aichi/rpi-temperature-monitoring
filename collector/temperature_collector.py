#!/usr/bin/env python3
"""
Temperature data collector for Raspberry Pi monitoring system.
"""

import json
import sqlite3
import subprocess
import time
import os
import glob
import importlib
from datetime import datetime
from pathlib import Path
import logging

class TemperatureCollector:
    def __init__(self, config_path="config/config.json"):
        self.config = self.load_config(config_path)
        self.db_path = self.config["storage"]["database_file"]
        self.external_sensors = {}
        self.setup_database()
        self.setup_logging()
        self.load_external_sensors()
    
    def load_config(self, config_path):
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logging.error(f"Config file not found: {config_path}")
            raise
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON in config file: {config_path}")
            raise
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('data/collector.log'),
                logging.StreamHandler()
            ]
        )
    
    def setup_database(self):
        """Create database and tables if they don't exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main temperature readings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS temperature_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                cpu_temp REAL,
                gpu_temp REAL
            )
        ''')
        
        # Storage device temperatures table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS storage_temperatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                device_path TEXT NOT NULL,
                device_name TEXT,
                temperature REAL
            )
        ''')
        
        # External sensor temperatures table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS external_temperatures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                sensor_name TEXT NOT NULL,
                sensor_type TEXT,
                temperature REAL
            )
        ''')
        
        # Create indexes for better query performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_temp_timestamp ON temperature_readings(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_storage_timestamp ON storage_temperatures(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_external_timestamp ON external_temperatures(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_storage_device ON storage_temperatures(device_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_external_sensor ON external_temperatures(sensor_name)')
        
        conn.commit()
        conn.close()
    
    def get_cpu_temperature(self):
        """Get CPU temperature from /sys/class/thermal/thermal_zone0/temp."""
        try:
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                return round(temp, 2)
        except Exception as e:
            logging.error(f"Error reading CPU temperature: {e}")
            return None
    
    def get_gpu_temperature(self):
        """Get GPU temperature using vcgencmd."""
        try:
            result = subprocess.run(['vcgencmd', 'measure_temp'], 
                                  capture_output=True, text=True, check=True)
            temp_str = result.stdout.strip()
            # Format: temp=XX.X'C
            temp = float(temp_str.split('=')[1].split("'")[0])
            return round(temp, 2)
        except Exception as e:
            logging.error(f"Error reading GPU temperature: {e}")
            return None
    
    def get_ssd_temperatures(self):
        """Get temperatures from all configured SSD devices with device names."""
        results = []
        
        try:
            # Get storage devices from configuration
            devices = self.config["collection"].get("storage_devices", [
                '/dev/nvme0n1', '/dev/sda', '/dev/sdb', '/dev/mmcblk0'
            ])
            
            for device in devices:
                if os.path.exists(device):
                    try:
                        # Get device information first
                        device_name = self._get_device_name(device)
                        
                        # Use sudo to run smartctl for elevated permissions
                        result = subprocess.run(['sudo', 'smartctl', '-A', device], 
                                              capture_output=True, text=True, check=True, timeout=10)
                        lines = result.stdout.split('\n')
                        
                        temperature = None
                        
                        # Look for temperature in different formats
                        for line in lines:
                            # NVME format: Temperature                        XX Celsius
                            if 'Temperature' in line and ('Celsius' in line or '°C' in line):
                                parts = line.split()
                                for i, part in enumerate(parts):
                                    if part.replace('.', '').isdigit():
                                        temp = float(part)
                                        if 20 <= temp <= 100:  # Reasonable temperature range
                                            temperature = round(temp, 2)
                                            break
                                if temperature:
                                    break
                            
                            # Traditional SATA format: Temperature_Celsius
                            if 'Temperature_Celsius' in line:
                                parts = line.split()
                                if len(parts) >= 10 and parts[9].replace('.', '').isdigit():
                                    temperature = round(float(parts[9]), 2)
                                    break
                        
                        # Try JSON output for NVME devices if no temperature found
                        if temperature is None:
                            try:
                                result_json = subprocess.run(['sudo', 'smartctl', '-A', '-j', device], 
                                                           capture_output=True, text=True, check=True, timeout=10)
                                data = json.loads(result_json.stdout)
                                
                                # NVME temperature in JSON format
                                if 'temperature' in data:
                                    temperature = round(data['temperature']['current'], 2)
                                
                                # Check SMART attributes for temperature
                                elif 'ata_smart_attributes' in data:
                                    for attr in data['ata_smart_attributes']['table']:
                                        if attr['name'] == 'Temperature_Celsius':
                                            temperature = round(attr['raw']['value'], 2)
                                            break
                                            
                            except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError):
                                # JSON parsing failed, continue without temperature
                                pass
                        
                        if temperature is not None:
                            results.append({
                                'device_path': device,
                                'device_name': device_name,
                                'temperature': temperature
                            })
                            logging.info(f"SSD temperature from {device} ({device_name}): {temperature}°C")
                        else:
                            logging.debug(f"No temperature found for {device} ({device_name})")
                            
                    except subprocess.TimeoutExpired:
                        logging.warning(f"Timeout reading temperature from {device}")
                        continue
                    except subprocess.CalledProcessError as e:
                        logging.debug(f"smartctl failed for {device}: {e}")
                        continue
                    except Exception as e:
                        logging.debug(f"Error reading temperature from {device}: {e}")
                        continue
            
            return results
        except Exception as e:
            logging.error(f"Error reading SSD temperatures: {e}")
            return []
    
    def _get_device_name(self, device):
        """Get the device name/model from smartctl."""
        try:
            result = subprocess.run(['sudo', 'smartctl', '-i', device], 
                                  capture_output=True, text=True, check=True, timeout=5)
            lines = result.stdout.split('\n')
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    if key in ['Device Model', 'Model Number', 'Product']:
                        return value
            
            # Fallback to device path
            return device
            
        except Exception:
            return device
    
    def load_external_sensors(self):
        """Load external sensor plugins based on configuration."""
        if not self.config["collection"]["sensors"].get("external_sensors", False):
            return
        
        external_sensors_config = self.config["collection"].get("external_sensors", {})
        
        for sensor_name, sensor_config in external_sensors_config.items():
            try:
                plugin_name = sensor_config.get("plugin")
                if not plugin_name:
                    logging.warning(f"No plugin specified for sensor {sensor_name}")
                    continue
                
                # Import the plugin module
                module_name = f"plugins.{plugin_name}"
                plugin_module = importlib.import_module(module_name)
                
                # Get the plugin class (assumes class name follows convention)
                class_name = plugin_name.upper() + "Plugin"
                if hasattr(plugin_module, class_name):
                    plugin_class = getattr(plugin_module, class_name)
                elif plugin_name == "dht11" or plugin_name == "dht22":
                    plugin_class = getattr(plugin_module, "DHTPlugin")
                elif plugin_name == "ds18b20":
                    plugin_class = getattr(plugin_module, "DS18B20Plugin")
                else:
                    logging.error(f"Unknown plugin class for {plugin_name}")
                    continue
                
                # Create sensor instance
                sensor_instance = plugin_class(sensor_name, sensor_config)
                
                # Check if sensor is available
                if sensor_instance.is_available():
                    self.external_sensors[sensor_name] = sensor_instance
                    logging.info(f"Loaded external sensor: {sensor_name} ({plugin_name})")
                else:
                    logging.warning(f"External sensor {sensor_name} ({plugin_name}) is not available")
                    
            except Exception as e:
                logging.error(f"Failed to load external sensor {sensor_name}: {e}")
    
    def get_external_temperatures(self):
        """Get temperatures from all loaded external sensors."""
        results = []
        
        for sensor_name, sensor_instance in self.external_sensors.items():
            try:
                temperature = sensor_instance.read_temperature()
                if temperature is not None:
                    sensor_info = sensor_instance.get_sensor_info()
                    results.append({
                        'sensor_name': sensor_name,
                        'sensor_type': sensor_info.get('type', 'Unknown'),
                        'temperature': temperature
                    })
                    logging.info(f"External sensor {sensor_name}: {temperature}°C")
                else:
                    logging.debug(f"Failed to read temperature from {sensor_name}")
            except Exception as e:
                logging.error(f"Error reading from external sensor {sensor_name}: {e}")
        
        return results
    
    def collect_temperatures(self):
        """Collect all enabled temperature readings."""
        sensors = self.config["collection"]["sensors"]
        readings = {
            'basic': {},
            'storage': [],
            'external': []
        }
        
        if sensors["cpu_temp"]:
            readings['basic']["cpu_temp"] = self.get_cpu_temperature()
        
        if sensors["gpu_temp"]:
            readings['basic']["gpu_temp"] = self.get_gpu_temperature()
        
        if sensors["ssd_temp"]:
            readings['storage'] = self.get_ssd_temperatures()
        
        if sensors.get("external_sensors", False):
            readings['external'] = self.get_external_temperatures()
        
        return readings
    
    def store_readings(self, readings):
        """Store temperature readings in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        current_time = datetime.now().isoformat()
        
        # Store basic readings (CPU, GPU)
        basic = readings.get('basic', {})
        if basic:
            cursor.execute('''
                INSERT INTO temperature_readings 
                (timestamp, cpu_temp, gpu_temp)
                VALUES (?, ?, ?)
            ''', (
                current_time,
                basic.get("cpu_temp"),
                basic.get("gpu_temp")
            ))
        
        # Store storage device readings
        storage_readings = readings.get('storage', [])
        for storage in storage_readings:
            cursor.execute('''
                INSERT INTO storage_temperatures 
                (timestamp, device_path, device_name, temperature)
                VALUES (?, ?, ?, ?)
            ''', (
                current_time,
                storage['device_path'],
                storage['device_name'],
                storage['temperature']
            ))
        
        # Store external sensor readings
        external_readings = readings.get('external', [])
        for external in external_readings:
            cursor.execute('''
                INSERT INTO external_temperatures 
                (timestamp, sensor_name, sensor_type, temperature)
                VALUES (?, ?, ?, ?)
            ''', (
                current_time,
                external['sensor_name'],
                external['sensor_type'],
                external['temperature']
            ))
        
        conn.commit()
        conn.close()
        
        # Log summary
        summary = []
        if basic:
            summary.append(f"Basic: {basic}")
        if storage_readings:
            summary.append(f"Storage: {len(storage_readings)} devices")
        if external_readings:
            summary.append(f"External: {len(external_readings)} sensors")
        
        logging.info(f"Stored readings - {', '.join(summary)}")
    
    def cleanup_old_data(self):
        """Remove old data based on retention policy."""
        retention_days = self.config["storage"]["retention_days"]
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clean up all tables
        tables = ['temperature_readings', 'storage_temperatures', 'external_temperatures']
        total_deleted = 0
        
        for table in tables:
            cursor.execute(f'''
                DELETE FROM {table} 
                WHERE timestamp < datetime('now', '-{retention_days} days')
            ''')
            deleted_rows = cursor.rowcount
            total_deleted += deleted_rows
            if deleted_rows > 0:
                logging.info(f"Cleaned up {deleted_rows} old records from {table}")
        
        conn.commit()
        conn.close()
        
        if total_deleted > 0:
            logging.info(f"Total cleanup: {total_deleted} old temperature records")
    
    def run_collection(self):
        """Run a single collection cycle."""
        try:
            readings = self.collect_temperatures()
            self.store_readings(readings)
            
            # Cleanup old data occasionally (every 100 collections)
            if int(time.time()) % 6000 == 0:  # Roughly every 100 minutes
                self.cleanup_old_data()
                
        except Exception as e:
            logging.error(f"Error during collection: {e}")

def main():
    """Main function to run the collector."""
    collector = TemperatureCollector()
    interval_minutes = collector.config["collection"]["interval_minutes"]
    
    logging.info(f"Starting temperature collector with {interval_minutes} minute interval")
    
    while True:
        collector.run_collection()
        time.sleep(interval_minutes * 60)

if __name__ == "__main__":
    main()
