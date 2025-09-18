"""
Configuration example for OLED Voltage Display Plugin

This file shows how to customize the plugin behavior.
Copy and modify as needed for your specific setup.
"""

# Display Configuration
DISPLAY_CONFIG = {
    # OLED Display Settings
    'width': 128,           # Display width in pixels
    'height': 64,           # Display height in pixels
    'i2c_address': 0x3C,    # I2C address (0x3C or 0x3D typically)
    
    # Update Settings
    'update_interval': 2,   # Update interval in seconds
    'startup_delay': 2,     # Startup message display time
    
    # Font Settings
    'font_path': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
    'font_size': 12,
    'small_font_size': 10,
    
    # Display Layout
    'title_y': 0,           # Title position
    'separator_y': 15,      # Separator line position
    'content_start_y': 20,  # Content start position
    'line_height': 12,      # Height between lines
    'sensor_gap': 2,        # Gap between sensors
    'timestamp_y_offset': 12, # Timestamp offset from bottom
    
    # Content Settings
    'show_timestamp': True,
    'show_current': True,
    'show_power': True,
    'voltage_decimals': 2,
    'current_decimals': 1,
    'power_decimals': 1,
}

# Sensor Filter Configuration
SENSOR_FILTER = {
    # Only show sensors with these names (empty list = show all)
    'include_sensors': [],  # e.g., ['Battery', 'Core']
    
    # Exclude sensors with these names
    'exclude_sensors': [],  # e.g., ['Temperature']
    
    # Only show sensors with voltage readings
    'voltage_only': True,
    
    # Minimum voltage to display (filters out very low readings)
    'min_voltage': 0.1,
}

# Display Messages
MESSAGES = {
    'startup_title': 'RotorHazard',
    'startup_subtitle': 'Voltage Monitor',
    'startup_status': 'Initializing...',
    'no_data': 'No voltage data',
    'no_data_sub': 'available',
    'title': 'Voltage Monitor',
}

# Advanced Configuration
ADVANCED_CONFIG = {
    # Thread settings
    'thread_daemon': True,
    'thread_timeout': 5,
    
    # Error handling
    'max_errors': 5,        # Max consecutive errors before stopping
    'error_delay': 5,       # Delay after error (seconds)
    
    # Display optimization
    'clear_on_error': True,
    'show_error_message': True,
    
    # Logging
    'log_level': 'INFO',    # DEBUG, INFO, WARNING, ERROR
    'log_sensor_data': False,
}

# Custom Display Layouts
LAYOUT_COMPACT = {
    'line_height': 10,
    'font_size': 10,
    'show_current': False,
    'show_power': False,
}

LAYOUT_DETAILED = {
    'line_height': 14,
    'font_size': 12,
    'show_current': True,
    'show_power': True,
    'voltage_decimals': 3,
}

# Example: How to apply custom configuration in the plugin
"""
To use these configurations, modify the OLEDVoltageDisplay class __init__ method:

def __init__(self, rhapi, config=None):
    self.rhapi = rhapi
    self.config = config or DISPLAY_CONFIG
    self.width = self.config['width']
    self.height = self.config['height']
    # ... rest of initialization
"""

# Example: Custom sensor filtering
"""
def get_voltage_data(self):
    voltage_data = {}
    filter_config = SENSOR_FILTER
    
    try:
        if hasattr(self.rhapi.racecontext, 'sensors'):
            for sensor_name, sensor in self.rhapi.racecontext.sensors.sensors_dict.items():
                # Apply include filter
                if filter_config['include_sensors'] and sensor_name not in filter_config['include_sensors']:
                    continue
                
                # Apply exclude filter
                if sensor_name in filter_config['exclude_sensors']:
                    continue
                
                readings = sensor.getReadings()
                
                # Check for voltage data
                has_voltage = any('voltage' in reading.lower() for reading in readings.keys())
                if filter_config['voltage_only'] and not has_voltage:
                    continue
                
                # Check minimum voltage
                if has_voltage and 'voltage' in readings:
                    voltage_value = readings['voltage']['value']
                    if voltage_value < filter_config['min_voltage']:
                        continue
                
                voltage_data[sensor_name] = readings
                
    except Exception as e:
        logger.error(f"Error getting voltage data: {e}")
        
    return voltage_data
"""
