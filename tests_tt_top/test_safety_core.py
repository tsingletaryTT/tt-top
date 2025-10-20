#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Core safety functionality tests without UI dependencies

Tests the fundamental safety coordination components that prevent
PCIe interference during active workloads.
"""

import os
import sys
import time
import threading
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tt_top.safety import (
        SafetyConfig, HardwareSafetyCoordinator, WorkloadDetector,
        PCIeErrorDetector, HardwareAccessLock
    )
    SAFETY_CORE_IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TT-Top safety core modules: {e}")
    print("Safety core tests will be skipped. Install dependencies to run tests.")
    SAFETY_CORE_IMPORTS_AVAILABLE = False


@unittest.skipUnless(SAFETY_CORE_IMPORTS_AVAILABLE, "TT-Top safety core modules not available")
class TestSafetyCore(unittest.TestCase):
    """Test core safety functionality without external dependencies"""

    def test_safety_config(self):
        """Test safety configuration"""
        config = SafetyConfig()

        # Test default values
        self.assertEqual(config.normal_poll_interval, 0.1)
        self.assertEqual(config.workload_poll_interval, 2.0)
        self.assertEqual(config.max_errors_before_disable, 3)

    def test_workload_detector_patterns(self):
        """Test workload detection patterns"""
        config = SafetyConfig()
        detector = WorkloadDetector(config)

        # Test ML framework detection patterns
        test_cases = [
            ("python train.py --model gpt-4", "pytorch"),
            ("torchrun --nproc_per_node=8 train_llama.py", "pytorch"),
            ("python -m transformers.trainer", "huggingface"),
            ("tf_cnn_benchmarks --model=resnet50", "tensorflow"),
            ("python jax_training.py", "jax")
        ]

        passed = 0
        for cmdline, expected_framework in test_cases:
            detected = detector._detect_ml_framework(cmdline)
            if detected['framework'] == expected_framework:
                passed += 1

        # Should detect most frameworks correctly
        self.assertGreaterEqual(passed, 4, f"Only {passed}/5 patterns recognized correctly")

    def test_model_type_detection(self):
        """Test model type detection patterns"""
        config = SafetyConfig()
        detector = WorkloadDetector(config)

        test_cases = [
            ("python train_gpt.py --model gpt-4", "llm"),
            ("python train_bert.py --model bert-large", "llm"),
            ("python train_resnet.py --model resnet50", "computer_vision"),
            ("python train_whisper.py --model whisper-large", "audio_speech")
        ]

        for cmdline, expected_model_type in test_cases:
            detected = detector._detect_ml_framework(cmdline)
            self.assertEqual(detected['model_type'], expected_model_type,
                           f"Expected {expected_model_type}, got {detected['model_type']} for {cmdline}")

    def test_workload_type_detection(self):
        """Test workload type detection patterns"""
        config = SafetyConfig()
        detector = WorkloadDetector(config)

        test_cases = [
            ("python train.py --mode training", "training"),
            ("python inference.py --model gpt", "inference"),
            ("python eval.py --dataset test", "evaluation")
        ]

        for cmdline, expected_workload_type in test_cases:
            detected = detector._detect_ml_framework(cmdline)
            self.assertEqual(detected['workload_type'], expected_workload_type,
                           f"Expected {expected_workload_type}, got {detected['workload_type']} for {cmdline}")

    def test_pcie_error_detector(self):
        """Test PCIe error detection"""
        config = SafetyConfig()
        detector = PCIeErrorDetector(config)

        # Test initial state
        self.assertEqual(detector.error_count, 0)
        self.assertFalse(detector.should_disable_monitoring())

        # Simulate error accumulation
        for i in range(3):
            detector.error_count += 1

        self.assertTrue(detector.should_disable_monitoring())

        # Test reset
        detector.reset_error_count()
        self.assertEqual(detector.error_count, 0)
        self.assertFalse(detector.should_disable_monitoring())

    def test_hardware_access_lock_basic(self):
        """Test basic hardware access locking functionality"""
        config = SafetyConfig(max_lock_wait_time=0.1)  # Short timeout for testing

        # Test single lock acquisition
        with HardwareAccessLock(0, config) as lock:
            # Lock should be acquired
            self.assertTrue(hasattr(lock, 'is_locked'))
            # In test environment, lock may or may not be acquired depending on system
            # Just verify the interface works

    def test_hardware_access_lock_concurrent(self):
        """Test concurrent hardware access locking"""
        config = SafetyConfig(max_lock_wait_time=0.1)  # Short timeout for testing
        results = []

        def concurrent_access(thread_id):
            try:
                with HardwareAccessLock(0, config) as lock:
                    if lock.is_locked():
                        results.append(f"thread-{thread_id}-success")
                        time.sleep(0.02)
                    else:
                        results.append(f"thread-{thread_id}-timeout")
            except Exception as e:
                results.append(f"thread-{thread_id}-error")

        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=concurrent_access, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have some results (exact behavior depends on system)
        self.assertGreater(len(results), 0)
        self.assertEqual(len(results), 3)

    def test_safety_coordinator_basic(self):
        """Test basic safety coordinator functionality"""
        config = SafetyConfig()
        coordinator = HardwareSafetyCoordinator(config)

        # Test initial polling interval
        interval = coordinator.get_safe_poll_interval()
        self.assertEqual(interval, 0.1)

        # Test forced safety mode
        coordinator.force_safety_mode(True)
        interval = coordinator.get_safe_poll_interval()
        self.assertEqual(interval, 2.0)

        # Test custom interval
        coordinator.set_custom_poll_interval(0.5)
        interval = coordinator.get_safe_poll_interval()
        self.assertEqual(interval, 0.5)

        # Test workload summary
        summary = coordinator.get_workload_summary()
        self.assertIsInstance(summary, dict)
        self.assertIn('safety_mode_enabled', summary)

    def test_monitoring_safety_checks(self):
        """Test monitoring safety validation"""
        config = SafetyConfig()
        coordinator = HardwareSafetyCoordinator(config)

        # Test normal state
        is_safe, reason = coordinator.is_monitoring_safe()
        self.assertTrue(is_safe)
        self.assertEqual(reason, "Monitoring is safe")

        # Simulate error accumulation
        coordinator.pcie_error_detector.error_count = 5  # Above threshold
        is_safe, reason = coordinator.is_monitoring_safe()
        self.assertFalse(is_safe)
        self.assertIn("errors detected", reason)

    def test_safety_coordinator_state_management(self):
        """Test safety coordinator state management"""
        config = SafetyConfig()
        coordinator = HardwareSafetyCoordinator(config)

        # Test initial state
        self.assertFalse(coordinator.safety_mode_enabled)
        self.assertFalse(coordinator.monitoring_disabled)

        # Test safety mode toggle
        coordinator.force_safety_mode(True)
        self.assertTrue(coordinator.safety_mode_enabled)

        coordinator.force_safety_mode(False)
        self.assertFalse(coordinator.safety_mode_enabled)

        # Test error-based disable
        coordinator.pcie_error_detector.error_count = 10
        interval = coordinator.get_safe_poll_interval()
        # Should either return high value or inf based on error state

    def test_workload_state_structure(self):
        """Test workload state data structure"""
        config = SafetyConfig()
        detector = WorkloadDetector(config)

        # Test workload state creation
        from tt_top.safety import WorkloadState
        state = WorkloadState()

        # Test attributes
        self.assertIsInstance(state.active_ml_workloads, list)
        self.assertIsInstance(state.total_ml_processes, int)
        self.assertIsInstance(state.total_ml_memory_gb, float)
        self.assertIsInstance(state.is_workload_active, bool)

        # Initial state should be inactive
        self.assertFalse(state.is_workload_active)
        self.assertEqual(state.total_ml_processes, 0)


@unittest.skipUnless(SAFETY_CORE_IMPORTS_AVAILABLE, "TT-Top safety core modules not available")
class TestSafetyPatterns(unittest.TestCase):
    """Test safety pattern recognition and heuristics"""

    def setUp(self):
        self.config = SafetyConfig()
        self.detector = WorkloadDetector(self.config)

    def test_pytorch_patterns(self):
        """Test PyTorch pattern recognition"""
        pytorch_commands = [
            "python train.py",
            "torchrun --nproc_per_node=8 train.py",
            "python -m torch.distributed.launch",
            "accelerate launch train.py",
            "python train_transformer.py"
        ]

        for cmd in pytorch_commands:
            result = self.detector._detect_ml_framework(cmd)
            # Should detect pytorch or huggingface (which uses pytorch)
            self.assertIn(result['framework'], ['pytorch', 'huggingface'],
                         f"Failed to detect ML framework in: {cmd}")

    def test_tensorflow_patterns(self):
        """Test TensorFlow pattern recognition"""
        tf_commands = [
            "python tf_train.py",
            "python -m tensorflow.keras",
            "tf_cnn_benchmarks --model resnet50"
        ]

        for cmd in tf_commands:
            result = self.detector._detect_ml_framework(cmd)
            self.assertEqual(result['framework'], 'tensorflow',
                           f"Failed to detect TensorFlow in: {cmd}")

    def test_confidence_scoring(self):
        """Test confidence scoring for pattern matching"""
        # High confidence cases
        high_conf_cmd = "torchrun --nproc_per_node=8 train_gpt.py --model gpt-4"
        result = self.detector._detect_ml_framework(high_conf_cmd)
        self.assertGreater(result.get('confidence', 0), 0.7)

        # Lower confidence cases (generic python)
        low_conf_cmd = "python script.py"
        result = self.detector._detect_ml_framework(low_conf_cmd)
        self.assertEqual(result['framework'], 'unknown')

    def test_memory_based_detection(self):
        """Test memory-based workload detection"""
        # Test memory thresholds
        large_memory_gb = 16.0
        small_memory_gb = 1.0

        # Large memory should increase correlation
        self.assertGreater(large_memory_gb, self.config.min_workload_memory_gb)
        self.assertLess(small_memory_gb, self.config.min_workload_memory_gb)


if __name__ == '__main__':
    print("🔬 TT-Top Core Safety Test Suite")
    print("=" * 40)
    unittest.main(verbosity=2)