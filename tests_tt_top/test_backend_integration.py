#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for TT-Top backend integration and hardware communication.

Tests the integration between TT-Top widgets and the TTSMIBackend,
including telemetry data processing and hardware-specific functionality.
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tt_top.tt_smi_backend import TTSMIBackend
    from tt_top.tt_top_widget import TTTopDisplay
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TT-Top backend modules: {e}")
    print("Tests will be skipped. Install dependencies to run tests.")
    IMPORTS_AVAILABLE = False


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestBackendIntegration(unittest.TestCase):
    """Test integration between TT-Top and backend"""

    def setUp(self):
        """Set up test fixtures with realistic backend mock"""
        # Create comprehensive backend mock
        self.mock_backend = Mock(spec=TTSMIBackend)

        # Mock realistic device data
        self.mock_devices = []
        for i in range(2):  # Two test devices
            device = Mock()
            device.as_gs.return_value = i == 0
            device.as_wh.return_value = i == 1
            device.as_bh.return_value = False
            self.mock_devices.append(device)

        self.mock_backend.devices = self.mock_devices
        self.mock_backend.get_device_name.side_effect = lambda d: f"Device_{self.mock_devices.index(d)}"

        # Mock telemetry with realistic values
        self.mock_backend.device_telemetrys = [
            {
                'power': '67.3',
                'asic_temperature': '72.1',
                'current': '31.2',
                'voltage': '0.87',
                'aiclk': '1200',
                'heartbeat': '156'
            },
            {
                'power': '45.8',
                'asic_temperature': '65.4',
                'current': '22.7',
                'voltage': '0.84',
                'aiclk': '1000',
                'heartbeat': '157'
            }
        ]

        # Mock device info
        self.mock_backend.device_infos = [
            {
                'board_type': 'e75',
                'board_id': 'GS001',
                'bus_id': '0000:01:00.0',
                'coords': '(0,0)'
            },
            {
                'board_type': 'n150',
                'board_id': 'WH001',
                'bus_id': '0000:02:00.0',
                'coords': '(1,0)'
            }
        ]

        # Mock SMBUS telemetry
        self.mock_backend.smbus_telem_info = [
            {'DDR_STATUS': '22222222'},  # All trained
            {'DDR_STATUS': '11110000'}   # Mixed status
        ]

        # Mock DDR methods
        self.mock_backend.get_dram_speed.side_effect = lambda i: "GDDR6-16000" if i == 0 else "DDR4-3200"
        self.mock_backend.get_dram_training_status.side_effect = lambda i: True

    def test_backend_device_access(self):
        """Test backend device access through TT-Top display"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test device count
        self.assertEqual(len(display.backend.devices), 2)

        # Test device naming
        name0 = display.backend.get_device_name(display.backend.devices[0])
        name1 = display.backend.get_device_name(display.backend.devices[1])
        self.assertEqual(name0, "Device_0")
        self.assertEqual(name1, "Device_1")

    def test_telemetry_data_processing(self):
        """Test telemetry data processing in display methods"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test power value extraction
        telem0 = display.backend.device_telemetrys[0]
        power = float(telem0.get('power', '0.0'))
        self.assertEqual(power, 67.3)

        # Test temperature extraction
        temp = float(telem0.get('asic_temperature', '0.0'))
        self.assertEqual(temp, 72.1)

        # Test status determination based on real values
        status_color = display._get_status_color(temp, power)
        self.assertEqual(status_color, "orange3")  # Should be orange for elevated temp

    def test_architecture_detection_integration(self):
        """Test architecture detection integration"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test Grayskull detection (device 0)
        channels0 = display._get_memory_channels_for_architecture(0)
        self.assertEqual(channels0, 4)  # Grayskull has 4 channels

        grid0 = display._get_tensix_grid_size(0)
        self.assertEqual(grid0, (10, 12))  # Grayskull grid

        # Test Wormhole detection (device 1)
        channels1 = display._get_memory_channels_for_architecture(1)
        self.assertEqual(channels1, 8)  # Wormhole has 8 channels

        grid1 = display._get_tensix_grid_size(1)
        self.assertEqual(grid1, (8, 10))  # Wormhole grid

    def test_ddr_status_integration(self):
        """Test DDR status integration from backend"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test DDR pattern generation with real backend data
        pattern0 = display._generate_real_ddr_pattern(
            display.backend.smbus_telem_info[0]['DDR_STATUS'], 8, 0
        )
        self.assertIn("●", pattern0)  # Should show trained channels

        # Test mixed DDR status
        pattern1 = display._generate_real_ddr_pattern(
            display.backend.smbus_telem_info[1]['DDR_STATUS'], 8, 1
        )
        # Should have both trained and untrained indicators
        self.assertTrue("●" in pattern1 and "◯" in pattern1)

    def test_memory_topology_integration(self):
        """Test memory topology creation with backend data"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test memory topology creation
        topology = display._create_memory_topology()

        # Should return list of strings
        self.assertIsInstance(topology, list)
        self.assertTrue(len(topology) > 0)

        # Should contain device information
        topology_str = "\n".join(topology)
        self.assertIn("Device_0", topology_str)
        self.assertIn("Device_1", topology_str)

    def test_workload_detection_with_backend(self):
        """Test workload detection integration with backend telemetry"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Mock process detection methods to avoid system dependencies
        with patch.object(display, '_detect_ml_workloads') as mock_detect:
            mock_detect.return_value = [
                {
                    'pid': 1234,
                    'framework': 'pytorch',
                    'model_type': 'llm',
                    'workload_type': 'training',
                    'confidence': 0.85,
                    'correlation_score': 0.7,
                    'memory_gb': 16.5,
                    'thread_count': 8
                }
            ]

            # Test workload section creation
            workload_section = display._create_workload_detection_section()

            self.assertIsInstance(workload_section, list)
            self.assertTrue(len(workload_section) > 0)

            # Should contain workload information
            section_str = "\n".join(workload_section)
            self.assertIn("pytorch", section_str.lower())

    def test_hardware_event_log_integration(self):
        """Test hardware event log with real telemetry data"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test event log creation with backend data
        event_log = display._create_live_hardware_log()

        self.assertIsInstance(event_log, list)
        self.assertTrue(len(event_log) > 0)

        # Should contain events based on actual telemetry
        log_str = "\n".join(event_log)
        # Should contain device references
        self.assertTrue("DEV" in log_str or "Device" in log_str)

    def test_bbs_display_integration(self):
        """Test BBS display creation with backend integration"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test main BBS display creation
        bbs_display = display._create_bbs_main_display()

        self.assertIsInstance(bbs_display, list)
        self.assertTrue(len(bbs_display) > 0)

        # Should integrate real device data
        display_str = "\n".join(bbs_display)
        self.assertIn("Device_0", display_str)
        self.assertIn("67.3W", display_str)  # Real power value

    def test_complete_display_rendering(self):
        """Test complete display rendering with backend"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Mock update method to avoid Textual dependencies
        display.update = Mock()

        # Test complete display rendering
        content = display._render_complete_display()

        self.assertIsInstance(content, str)
        self.assertTrue(len(content) > 0)

        # Should contain real device data
        self.assertIn("Device_0", content)
        self.assertIn("Device_1", content)

    def test_backend_error_handling(self):
        """Test error handling when backend fails"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Mock backend failure
        self.mock_backend.update_telem.side_effect = Exception("Hardware communication error")
        display.update = Mock()

        # Should handle errors gracefully
        display._update_display()

        # Should still call update with error message
        display.update.assert_called_once()
        error_message = display.update.call_args[0][0]
        self.assertIn("Error updating display", error_message)

    def test_backend_method_integration(self):
        """Test integration with specific backend methods"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test DDR speed integration
        speed = display.backend.get_dram_speed(0)
        self.assertEqual(speed, "GDDR6-16000")

        # Test DDR training status
        trained = display.backend.get_dram_training_status(0)
        self.assertTrue(trained)

        # Test that these are used in display creation
        memory_topology = display._create_memory_topology()
        topology_str = "\n".join(memory_topology)
        self.assertIn("GDDR6-16000", topology_str)


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestDataValidation(unittest.TestCase):
    """Test data validation and error handling"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_backend = Mock(spec=TTSMIBackend)
        self.mock_backend.devices = [Mock()]

    def test_missing_telemetry_data(self):
        """Test handling of missing telemetry data"""
        # Mock missing telemetry data
        self.mock_backend.device_telemetrys = [{}]  # Empty telemetry
        self.mock_backend.get_device_name.return_value = "TestDevice"

        display = TTTopDisplay(backend=self.mock_backend)

        # Should handle missing data gracefully
        telem = display.backend.device_telemetrys[0]
        power = float(telem.get('power', '0.0'))
        temp = float(telem.get('asic_temperature', '0.0'))

        self.assertEqual(power, 0.0)
        self.assertEqual(temp, 0.0)

        # Status methods should handle zero values
        status = display._get_device_status_text(temp, power)
        self.assertIn("SLEEP", status)

    def test_invalid_telemetry_values(self):
        """Test handling of invalid telemetry values"""
        # Mock invalid telemetry data
        self.mock_backend.device_telemetrys = [{
            'power': 'invalid',
            'asic_temperature': 'NaN',
            'current': '',
            'voltage': 'error'
        }]
        self.mock_backend.get_device_name.return_value = "TestDevice"

        display = TTTopDisplay(backend=self.mock_backend)

        # Should handle invalid data by using defaults
        telem = display.backend.device_telemetrys[0]

        try:
            power = float(telem.get('power', '0.0'))
        except ValueError:
            power = 0.0

        try:
            temp = float(telem.get('asic_temperature', '0.0'))
        except ValueError:
            temp = 0.0

        # Should use safe default values
        self.assertEqual(power, 0.0)
        self.assertEqual(temp, 0.0)

    def test_empty_device_list(self):
        """Test handling of empty device list"""
        self.mock_backend.devices = []
        self.mock_backend.device_telemetrys = []
        self.mock_backend.device_infos = []

        display = TTTopDisplay(backend=self.mock_backend)

        # Should handle empty device list gracefully
        self.assertEqual(len(display.backend.devices), 0)

        # Display methods should handle empty lists
        bbs_display = display._create_bbs_main_display()
        self.assertIsInstance(bbs_display, list)


if __name__ == '__main__':
    unittest.main()