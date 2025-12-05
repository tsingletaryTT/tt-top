#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Integration tests for TT-Top JSON architecture

Tests the complete data flow from JSON files through backend adapter to ensure
all components work together correctly. These tests verify that the JSON-based
architecture maintains full compatibility with the visualization layer.
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
sys.modules['device_proxy'] = device_proxy_module  # Add to sys.modules
spec_device.loader.exec_module(device_proxy_module)
DeviceProxy = device_proxy_module.DeviceProxy

# Import TTSMILog (required by json_backend_adapter)
spec_log = importlib.util.spec_from_file_location(
    "log",
    Path(__file__).parent.parent / "tt_top" / "log.py"
)
log_module = importlib.util.module_from_spec(spec_log)
sys.modules['log'] = log_module  # Add to sys.modules
spec_log.loader.exec_module(log_module)

# Now import JSONBackendAdapter (which depends on device_proxy and log)
spec_adapter = importlib.util.spec_from_file_location(
    "json_backend_adapter",
    Path(__file__).parent.parent / "tt_top" / "json_backend_adapter.py"
)
json_backend_adapter = importlib.util.module_from_spec(spec_adapter)
spec_adapter.loader.exec_module(json_backend_adapter)
JSONBackendAdapter = json_backend_adapter.JSONBackendAdapter


class TestCompleteDataFlow(unittest.TestCase):
    """Test complete data flow from JSON to visualization-ready data"""

    def setUp(self):
        """Set up backends with different device types"""
        fixtures_dir = Path(__file__).parent / 'fixtures'

        self.gs_backend = JSONBackendAdapter(
            mock_mode=True,
            mock_json_file=str(fixtures_dir / 'grayskull_sample.json')
        )

        self.wh_backend = JSONBackendAdapter(
            mock_mode=True,
            mock_json_file=str(fixtures_dir / 'wormhole_sample.json')
        )

        self.bh_backend = JSONBackendAdapter(
            mock_mode=True,
            mock_json_file=str(fixtures_dir / 'blackhole_sample.json')
        )

        self.multi_backend = JSONBackendAdapter(
            mock_mode=True,
            mock_json_file=str(fixtures_dir / 'multi_device_sample.json')
        )

    def test_grayskull_complete_flow(self):
        """Test complete data flow for Grayskull device"""
        backend = self.gs_backend

        # Verify device detection
        self.assertEqual(len(backend.devices), 1)
        device = backend.devices[0]
        self.assertTrue(device.as_gs())
        self.assertEqual(device.get_num_ddr_channels(), 4)
        self.assertEqual(device.get_tensix_grid(), (10, 12))

        # Verify telemetry data
        telem = backend.device_telemetrys[0]
        self.assertEqual(telem['voltage'], '0.80')
        self.assertEqual(telem['power'], '38.2')

        # Verify SMBUS data
        smbus = backend.smbus_telem_info[0]
        self.assertEqual(smbus['DDR_SPEED'], '3200')
        self.assertEqual(smbus['AICLK'], '900')

        # Verify device info
        info = backend.device_infos[0]
        self.assertEqual(info['board_type'], 'e150')
        self.assertEqual(info['dram_status'], 'Trained')

    def test_wormhole_complete_flow(self):
        """Test complete data flow for Wormhole device"""
        backend = self.wh_backend

        # Verify device detection
        device = backend.devices[0]
        self.assertTrue(device.as_wh())
        self.assertEqual(device.get_num_ddr_channels(), 8)
        self.assertEqual(device.get_tensix_grid(), (8, 10))

        # Verify telemetry data
        telem = backend.device_telemetrys[0]
        self.assertEqual(telem['voltage'], '0.85')
        self.assertEqual(telem['current'], '25.5')

        # Verify SMBUS data
        smbus = backend.smbus_telem_info[0]
        self.assertEqual(smbus['DDR_STATUS'], '255')  # All 8 channels trained
        self.assertEqual(smbus['DDR_SPEED'], '6400')

    def test_blackhole_complete_flow(self):
        """Test complete data flow for Blackhole device"""
        backend = self.bh_backend

        # Verify device detection
        device = backend.devices[0]
        self.assertTrue(device.as_bh())
        self.assertEqual(device.get_num_ddr_channels(), 12)
        self.assertEqual(device.get_tensix_grid(), (14, 16))

        # Verify telemetry data
        telem = backend.device_telemetrys[0]
        self.assertEqual(telem['voltage'], '0.90')
        self.assertEqual(telem['current'], '42.8')

        # Verify SMBUS data
        smbus = backend.smbus_telem_info[0]
        self.assertEqual(smbus['DDR_STATUS'], '4095')  # All 12 channels trained
        self.assertEqual(smbus['DDR_SPEED'], '8000')

    def test_multi_device_complete_flow(self):
        """Test complete data flow for multi-device system"""
        backend = self.multi_backend

        # Verify 3 devices detected
        self.assertEqual(len(backend.devices), 3)
        self.assertEqual(len(backend.device_telemetrys), 3)
        self.assertEqual(len(backend.smbus_telem_info), 3)
        self.assertEqual(len(backend.device_infos), 3)

        # Verify each device individually
        # Device 0: Wormhole n150
        self.assertTrue(backend.devices[0].as_wh())
        self.assertEqual(backend.device_infos[0]['board_type'], 'n150')

        # Device 1: Wormhole n300
        self.assertTrue(backend.devices[1].as_wh())
        self.assertEqual(backend.device_infos[1]['board_type'], 'n300')

        # Device 2: Grayskull e75
        self.assertTrue(backend.devices[2].as_gs())
        self.assertEqual(backend.device_infos[2]['board_type'], 'e75')


class TestVisualizationLayerCompatibility(unittest.TestCase):
    """Test that backend interface matches visualization layer expectations"""

    def setUp(self):
        """Set up backend with sample data"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'wormhole_sample.json')
        self.backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

    def test_widget_can_enumerate_devices(self):
        """Test that widgets can enumerate devices as expected"""
        # Widgets typically do: for i, device in enumerate(backend.devices)
        for i, device in enumerate(self.backend.devices):
            self.assertIsNotNone(device)
            self.assertEqual(device.device_idx, i)

            # Widgets access telemetry via index
            telem = self.backend.device_telemetrys[i]
            smbus = self.backend.smbus_telem_info[i]
            info = self.backend.device_infos[i]

            self.assertIsInstance(telem, dict)
            self.assertIsInstance(smbus, dict)
            self.assertIsInstance(info, dict)

    def test_widget_can_check_architecture(self):
        """Test that widgets can check device architecture"""
        device = self.backend.devices[0]

        # Widgets call these methods for conditional rendering
        can_call_as_gs = hasattr(device, 'as_gs') and callable(device.as_gs)
        can_call_as_wh = hasattr(device, 'as_wh') and callable(device.as_wh)
        can_call_as_bh = hasattr(device, 'as_bh') and callable(device.as_bh)

        self.assertTrue(can_call_as_gs)
        self.assertTrue(can_call_as_wh)
        self.assertTrue(can_call_as_bh)

        # Widgets use architecture for memory channel visualization
        if device.as_gs():
            expected_channels = 4
        elif device.as_wh():
            expected_channels = 8
        elif device.as_bh():
            expected_channels = 12
        else:
            expected_channels = 8  # fallback

        self.assertEqual(device.get_num_ddr_channels(), expected_channels)

    def test_widget_can_get_device_name(self):
        """Test that widgets can get human-readable device names"""
        device = self.backend.devices[0]
        name = self.backend.get_device_name(device)

        self.assertIsInstance(name, str)
        self.assertGreater(len(name), 0)

    def test_widget_can_access_telemetry_strings(self):
        """Test that widgets get telemetry as strings (not floats)"""
        telem = self.backend.device_telemetrys[0]

        # Widgets expect strings for display formatting
        self.assertIsInstance(telem['voltage'], str)
        self.assertIsInstance(telem['current'], str)
        self.assertIsInstance(telem['power'], str)
        self.assertIsInstance(telem['asic_temperature'], str)
        self.assertIsInstance(telem['aiclk'], str)

        # Strings should be parseable to float for calculations
        float(telem['voltage'])
        float(telem['current'])
        float(telem['power'])
        float(telem['asic_temperature'])
        float(telem['aiclk'])

    def test_widget_can_access_smbus_strings(self):
        """Test that widgets get SMBUS data as strings"""
        smbus = self.backend.smbus_telem_info[0]

        # All SMBUS fields should be strings
        self.assertIsInstance(smbus['DDR_STATUS'], str)
        self.assertIsInstance(smbus['DDR_SPEED'], str)
        self.assertIsInstance(smbus['ARC0_HEALTH'], str)
        self.assertIsInstance(smbus['AICLK'], str)

        # Strings should be parseable for logic
        int(smbus['DDR_STATUS'])
        int(smbus['DDR_SPEED'])
        int(smbus['ARC0_HEALTH'])
        int(smbus['AICLK'])


class TestMemoryVisualizationData(unittest.TestCase):
    """Test data required for memory hierarchy visualization"""

    def test_ddr_channel_status_grayskull(self):
        """Test DDR channel status for Grayskull (4 channels)"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'grayskull_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        device = backend.devices[0]
        smbus = backend.smbus_telem_info[0]

        num_channels = device.get_num_ddr_channels()
        self.assertEqual(num_channels, 4)

        # DDR_STATUS should indicate training status
        ddr_status = int(smbus['DDR_STATUS'])
        self.assertGreater(ddr_status, 0, "Sample data should have trained channels")

        # Verify channel status interpretation
        # DDR_STATUS = 15 = 0b1111 = all 4 channels trained
        self.assertEqual(ddr_status, 15)

    def test_ddr_channel_status_wormhole(self):
        """Test DDR channel status for Wormhole (8 channels)"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'wormhole_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        device = backend.devices[0]
        smbus = backend.smbus_telem_info[0]

        num_channels = device.get_num_ddr_channels()
        self.assertEqual(num_channels, 8)

        # DDR_STATUS = 255 = 0b11111111 = all 8 channels trained
        ddr_status = int(smbus['DDR_STATUS'])
        self.assertEqual(ddr_status, 255)

    def test_ddr_channel_status_blackhole(self):
        """Test DDR channel status for Blackhole (12 channels)"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'blackhole_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        device = backend.devices[0]
        smbus = backend.smbus_telem_info[0]

        num_channels = device.get_num_ddr_channels()
        self.assertEqual(num_channels, 12)

        # DDR_STATUS = 4095 = 0b111111111111 = all 12 channels trained
        ddr_status = int(smbus['DDR_STATUS'])
        self.assertEqual(ddr_status, 4095)

    def test_ddr_training_status_method(self):
        """Test get_dram_training_status method"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'wormhole_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        # Method should return True for trained DDR
        is_trained = backend.get_dram_training_status(0)
        self.assertTrue(is_trained)

    def test_ddr_speed_method(self):
        """Test get_dram_speed method"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'wormhole_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        speed = backend.get_dram_speed(0)
        self.assertEqual(speed, '6400')


class TestWorkloadDetectionData(unittest.TestCase):
    """Test data required for workload detection and event generation"""

    def setUp(self):
        """Set up backend with sample data"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'wormhole_sample.json')
        self.backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

    def test_workload_state_detection(self):
        """Test detect_workload_state based on power thresholds"""
        state = self.backend.detect_workload_state(0)

        # Sample data has power = 45.2W, should be 'active' (25-75W range)
        self.assertEqual(state, 'active')

    def test_power_event_generation(self):
        """Test power event text generation"""
        event = self.backend.get_workload_event_text(0, 'power')

        self.assertIsInstance(event, str)
        self.assertIn('45.2W', event)  # Should include actual power value

    def test_thermal_event_generation(self):
        """Test thermal event text generation"""
        event = self.backend.get_workload_event_text(0, 'thermal')

        self.assertIsInstance(event, str)
        self.assertIn('52.3', event)  # Should include actual temperature

    def test_current_event_generation(self):
        """Test current event text generation"""
        event = self.backend.get_workload_event_text(0, 'current')

        self.assertIsInstance(event, str)
        self.assertIn('25.5', event)  # Should include actual current

    def test_clock_event_generation(self):
        """Test clock event text generation"""
        event = self.backend.get_workload_event_text(0, 'clock')

        self.assertIsInstance(event, str)
        self.assertIn('1000', event)  # Should include actual AICLK


class TestErrorHandlingAndEdgeCases(unittest.TestCase):
    """Test error handling and edge cases"""

    def test_access_invalid_device_index(self):
        """Test accessing telemetry with invalid device index"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'wormhole_sample.json')
        backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

        # Should handle out-of-bounds gracefully
        speed = backend.get_dram_speed(999)
        self.assertEqual(speed, '0', "Invalid index should return '0'")

        is_trained = backend.get_dram_training_status(999)
        self.assertFalse(is_trained, "Invalid index should return False")

    def test_mock_mode_without_file(self):
        """Test mock mode generates data when no file provided"""
        backend = JSONBackendAdapter(mock_mode=True)

        # Should create at least one mock device
        self.assertGreater(len(backend.devices), 0)
        self.assertGreater(len(backend.device_telemetrys), 0)

    def test_cleanup_method_exists(self):
        """Test that cleanup method exists for proper shutdown"""
        backend = JSONBackendAdapter(mock_mode=True)

        self.assertTrue(hasattr(backend, 'cleanup'))
        self.assertTrue(callable(backend.cleanup))

        # Should be safe to call cleanup
        backend.cleanup()


if __name__ == '__main__':
    unittest.main()
