# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Workload Detection Configuration Utility

Provides utilities to customize workload detection thresholds and chip-specific
idle power baselines for different deployment scenarios.
"""

import os
import json
from pathlib import Path
from typing import Dict, Any
from tt_smi import constants

class WorkloadConfig:
    """Configuration manager for intelligent workload detection"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path or os.path.expanduser("~/.tt-smi/workload_config.json")
        self.config_dir = os.path.dirname(self.config_path)
        self.custom_config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from file, creating defaults if needed"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    self.custom_config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Failed to load workload config from {self.config_path}: {e}")
                self.custom_config = {}
        else:
            # Create default config
            self.create_default_config()
    
    def save_config(self):
        """Save current configuration to file"""
        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)
        
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.custom_config, f, indent=4)
        except IOError as e:
            print(f"Warning: Failed to save workload config to {self.config_path}: {e}")
    
    def create_default_config(self):
        """Create default configuration file"""
        self.custom_config = {
            "chip_idle_power": dict(constants.CHIP_IDLE_POWER),
            "workload_detection": dict(constants.WORKLOAD_DETECTION),
            "workload_states": dict(constants.WORKLOAD_STATES),
            "version": "1.0",
            "description": "TT-SMI Workload Detection Configuration"
        }
        self.save_config()
    
    def get_chip_idle_power(self, architecture: str) -> float:
        """Get idle power baseline for chip architecture"""
        idle_powers = self.custom_config.get("chip_idle_power", constants.CHIP_IDLE_POWER)
        return idle_powers.get(architecture, constants.CHIP_IDLE_POWER.get(architecture, 25.0))
    
    def set_chip_idle_power(self, architecture: str, idle_power: float):
        """Set idle power baseline for chip architecture"""
        if "chip_idle_power" not in self.custom_config:
            self.custom_config["chip_idle_power"] = dict(constants.CHIP_IDLE_POWER)
        self.custom_config["chip_idle_power"][architecture] = idle_power
        self.save_config()
    
    def get_workload_detection(self) -> Dict[str, Any]:
        """Get workload detection thresholds"""
        return self.custom_config.get("workload_detection", constants.WORKLOAD_DETECTION)
    
    def set_workload_threshold(self, threshold_name: str, value: float):
        """Set specific workload detection threshold"""
        if "workload_detection" not in self.custom_config:
            self.custom_config["workload_detection"] = dict(constants.WORKLOAD_DETECTION)
        self.custom_config["workload_detection"][threshold_name] = value
        self.save_config()
    
    def get_workload_states(self) -> Dict[str, Any]:
        """Get workload state definitions"""
        return self.custom_config.get("workload_states", constants.WORKLOAD_STATES)
    
    def reset_to_defaults(self):
        """Reset configuration to default values"""
        self.create_default_config()
    
    def calibrate_idle_power(self, backend, duration: int = 30):
        """Auto-calibrate idle power baselines by measuring idle consumption
        
        Args:
            backend: TTSMIBackend instance
            duration: Measurement duration in seconds
        """
        print(f"Calibrating idle power baselines for {len(backend.devices)} devices...")
        print(f"Please ensure no workloads are running for {duration} seconds...")
        
        import time
        measurements = {}
        
        # Take measurements over the specified duration
        for i in range(duration):
            backend.update_telem()  # Refresh telemetry
            
            for device_idx, device in enumerate(backend.devices):
                arch = backend.get_chip_architecture(device)
                telem = backend.device_telemetrys[device_idx]
                power = float(telem.get('power', '0.0'))
                
                if arch not in measurements:
                    measurements[arch] = []
                measurements[arch].append(power)
            
            time.sleep(1)
            if i % 10 == 0:
                print(f"  Progress: {i+1}/{duration} seconds")
        
        # Calculate averages and update config
        for arch, powers in measurements.items():
            if powers:
                avg_power = sum(powers) / len(powers)
                # Add 5% margin to account for measurement noise
                idle_power = avg_power * 1.05
                
                print(f"  {arch.title()}: {avg_power:.1f}W average → {idle_power:.1f}W idle baseline")
                self.set_chip_idle_power(arch, idle_power)
        
        print("Calibration complete! Configuration saved.")
    
    def show_current_config(self):
        """Display current configuration"""
        print("Current Workload Detection Configuration:")
        print("=" * 50)
        
        print("\nChip Idle Power Baselines:")
        for arch, power in self.get_chip_idle_power("").items() if isinstance(self.get_chip_idle_power(""), dict) else []:
            print(f"  {arch.title()}: {power:.1f}W")
        
        print("\nWorkload Detection Thresholds:")
        detection = self.get_workload_detection()
        for key, value in detection.items():
            if isinstance(value, (int, float)):
                unit = "W" if "threshold" in key else ("MHz" if "aiclk" in key else ("A" if "current" in key else "°C" if "thermal" in key else ""))
                print(f"  {key.replace('_', ' ').title()}: {value}{unit}")
    
    def export_config(self, export_path: str):
        """Export configuration to specified file"""
        try:
            with open(export_path, 'w') as f:
                json.dump(self.custom_config, f, indent=4)
            print(f"Configuration exported to {export_path}")
        except IOError as e:
            print(f"Error exporting config: {e}")
    
    def import_config(self, import_path: str):
        """Import configuration from specified file"""
        try:
            with open(import_path, 'r') as f:
                imported_config = json.load(f)
            
            # Validate basic structure
            required_keys = ["chip_idle_power", "workload_detection"]
            if all(key in imported_config for key in required_keys):
                self.custom_config = imported_config
                self.save_config()
                print(f"Configuration imported from {import_path}")
            else:
                print(f"Error: Invalid configuration file format")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error importing config: {e}")


# Global configuration instance
_config_instance = None

def get_workload_config() -> WorkloadConfig:
    """Get global workload configuration instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = WorkloadConfig()
    return _config_instance