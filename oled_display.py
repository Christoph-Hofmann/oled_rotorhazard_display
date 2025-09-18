"""
OLED Display Handler for RotorHazard

This module contains the main OLED display logic for showing voltage sensor data
and race information on I2C OLED displays.
"""

import logging
import time
import threading
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106
from PIL import ImageFont

logger = logging.getLogger(__name__)


class OLEDDisplay:
    def __init__(self, rhapi):
        self.rhapi = rhapi
        self.display = None
        self.width = 128
        self.height = 64
        self.font = None
        self.last_voltage_data = {}
        self.display_enabled = False

        # Race display state
        self.show_race_info = False
        self.last_lap_info = None
        self.race_info_timeout = 0
        
        # Burn-in protection
        self.voltage_monitor_start_time = time.time()
        self.burn_in_protection_active = False

        # Display thread
        self.display_thread = None
        self.thread_running = False

    def initialize_display(self, i2c_address=0x3C):
        """Initialize the OLED display"""
        try:
            # Create I2C interface
            serial = i2c(port=1, address=i2c_address)
            
            # Create SH1106 display
            self.display = sh1106(serial, width=self.width, height=self.height)
            
            # Load font - try DejaVu Sans Bold first, then fallback to default
            try:
                self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 12)
                logger.info("Loaded DejaVu Sans Bold font")
            except (OSError, IOError):
                try:
                    self.font = ImageFont.load_default()
                    logger.info("Using default font (DejaVu font not found)")
                except Exception as e:
                    logger.warning(f"Could not load any font: {e}")
                    self.font = None
            
            # Clear display
            self.display.clear()
            
            self.display_enabled = True
            logger.info("OLED display initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize OLED display: {e}")
            self.display_enabled = False
            return False

    def start_display_thread(self):
        """Start the display update thread"""
        if self.display_thread and self.display_thread.is_alive():
            logger.warning("Display thread already running")
            return
            
        self.thread_running = True
        self.display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self.display_thread.start()
        logger.info("OLED RotorHazard Display thread started successfully")

    def stop_display_thread(self):
        """Stop the display update thread"""
        self.thread_running = False
        if self.display_thread and self.display_thread.is_alive():
            self.display_thread.join(timeout=2)
        logger.info("OLED RotorHazard Display thread stopped")

    def _display_loop(self):
        """Main display update loop"""
        while self.thread_running:
            try:
                self.update_display()
                time.sleep(2)  # Update every 2 seconds
            except Exception as e:
                logger.error(f"Error in display loop: {e}")
                time.sleep(5)  # Wait longer on error

    def update_display(self):
        """Update the display with current information"""
        if not self.display_enabled:
            return

        try:
            # Check if we should show race info instead of voltage data
            if self.show_race_info and time.time() < self.race_info_timeout:
                self.display_race_info()
                return
            elif self.is_race_active():
                # During active race, show race status instead of voltage data
                # Reset burn-in timer when race starts
                self.voltage_monitor_start_time = time.time()
                self.display_race_status()
                return
            else:
                # Reset race info display when race is not active
                self.show_race_info = False
                self.last_lap_info = None
                # Reset burn-in timer when switching back to voltage monitor
                if not hasattr(self, 'voltage_monitor_start_time') or self.voltage_monitor_start_time == 0:
                    self.voltage_monitor_start_time = time.time()

            # Check if burn-in protection should be active
            voltage_monitor_duration = time.time() - self.voltage_monitor_start_time
            self.burn_in_protection_active = voltage_monitor_duration > 60  # 60 seconds
            
            # Get sensor data from RotorHazard
            voltage_data = self.get_voltage_data()
            logger.debug(f"Retrieved voltage data: {voltage_data}")
            
            # Use luma.oled canvas for drawing
            with canvas(self.display) as draw:
                if self.burn_in_protection_active:
                    # Burn-in protection mode: minimal display with random positioning
                    self.display_burn_in_protection(draw, voltage_data)
                else:
                    # Normal voltage monitor display
                    self.display_normal_voltage_monitor(draw, voltage_data)

        except Exception as e:
            logger.error(f"Error updating display: {e}")

    def get_voltage_data(self):
        """Get voltage sensor data from RotorHazard"""
        try:
            if not hasattr(self.rhapi, 'sensors') or not self.rhapi.sensors:
                logger.debug("No sensor system available")
                return None
                
            sensors_dict = self.rhapi.sensors.sensors_dict
            if not sensors_dict:
                logger.debug("No sensors found in sensors_dict")
                return None
            
            voltage_data = {}
            for sensor_name, sensor_obj in sensors_dict.items():
                try:
                    if hasattr(sensor_obj, 'getReadings'):
                        readings = sensor_obj.getReadings()
                        if readings and any('voltage' in str(key).lower() for key in readings.keys()):
                            voltage_data[sensor_name] = readings
                            logger.debug(f"Found voltage data for sensor {sensor_name}: {readings}")
                except Exception as e:
                    logger.debug(f"Error reading sensor {sensor_name}: {e}")
                    continue
            
            return voltage_data if voltage_data else None
            
        except Exception as e:
            logger.error(f"Error getting voltage data: {e}")
            return None

    def get_race_status(self):
        """Get current race status for display"""
        try:
            if hasattr(self.rhapi, 'race') and self.rhapi.race:
                race_status = self.rhapi.race.status
                if race_status and race_status != 0:  # 0 = READY, 1 = STAGING, 2 = RACING, 3 = DONE
                    if race_status == 1:
                        return "Race: Staging"
                    elif race_status == 2:
                        return "Race: Running"
                    elif race_status == 3:
                        return "Race: Finished"
            return None
        except Exception as e:
            logger.debug(f"Error getting race status: {e}")
            return None
    
    def is_race_active(self):
        """Check if race is currently active (staging or running)"""
        try:
            if hasattr(self.rhapi, 'race') and self.rhapi.race:
                race_status = self.rhapi.race.status
                return race_status in [1, 2]  # 1 = STAGING, 2 = RACING
            return False
        except Exception as e:
            logger.debug(f"Error checking race active status: {e}")
            return False

    def display_race_info(self):
        """Display lap completion information"""
        if not self.display_enabled or not self.last_lap_info:
            return
            
        try:
            with canvas(self.display) as draw:
                # Header
                draw.text((5, 0), "LAP COMPLETED", font=self.font, fill="white")
                draw.line([(0, 13), (self.width, 13)], fill="white")
                
                y_pos = 18
                line_height = 12
                
                # Pilot name
                pilot_name = self.last_lap_info.get('pilot_name', 'Unknown')
                draw.text((5, y_pos), f"Pilot: {pilot_name}", font=self.font, fill="white")
                y_pos += line_height
                
                # Lap number
                lap_number = self.last_lap_info.get('lap_number', 0)
                draw.text((5, y_pos), f"Lap: {lap_number}", font=self.font, fill="white")
                y_pos += line_height
                
                # Lap time
                lap_time = self.last_lap_info.get('lap_time', 'N/A')
                draw.text((5, y_pos), f"Time: {lap_time}", font=self.font, fill="white")
                y_pos += line_height
                
                # Position if available
                if 'position' in self.last_lap_info:
                    position = self.last_lap_info['position']
                    draw.text((5, y_pos), f"Position: {position}", font=self.font, fill="white")
                
                # Don't show clock during race - more space for race info
                
        except Exception as e:
            logger.error(f"Error displaying race info: {e}")

    def display_race_status(self):
        """Display race status and current standings during active race"""
        if not self.display_enabled:
            return
            
        try:
            with canvas(self.display) as draw:
                # Get race status
                race_status = self.get_race_status() or "Race Active"
                draw.text((5, 0), race_status, font=self.font, fill="white")
                draw.line([(0, 13), (self.width, 13)], fill="white")
                
                y_pos = 16  # Start closer to separator line
                line_height = 10  # Smaller line height to fit 4 pilots
                
                # Try to get current race results/standings
                try:
                    if hasattr(self.rhapi, 'race') and self.rhapi.race:
                        # Get current race results
                        results = self.rhapi.race.results
                        if results and 'by_race_time' in results:
                            standings = results['by_race_time'][:4]  # Show top 4
                            
                            for i, pilot_result in enumerate(standings):
                                # Force show exactly 4 pilots - no height check for first 4
                                if i >= 4:
                                    break
                                    
                                position = i + 1
                                pilot_name = pilot_result.get('callsign', pilot_result.get('name', f'Pilot {pilot_result.get("pilot_id", "?")}'))
                                fastest_lap = pilot_result.get('fastest_lap', 'N/A')
                                
                                # Format display line - shorter pilot names for more space
                                if len(pilot_name) > 6:
                                    pilot_name = pilot_name[:6]
                                
                                # Format fastest lap time - remove leading zeros if present
                                if fastest_lap and fastest_lap != 'N/A':
                                    # Remove leading "0:" if time is less than 1 minute
                                    if fastest_lap.startswith('0:'):
                                        fastest_lap = fastest_lap[2:]
                                
                                line_text = f"{position}.{pilot_name} {fastest_lap}"  # Remove space after position
                                draw.text((5, y_pos), line_text, font=self.font, fill="white")
                                y_pos += line_height
                        else:
                            # No results yet, show waiting message
                            draw.text((5, y_pos), "Waiting for", font=self.font, fill="white")
                            draw.text((5, y_pos + line_height), "race data...", font=self.font, fill="white")
                            
                except Exception as e:
                    logger.debug(f"Error getting race results: {e}")
                    draw.text((5, y_pos), "Race in progress", font=self.font, fill="white")
                    draw.text((5, y_pos + line_height), "Monitoring laps...", font=self.font, fill="white")
                
        except Exception as e:
            logger.error(f"Error displaying race status: {e}")
    
    def display_normal_voltage_monitor(self, draw, voltage_data):
        """Display normal voltage monitor with full information"""
        # Check if race is running and show race status
        race_status = self.get_race_status()
        if race_status:
            # Draw race status header
            draw.text((5, 0), race_status, font=self.font, fill="white")
            draw.line([(0, 15), (self.width, 15)], fill="white")
            y_start = 20
        else:
            # Draw voltage monitor title
            draw.text((5, 0), "Voltage Monitor", font=self.font, fill="white")
            draw.line([(0, 15), (self.width, 15)], fill="white")
            y_start = 20
        
        y_pos = y_start
        line_height = 12
        
        if voltage_data:
            sensor_count = 0
            for sensor_name, readings in voltage_data.items():
                if 'voltage' in readings:
                    voltage = readings['voltage']['value']
                    units = readings['voltage']['units']
                    
                    # Format voltage display (no power)
                    voltage_text = f"{sensor_name}: {voltage:.2f}{units}"
                    draw.text((5, y_pos), voltage_text, font=self.font, fill="white")
                    y_pos += line_height
                    sensor_count += 1
                    
                    # Add current if available
                    if 'current' in readings:
                        current = readings['current']['value']
                        current_units = readings['current']['units']
                        current_text = f"  I: {current:.1f}{current_units}"
                        draw.text((5, y_pos), current_text, font=self.font, fill="white")
                        y_pos += line_height
                    
                    y_pos += 2  # Small gap between sensors
                    
                    # Prevent overflow
                    if y_pos > self.height - 20:
                        break
            
            logger.debug(f"Displayed {sensor_count} voltage sensors")
        else:
            # Show system info instead of voltage data
            draw.text((5, y_pos), "No voltage sensors", font=self.font, fill="white")
            y_pos += line_height + 2
            
            # Show available sensors
            try:
                if hasattr(self.rhapi, 'sensors') and self.rhapi.sensors.sensors_dict:
                    sensor_names = list(self.rhapi.sensors.sensors_dict.keys())
                    if sensor_names:
                        draw.text((5, y_pos), f"Sensors: {len(sensor_names)}", font=self.font, fill="white")
                        y_pos += line_height
                        for name in sensor_names[:2]:  # Show first 2 sensor names
                            draw.text((5, y_pos), f"  {name}", font=self.font, fill="white")
                            y_pos += line_height
                    else:
                        draw.text((5, y_pos), "No sensors found", font=self.font, fill="white")
                else:
                    draw.text((5, y_pos), "Sensor system", font=self.font, fill="white")
                    draw.text((5, y_pos + line_height), "not available", font=self.font, fill="white")
            except Exception as e:
                draw.text((5, y_pos), "Sensor error", font=self.font, fill="white")
                logger.debug(f"Error showing sensor info: {e}")
            
            logger.debug("No voltage data available to display")
        
        # Add timestamp
        current_time = time.strftime("%H:%M:%S")
        draw.text((5, self.height - 12), current_time, font=self.font, fill="white")
    
    def display_burn_in_protection(self, draw, voltage_data):
        """Display minimal information with random positioning to prevent burn-in"""
        import random
        
        # Get primary voltage reading
        voltage_text = "No Data"
        if voltage_data:
            for _, readings in voltage_data.items():
                if 'voltage' in readings:
                    voltage = readings['voltage']['value']
                    units = readings['voltage']['units']
                    voltage_text = f"{voltage:.1f}{units}"
                    break  # Use first voltage sensor only
        
        # Get current time
        current_time = time.strftime("%H:%M")
        
        # Calculate random positions (with margins to keep text on screen)
        margin = 10
        max_x = self.width - 50  # Leave space for text width
        max_y = self.height - 20  # Leave space for text height
        
        # Random position for voltage
        voltage_x = random.randint(margin, max_x)
        voltage_y = random.randint(margin, max_y // 2)
        
        # Random position for time (different area)
        time_x = random.randint(margin, max_x)
        time_y = random.randint(max_y // 2 + 10, max_y)
        
        # Draw minimal info at random positions
        draw.text((voltage_x, voltage_y), voltage_text, font=self.font, fill="white")
        draw.text((time_x, time_y), current_time, font=self.font, fill="white")
    
    def show_lap_completion(self, pilot_name, lap_number, lap_time, position=None):
        """Show lap completion information for a few seconds"""
        try:
            self.last_lap_info = {
                'pilot_name': pilot_name,
                'lap_number': lap_number,
                'lap_time': lap_time,
                'position': position
            }
            self.show_race_info = True
            self.race_info_timeout = time.time() + 5  # Show for 5 seconds
            logger.info(f"Showing lap completion: {pilot_name} - Lap {lap_number} - {lap_time}")
        except Exception as e:
            logger.error(f"Error setting lap completion info: {e}")

    def cleanup(self):
        """Clean up display resources"""
        try:
            self.stop_display_thread()
            if self.display:
                self.display.clear()
            logger.info("OLED display cleaned up")
        except Exception as e:
            logger.error(f"Error during display cleanup: {e}")
