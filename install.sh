#!/bin/bash

# Installation script for OLED Voltage Display Plugin
# This script helps set up the plugin and its dependencies

set -e  # Exit on any error

echo "=========================================="
echo "OLED Voltage Display Plugin Installation"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if we're on a Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    print_warning "This doesn't appear to be a Raspberry Pi"
    print_warning "The plugin may still work on other systems with I2C support"
fi

print_status "Checking system requirements..."

# Check if I2C is enabled
if ! lsmod | grep -q i2c_dev; then
    print_error "I2C is not enabled!"
    echo "Please enable I2C using: sudo raspi-config"
    echo "Navigate to: Interfacing Options -> I2C -> Enable"
    exit 1
else
    print_success "I2C is enabled"
fi

# Check if i2c-tools is installed
if ! command -v i2cdetect &> /dev/null; then
    print_status "Installing i2c-tools..."
    sudo apt-get update
    sudo apt-get install -y i2c-tools
else
    print_success "i2c-tools is installed"
fi

# Check for I2C devices
print_status "Scanning for I2C devices..."
if command -v i2cdetect &> /dev/null; then
    echo "I2C devices found:"
    sudo i2cdetect -y 1 | grep -E "(3c|3d)" && print_success "OLED display detected!" || print_warning "No OLED display detected at common addresses (0x3C, 0x3D)"
fi

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
print_status "Python version: $python_version"

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed"
    print_status "Installing pip3..."
    sudo apt-get install -y python3-pip
fi

# Install Python dependencies
print_status "Installing Python dependencies..."

# Check if we're in a virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    print_status "Virtual environment detected: $VIRTUAL_ENV"
    pip_cmd="pip"
else
    print_status "Installing system-wide (no virtual environment detected)"
    pip_cmd="pip3"
fi

# Install dependencies
dependencies=("luma.oled" "pillow")

for dep in "${dependencies[@]}"; do
    print_status "Installing $dep..."
    if $pip_cmd install "$dep"; then
        print_success "$dep installed successfully"
    else
        print_error "Failed to install $dep"
        exit 1
    fi
done

# Test the installation
print_status "Testing OLED display..."
if python3 -c "
from luma.core.interface.serial import i2c
from luma.oled.device import sh1106
from PIL import Image, ImageDraw, ImageFont

try:
    for addr in [0x3C, 0x3D]:
        try:
            serial = i2c(port=1, address=addr)
            display = sh1106(serial, width=128, height=64)
            display.clear()
            print(f'SH1106 OLED display test successful at address 0x{addr:02X}')
            break
        except:
            continue
    else:
        print('No SH1106 OLED display found')
        exit(1)
except Exception as e:
    print(f'Test failed: {e}')
    exit(1)
"; then
    print_success "OLED display test passed!"
else
    print_error "OLED display test failed!"
    print_warning "Check your wiring and I2C connections"
fi

# Check if RotorHazard is running
if pgrep -f "server.py" > /dev/null; then
    print_warning "RotorHazard appears to be running"
    print_warning "You may need to restart RotorHazard for the plugin to load"
fi

echo ""
print_success "Installation completed successfully!"
echo ""
echo "Next steps:"
echo "1. Restart RotorHazard if it's currently running"
echo "2. Check the RotorHazard logs for plugin initialization messages"
echo "3. The OLED display should show voltage data automatically"
echo ""
echo "Troubleshooting:"
echo "- Check wiring: VCC->3.3V, GND->GND, SDA->GPIO2, SCL->GPIO3"
echo "- Verify I2C devices: sudo i2cdetect -y 1"
echo "- Check RotorHazard logs for error messages"
echo ""
echo "For more help, see the README.md file"
