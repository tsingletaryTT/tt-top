#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Test script for TT-Top hardware safety measures

Tests the safety coordination system under various workload conditions
to ensure PCIe interference prevention works correctly.
"""

import os
import sys
import time
import threading
import subprocess
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tt_top.safety import (
        SafetyConfig, HardwareSafetyCoordinator, WorkloadDetector,
        PCIeErrorDetector, HardwareAccessLock
    )
    from tt_top.mock_hardware import MockPciChip
    from tt_top.tt_smi_backend import TTSMIBackend
    SAFETY_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TT-Top safety modules: {e}")
    print("Safety tests will be skipped. Install dependencies to run tests.")
    SAFETY_IMPORTS_AVAILABLE = False


@unittest.skipUnless(SAFETY_IMPORTS_AVAILABLE, "TT-Top safety modules not available")
class TestSafetyMeasures(unittest.TestCase):
    """Comprehensive test suite for hardware safety measures"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_devices = [MockPciChip(i) for i in range(2)]

        # Create safety config for testing
        self.safety_config = SafetyConfig(
            normal_poll_interval=0.1,
            workload_poll_interval=2.0,
            critical_poll_interval=5.0,
            max_lock_wait_time=0.5,  # Shorter for testing
            workload_check_interval=0.5,
            max_errors_before_disable=2  # Lower threshold for testing
        )

    def test_workload_detection(self):
        """Test workload detection system with simulated processes"""
        detector = WorkloadDetector(self.safety_config)

        # Test basic workload detection (may find real processes)
        workload_state = detector.detect_ml_workloads()

        # Should return a WorkloadState object
        self.assertTrue(hasattr(workload_state, 'active_ml_workloads'))
        self.assertTrue(hasattr(workload_state, 'is_workload_active'))
        self.assertIsInstance(workload_state.active_ml_workloads, list)

        # Test framework detection patterns
        test_cmdlines = [
            "python train.py --model gpt-4",
            "torchrun --nproc_per_node=8 train_llama.py",
            "accelerate launch --multi_gpu train.py",
            "python -m transformers.trainer",
            "tf_cnn_benchmarks --model=resnet50"
        ]

        detected_frameworks = []
        for cmdline in test_cmdlines:
            ml_info = detector._detect_ml_framework(cmdline)
            if ml_info['framework'] != 'unknown':
                detected_frameworks.append(ml_info['framework'])

        # Should detect at least some frameworks
        self.assertGreaterEqual(len(detected_frameworks), 3)
        self.assertIn('pytorch', detected_frameworks)
        self.assertIn('huggingface', detected_frameworks)

    def test_safety_coordinator_polling(self):
        """Test dynamic polling interval adjustment"""
        coordinator = HardwareSafetyCoordinator(self.safety_config)

        # Test normal polling interval
        initial_interval = coordinator.get_safe_poll_interval()
        self.assertEqual(initial_interval, 0.1)

        # Test forced safety mode
        coordinator.force_safety_mode(True)
        safety_interval = coordinator.get_safe_poll_interval()
        self.assertEqual(safety_interval, 2.0)

        # Test custom polling override
        coordinator.set_custom_poll_interval(0.5)
        custom_interval = coordinator.get_safe_poll_interval()
        self.assertEqual(custom_interval, 0.5)

        # Reset to normal
        coordinator.force_safety_mode(False)

    def test_hardware_access_locking(self):
        """Test hardware access coordination"""
        def test_concurrent_access():
            """Test concurrent access from multiple threads"""
            results = []

            def try_access(device_id: int, thread_id: int):
                with HardwareAccessLock(device_id, self.safety_config) as lock:
                    if lock.is_locked():
                        time.sleep(0.05)  # Hold lock briefly
                        results.append(f"Thread-{thread_id}")
                    else:
                        results.append(f"Thread-{thread_id}-FAILED")

            # Start multiple threads trying to access same device
            threads = []
            for i in range(3):
                thread = threading.Thread(target=try_access, args=(0, i))
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

            # Check that locks worked (should have some coordination)
            successful_accesses = [r for r in results if not r.endswith("-FAILED")]

            # At least one thread should succeed, and there should be some coordination
            self.assertGreaterEqual(len(successful_accesses), 1)
            self.assertLessEqual(len(successful_accesses), 3)

        test_concurrent_access()

    def test_pcie_error_detection(self):
        """Test PCIe error detection and monitoring disable"""
        detector = PCIeErrorDetector(self.safety_config)

        # Test initial state
        self.assertEqual(detector.error_count, 0)
        self.assertFalse(detector.should_disable_monitoring())

        # Simulate error accumulation
        for i in range(3):
            detector.error_count += 1

        self.assertTrue(detector.should_disable_monitoring())

        # Test error reset
        detector.reset_error_count()
        self.assertEqual(detector.error_count, 0)
        self.assertFalse(detector.should_disable_monitoring())

    def test_backend_integration(self):
        """Test safety integration with TTSMIBackend"""
        # Create backend with safety configuration
        backend = TTSMIBackend(
            devices=self.mock_devices,
            fully_init=False,  # Skip full init for testing
            safety_config=self.safety_config
        )

        # Test safety coordinator initialization
        self.assertTrue(hasattr(backend, 'safety_coordinator'))
        self.assertIsNotNone(backend.safety_coordinator)

        # Test retry count configuration
        backend.max_retries = 5
        self.assertEqual(backend.max_retries, 5)

        # Test safe telemetry update (mock mode)
        try:
            backend.update_telem()
            # Should complete without errors in mock mode
        except Exception as e:
            self.fail(f"Safe telemetry update failed: {e}")

    def test_monitoring_safety_checks(self):
        """Test monitoring safety validation"""
        coordinator = HardwareSafetyCoordinator(self.safety_config)

        # Test normal state
        is_safe, reason = coordinator.is_monitoring_safe()
        self.assertTrue(is_safe)
        self.assertEqual(reason, "Monitoring is safe")

        # Simulate error accumulation
        coordinator.pcie_error_detector.error_count = 5  # Above threshold
        is_safe, reason = coordinator.is_monitoring_safe()
        self.assertFalse(is_safe)
        self.assertIn("errors detected", reason)

    def test_workload_summary(self):
        """Test workload summary generation"""
        coordinator = HardwareSafetyCoordinator(self.safety_config)
        summary = coordinator.get_workload_summary()

        # Should return dict with expected fields
        self.assertIsInstance(summary, dict)
        self.assertIn('safety_mode_enabled', summary)
        self.assertIn('current_poll_interval', summary)
        self.assertIn('pcie_error_count', summary)
        self.assertIn('active_ml_processes', summary)

    def test_retry_mechanism(self):
        """Test retry logic with exponential backoff"""
        backend = TTSMIBackend(
            devices=self.mock_devices,
            fully_init=False,
            safety_config=self.safety_config
        )

        # Create a mock function that fails initially then succeeds
        call_count = 0
        def mock_read_func(device_idx):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:  # Fail first 2 attempts
                raise Exception("Simulated hardware read failure")
            return {"test": "data"}

        # Test retry mechanism
        result = backend._telemetry_read_with_retry(
            mock_read_func, 0, "test operation", max_retries=3
        )

        # Should succeed on 3rd attempt
        self.assertEqual(result, {"test": "data"})
        self.assertEqual(call_count, 3)

    def test_fallback_data(self):
        """Test fallback data when all retries fail"""
        backend = TTSMIBackend(
            devices=self.mock_devices,
            fully_init=False,
            safety_config=self.safety_config
        )

        def always_fail_func(device_idx):
            raise Exception("Persistent hardware failure")

        # Test SMBUS fallback
        result = backend._telemetry_read_with_retry(
            always_fail_func, 0, "SMBUS telemetry read", max_retries=1
        )

        # Should get fallback data
        self.assertIsInstance(result, dict)

        # Test chip telemetry fallback
        result = backend._telemetry_read_with_retry(
            always_fail_func, 0, "chip telemetry read", max_retries=1
        )

        # Should get fallback data with expected fields
        self.assertIsInstance(result, dict)
        self.assertIn("voltage", result)
        self.assertIn("power", result)


@unittest.skipUnless(SAFETY_IMPORTS_AVAILABLE, "TT-Top safety modules not available")
class TestSafetyConfiguration(unittest.TestCase):
    """Test safety configuration and CLI integration"""

    def test_default_safety_config(self):
        """Test default safety configuration"""
        config = SafetyConfig()

        self.assertEqual(config.normal_poll_interval, 0.1)
        self.assertEqual(config.workload_poll_interval, 2.0)
        self.assertEqual(config.critical_poll_interval, 5.0)
        self.assertEqual(config.max_errors_before_disable, 3)
        self.assertEqual(config.max_lock_wait_time, 1.0)

    def test_custom_safety_config(self):
        """Test custom safety configuration"""
        config = SafetyConfig(
            normal_poll_interval=0.05,
            workload_poll_interval=1.0,
            max_errors_before_disable=5
        )

        self.assertEqual(config.normal_poll_interval, 0.05)
        self.assertEqual(config.workload_poll_interval, 1.0)
        self.assertEqual(config.max_errors_before_disable, 5)

    def test_safety_coordinator_with_config(self):
        """Test safety coordinator with custom config"""
        config = SafetyConfig(
            normal_poll_interval=0.2,
            workload_poll_interval=3.0
        )

        coordinator = HardwareSafetyCoordinator(config)

        # Should use custom config values
        self.assertEqual(coordinator.config.normal_poll_interval, 0.2)
        self.assertEqual(coordinator.config.workload_poll_interval, 3.0)

        # Initial interval should match normal interval
        interval = coordinator.get_safe_poll_interval()
        self.assertEqual(interval, 0.2)


if __name__ == '__main__':
    print("🔬 TT-Top Hardware Safety Test Suite")
    print("=" * 50)
    unittest.main(verbosity=2)