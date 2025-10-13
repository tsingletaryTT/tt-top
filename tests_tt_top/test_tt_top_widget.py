#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for TT-Top widget functionality.

Tests the TTTopDisplay and TTLiveMonitor widgets including visualization logic,
telemetry processing, and hardware-specific functionality.
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tt_top.tt_top_widget import TTTopDisplay, TTLiveMonitor
    from tt_top.tt_smi_backend import TTSMIBackend
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TT-Top widgets: {e}")
    print("Tests will be skipped. Install dependencies to run tests.")
    IMPORTS_AVAILABLE = False


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestTTTopDisplay(unittest.TestCase):
    """Test TTTopDisplay main widget functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock backend with realistic device data
        self.mock_backend = Mock(spec=TTSMIBackend)

        # Mock devices
        self.mock_devices = [Mock(), Mock()]
        for i, device in enumerate(self.mock_devices):
            device.as_gs.return_value = i == 0  # First device is Grayskull
            device.as_wh.return_value = i == 1  # Second device is Wormhole
            device.as_bh.return_value = False

        self.mock_backend.devices = self.mock_devices

        # Mock device names
        self.mock_backend.get_device_name.side_effect = lambda d: f"TestDevice{self.mock_devices.index(d)}"

        # Mock telemetry data
        self.mock_backend.device_telemetrys = [
            {
                'power': '45.5',
                'asic_temperature': '67.2',
                'current': '23.1',
                'voltage': '0.85',
                'aiclk': '1000',
                'heartbeat': '42'
            },
            {
                'power': '32.1',
                'asic_temperature': '55.8',
                'current': '18.7',
                'voltage': '0.82',
                'aiclk': '900',
                'heartbeat': '43'
            }
        ]

        # Mock device info
        self.mock_backend.device_infos = [
            {
                'board_type': 'e75',
                'board_id': 'TT001',
                'bus_id': '0000:01:00.0'
            },
            {
                'board_type': 'n150',
                'board_id': 'TT002',
                'bus_id': '0000:02:00.0'
            }
        ]

        # Mock SMBUS telemetry info
        self.mock_backend.smbus_telem_info = [
            {'DDR_STATUS': '22222222'},  # All channels trained
            {'DDR_STATUS': '11111111'}   # All channels training
        ]

    def test_display_initialization(self):
        """Test TTTopDisplay initialization"""
        display = TTTopDisplay(backend=self.mock_backend)

        self.assertEqual(display.backend, self.mock_backend)
        self.assertEqual(display.animation_frame, 0)
        self.assertIsInstance(display.start_time, float)

    def test_should_show_logo_timing(self):
        """Test logo display timing logic"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Should show logo immediately after creation
        self.assertTrue(display._should_show_logo())

        # Mock time passing
        display.start_time = time.time() - 6.0  # 6 seconds ago
        self.assertFalse(display._should_show_logo())

    def test_status_color_logic(self):
        """Test status color determination"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test temperature-based coloring
        self.assertEqual(display._get_status_color(90, 30), "bold red")  # High temp
        self.assertEqual(display._get_status_color(70, 30), "orange3")   # Medium temp
        self.assertEqual(display._get_status_color(50, 250), "orange3")  # High power
        self.assertEqual(display._get_status_color(40, 60), "bright_green")  # Medium power
        self.assertEqual(display._get_status_color(30, 20), "bright_cyan")   # Low power

    def test_temperature_color_logic(self):
        """Test temperature-specific color coding"""
        display = TTTopDisplay(backend=self.mock_backend)

        self.assertEqual(display._get_temperature_color(85), "bold red")
        self.assertEqual(display._get_temperature_color(70), "orange3")
        self.assertEqual(display._get_temperature_color(50), "orange1")
        self.assertEqual(display._get_temperature_color(30), "bright_cyan")

    def test_power_color_logic(self):
        """Test power-specific color coding"""
        display = TTTopDisplay(backend=self.mock_backend)

        self.assertEqual(display._get_power_color(80), "bold red")
        self.assertEqual(display._get_power_color(60), "orange3")
        self.assertEqual(display._get_power_color(40), "bright_green")
        self.assertEqual(display._get_power_color(15), "bright_cyan")

    def test_status_indicator_logic(self):
        """Test status block and icon generation"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test high power status
        block, icon = display._get_status_indicator(60)
        self.assertIn("██████████", block)
        self.assertIn("◉", icon)

        # Test medium power status
        block, icon = display._get_status_indicator(35)
        self.assertIn("██████", block)
        self.assertIn("◎", icon)

        # Test low power status
        block, icon = display._get_status_indicator(15)
        self.assertIn("████", block)
        self.assertIn("○", icon)

        # Test idle status
        block, icon = display._get_status_indicator(5)
        self.assertIn("▓▓▓▓▓▓▓▓▓▓", block)
        self.assertIn("·", icon)

    def test_device_status_text(self):
        """Test device status text generation"""
        display = TTTopDisplay(backend=self.mock_backend)

        self.assertIn("CRITICAL", display._get_device_status_text(90, 50))
        self.assertIn("HOT", display._get_device_status_text(80, 50))
        self.assertIn("HIGH LOAD", display._get_device_status_text(60, 80))
        self.assertIn("ACTIVE", display._get_device_status_text(50, 40))
        self.assertIn("IDLE", display._get_device_status_text(40, 15))
        self.assertIn("SLEEP", display._get_device_status_text(30, 2))

    def test_memory_channels_for_architecture(self):
        """Test architecture-specific memory channel count"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test Grayskull (device 0)
        self.assertEqual(display._get_memory_channels_for_architecture(0), 4)

        # Test Wormhole (device 1)
        self.assertEqual(display._get_memory_channels_for_architecture(1), 8)

        # Test unknown architecture fallback
        self.mock_devices[0].as_gs.return_value = False
        self.mock_devices[0].as_wh.return_value = False
        self.mock_devices[0].as_bh.return_value = False
        self.assertEqual(display._get_memory_channels_for_architecture(0), 8)

    def test_tensix_grid_size(self):
        """Test Tensix grid dimensions for different architectures"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test Grayskull
        rows, cols = display._get_tensix_grid_size(0)
        self.assertEqual((rows, cols), (10, 12))

        # Test Wormhole
        rows, cols = display._get_tensix_grid_size(1)
        self.assertEqual((rows, cols), (8, 10))

    def test_ddr_channel_matrix_creation(self):
        """Test DDR channel matrix visualization"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test with mock current values
        result = display._create_ddr_channel_matrix(0, 4, 25.0)  # High current
        self.assertIsInstance(result, str)
        self.assertIn("█", result)  # Should contain high activity indicators

        # Test with low current
        result = display._create_ddr_channel_matrix(1, 8, 2.0)   # Low current
        self.assertIn("·", result)  # Should contain low activity indicators

    def test_real_ddr_pattern_generation(self):
        """Test real DDR pattern generation from hardware status"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test with trained channels (status = 2 for each 4-bit channel)
        result = display._generate_real_ddr_pattern('22222222', 8, 0)
        self.assertIn("●", result)  # Should contain trained indicators

        # Test with training channels (status = 1)
        result = display._generate_real_ddr_pattern('11111111', 8, 1)
        # Should contain training indicators (animated)
        self.assertTrue("◐" in result or "◑" in result)

        # Test with error status (status = 3+)
        result = display._generate_real_ddr_pattern('33333333', 8, 0)
        self.assertIn("✗", result)  # Should contain error indicators

    def test_l2_cache_matrix_creation(self):
        """Test L2 cache bank utilization matrix"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test with high power (should show high utilization)
        result = display._create_l2_cache_matrix(80.0, 8)
        self.assertIn("█", result)  # Should contain high utilization indicators

        # Test with low power
        result = display._create_l2_cache_matrix(10.0, 4)
        self.assertIn("·", result)  # Should contain low utilization indicators

    def test_memory_flow_indicators(self):
        """Test memory data flow visualization"""
        display = TTTopDisplay(backend=self.mock_backend)

        result = display._create_memory_flow_indicators(30.0, 60.0)

        # Should contain flow indicators
        self.assertTrue("▶" in result or "▷" in result or "▸" in result)

        # Should contain bandwidth estimates
        self.assertIn("GB/s", result)

    def test_border_and_formatting_methods(self):
        """Test border creation and formatting methods"""
        display = TTTopDisplay(backend=self.mock_backend)

        # Test section header
        header = display._create_section_header("TEST SECTION")
        self.assertIn("TEST SECTION", header)
        self.assertIn("┌", header)

        # Test bordered line
        line = display._create_bordered_line("test content")
        self.assertIn("test content", line)
        self.assertIn("│", line)

        # Test section footer
        footer = display._create_section_footer()
        self.assertIn("└", footer)

    @patch('time.time')
    def test_update_display_method(self, mock_time):
        """Test display update method"""
        mock_time.return_value = 1000.0
        display = TTTopDisplay(backend=self.mock_backend)

        # Mock the update method to avoid Textual dependencies
        display.update = Mock()

        # Test successful update
        display._update_display()

        self.mock_backend.update_telem.assert_called_once()
        self.assertEqual(display.animation_frame, 1)
        display.update.assert_called_once()

    def test_update_display_error_handling(self):
        """Test error handling in display update"""
        display = TTTopDisplay(backend=self.mock_backend)
        display.update = Mock()

        # Mock backend error
        self.mock_backend.update_telem.side_effect = Exception("Backend error")

        display._update_display()

        # Should handle error gracefully
        display.update.assert_called_once()
        self.assertIn("Error updating display", display.update.call_args[0][0])

    def test_colorize_text_method(self):
        """Test text colorization method"""
        display = TTTopDisplay(backend=self.mock_backend)

        result = display._colorize_text("test", "red")
        self.assertEqual(result, "[red]test[/red]")

    def test_create_border_line_method(self):
        """Test border line creation"""
        display = TTTopDisplay(backend=self.mock_backend)

        result = display._create_border_line("content", "blue", "X")
        self.assertIn("content", result)
        self.assertIn("blue", result)


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestTTLiveMonitor(unittest.TestCase):
    """Test TTLiveMonitor container functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_backend = Mock(spec=TTSMIBackend)
        self.mock_backend.devices = []
        self.mock_backend.device_telemetrys = []

    def test_live_monitor_initialization(self):
        """Test TTLiveMonitor initialization"""
        monitor = TTLiveMonitor(backend=self.mock_backend)

        self.assertEqual(monitor.backend, self.mock_backend)

    def test_bindings_present(self):
        """Test that scroll bindings are defined"""
        monitor = TTLiveMonitor(backend=self.mock_backend)

        # Check bindings exist
        self.assertTrue(len(monitor.BINDINGS) > 0)

        # Check for scroll bindings
        binding_keys = [binding.key for binding in monitor.BINDINGS]
        self.assertIn("up", binding_keys)
        self.assertIn("down", binding_keys)
        self.assertIn("page_up", binding_keys)
        self.assertIn("page_down", binding_keys)
        self.assertIn("home", binding_keys)
        self.assertIn("end", binding_keys)

    def test_scroll_action_methods_exist(self):
        """Test that scroll action methods exist"""
        monitor = TTLiveMonitor(backend=self.mock_backend)

        self.assertTrue(hasattr(monitor, 'action_scroll_up'))
        self.assertTrue(hasattr(monitor, 'action_scroll_down'))
        self.assertTrue(hasattr(monitor, 'action_page_up'))
        self.assertTrue(hasattr(monitor, 'action_page_down'))
        self.assertTrue(hasattr(monitor, 'action_scroll_home'))
        self.assertTrue(hasattr(monitor, 'action_scroll_end'))


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestWorkloadDetection(unittest.TestCase):
    """Test ML workload detection functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_backend = Mock(spec=TTSMIBackend)
        self.mock_backend.devices = [Mock()]
        self.mock_backend.device_telemetrys = [{'power': '45.0', 'current': '20.0'}]

        self.display = TTTopDisplay(backend=self.mock_backend)

    def test_analyze_cmdline_for_ml_patterns(self):
        """Test ML pattern analysis in command lines"""
        # Test PyTorch detection
        result = self.display._analyze_cmdline_for_ml_patterns(
            123, "python train.py --model torch", None, 1
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['framework'], 'pytorch')

        # Test TensorFlow detection
        result = self.display._analyze_cmdline_for_ml_patterns(
            124, "python tensorflow_model.py", None, 1
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['framework'], 'tensorflow')

    def test_analyze_cmdline_model_detection(self):
        """Test model type detection in command lines"""
        # Test LLM model detection
        result = self.display._analyze_cmdline_for_ml_patterns(
            123, "python train_gpt.py", None, 1
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['model_type'], 'llm')

        # Test computer vision model detection
        result = self.display._analyze_cmdline_for_ml_patterns(
            124, "python resnet_training.py", None, 1
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['model_type'], 'computer_vision')

    def test_analyze_cmdline_workload_detection(self):
        """Test workload type detection"""
        # Test training workload
        result = self.display._analyze_cmdline_for_ml_patterns(
            123, "python train.py --epochs 100", None, 1
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['workload_type'], 'training')

        # Test inference workload
        result = self.display._analyze_cmdline_for_ml_patterns(
            124, "python inference.py --model saved_model", None, 1
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['workload_type'], 'inference')

    def test_analyze_cmdline_confidence_scoring(self):
        """Test confidence scoring for ML detection"""
        # High confidence case (clear ML patterns)
        result = self.display._analyze_cmdline_for_ml_patterns(
            123, "python torch_train.py --model gpt --epochs 100", None, 8
        )
        self.assertIsNotNone(result)
        self.assertGreater(result['confidence'], 0.7)

        # Low confidence case (ambiguous patterns)
        result = self.display._analyze_cmdline_for_ml_patterns(
            124, "python script.py", None, 1
        )
        self.assertIsNone(result)  # Should return None for low confidence

    def test_correlate_process_with_telemetry(self):
        """Test process correlation with hardware telemetry"""
        resource_info = {
            'memory_gb': 12.0,
            'threads': 16,
            'cpu_percent': 50
        }

        correlation = self.display._correlate_process_with_telemetry(123, resource_info)

        # Should return a correlation score between 0 and 1
        self.assertGreaterEqual(correlation, 0.0)
        self.assertLessEqual(correlation, 1.0)


if __name__ == '__main__':
    unittest.main()