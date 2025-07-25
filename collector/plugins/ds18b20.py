"""
DS18B20 Temperature Sensor Plugin
1-Wire digital temperature sensor plugin for the monitoring system.
"""

import os
import glob
from . import TemperatureSensorPlugin

class DS18B20Plugin(TemperatureSensorPlugin):
    """Plugin for DS18B20 1-Wire temperature sensors."""
    
    def __init__(self, name, config):
        super().__init__(name, config)
        self.base_dir = '/sys/bus/w1/devices/'
        self.device_file = None
        self._find_device()
    
    def _find_device(self):
        """Find the DS18B20 device file."""
        try:
            # Check if specific device_id is configured
            if 'device_id' in self.config and self.config['device_id']:
                device_path = os.path.join(self.base_dir, self.config['device_id'], 'w1_slave')
                if os.path.exists(device_path):
                    self.device_file = device_path
                    return
            
            # Find any DS18B20 device (starts with 28-)
            device_folders = glob.glob(self.base_dir + '28*')
            if device_folders:
                self.device_file = os.path.join(device_folders[0], 'w1_slave')
                
        except Exception as e:
            self.logger.error(f"Error finding DS18B20 device: {e}")
    
    def is_available(self):
        """Check if DS18B20 sensor is available."""
        if not os.path.exists(self.base_dir):
            self.logger.debug("1-wire interface not available")
            return False
        
        if not self.device_file or not os.path.exists(self.device_file):
            self.logger.debug("DS18B20 device file not found")
            return False
        
        return True
    
    def read_temperature(self):
        """Read temperature from DS18B20 sensor."""
        if not self.is_available():
            return None
        
        try:
            with open(self.device_file, 'r') as f:
                lines = f.readlines()
            
            # Check if reading is valid (ends with YES)
            if len(lines) >= 2 and lines[0].strip().endswith('YES'):
                # Extract temperature from second line
                temp_line = lines[1]
                equals_pos = temp_line.find('t=')
                if equals_pos != -1:
                    temp_string = temp_line[equals_pos + 2:]
                    temp_c = float(temp_string) / 1000.0
                    
                    # Sanity check for reasonable temperature range
                    if -55 <= temp_c <= 125:  # DS18B20 operating range
                        return round(temp_c, 2)
                    else:
                        self.logger.warning(f"Temperature reading out of range: {temp_c}°C")
            else:
                self.logger.warning("DS18B20 reading failed (CRC error)")
                
        except Exception as e:
            self.logger.error(f"Error reading DS18B20 temperature: {e}")
        
        return None
    
    def get_sensor_info(self):
        """Get DS18B20 sensor information."""
        info = {
            'type': 'DS18B20',
            'interface': '1-Wire',
            'range': '-55°C to +125°C',
            'accuracy': '±0.5°C'
        }
        
        if self.device_file:
            device_id = os.path.basename(os.path.dirname(self.device_file))
            info['device_id'] = device_id
            info['device_file'] = self.device_file
        
        return info
