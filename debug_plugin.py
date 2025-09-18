#!/usr/bin/env python3
"""
Debug version of the OLED Voltage Display Plugin

This script helps debug plugin loading issues by testing each component separately.
Run this to identify what's causing the plugin to fail.

Usage:
    python debug_plugin.py
"""

import sys
import os
import logging
import traceback

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test all required imports"""
    logger.info("Testing imports...")
    
    results = {}
    
    # Test standard library imports
    try:
        import time
        import threading
        results['time'] = True
        logger.info("✓ time module imported")
    except Exception as e:
        results['time'] = False
        logger.error(f"✗ time module failed: {e}")
    
    try:
        import threading
        results['threading'] = True
        logger.info("✓ threading module imported")
    except Exception as e:
        results['threading'] = False
        logger.error(f"✗ threading module failed: {e}")
    
    # Test hardware-specific imports
    try:
        import board
        results['board'] = True
        logger.info("✓ board module imported")
    except Exception as e:
        results['board'] = False
        logger.error(f"✗ board module failed: {e}")
    
    try:
        import busio
        results['busio'] = True
        logger.info("✓ busio module imported")
    except Exception as e:
        results['busio'] = False
        logger.error(f"✗ busio module failed: {e}")
    
    try:
        from luma.core.interface.serial import i2c
        from luma.oled.device import sh1106
        results['luma_oled'] = True
        logger.info("✓ luma.oled modules imported")
    except Exception as e:
        results['luma_oled'] = False
        logger.error(f"✗ luma.oled modules failed: {e}")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
        results['PIL'] = True
        logger.info("✓ PIL modules imported")
    except Exception as e:
        results['PIL'] = False
        logger.error(f"✗ PIL modules failed: {e}")
    
    return results

def test_i2c_hardware():
    """Test I2C hardware connectivity"""
    logger.info("Testing I2C hardware...")
    
    try:
        import board
        import busio
        
        # Create I2C interface
        i2c = busio.I2C(board.SCL, board.SDA)
        logger.info("✓ I2C interface created")
        
        # Try to scan for devices
        try:
            from luma.core.interface.serial import i2c
            from luma.oled.device import sh1106

            for addr in [0x3C, 0x3D]:
                try:
                    serial = i2c(port=1, address=addr)
                    display = sh1106(serial, width=128, height=64)
                    logger.info(f"✓ SH1106 OLED display found at address 0x{addr:02X}")

                    # Test basic operations
                    display.clear()
                    logger.info("✓ Display clear test passed")

                    return True

                except Exception as e:
                    logger.debug(f"No SH1106 display at 0x{addr:02X}: {e}")
                    continue

            logger.error("✗ No SH1106 OLED display found at common addresses")
            return False
            
        except Exception as e:
            logger.error(f"✗ OLED test failed: {e}")
            return False
            
    except Exception as e:
        logger.error(f"✗ I2C hardware test failed: {e}")
        return False

def test_plugin_structure():
    """Test plugin file structure"""
    logger.info("Testing plugin structure...")
    
    plugin_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = ['__init__.py', 'manifest.json', 'README.md']
    
    for filename in required_files:
        filepath = os.path.join(plugin_dir, filename)
        if os.path.exists(filepath):
            logger.info(f"✓ {filename} exists")
        else:
            logger.error(f"✗ {filename} missing")
            return False
    
    # Test manifest.json
    try:
        import json
        with open(os.path.join(plugin_dir, 'manifest.json'), 'r') as f:
            manifest = json.load(f)
        
        required_keys = ['domain', 'name', 'description', 'version', 'required_rhapi_version']
        for key in required_keys:
            if key in manifest:
                logger.info(f"✓ manifest.json has {key}: {manifest[key]}")
            else:
                logger.error(f"✗ manifest.json missing {key}")
                return False
                
    except Exception as e:
        logger.error(f"✗ manifest.json test failed: {e}")
        return False
    
    return True

def test_plugin_import():
    """Test plugin import"""
    logger.info("Testing plugin import...")
    
    try:
        # Add plugin directory to path
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        
        # Import the plugin
        import __init__ as plugin_module
        logger.info("✓ Plugin module imported successfully")
        
        # Test key components
        if hasattr(plugin_module, 'DEPENDENCIES_AVAILABLE'):
            logger.info(f"✓ DEPENDENCIES_AVAILABLE: {plugin_module.DEPENDENCIES_AVAILABLE}")
        else:
            logger.error("✗ DEPENDENCIES_AVAILABLE not found")
        
        if hasattr(plugin_module, 'initialize'):
            logger.info("✓ initialize function found")
        else:
            logger.error("✗ initialize function not found")
            return False
        
        if hasattr(plugin_module, 'OLEDVoltageDisplay'):
            logger.info("✓ OLEDVoltageDisplay class found")
        else:
            logger.error("✗ OLEDVoltageDisplay class not found")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Plugin import failed: {e}")
        traceback.print_exc()
        return False

def test_mock_rhapi():
    """Test plugin with mock RHAPI"""
    logger.info("Testing plugin with mock RHAPI...")
    
    try:
        # Create a mock RHAPI object
        class MockEvents:
            def on(self, event, name, handler):
                logger.info(f"Mock event registered: {event} -> {name}")
                return True
        
        class MockRHAPI:
            def __init__(self):
                self.events = MockEvents()
        
        # Import and test plugin
        plugin_dir = os.path.dirname(os.path.abspath(__file__))
        if plugin_dir not in sys.path:
            sys.path.insert(0, plugin_dir)
        
        import __init__ as plugin_module
        
        # Test initialize function
        mock_rhapi = MockRHAPI()
        plugin_module.initialize(mock_rhapi)
        logger.info("✓ Plugin initialize function completed")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Mock RHAPI test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Main debug function"""
    logger.info("Starting OLED Voltage Display Plugin Debug")
    logger.info("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Plugin Structure Test", test_plugin_structure),
        ("Plugin Import Test", test_plugin_import),
        ("Mock RHAPI Test", test_mock_rhapi),
        ("I2C Hardware Test", test_i2c_hardware),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("DEBUG SUMMARY")
    logger.info("=" * 50)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        logger.info(f"{test_name}: {status}")
    
    # Recommendations
    logger.info("\nRECOMMENDations:")
    
    if not results.get("Import Test", False):
        logger.info("- Install missing dependencies: pip install luma.oled pillow")
    
    if not results.get("I2C Hardware Test", False):
        logger.info("- Check I2C is enabled: sudo raspi-config")
        logger.info("- Check wiring: VCC->3.3V, GND->GND, SDA->GPIO2, SCL->GPIO3")
        logger.info("- Scan I2C devices: sudo i2cdetect -y 1")
    
    if not results.get("Plugin Import Test", False):
        logger.info("- Check plugin file structure and syntax")
    
    if results.get("Mock RHAPI Test", False):
        logger.info("- Plugin should work with RotorHazard (event registration successful)")
    
    logger.info("\nDebug completed!")

if __name__ == "__main__":
    main()
