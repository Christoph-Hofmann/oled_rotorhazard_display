# SH1106 OLED Display Setup Guide

This guide specifically covers setting up the plugin with SH1106 OLED displays.

## SH1106 vs SSD1306 Differences

The SH1106 is similar to the SSD1306 but has some key differences:

- **Memory Layout**: SH1106 has 132x64 pixels but only displays 128x64 (offset by 2 pixels)
- **Command Set**: Slightly different initialization commands
- **Library**: Requires `adafruit-circuitpython-sh1106` instead of `adafruit-circuitpython-ssd1306`

## Quick Installation

### 1. Install Dependencies
```bash
pip install luma.oled pillow
```

### 2. Enable I2C
```bash
sudo raspi-config
# Navigate to: Interfacing Options -> I2C -> Enable
```

### 3. Test Hardware Connection
```bash
# Scan for I2C devices
sudo i2cdetect -y 1

# Should show device at 0x3C or 0x3D
```

### 4. Run Test Script
```bash
cd src/server/plugins/oled_rotorhazard_display/
python test_display.py
```

## Wiring for SH1106

```
SH1106 Display    Raspberry Pi
VCC           ->  3.3V (Pin 1) or 5V (Pin 2)
GND           ->  Ground (Pin 6)
SDA           ->  GPIO 2 (Pin 3)
SCL           ->  GPIO 3 (Pin 5)
```

## Common SH1106 Display Modules

- **0.96" 128x64 OLED** - Most common, usually I2C address 0x3C
- **1.3" 128x64 OLED** - Larger version, may use 0x3D
- **Generic SH1106 modules** - Check datasheet for I2C address

## Troubleshooting SH1106 Issues

### Display Not Found
```bash
# Check I2C is enabled
sudo raspi-config

# Scan for devices
sudo i2cdetect -y 1

# Should see:
#      0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
# 00:          -- -- -- -- -- -- -- -- -- -- -- -- --
# 10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
# 30: -- -- -- -- -- -- -- -- -- -- -- -- 3c -- -- --
```

### Wrong Library Error
If you see errors about missing libraries, make sure you have the correct SH1106 library:
```bash
pip uninstall adafruit-circuitpython-ssd1306 adafruit-circuitpython-sh1106
pip install luma.oled pillow
```

### Display Shows Garbled Text
- Check wiring connections
- Verify I2C address (try both 0x3C and 0x3D)
- Ensure 3.3V power supply is stable

### Permission Errors
```bash
# Add user to i2c group
sudo usermod -a -G i2c $USER

# Logout and login again, or reboot
```

## Testing Your SH1106 Display

### Quick Python Test
```python
from luma.core.interface.serial import i2c
from luma.core.render import canvas
from luma.oled.device import sh1106

# Create display (try both addresses)
try:
    serial = i2c(port=1, address=0x3C)
    display = sh1106(serial, width=128, height=64)
    print("SH1106 display found at 0x3C")
except:
    serial = i2c(port=1, address=0x3D)
    display = sh1106(serial, width=128, height=64)
    print("SH1106 display found at 0x3D")

# Clear display
display.clear()

# Draw text using canvas
with canvas(display) as draw:
    draw.text((10, 10), "SH1106 Test", fill="white")
    draw.text((10, 30), "Working!", fill="white")

print("Test completed successfully!")
```

## Integration with RotorHazard

Once your SH1106 display is working:

1. **Copy the plugin** to your RotorHazard plugins directory
2. **Restart RotorHazard** to load the plugin
3. **Check logs** for initialization messages
4. **Monitor display** for voltage data updates

The plugin will automatically:
- Detect your SH1106 display
- Connect to RotorHazard's sensor system
- Display voltage data from connected sensors
- Update every 2 seconds

## Support

If you encounter issues:

1. **Run the debug script**: `python debug_plugin.py`
2. **Check RotorHazard logs** for error messages
3. **Verify hardware connections** with `i2cdetect`
4. **Test display independently** with the test script

The plugin is designed to be robust and will provide helpful error messages to guide troubleshooting.
