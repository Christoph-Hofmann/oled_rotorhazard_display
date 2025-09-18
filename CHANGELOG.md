# Changelog

All notable changes to the OLED RotorHazard Display Plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2024-12-19

### Added
- Race information display during active races
- Pilot name and lap time display when laps are completed
- Real-time race standings with fastest lap times
- Burn-in protection for OLED displays after 60 seconds
- Random positioning of voltage and time in burn-in mode
- Support for both SH1106 and SSD1306 OLED displays

### Changed
- Switched from Adafruit libraries to luma.oled for better I2C support
- Removed power display from voltage monitor to simplify interface
- Optimized display layout to show 4 pilots during races
- Improved space utilization with compact formatting
- Enhanced error handling and logging

### Fixed
- Event handler registration issues with RHAPI
- Display clearing method compatibility with luma.oled
- Lap data extraction from race events
- Startup delay blocking RotorHazard initialization
- Display overflow issues with multiple sensors

### Removed
- Power consumption display (kept voltage and current only)
- Clock display during active races
- Verbose debug logging in production

## [1.0.0] - 2024-12-18

### Added
- Initial release of OLED Voltage Display Plugin
- Basic voltage sensor monitoring
- I2C OLED display support (SSD1306)
- Real-time voltage and current display
- Integration with RotorHazard sensor system
- Plugin manifest and documentation

### Features
- 128x64 OLED display support
- Multiple voltage sensor monitoring
- Automatic sensor discovery
- Clean, readable display layout
- Error handling and logging
