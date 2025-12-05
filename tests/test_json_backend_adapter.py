#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for JSONBackendAdapter class

Tests JSON parsing, data conversion, and backend interface compatibility.
Uses cached sample JSON files instead of live tt-smi subprocess for reliable testing.
"""

import unittest
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from modules to avoid __init__.py dependencies
import importlib.util

# First import device_proxy (required by json_backend_adapter)
spec_device = importlib.util.spec_from_file_location(
    "device_proxy",
    Path(__file__).parent.parent / "tt_top" / "device_proxy.py"
)
device_proxy_module = importlib.util.module_from_spec(spec_device)
sys.modules['device_proxy'] = device_proxy_module  # Add to sys.modules so other imports can find it
spec_device.loader.exec_module(device_proxy_module)

# Import TTSMILog (required by json_backend_adapter)
spec_log = importlib.util.spec_from_file_location(
    "log",
    Path(__file__).parent.parent / "tt_top" / "log.py"
)
log_module = importlib.util.module_from_spec(spec_log)
sys.modules['log'] = log_module  # Add to sys.modules
spec_log.loader.exec_module(log_module)
TTSMILog = log_module.TTSMILog

# Now import JSONBackendAdapter (which depends on device_proxy and log)
spec_adapter = importlib.util.spec_from_file_location(
    "json_backend_adapter",
    Path(__file__).parent.parent / "tt_top" / "json_backend_adapter.py"
)
json_backend_adapter = importlib.util.module_from_spec(spec_adapter)
spec_adapter.loader.exec_module(json_backend_adapter)
JSONBackendAdapter = json_backend_adapter.JSONBackendAdapter


class TestJSONBackendAdapterParsing(unittest.TestCase):
    """Test JSON parsing and Pydantic model conversion"""

    def setUp(self):
        """Set up test fixtures path"""
        self.fixtures_dir = Path(__file__).parent / 'fixtures'

    def test_parse_grayskull_json(self):
        """Test parsing Grayskull device JSON"""
        json_file = self.fixtures_dir / 'grayskull_sample.json'

        with open(json_file, 'r') as f:
            json_data = json.load(f)

        # Parse into Pydantic model
        log = TTSMILog(**json_data)

        self.assertIsNotNone(log, "TTSMILog should parse successfully")
        self.assertEqual(len(log.device_info), 1, "Should have 1 device")
        self.assertEqual(log.device_info[0].board_info.board_type, 'e150')
        self.assertEqual(log.device_info[0].board_info.bus_id, '0000:01:00.0')

    def test_parse_wormhole_json(self):
        """Test parsing Wormhole device JSON"""
        json_file = self.fixtures_dir / 'wormhole_sample.json'

        with open(json_file, 'r') as f:
            json_data = json.load(f)

        log = TTSMILog(**json_data)

        self.assertIsNotNone(log)
        self.assertEqual(len(log.device_info), 1)
        self.assertEqual(log.device_info[0].board_info.board_type, 'n150')
        self.assertEqual(log.device_info[0].smbus_telem.DDR_SPEED, '6400')

    def test_parse_blackhole_json(self):
        """Test parsing Blackhole device JSON"""
        json_file = self.fixtures_dir / 'blackhole_sample.json'

        with open(json_file, 'r') as f:
            json_data = json.load(f)

        log = TTSMILog(**json_data)

        self.assertIsNotNone(log)
        self.assertEqual(len(log.device_info), 1)
        self.assertEqual(log.device_info[0].board_info.board_type, 'p150')
        self.assertEqual(log.device_info[0].smbus_telem.DDR_SPEED, '8000')

    def test_parse_multi_device_json(self):
        """Test parsing multi-device JSON"""
        json_file = self.fixtures_dir / 'multi_device_sample.json'

        with open(json_file, 'r') as f:
            json_data = json.load(f)

        log = TTSMILog(**json_data)

        self.assertEqual(len(log.device_info), 3, "Should have 3 devices")
        self.assertEqual(log.device_info[0].board_info.board_type, 'n150')
        self.assertEqual(log.device_info[1].board_info.board_type, 'n300')
        self.assertEqual(log.device_info[2].board_info.board_type, 'e75')


class TestJSONBackendAdapterMockMode(unittest.TestCase):
    """Test JSONBackendAdapter in mock mode (no subprocess)"""

    def test_mock_mode_initialization(self):
        """Test that mock mode initializes without subprocess"""
        backend = JSONBackendAdapter(mock_mode=True)

        self.assertIsNotNone(backend, "Backend should initialize in mock mode")
        self.assertTrue(backend.mock_mode, "Mock mode should be enabled")
        self.assertIsNone(backend.process, "Should not spawn subprocess in mock mode")
        self.assertEqual(len(backend.devices), 1, "Mock mode should create 1 device")

    def test_mock_mode_device_properties(self):
        """Test that mock mode creates valid device data"""
        backend = JSONBackendAdapter(mock_mode=True)

        device = backend.devices[0]
        self.assertEqual(device.board_type, 'n150', "Mock device should be Wormhole n150")
        self.assertTrue(device.as_wh(), "Mock device should be detected as Wormhole")

    def test_mock_mode_telemetry_data(self):
        """Test that mock mode generates realistic telemetry"""
        backend = JSONBackendAdapter(mock_mode=True)

        self.assertEqual(len(backend.device_telemetrys), 1)
        telem = backend.device_telemetrys[0]

        # Check that all required fields exist and have reasonable values
        self.assertIn('voltage', telem)
        self.assertIn('current', telem)
        self.assertIn('power', telem)
        self.assertIn('asic_temperature', telem)
        self.assertIn('aiclk', telem)

        # Validate reasonable ranges
        voltage = float(telem['voltage'])
        self.assertGreater(voltage, 0.5, "Voltage should be > 0.5V")
        self.assertLess(voltage, 1.5, "Voltage should be < 1.5V")

        power = float(telem['power'])
        self.assertGreater(power, 0, "Power should be positive")
        self.assertLess(power, 200, "Power should be < 200W")

    def test_mock_mode_smbus_data(self):
        """Test that mock mode generates valid SMBUS data"""
        backend = JSONBackendAdapter(mock_mode=True)

        self.assertEqual(len(backend.smbus_telem_info), 1)
        smbus = backend.smbus_telem_info[0]

        # Check required SMBUS fields
        self.assertIn('DDR_STATUS', smbus)
        self.assertIn('DDR_SPEED', smbus)
        self.assertIn('ARC0_HEALTH', smbus)
        self.assertIn('AICLK', smbus)

        # Validate DDR training status
        ddr_status = int(smbus['DDR_STATUS'])
        self.assertGreater(ddr_status, 0, "DDR should be trained (status > 0)")


class TestJSONBackendAdapterFileMode(unittest.TestCase):
    """Test JSONBackendAdapter with JSON file input"""

    def setUp(self):
        """Set up test fixtures path"""
        self.fixtures_dir = Path(__file__).parent / 'fixtures'

    def test_load_from_json_file_grayskull(self):
        """Test loading Grayskull data from JSON file"""
        json_file = str(self.fixtures_dir / 'grayskull_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        self.assertEqual(len(backend.devices), 1)
        device = backend.devices[0]

        self.assertTrue(device.as_gs(), "Should detect Grayskull architecture")
        self.assertEqual(device.board_type, 'e150')
        self.assertEqual(device.get_num_ddr_channels(), 4)

    def test_load_from_json_file_wormhole(self):
        """Test loading Wormhole data from JSON file"""
        json_file = str(self.fixtures_dir / 'wormhole_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        self.assertEqual(len(backend.devices), 1)
        device = backend.devices[0]

        self.assertTrue(device.as_wh(), "Should detect Wormhole architecture")
        self.assertEqual(device.board_type, 'n150')
        self.assertEqual(device.get_num_ddr_channels(), 8)

    def test_load_from_json_file_blackhole(self):
        """Test loading Blackhole data from JSON file"""
        json_file = str(self.fixtures_dir / 'blackhole_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        self.assertEqual(len(backend.devices), 1)
        device = backend.devices[0]

        self.assertTrue(device.as_bh(), "Should detect Blackhole architecture")
        self.assertEqual(device.board_type, 'p150')
        self.assertEqual(device.get_num_ddr_channels(), 12)

    def test_load_from_json_file_multi_device(self):
        """Test loading multi-device data from JSON file"""
        json_file = str(self.fixtures_dir / 'multi_device_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        self.assertEqual(len(backend.devices), 3, "Should load 3 devices")

        # Check architecture detection for each device
        self.assertTrue(backend.devices[0].as_wh(), "Device 0 should be Wormhole")
        self.assertTrue(backend.devices[1].as_wh(), "Device 1 should be Wormhole")
        self.assertTrue(backend.devices[2].as_gs(), "Device 2 should be Grayskull")


class TestJSONBackendAdapterInterface(unittest.TestCase):
    """Test backend interface methods for compatibility"""

    def setUp(self):
        """Set up backend with sample data"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'wormhole_sample.json')
        self.backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

    def test_devices_property(self):
        """Test devices property returns DeviceProxy list"""
        devices = self.backend.devices

        self.assertIsInstance(devices, list)
        self.assertEqual(len(devices), 1)
        self.assertTrue(hasattr(devices[0], 'as_wh'))
        self.assertTrue(hasattr(devices[0], 'as_gs'))
        self.assertTrue(hasattr(devices[0], 'as_bh'))

    def test_device_telemetrys_property(self):
        """Test device_telemetrys property returns telemetry dicts"""
        telems = self.backend.device_telemetrys

        self.assertIsInstance(telems, list)
        self.assertEqual(len(telems), 1)

        telem = telems[0]
        self.assertIsInstance(telem, dict)
        self.assertIn('voltage', telem)
        self.assertIn('current', telem)
        self.assertIn('power', telem)
        self.assertIn('asic_temperature', telem)
        self.assertIn('aiclk', telem)

    def test_smbus_telem_info_property(self):
        """Test smbus_telem_info property returns SMBUS dicts"""
        smbus_list = self.backend.smbus_telem_info

        self.assertIsInstance(smbus_list, list)
        self.assertEqual(len(smbus_list), 1)

        smbus = smbus_list[0]
        self.assertIsInstance(smbus, dict)
        self.assertIn('DDR_STATUS', smbus)
        self.assertIn('DDR_SPEED', smbus)
        self.assertIn('ARC0_HEALTH', smbus)

    def test_device_infos_property(self):
        """Test device_infos property returns device info dicts"""
        infos = self.backend.device_infos

        self.assertIsInstance(infos, list)
        self.assertEqual(len(infos), 1)

        info = infos[0]
        self.assertIsInstance(info, dict)
        self.assertIn('board_type', info)
        self.assertIn('bus_id', info)
        self.assertIn('dram_status', info)
        self.assertIn('dram_speed', info)

    def test_get_device_name(self):
        """Test get_device_name method"""
        device = self.backend.devices[0]
        name = self.backend.get_device_name(device)

        self.assertIsInstance(name, str)
        self.assertIn('Wormhole', name)
        self.assertIn('0', name)  # Device index

    def test_get_dram_speed(self):
        """Test get_dram_speed method"""
        speed = self.backend.get_dram_speed(0)

        self.assertIsInstance(speed, str)
        self.assertEqual(speed, '6400', "Wormhole sample should have 6400 MT/s DDR")

    def test_get_dram_training_status(self):
        """Test get_dram_training_status method"""
        is_trained = self.backend.get_dram_training_status(0)

        self.assertIsInstance(is_trained, bool)
        self.assertTrue(is_trained, "Sample data DDR should be trained")

    def test_detect_workload_state(self):
        """Test detect_workload_state method"""
        state = self.backend.detect_workload_state(0)

        self.assertIsInstance(state, str)
        self.assertIn(state, ['idle', 'active', 'high'])

    def test_get_workload_event_text(self):
        """Test get_workload_event_text method"""
        power_event = self.backend.get_workload_event_text(0, 'power')
        thermal_event = self.backend.get_workload_event_text(0, 'thermal')

        self.assertIsInstance(power_event, str)
        self.assertIsInstance(thermal_event, str)
        self.assertGreater(len(power_event), 0)
        self.assertGreater(len(thermal_event), 0)


class TestJSONBackendAdapterDataConsistency(unittest.TestCase):
    """Test data consistency across different device types"""

    def test_telemetry_matches_smbus(self):
        """Test that telemetry data matches SMBUS data where applicable"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'wormhole_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        telem = backend.device_telemetrys[0]
        smbus = backend.smbus_telem_info[0]

        # AICLK should match between telemetry and SMBUS
        self.assertEqual(telem['aiclk'], smbus['AICLK'])

    def test_device_count_consistency(self):
        """Test that device counts are consistent across all lists"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'multi_device_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        num_devices = len(backend.devices)
        self.assertEqual(len(backend.device_telemetrys), num_devices)
        self.assertEqual(len(backend.smbus_telem_info), num_devices)
        self.assertEqual(len(backend.device_infos), num_devices)

    def test_device_index_ordering(self):
        """Test that device indices match array positions"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'multi_device_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        for idx, device in enumerate(backend.devices):
            self.assertEqual(device.device_idx, idx,
                           f"Device at position {idx} should have device_idx={idx}")


class TestJSONBackendAdapterTelemetryValidation(unittest.TestCase):
    """Test telemetry data validation and range checking"""

    def setUp(self):
        """Set up backend with Wormhole sample data"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'wormhole_sample.json')
        self.backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

    def test_voltage_range(self):
        """Test voltage is within reasonable range"""
        voltage = float(self.backend.device_telemetrys[0]['voltage'])
        self.assertGreater(voltage, 0.5, "Voltage should be > 0.5V")
        self.assertLess(voltage, 1.2, "Voltage should be < 1.2V")

    def test_current_range(self):
        """Test current is within reasonable range"""
        current = float(self.backend.device_telemetrys[0]['current'])
        self.assertGreater(current, 0, "Current should be positive")
        self.assertLess(current, 150, "Current should be < 150A")

    def test_power_range(self):
        """Test power is within reasonable range"""
        power = float(self.backend.device_telemetrys[0]['power'])
        self.assertGreater(power, 0, "Power should be positive")
        self.assertLess(power, 500, "Power should be < 500W")

    def test_temperature_range(self):
        """Test temperature is within reasonable range"""
        temp = float(self.backend.device_telemetrys[0]['asic_temperature'])
        self.assertGreater(temp, 0, "Temperature should be > 0°C")
        self.assertLess(temp, 120, "Temperature should be < 120°C")

    def test_aiclk_range(self):
        """Test AICLK is within reasonable range"""
        aiclk = float(self.backend.device_telemetrys[0]['aiclk'])
        self.assertGreater(aiclk, 0, "AICLK should be positive")
        self.assertLess(aiclk, 2000, "AICLK should be < 2000 MHz")


if __name__ == '__main__':
    unittest.main()
