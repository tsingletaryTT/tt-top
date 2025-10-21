#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-SMI Workload Detection Configuration Utility

This script allows you to configure and calibrate workload detection thresholds
for more accurate ACTIVE_WORKLOAD determination.
"""

import sys
import argparse
from tt_smi.workload_config import get_workload_config

def main():
    parser = argparse.ArgumentParser(
        description="Configure TT-SMI workload detection thresholds",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show current configuration
  python configure_workload.py --show

  # Calibrate idle power (requires hardware and no running workloads)  
  python configure_workload.py --calibrate

  # Set custom idle power for Wormhole chips
  python configure_workload.py --set-idle wormhole 30.0

  # Set custom threshold for active workload detection
  python configure_workload.py --set-threshold light_threshold 15.0

  # Reset to default values
  python configure_workload.py --reset

  # Export current config to file
  python configure_workload.py --export my_workload_config.json

  # Import config from file  
  python configure_workload.py --import my_workload_config.json
"""
    )
    
    parser.add_argument("--show", action="store_true", 
                       help="Show current workload detection configuration")
    
    parser.add_argument("--calibrate", action="store_true", 
                       help="Auto-calibrate idle power baselines (requires hardware)")
    
    parser.add_argument("--calibrate-duration", type=int, default=30,
                       help="Calibration duration in seconds (default: 30)")
    
    parser.add_argument("--set-idle", nargs=2, metavar=("ARCH", "POWER"),
                       help="Set idle power baseline for architecture (e.g., wormhole 25.0)")
    
    parser.add_argument("--set-threshold", nargs=2, metavar=("NAME", "VALUE"),
                       help="Set workload detection threshold (e.g., light_threshold 15.0)")
    
    parser.add_argument("--reset", action="store_true",
                       help="Reset configuration to default values")
    
    parser.add_argument("--export", metavar="FILE",
                       help="Export current configuration to file")
    
    parser.add_argument("--import", dest="import_file", metavar="FILE", 
                       help="Import configuration from file")

    args = parser.parse_args()

    # Get configuration manager
    config = get_workload_config()

    # Handle commands
    if args.show:
        config.show_current_config()
    
    elif args.calibrate:
        try:
            from tt_tools_common.utils_common.tools_utils import detect_chips_with_callback
            from tt_smi.tt_smi_backend import TTSMIBackend
            
            print("Detecting TT devices...")
            devices = detect_chips_with_callback()
            
            if not devices:
                print("Error: No TT devices found. Make sure devices are connected and drivers loaded.")
                return 1
            
            backend = TTSMIBackend(devices, fully_init=True, pretty_output=True)
            config.calibrate_idle_power(backend, args.calibrate_duration)
            
        except ImportError:
            print("Error: TT hardware stack not available. Cannot calibrate without hardware access.")
            return 1
        except Exception as e:
            print(f"Error during calibration: {e}")
            return 1
    
    elif args.set_idle:
        arch, power = args.set_idle
        try:
            power_val = float(power)
            config.set_chip_idle_power(arch, power_val)
            print(f"Set {arch} idle power baseline to {power_val}W")
        except ValueError:
            print(f"Error: Power value must be a number, got '{power}'")
            return 1
    
    elif args.set_threshold:
        name, value = args.set_threshold
        try:
            threshold_val = float(value)
            config.set_workload_threshold(name, threshold_val)
            print(f"Set {name} threshold to {threshold_val}")
        except ValueError:
            print(f"Error: Threshold value must be a number, got '{value}'")
            return 1
    
    elif args.reset:
        config.reset_to_defaults()
        print("Configuration reset to defaults")
    
    elif args.export:
        config.export_config(args.export)
    
    elif args.import_file:
        config.import_config(args.import_file)
    
    else:
        # Default to showing config if no command given
        config.show_current_config()
        print("\nUse --help for configuration options")

    return 0

if __name__ == "__main__":
    sys.exit(main())