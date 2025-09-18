# OLED RotorHazard Display Plugin

This RotorHazard plugin displays voltage information and race data from connected sensors on an I2C OLED display. It's perfect for monitoring battery voltage, race standings, and lap times during races.

## Features

- Real-time voltage display on SH1106 OLED screens
- Supports multiple voltage sensors (INA219, Linux battery sensors, etc.)
- Shows voltage, current, and power readings when available
- Automatic sensor detection and display
- Background thread for continuous updates
- Clean, readable display format with timestamps

## Hardware Requirements

### OLED Display
- SH1106-based OLED display (128x64 pixels recommended)
- I2C interface (most common)
- 3.3V or 5V compatible

### Supported Voltage Sensors
- INA219 current/voltage sensors
- Linux system battery sensors
- Any RotorHazard-compatible voltage sensor

## Wiring

### OLED Display (SH1106)
```
OLED Display    Raspberry Pi
VCC         ->  3.3V (Pin 1) or 5V (Pin 2)
GND         ->  Ground (Pin 6)
SDA         ->  GPIO 2 (Pin 3)
SCL         ->  GPIO 3 (Pin 5)
```

### INA219 Voltage Sensor (if using)
```
INA219          Raspberry Pi
VCC         ->  3.3V (Pin 1)
GND         ->  Ground (Pin 6)
SDA         ->  GPIO 2 (Pin 3)
SCL         ->  GPIO 3 (Pin 5)
```

## Installation

### 1. Enable I2C on Raspberry Pi
```bash
sudo raspi-config
# Navigate to Interfacing Options -> I2C -> Enable
```

### 2. Install Python Dependencies
```bash
pip install luma.oled pillow
```

### 3. Install the Plugin

#### Option A: Manual Installation
1. Copy the plugin files to your RotorHazard plugins directory:
   ```
   src/server/plugins/oled_rotorhazard_display/
   ├── __init__.py
   ├── manifest.json
   └── README.md
   ```

2. Restart RotorHazard server

#### Option B: Community Plugin (when published)
1. Go to RotorHazard Settings -> Plugins
2. Search for "I2C OLED RotorHazard Display"
3. Click Install
4. Restart RotorHazard

## Configuration

### OLED Display Address
The plugin automatically tries common I2C addresses:
- 0x3C (most common)
- 0x3D (alternate)

If your display uses a different address, you may need to modify the plugin code.

### Check I2C Devices
To verify your devices are detected:
```bash
sudo i2cdetect -y 1
```

You should see your OLED display and any I2C sensors listed.

## Usage

Once installed and configured:

1. The plugin starts automatically when RotorHazard starts
2. The OLED display shows a startup message
3. Voltage data updates every 2 seconds
4. Display shows:
   - Sensor name and voltage
   - Current (if available)
   - Power (if available)
   - Current timestamp

### Display Format
```
Voltage Monitor
───────────────
Battery: 12.34V
  I: 1.2A
  P: 14.8W

Core: 3.30V

12:34:56
```

## Troubleshooting

### Display Not Working
1. Check I2C is enabled: `sudo raspi-config`
2. Verify wiring connections
3. Check I2C address: `sudo i2cdetect -y 1`
4. Check RotorHazard logs for error messages

### No Voltage Data
1. Ensure voltage sensors are properly configured in RotorHazard
2. Check sensor connections and I2C addresses
3. Verify sensors appear in RotorHazard's sensor list

### Dependencies Issues
```bash
# Install missing dependencies
pip install luma.oled pillow

# For system-wide installation
sudo pip install luma.oled pillow
```

### Permission Issues
```bash
# Add user to i2c group
sudo usermod -a -G i2c $USER
# Logout and login again
```

## Customization

### Display Update Rate
Modify the sleep time in the `display_update_thread()` function:
```python
time.sleep(2)  # Change to desired update interval in seconds
```

### Display Layout
Customize the display layout in the `update_voltage_display()` method to change:
- Font sizes
- Text positioning
- Information displayed
- Display format

### Font Selection
The plugin tries to use DejaVu Sans Bold font, falling back to default if not available. To use a different font:
```python
self.font = ImageFont.truetype("/path/to/your/font.ttf", 12)
```

## Development

### Plugin Structure
```
voltage_oled_display/
├── __init__.py      # Main plugin code
├── manifest.json    # Plugin metadata
└── README.md        # Documentation
```

### Key Components
- `OLEDVoltageDisplay`: Main display class
- `display_update_thread()`: Background update loop
- Event handlers for startup/shutdown
- Sensor data integration with RotorHazard

## License

MIT License - see LICENSE file for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review RotorHazard logs
3. Open an issue on GitHub
4. Ask on RotorHazard Discord/forums
