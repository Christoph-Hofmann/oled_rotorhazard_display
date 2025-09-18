"""
OLED RotorHazard Display Plugin

This plugin displays voltage information and race data from RotorHazard on an I2C OLED display.
Supports SH1106 OLED displays connected via I2C.

Requirements:
- luma.oled library (supports SH1106, SSD1306, and many others)
- PIL (Pillow) for text rendering
- I2C enabled on Raspberry Pi

Installation:
pip install luma.oled pillow

Wiring:
- VCC -> 3.3V or 5V
- GND -> Ground
- SDA -> GPIO 2 (Pin 3)
- SCL -> GPIO 3 (Pin 5)
"""

import logging
import time
import threading

logger = logging.getLogger(__name__)

# Global variables
plugin_rhapi = None
oled_display = None

# Try to import the display module
try:
    from .oled_display import OLEDDisplay
    DISPLAY_MODULE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"OLED Display module not available: {e}")
    DISPLAY_MODULE_AVAILABLE = False


def test_sensor_access(rhapi):
    """Test if we can access sensor data"""
    try:
        if hasattr(rhapi, 'sensors') and rhapi.sensors:
            sensors_dict = rhapi.sensors.sensors_dict
            logger.info(f"Found {len(sensors_dict)} sensors: {list(sensors_dict.keys())}")
            return True
        else:
            logger.warning("No sensor system available")
            return False
    except Exception as e:
        logger.error(f"Error accessing sensors: {e}")
        return False


def start_display_thread():
    """Start the OLED display thread"""
    global oled_display

    if not DISPLAY_MODULE_AVAILABLE:
        logger.error("Cannot start display - OLED display module not available")
        return

    try:
        if oled_display:
            logger.info(f"OLED display object exists, display_enabled: {oled_display.display_enabled}")
            if oled_display.display_enabled:
                oled_display.start_display_thread()
                logger.info("Display thread startup initiated successfully")
            else:
                logger.error("Cannot start display thread - display not enabled")
        else:
            logger.error("Cannot start display thread - oled_display object is None")
    except Exception as e:
        logger.error(f"Error starting display thread: {e}")
        logger.debug("Exception details:", exc_info=True)


def lap_recorded_handler(args):
    """Handle lap recorded event"""
    global oled_display
    if oled_display and args:
        try:
            # Extract lap information from event args
            pilot_id = args.get('pilot_id')

            # Get lap data from the 'lap' object in the event args
            lap_data = args.get('lap')

            if lap_data:
                # Check if lap_data is a dict or has attributes
                if hasattr(lap_data, 'lap_number'):
                    # It's an object with attributes
                    lap_number = lap_data.lap_number
                    lap_time = getattr(lap_data, 'lap_time_formatted', 'N/A')
                    lap_time_raw = getattr(lap_data, 'lap_time', None)
                elif isinstance(lap_data, dict):
                    # It's a dictionary
                    lap_number = lap_data.get('lap_number', 0)
                    lap_time = lap_data.get('lap_time_formatted', 'N/A')
                    lap_time_raw = lap_data.get('lap_time', None)
                else:
                    lap_number = 0
                    lap_time = 'N/A'
                    lap_time_raw = None

                # If lap_time_formatted is not available, try to format lap_time
                if lap_time == 'N/A' and lap_time_raw and isinstance(lap_time_raw, (int, float)) and lap_time_raw > 0:
                    # Use RotorHazard's time formatting
                    try:
                        if hasattr(plugin_rhapi, 'util'):
                            lap_time = plugin_rhapi.util.format_time_to_str(lap_time_raw)
                        else:
                            # Fallback formatting
                            lap_time_sec = lap_time_raw / 1000.0
                            minutes = int(lap_time_sec // 60)
                            seconds = lap_time_sec % 60
                            lap_time = f"{minutes}:{seconds:06.3f}"
                    except Exception as e:
                        logger.debug(f"Error formatting lap time: {e}")
                        lap_time = f"{lap_time_raw}ms"
            else:
                # Fallback if no lap object - maybe data is directly in args
                lap_number = args.get('lap_number', 0)
                lap_time = args.get('lap_time_formatted', 'N/A')

            # Get pilot information
            pilot_name = "Unknown"
            if pilot_id and hasattr(plugin_rhapi, 'db') and plugin_rhapi.db:
                try:
                    pilot = plugin_rhapi.db.pilot_by_id(pilot_id)
                    if pilot:
                        pilot_name = pilot.callsign or pilot.name or f"Pilot {pilot_id}"
                except Exception as e:
                    logger.debug(f"Error getting pilot info: {e}")
                    pilot_name = f"Pilot {pilot_id}"

            # Show lap completion on display
            oled_display.show_lap_completion(pilot_name, lap_number, lap_time)
            logger.info(f"Lap recorded: {pilot_name} completed lap {lap_number} in {lap_time}")

        except Exception as e:
            logger.error(f"Error handling lap recorded event: {e}")
            logger.debug("Exception details:", exc_info=True)


def startup_handler(args):
    """Handle startup event"""
    logger.info("OLED RotorHazard Display: Handling startup event")
    if plugin_rhapi:
        # Test sensor access first
        test_sensor_access(plugin_rhapi)
        # Start delayed startup in separate thread to avoid blocking RotorHazard
        startup_thread = threading.Thread(target=delayed_startup, daemon=True)
        startup_thread.start()
        logger.info("Delayed startup thread started")
    else:
        logger.error("plugin_rhapi is None - cannot start delayed startup")


def shutdown_handler(args):
    """Handle shutdown event"""
    logger.info("OLED RotorHazard Display: Handling shutdown event")

    global oled_display
    if oled_display:
        oled_display.cleanup()


def delayed_startup():
    """Start display thread after delay"""
    logger.info("Delayed startup thread is running...")
    logger.info("Waiting 15 seconds before starting display thread...")
    time.sleep(15)  # This now runs in background thread
    logger.info("15 second delay completed, starting display thread...")
    start_display_thread()
    logger.info("Display thread startup call completed")


def initialize(rhapi):
    """Initialize the plugin"""
    global plugin_rhapi, oled_display

    if not DISPLAY_MODULE_AVAILABLE:
        logger.error("Cannot initialize OLED display - module not available")
        return False

    try:
        plugin_rhapi = rhapi

        # Create display instance
        oled_display = OLEDDisplay(rhapi)

        # Initialize the display hardware
        if not oled_display.initialize_display():
            logger.error("Failed to initialize OLED display hardware")
            return False

        logger.info("OLED RotorHazard Display plugin v1.0.1 initialized successfully")

        # Start display thread immediately after successful initialization
        logger.info("Starting display thread immediately after initialization...")
        # Small delay to ensure hardware is ready
        time.sleep(1)
        start_display_thread()

        return True

    except Exception as e:
        logger.error(f"Error initializing OLED RotorHazard Display plugin: {e}")
        return False


def discover(rhapi):
    """Discover and register event handlers"""
    try:
        # Import event types
        from eventmanager import Evt

        # Register event handlers with module attribution
        startup_handler.__module__ = __name__
        shutdown_handler.__module__ = __name__
        lap_recorded_handler.__module__ = __name__

        return [
            {
                'event': Evt.STARTUP,
                'callback': startup_handler
            },
            {
                'event': Evt.SHUTDOWN,
                'callback': shutdown_handler
            },
            {
                'event': Evt.RACE_LAP_RECORDED,
                'callback': lap_recorded_handler
            }
        ]

    except Exception as e:
        logger.error(f"Error in discover function: {e}")
        return []