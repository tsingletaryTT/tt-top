#!/usr/bin/env python3
"""
TT-Top Basic Usage Examples

This script demonstrates various ways to use TT-Top for hardware monitoring
and shows how to programmatically access the monitoring capabilities.
"""

import sys
import time
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tt_top.tt_smi_backend import TTSMIBackend
    from tt_top.tt_top_widget import TTTopDisplay
    from tt_top.tt_top_app import TTTopApp, parse_args
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure TT-Top is properly installed with dependencies")
    sys.exit(1)


def basic_telemetry_example():
    """Example 1: Basic telemetry reading without GUI"""
    print("=== Basic Telemetry Example ===")

    try:
        backend = TTSMIBackend()
        print(f"Detected {len(backend.devices)} Tenstorrent devices")

        # Update telemetry once
        backend.update_telem()

        # Display basic device information
        for i, device in enumerate(backend.devices):
            device_name = backend.get_device_name(device)
            telem = backend.device_telemetrys[i]

            print(f"\nDevice {i}: {device_name}")
            print(f"  Power: {telem.get('power', 'N/A')}W")
            print(f"  Temperature: {telem.get('asic_temperature', 'N/A')}°C")
            print(f"  Current: {telem.get('current', 'N/A')}A")
            print(f"  AICLK: {telem.get('aiclk', 'N/A')}MHz")
            print(f"  Heartbeat: {telem.get('heartbeat', 'N/A')}")

    except Exception as e:
        print(f"Error accessing telemetry: {e}")


def monitoring_loop_example():
    """Example 2: Continuous monitoring loop (non-GUI)"""
    print("\n=== Continuous Monitoring Example ===")
    print("Monitoring for 10 seconds (Ctrl+C to stop early)...")

    try:
        backend = TTSMIBackend()
        start_time = time.time()

        while time.time() - start_time < 10:  # Monitor for 10 seconds
            backend.update_telem()

            # Simple status line
            total_power = sum(float(backend.device_telemetrys[i].get('power', '0'))
                            for i in range(len(backend.devices)))
            avg_temp = sum(float(backend.device_telemetrys[i].get('asic_temperature', '0'))
                         for i in range(len(backend.devices))) / len(backend.devices)

            print(f"[{time.time() - start_time:6.1f}s] "
                  f"Total Power: {total_power:6.1f}W | "
                  f"Avg Temp: {avg_temp:5.1f}°C", end='\r')

            time.sleep(0.1)  # 100ms update rate like TT-Top

        print()  # New line after monitoring

    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
    except Exception as e:
        print(f"Error in monitoring loop: {e}")


def device_info_example():
    """Example 3: Display detailed device information"""
    print("\n=== Device Information Example ===")

    try:
        backend = TTSMIBackend()

        for i, device in enumerate(backend.devices):
            device_name = backend.get_device_name(device)
            device_info = backend.device_infos[i]

            print(f"\nDevice {i}: {device_name}")
            print("  Hardware Information:")
            print(f"    Board Type: {device_info.get('board_type', 'Unknown')}")
            print(f"    Board ID: {device_info.get('board_id', 'Unknown')}")
            print(f"    Bus ID: {device_info.get('bus_id', 'Unknown')}")
            print(f"    Coordinates: {device_info.get('coords', 'Unknown')}")

            # Architecture-specific details
            if device.as_gs():
                print("    Architecture: Grayskull (4 DDR channels, 10×12 Tensix)")
            elif device.as_wh():
                print("    Architecture: Wormhole (8 DDR channels, 8×10 Tensix)")
            elif device.as_bh():
                print("    Architecture: Blackhole (12 DDR channels, 14×16 Tensix)")
            else:
                print("    Architecture: Unknown")

            # DDR status if available
            try:
                ddr_speed = backend.get_dram_speed(i)
                ddr_trained = backend.get_dram_training_status(i)
                print(f"    DDR Speed: {ddr_speed}")
                print(f"    DDR Trained: {'Yes' if ddr_trained else 'No'}")
            except:
                print("    DDR Status: Not available")

    except Exception as e:
        print(f"Error getting device information: {e}")


def cli_args_example():
    """Example 4: Demonstrate CLI argument parsing"""
    print("\n=== CLI Arguments Example ===")

    # Save original argv
    original_argv = sys.argv.copy()

    try:
        # Test different argument combinations
        test_cases = [
            ['tt-top'],
            ['tt-top', '--device', '0'],
            ['tt-top', '--log-level', 'DEBUG'],
            ['tt-top', '--no-telemetry-warnings'],
            ['tt-top', '--version'],
        ]

        for test_args in test_cases[:-1]:  # Skip version test to avoid SystemExit
            print(f"Testing args: {' '.join(test_args)}")
            sys.argv = test_args

            try:
                args = parse_args()
                print(f"  Device: {args.device}")
                print(f"  Log Level: {args.log_level}")
                print(f"  No Telemetry Warnings: {args.no_telemetry_warnings}")
            except SystemExit:
                print("  (Help or version requested)")

    finally:
        # Restore original argv
        sys.argv = original_argv


def main():
    """Run all examples"""
    print("TT-Top Usage Examples")
    print("=" * 50)

    # Set up basic logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

    try:
        # Run examples
        basic_telemetry_example()
        monitoring_loop_example()
        device_info_example()
        cli_args_example()

        print("\n=== Full TT-Top GUI Example ===")
        print("To run the full TT-Top interface:")
        print("  tt-top                    # All devices")
        print("  tt-top --device 0         # Specific device")
        print("  tt-top --log-level DEBUG  # Debug mode")
        print("\nPress 'q' to quit when running the full interface")

    except Exception as e:
        print(f"Example failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())