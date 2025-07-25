"""
Base plugin interface for external temperature sensors.
All sensor plugins should inherit from this base class.
"""

from abc import ABC, abstractmethod
import logging

class TemperatureSensorPlugin(ABC):
    """Abstract base class for temperature sensor plugins."""
    
    def __init__(self, name, config):
        """
        Initialize the sensor plugin.
        
        Args:
            name (str): Unique name for this sensor instance
            config (dict): Configuration parameters for this sensor
        """
        self.name = name
        self.config = config
        self.logger = logging.getLogger(f"sensor.{name}")
    
    @abstractmethod
    def read_temperature(self):
        """
        Read temperature from the sensor.
        
        Returns:
            float or None: Temperature in Celsius, or None if reading failed
        """
        pass
    
    @abstractmethod
    def is_available(self):
        """
        Check if the sensor is available and can be read.
        
        Returns:
            bool: True if sensor is available, False otherwise
        """
        pass
    
    @abstractmethod
    def get_sensor_info(self):
        """
        Get information about the sensor.
        
        Returns:
            dict: Dictionary with sensor information (type, model, etc.)
        """
        pass
    
    def validate_config(self, required_fields):
        """
        Validate that required configuration fields are present.
        
        Args:
            required_fields (list): List of required configuration field names
            
        Returns:
            bool: True if all required fields are present
        """
        for field in required_fields:
            if field not in self.config:
                self.logger.error(f"Missing required configuration field: {field}")
                return False
        return True

# Export the base class and available plugins
__all__ = ['TemperatureSensorPlugin']

# Plugin registry for dynamic loading
AVAILABLE_PLUGINS = {
    'ds18b20': 'ds18b20.DS18B20Plugin',
    'dht11': 'dht.DHTPlugin',
    'dht22': 'dht.DHTPlugin',
}
