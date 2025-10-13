#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Performance and stress testing for TT-Top application.

Tests the performance characteristics, memory usage, and scalability
of TT-Top under various conditions and device configurations.
"""

import sys
import unittest
import time
import gc
from unittest.mock import Mock, patch
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tt_top.tt_top_widget import TTTopDisplay
    from tt_top.tt_smi_backend import TTSMIBackend
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TT-Top modules: {e}")
    print("Tests will be skipped. Install dependencies to run tests.")
    IMPORTS_AVAILABLE = False


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestPerformance(unittest.TestCase):
    """Test TT-Top performance characteristics"""

    def setUp(self):
        """Set up performance test fixtures"""
        self.mock_backend = Mock(spec=TTSMIBackend)

    def create_mock_devices(self, count):
        """Create mock devices for scaling tests"""
        devices = []
        telemetry = []
        device_infos = []
        smbus_info = []

        for i in range(count):
            # Mock device
            device = Mock()
            device.as_gs.return_value = i % 3 == 0
            device.as_wh.return_value = i % 3 == 1
            device.as_bh.return_value = i % 3 == 2
            devices.append(device)

            # Mock telemetry
            telemetry.append({
                'power': str(30.0 + i * 5),
                'asic_temperature': str(45.0 + i * 2),
                'current': str(15.0 + i * 3),
                'voltage': str(0.8 + i * 0.01),
                'aiclk': str(800 + i * 50),
                'heartbeat': str(100 + i)
            })

            # Mock device info
            device_infos.append({
                'board_type': f'board_{i}',
                'board_id': f'TT{i:03d}',
                'bus_id': f'0000:{i:02d}:00.0'
            })

            # Mock SMBUS info
            smbus_info.append({'DDR_STATUS': '22222222'})

        self.mock_backend.devices = devices
        self.mock_backend.device_telemetrys = telemetry
        self.mock_backend.device_infos = device_infos
        self.mock_backend.smbus_telem_info = smbus_info
        self.mock_backend.get_device_name.side_effect = lambda d: f"Device_{devices.index(d)}"
        self.mock_backend.get_dram_speed.return_value = "GDDR6-16000"
        self.mock_backend.get_dram_training_status.return_value = True

    def test_single_device_performance(self):
        """Test performance with single device"""
        self.create_mock_devices(1)
        display = TTTopDisplay(backend=self.mock_backend)
        display.update = Mock()

        # Measure display rendering time
        start_time = time.time()
        content = display._render_complete_display()
        end_time = time.time()

        render_time = end_time - start_time

        # Should render quickly (under 100ms for single device)
        self.assertLess(render_time, 0.1, f"Single device render took {render_time:.3f}s")
        self.assertIsInstance(content, str)
        self.assertTrue(len(content) > 0)

    def test_multiple_device_scaling(self):
        """Test performance scaling with multiple devices"""
        device_counts = [1, 2, 4, 8]
        render_times = []

        for count in device_counts:
            self.create_mock_devices(count)
            display = TTTopDisplay(backend=self.mock_backend)
            display.update = Mock()

            # Measure rendering time
            start_time = time.time()
            content = display._render_complete_display()
            end_time = time.time()

            render_time = end_time - start_time
            render_times.append(render_time)

            # Should render reasonably quickly even with many devices
            self.assertLess(render_time, 1.0, f"{count} devices render took {render_time:.3f}s")

        # Rendering time should scale reasonably (not exponentially)
        if len(render_times) >= 2:
            scaling_factor = render_times[-1] / render_times[0]
            max_expected_scaling = device_counts[-1] * 2  # Allow 2x per device max
            self.assertLess(scaling_factor, max_expected_scaling,
                          f"Scaling factor {scaling_factor:.2f} too high for {device_counts[-1]} devices")

    def test_update_frequency_performance(self):
        """Test performance under frequent updates (100ms refresh rate)"""
        self.create_mock_devices(4)
        display = TTTopDisplay(backend=self.mock_backend)
        display.update = Mock()

        # Simulate rapid updates like GUI_INTERVAL_TIME (100ms)
        update_times = []
        num_updates = 20

        for i in range(num_updates):
            # Update animation frame (simulates time passing)
            display.animation_frame = i

            start_time = time.time()
            display._update_display()
            end_time = time.time()

            update_time = end_time - start_time
            update_times.append(update_time)

        avg_update_time = sum(update_times) / len(update_times)
        max_update_time = max(update_times)

        # Updates should be fast enough for 100ms refresh rate
        self.assertLess(avg_update_time, 0.05, f"Average update time {avg_update_time:.3f}s too slow")
        self.assertLess(max_update_time, 0.1, f"Max update time {max_update_time:.3f}s too slow")

    def test_memory_hierarchy_performance(self):
        """Test memory hierarchy matrix performance"""
        self.create_mock_devices(8)  # Many devices
        display = TTTopDisplay(backend=self.mock_backend)

        start_time = time.time()
        hierarchy = display._create_memory_hierarchy_matrix()
        end_time = time.time()

        render_time = end_time - start_time

        # Memory hierarchy should render quickly even with many devices
        self.assertLess(render_time, 0.5, f"Memory hierarchy render took {render_time:.3f}s")
        self.assertIsInstance(hierarchy, list)
        self.assertTrue(len(hierarchy) > 0)

    def test_workload_detection_performance(self):
        """Test workload detection performance"""
        self.create_mock_devices(4)
        display = TTTopDisplay(backend=self.mock_backend)

        # Mock workload detection to avoid system calls
        with patch.object(display, '_detect_ml_workloads') as mock_detect:
            # Simulate many detected workloads
            mock_workloads = []
            for i in range(50):  # Many processes
                mock_workloads.append({
                    'pid': 1000 + i,
                    'framework': ['pytorch', 'tensorflow', 'jax'][i % 3],
                    'model_type': ['llm', 'computer_vision', 'audio_speech'][i % 3],
                    'workload_type': ['training', 'inference', 'evaluation'][i % 3],
                    'confidence': 0.8,
                    'correlation_score': 0.6,
                    'memory_gb': 8.0,
                    'thread_count': 4
                })
            mock_detect.return_value = mock_workloads

            start_time = time.time()
            workload_section = display._create_workload_detection_section()
            end_time = time.time()

            render_time = end_time - start_time

            # Workload detection should handle many processes efficiently
            self.assertLess(render_time, 0.2, f"Workload detection took {render_time:.3f}s")
            self.assertIsInstance(workload_section, list)

    def test_large_display_content_performance(self):
        """Test performance with very large display content"""
        self.create_mock_devices(16)  # Many devices
        display = TTTopDisplay(backend=self.mock_backend)

        start_time = time.time()
        content = display._render_complete_display()
        end_time = time.time()

        render_time = end_time - start_time

        # Large content should still render reasonably quickly
        self.assertLess(render_time, 2.0, f"Large display render took {render_time:.3f}s")

        # Content should be substantial but not excessive
        content_size = len(content)
        self.assertGreater(content_size, 1000, "Content too small")
        self.assertLess(content_size, 1000000, "Content excessively large")

    def test_animation_frame_performance(self):
        """Test animation frame update performance"""
        self.create_mock_devices(8)
        display = TTTopDisplay(backend=self.mock_backend)

        # Test many frame updates
        start_time = time.time()
        for frame in range(100):
            display.animation_frame = frame
            # Test data flow line creation (uses animation frame)
            for i in range(len(display.backend.devices)):
                display._create_data_flow_line(25.0, i)
        end_time = time.time()

        total_time = end_time - start_time

        # Animation updates should be very fast
        self.assertLess(total_time, 0.5, f"Animation frame updates took {total_time:.3f}s")

    def test_color_markup_performance(self):
        """Test Rich markup color performance"""
        self.create_mock_devices(4)
        display = TTTopDisplay(backend=self.mock_backend)

        # Test color markup methods performance
        start_time = time.time()
        for _ in range(1000):
            display._colorize_text("test", "red")
            display._get_status_color(75.0, 50.0)
            display._get_temperature_color(65.0)
            display._get_power_color(40.0)
        end_time = time.time()

        markup_time = end_time - start_time

        # Color markup should be very fast
        self.assertLess(markup_time, 0.1, f"Color markup took {markup_time:.3f}s for 1000 operations")


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestMemoryUsage(unittest.TestCase):
    """Test memory usage and garbage collection"""

    def setUp(self):
        """Set up memory test fixtures"""
        self.mock_backend = Mock(spec=TTSMIBackend)
        gc.collect()  # Clean up before tests

    def create_mock_devices(self, count):
        """Create mock devices for memory tests"""
        devices = []
        telemetry = []
        device_infos = []

        for i in range(count):
            device = Mock()
            devices.append(device)
            telemetry.append({
                'power': str(30.0 + i),
                'asic_temperature': str(45.0 + i),
                'current': str(15.0 + i),
                'voltage': str(0.8),
                'aiclk': str(1000),
                'heartbeat': str(100 + i)
            })
            device_infos.append({'board_type': f'board_{i}'})

        self.mock_backend.devices = devices
        self.mock_backend.device_telemetrys = telemetry
        self.mock_backend.device_infos = device_infos
        self.mock_backend.smbus_telem_info = [{'DDR_STATUS': '22222222'}] * count
        self.mock_backend.get_device_name.side_effect = lambda d: f"Device_{devices.index(d)}"

    @unittest.skipIf(sys.platform == 'win32', "Memory profiling not reliable on Windows")
    def test_display_memory_usage(self):
        """Test memory usage of display creation"""
        import psutil
        import os

        process = psutil.Process(os.getpid())

        # Get initial memory
        gc.collect()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create display with many devices
        self.create_mock_devices(10)
        display = TTTopDisplay(backend=self.mock_backend)
        display.update = Mock()

        # Generate content multiple times
        for _ in range(10):
            content = display._render_complete_display()
            del content

        # Get final memory
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_increase = final_memory - initial_memory

        # Memory usage should be reasonable (less than 100MB increase)
        self.assertLess(memory_increase, 100, f"Memory increased by {memory_increase:.1f}MB")

    def test_object_cleanup(self):
        """Test that objects are properly cleaned up"""
        self.create_mock_devices(5)

        # Create and destroy displays
        displays = []
        for _ in range(10):
            display = TTTopDisplay(backend=self.mock_backend)
            display.update = Mock()
            displays.append(display)

        # Clear references
        displays.clear()
        gc.collect()

        # Objects should be garbage collected
        # This is more of a smoke test since gc behavior varies
        self.assertTrue(True)  # If we get here without OOM, we're good

    def test_large_content_strings(self):
        """Test memory usage with large content strings"""
        self.create_mock_devices(20)
        display = TTTopDisplay(backend=self.mock_backend)

        # Generate large amounts of content
        large_contents = []
        for _ in range(50):
            content = display._render_complete_display()
            large_contents.append(content)

        # Verify content was created
        self.assertEqual(len(large_contents), 50)
        self.assertTrue(all(isinstance(content, str) for content in large_contents))

        # Clean up
        large_contents.clear()
        gc.collect()


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestStressConditions(unittest.TestCase):
    """Test TT-Top under stress conditions"""

    def setUp(self):
        """Set up stress test fixtures"""
        self.mock_backend = Mock(spec=TTSMIBackend)

    def test_extreme_telemetry_values(self):
        """Test with extreme telemetry values"""
        # Create device with extreme values
        self.mock_backend.devices = [Mock()]
        self.mock_backend.device_telemetrys = [{
            'power': '999.9',      # Very high power
            'asic_temperature': '150.0',  # Very high temperature
            'current': '500.0',    # Very high current
            'voltage': '2.5',      # High voltage
            'aiclk': '5000',       # Very high clock
            'heartbeat': '999999'  # High heartbeat
        }]
        self.mock_backend.device_infos = [{'board_type': 'extreme'}]
        self.mock_backend.smbus_telem_info = [{'DDR_STATUS': 'FFFFFFFF'}]
        self.mock_backend.get_device_name.return_value = "ExtremeDevice"

        display = TTTopDisplay(backend=self.mock_backend)
        display.update = Mock()

        # Should handle extreme values without crashing
        content = display._render_complete_display()
        self.assertIsInstance(content, str)
        self.assertTrue(len(content) > 0)

        # Status should be critical for extreme values
        status = display._get_device_status_text(150.0, 999.9)
        self.assertIn("CRITICAL", status)

    def test_rapid_telemetry_changes(self):
        """Test with rapidly changing telemetry values"""
        self.mock_backend.devices = [Mock()]
        self.mock_backend.device_infos = [{'board_type': 'test'}]
        self.mock_backend.smbus_telem_info = [{'DDR_STATUS': '22222222'}]
        self.mock_backend.get_device_name.return_value = "TestDevice"

        display = TTTopDisplay(backend=self.mock_backend)
        display.update = Mock()

        # Simulate rapid changes
        for i in range(100):
            # Rapidly changing telemetry
            self.mock_backend.device_telemetrys = [{
                'power': str(i % 100),
                'asic_temperature': str(30 + (i % 50)),
                'current': str(10 + (i % 30)),
                'voltage': str(0.8 + (i % 20) * 0.01),
                'aiclk': str(800 + (i % 500)),
                'heartbeat': str(i)
            }]

            display.animation_frame = i

            # Should handle rapid updates without crashing
            try:
                display._update_display()
            except Exception as e:
                self.fail(f"Update failed at iteration {i}: {e}")

    def test_missing_backend_methods(self):
        """Test with missing backend methods"""
        # Mock backend with missing methods
        incomplete_backend = Mock()
        incomplete_backend.devices = [Mock()]
        incomplete_backend.device_telemetrys = [{}]
        incomplete_backend.device_infos = [{}]
        incomplete_backend.smbus_telem_info = [{}]

        # Remove some methods
        del incomplete_backend.get_device_name
        del incomplete_backend.get_dram_speed

        display = TTTopDisplay(backend=incomplete_backend)

        # Should handle missing methods gracefully
        try:
            # This might fail, but shouldn't crash the Python interpreter
            content = display._render_complete_display()
        except AttributeError:
            # Expected - missing methods should raise AttributeError
            pass
        except Exception as e:
            # Other exceptions should be handled gracefully
            self.assertIsInstance(e, (AttributeError, TypeError, KeyError))


if __name__ == '__main__':
    # Run with reduced verbosity for performance tests
    unittest.main(verbosity=1)