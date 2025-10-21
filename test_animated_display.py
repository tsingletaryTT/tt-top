#!/usr/bin/env python3
"""
Test script for the new hardware-responsive animated ASCII art display

This script tests the animated visualization functionality to ensure it works
correctly with both real hardware and mock hardware for development.
"""

import sys
import logging
from pathlib import Path

# Set up logging for test
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_animated_display():
    """Test the animated display functionality"""
    try:
        # Import required modules
        from tt_top.tt_smi_backend import TTSMIBackend, HARDWARE_AVAILABLE
        from tt_top.animated_display import HardwareResponsiveASCII
        from tt_top.tt_top_app import TTTopApp

        logger.info("Testing hardware-responsive animated ASCII art display...")

        # Initialize with mock hardware for testing
        if HARDWARE_AVAILABLE:
            logger.info("Real hardware detected - using real telemetry")
            from tt_top.tt_smi_backend import detect_chips_with_callback
            devices = detect_chips_with_callback(print_status=False)
            if not devices:
                logger.warning("No devices found, falling back to mock hardware")
                from tt_top.mock_hardware import MockPciChip
                devices = [MockPciChip(i) for i in range(2)]
        else:
            logger.info("Using mock hardware for testing")
            from tt_top.mock_hardware import MockPciChip
            devices = [MockPciChip(i) for i in range(2)]  # Create 2 mock devices

        logger.info(f"Initialized with {len(devices)} device(s)")

        # Create backend with safety configuration
        from tt_top.safety import SafetyConfig
        safety_config = SafetyConfig(
            max_errors_before_disable=3,
            workload_check_interval=1.0,
            max_lock_wait_time=1.0,
            normal_poll_interval=0.1,
            workload_poll_interval=2.0,
            critical_poll_interval=5.0,
        )

        backend = TTSMIBackend(devices=devices, fully_init=True, safety_config=safety_config)
        logger.info("Backend initialized successfully")

        # Test telemetry update
        backend.update_telem()
        logger.info("Telemetry update successful")

        # Launch the application with animated display support
        logger.info("Launching TT-Top with animated visualization support...")
        logger.info("Press 'v' to toggle animated visualization mode")
        logger.info("Press 'q' to quit, 'h' for help")

        app = TTTopApp(backend=backend)
        app.run()

        logger.info("Test completed successfully")
        return True

    except ImportError as e:
        logger.error(f"Import error during testing: {e}")
        logger.error("Make sure all required modules are available")
        return False
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return False

def test_starfield_generation():
    """Test starfield generation without running full app"""
    try:
        logger.info("Testing starfield generation...")

        from tt_top.animated_display import HardwareStarfield
        from tt_top.mock_hardware import MockPciChip
        from tt_top.tt_smi_backend import TTSMIBackend
        from tt_top.safety import SafetyConfig

        # Create mock devices and backend
        devices = [MockPciChip(i) for i in range(2)]
        safety_config = SafetyConfig()
        backend = TTSMIBackend(devices=devices, fully_init=True, safety_config=safety_config)
        backend.update_telem()

        # Create starfield and test initialization
        starfield = HardwareStarfield(width=80, height=24, num_stars=100)
        starfield.initialize_stars(backend)

        logger.info(f"Generated {len(starfield.stars)} stars")

        # Test telemetry update
        starfield.update_from_telemetry(backend, frame_count=1)
        logger.info("Starfield telemetry update successful")

        # Test rendering
        rendered_lines = starfield.render_starfield()
        logger.info(f"Rendered {len(rendered_lines)} lines of starfield")

        # Print first few lines as sample
        logger.info("Sample starfield output:")
        for i, line in enumerate(rendered_lines[:5]):
            logger.info(f"Line {i}: {line[:50]}{'...' if len(line) > 50 else ''}")

        return True

    except Exception as e:
        logger.error(f"Starfield test failed: {e}")
        return False

def main():
    """Main test function"""
    logger.info("Starting animated display tests...")

    # Test starfield generation first
    if not test_starfield_generation():
        logger.error("Starfield generation test failed")
        return 1

    # Ask user if they want to run the full interactive test
    try:
        response = input("Run full interactive test? (y/N): ").strip().lower()
        if response in ('y', 'yes'):
            if not test_animated_display():
                logger.error("Interactive test failed")
                return 1
        else:
            logger.info("Skipping interactive test")
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 0

    logger.info("All tests completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())