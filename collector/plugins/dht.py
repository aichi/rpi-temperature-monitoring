"""
DHT11/DHT22 Temperature and Humidity Sensor Plugin
Digital temperature and humidity sensor plugin for the monitoring system.
"""

import subprocess
import time
from . import TemperatureSensorPlugin

class DHTPlugin(TemperatureSensorPlugin):
    """Plugin for DHT11/DHT22 temperature and humidity sensors."""
    
    def __init__(self, name, config):
        super().__init__(name, config)
        self.sensor_type = config.get('sensor_type', 'DHT22')  # DHT11 or DHT22
        self.gpio_pin = config.get('gpio_pin')
        self.last_reading_time = 0
        self.min_interval = 2  # Minimum seconds between readings
    
    def is_available(self):
        """Check if DHT sensor is available."""
        if not self.validate_config(['gpio_pin']):
            return False
        
        # Check if we have a method to read DHT sensors
        # This could be via Adafruit library, pigpio, or other methods
        try:
            # Try to import a DHT library (this is an example - actual implementation
            # would depend on which DHT library is installed)
            import Adafruit_DHT
            return True
        except ImportError:
            self.logger.debug("Adafruit_DHT library not available")
            
        # Alternative: check if pigpio daemon is running for bit-banging DHT
        try:
            import pigpio
            pi = pigpio.pi()
            if pi.connected:
                pi.stop()
                return True
        except ImportError:
            pass
        
        self.logger.debug("No DHT reading method available")
        return False
    
    def read_temperature(self):
        """Read temperature from DHT sensor."""
        if not self.is_available():
            return None
        
        # Respect minimum interval between readings
        current_time = time.time()
        if current_time - self.last_reading_time < self.min_interval:
            self.logger.debug("Too soon since last reading, skipping")
            return None
        
        try:
            # Try Adafruit_DHT library first
            try:
                import Adafruit_DHT
                
                sensor_map = {
                    'DHT11': Adafruit_DHT.DHT11,
                    'DHT22': Adafruit_DHT.DHT22,
                    'AM2302': Adafruit_DHT.AM2302
                }
                
                sensor = sensor_map.get(self.sensor_type, Adafruit_DHT.DHT22)
                humidity, temperature = Adafruit_DHT.read_retry(sensor, self.gpio_pin)
                
                if temperature is not None:
                    self.last_reading_time = current_time
                    
                    # Sanity check for reasonable temperature range
                    if -40 <= temperature <= 80:  # DHT22 operating range
                        return round(temperature, 2)
                    else:
                        self.logger.warning(f"Temperature reading out of range: {temperature}°C")
                
            except ImportError:
                self.logger.debug("Adafruit_DHT not available, trying alternative methods")
                
            # Alternative method using pigpio (bit-banging)
            try:
                import pigpio
                import DHT22  # Custom DHT22 implementation using pigpio
                
                pi = pigpio.pi()
                if pi.connected:
                    dht = DHT22.sensor(pi, self.gpio_pin)
                    dht.trigger()
                    time.sleep(0.2)
                    
                    if dht.temperature() != DHT22.TIMEOUT:
                        temperature = dht.temperature()
                        pi.stop()
                        self.last_reading_time = current_time
                        return round(temperature, 2)
                    
                    pi.stop()
                    
            except ImportError:
                pass
            
            # Fallback: try external DHT reading utility
            try:
                cmd = ['python3', '-c', f'''
import Adafruit_DHT
sensor = Adafruit_DHT.DHT22
pin = {self.gpio_pin}
humidity, temperature = Adafruit_DHT.read_retry(sensor, pin)
if temperature is not None:
    print(temperature)
else:
    exit(1)
''']
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    temperature = float(result.stdout.strip())
                    self.last_reading_time = current_time
                    return round(temperature, 2)
                    
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, ValueError):
                pass
                
        except Exception as e:
            self.logger.error(f"Error reading DHT temperature: {e}")
        
        return None
    
    def get_sensor_info(self):
        """Get DHT sensor information."""
        info = {
            'type': self.sensor_type,
            'interface': 'GPIO',
            'gpio_pin': self.gpio_pin,
            'measures': 'Temperature and Humidity'
        }
        
        if self.sensor_type == 'DHT11':
            info.update({
                'temp_range': '0°C to +50°C',
                'temp_accuracy': '±2°C',
                'humidity_range': '20% to 90% RH',
                'humidity_accuracy': '±5% RH'
            })
        elif self.sensor_type == 'DHT22':
            info.update({
                'temp_range': '-40°C to +80°C',
                'temp_accuracy': '±0.5°C',
                'humidity_range': '0% to 100% RH',
                'humidity_accuracy': '±2-5% RH'
            })
        
        return info
