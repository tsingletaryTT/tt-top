#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-Top Hardware Safety Coordination Module

Prevents hardware interference during active workloads by implementing:
- Workload detection and monitoring frequency adjustment
- Hardware access synchronization and locking
- PCIe error detection and automatic mitigation
- Multi-process monitoring coordination

This module addresses the critical issue where monitoring tools can cause
PCIe DPC errors during active ML workloads due to concurrent register access.
"""

import os
import time
import fcntl
import psutil
import logging
import threading
import subprocess
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class SafetyConfig:
    """Configuration for hardware safety measures"""
    # Polling frequencies (seconds)
    normal_poll_interval: float = 0.1      # 100ms - normal operation
    workload_poll_interval: float = 2.0    # 2s - during active workloads
    critical_poll_interval: float = 5.0    # 5s - when errors detected

    # Safety thresholds
    max_lock_wait_time: float = 1.0        # Max time to wait for hardware lock
    error_detection_window: int = 60       # Seconds to check for PCIe errors
    max_errors_before_disable: int = 3     # PCIe errors before disabling monitoring

    # Workload detection settings
    workload_check_interval: float = 1.0   # How often to check for workloads
    min_workload_memory_gb: float = 1.0    # Minimum memory for ML workload detection

    # Lock file settings
    lock_base_path: str = "/tmp/tt_device_lock"
    coordination_file: str = "/tmp/tt_monitors_active"

class WorkloadState:
    """Represents the current system workload state"""

    def __init__(self):
        self.active_ml_workloads: List[Dict] = []
        self.total_ml_processes: int = 0
        self.total_ml_memory_gb: float = 0.0
        self.high_memory_processes: List[Dict] = []
        self.last_check_time: float = 0.0
        self.is_workload_active: bool = False

class HardwareAccessLock:
    """File-based hardware access coordination"""

    def __init__(self, device_id: int, config: SafetyConfig):
        self.device_id = device_id
        self.config = config
        self.lock_file_path = f"{config.lock_base_path}_{device_id}"
        self.lock_file = None
        self.acquired = False

    def __enter__(self):
        """Acquire hardware access lock with timeout"""
        try:
            self.lock_file = open(self.lock_file_path, 'w')

            # Try to acquire lock with timeout
            start_time = time.time()
            while time.time() - start_time < self.config.max_lock_wait_time:
                try:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    self.acquired = True
                    logger.debug(f"Acquired hardware lock for device {self.device_id}")
                    return self
                except BlockingIOError:
                    # Lock is held by another process
                    time.sleep(0.01)  # Wait 10ms before retry

            # Timeout exceeded
            logger.warning(f"Failed to acquire hardware lock for device {self.device_id} within {self.config.max_lock_wait_time}s")
            return self

        except Exception as e:
            logger.error(f"Failed to acquire hardware lock for device {self.device_id}: {e}")
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release hardware access lock"""
        if self.lock_file and self.acquired:
            try:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.acquired = False
                logger.debug(f"Released hardware lock for device {self.device_id}")
            except Exception as e:
                logger.error(f"Failed to release hardware lock for device {self.device_id}: {e}")

        if self.lock_file:
            try:
                self.lock_file.close()
            except Exception as e:
                logger.error(f"Failed to close lock file for device {self.device_id}: {e}")

    def is_locked(self) -> bool:
        """Check if we successfully acquired the lock"""
        return self.acquired

class PCIeErrorDetector:
    """Monitors for PCIe DPC errors that indicate hardware interference"""

    def __init__(self, config: SafetyConfig):
        self.config = config
        self.error_count = 0
        self.last_check_time = time.time()
        self.monitoring_disabled = False

    def check_for_pcie_errors(self) -> Tuple[bool, List[str]]:
        """
        Check for PCIe DPC errors in system logs

        Returns:
            (errors_found, error_messages)
        """
        errors_found = []

        try:
            # Check dmesg for recent PCIe errors
            result = subprocess.run([
                'dmesg', '-T', '--since', f'{int(self.config.error_detection_window)} seconds ago'
            ], capture_output=True, text=True, timeout=5)

            if result.returncode == 0:
                log_lines = result.stdout.split('\n')

                # Look for PCIe DPC and AER errors
                pcie_error_patterns = [
                    'DPC: containment event',
                    'PCIe Bus Error',
                    'unmasked uncorrectable error',
                    'SDES',  # Symbol/Dword Error Status
                    'AER: device recovery failed',
                    'tenstorrent.*AER:'
                ]

                for line in log_lines:
                    line_lower = line.lower()
                    for pattern in pcie_error_patterns:
                        if pattern.lower() in line_lower:
                            errors_found.append(line.strip())
                            self.error_count += 1
                            logger.warning(f"PCIe error detected: {line.strip()}")

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.debug(f"Could not check PCIe errors via dmesg: {e}")

        # Check if we should disable monitoring
        if self.error_count >= self.config.max_errors_before_disable:
            self.monitoring_disabled = True
            logger.error(f"Disabling monitoring after {self.error_count} PCIe errors detected")

        self.last_check_time = time.time()
        return len(errors_found) > 0, errors_found

    def should_disable_monitoring(self) -> bool:
        """Check if monitoring should be disabled due to errors"""
        return self.monitoring_disabled

    def reset_error_count(self):
        """Reset error count (for testing or manual recovery)"""
        self.error_count = 0
        self.monitoring_disabled = False
        logger.info("PCIe error count reset - monitoring re-enabled")

class WorkloadDetector:
    """Detects active ML workloads that could conflict with monitoring"""

    def __init__(self, config: SafetyConfig):
        self.config = config
        self.last_check = WorkloadState()

    def detect_ml_workloads(self) -> WorkloadState:
        """
        Detect active ML workloads using process analysis

        Returns WorkloadState with current system state
        """
        workload_state = WorkloadState()
        workload_state.last_check_time = time.time()

        try:
            # Use psutil for robust process detection
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info', 'num_threads']):
                try:
                    proc_info = proc.info
                    if not proc_info['cmdline']:
                        continue

                    cmdline = ' '.join(proc_info['cmdline']).lower()
                    memory_gb = 0

                    # Calculate memory usage
                    if proc_info['memory_info']:
                        memory_gb = proc_info['memory_info'].rss / (1024 * 1024 * 1024)

                    # Detect ML frameworks
                    ml_frameworks = self._detect_ml_framework(cmdline)

                    if ml_frameworks['framework'] != 'unknown':
                        workload_info = {
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'cmdline_snippet': cmdline[:100],
                            'framework': ml_frameworks['framework'],
                            'model_type': ml_frameworks['model_type'],
                            'workload_type': ml_frameworks['workload_type'],
                            'memory_gb': memory_gb,
                            'threads': proc_info.get('num_threads', 1)
                        }

                        workload_state.active_ml_workloads.append(workload_info)
                        workload_state.total_ml_memory_gb += memory_gb
                        workload_state.total_ml_processes += 1

                    # Track high-memory processes (potential ML jobs)
                    if memory_gb > self.config.min_workload_memory_gb:
                        high_mem_info = {
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'memory_gb': memory_gb,
                            'threads': proc_info.get('num_threads', 1)
                        }
                        workload_state.high_memory_processes.append(high_mem_info)

                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

        except Exception as e:
            logger.error(f"Error detecting workloads: {e}")

        # Determine if workloads are active
        workload_state.is_workload_active = (
            workload_state.total_ml_processes > 0 or
            workload_state.total_ml_memory_gb > self.config.min_workload_memory_gb or
            len(workload_state.high_memory_processes) > 0
        )

        self.last_check = workload_state
        return workload_state

    def _detect_ml_framework(self, cmdline: str) -> Dict[str, str]:
        """Detect ML framework from command line"""

        # Framework patterns
        framework_patterns = {
            'pytorch': ['torch', 'torchrun', 'pytorch', 'transformers', 'accelerate'],
            'tensorflow': ['tensorflow', 'tf.', 'keras', 'tf_'],
            'jax': ['jax', 'flax', 'optax', 'haiku'],
            'huggingface': ['transformers', 'datasets', 'accelerate', 'peft']
        }

        # Model type patterns
        model_patterns = {
            'llm': ['gpt', 'bert', 'roberta', 'llama', 'mistral', 'falcon', 't5'],
            'computer_vision': ['resnet', 'vgg', 'yolo', 'rcnn', 'efficientnet'],
            'audio_speech': ['whisper', 'wav2vec', 'hubert', 'speechbrain']
        }

        # Workload type patterns
        workload_patterns = {
            'training': ['train', 'training', 'fit', 'finetune'],
            'inference': ['inference', 'infer', 'predict', 'generate', 'serve'],
            'evaluation': ['eval', 'evaluate', 'test', 'benchmark']
        }

        # Detect framework
        detected_framework = 'unknown'
        for framework, patterns in framework_patterns.items():
            if any(pattern in cmdline for pattern in patterns):
                detected_framework = framework
                break

        # Detect model type
        detected_model_type = 'unknown'
        for model_type, patterns in model_patterns.items():
            if any(pattern in cmdline for pattern in patterns):
                detected_model_type = model_type
                break

        # Detect workload type
        detected_workload_type = 'unknown'
        for workload_type, patterns in workload_patterns.items():
            if any(pattern in cmdline for pattern in patterns):
                detected_workload_type = workload_type
                break

        return {
            'framework': detected_framework,
            'model_type': detected_model_type,
            'workload_type': detected_workload_type
        }

class HardwareSafetyCoordinator:
    """Main coordinator for safe hardware monitoring"""

    def __init__(self, config: Optional[SafetyConfig] = None):
        self.config = config or SafetyConfig()
        self.workload_detector = WorkloadDetector(self.config)
        self.pcie_error_detector = PCIeErrorDetector(self.config)
        self.current_poll_interval = self.config.normal_poll_interval
        self.safety_mode_enabled = False
        self.monitoring_disabled = False

        # Thread-safe state tracking
        self._state_lock = threading.Lock()
        self._last_workload_check = 0

        logger.info(f"Hardware Safety Coordinator initialized with config: {self.config}")

    def get_safe_poll_interval(self) -> float:
        """Get the current safe polling interval based on system state"""

        # Check if monitoring is disabled due to errors
        if self.pcie_error_detector.should_disable_monitoring():
            self.monitoring_disabled = True
            return float('inf')  # Effectively disable polling

        # Check for workloads periodically
        current_time = time.time()
        if current_time - self._last_workload_check > self.config.workload_check_interval:
            with self._state_lock:
                workload_state = self.workload_detector.detect_ml_workloads()
                self._last_workload_check = current_time

                # Adjust polling based on workload state
                if workload_state.is_workload_active:
                    if not self.safety_mode_enabled:
                        logger.info(f"Active workloads detected ({workload_state.total_ml_processes} ML processes, "
                                  f"{workload_state.total_ml_memory_gb:.1f}GB memory) - reducing poll frequency")
                        self.safety_mode_enabled = True

                    self.current_poll_interval = self.config.workload_poll_interval
                else:
                    if self.safety_mode_enabled:
                        logger.info("No active workloads detected - resuming normal poll frequency")
                        self.safety_mode_enabled = False

                    self.current_poll_interval = self.config.normal_poll_interval

        # Check for PCIe errors and adjust accordingly
        errors_found, error_messages = self.pcie_error_detector.check_for_pcie_errors()
        if errors_found:
            logger.warning(f"PCIe errors detected - switching to critical poll interval")
            self.current_poll_interval = self.config.critical_poll_interval

        return self.current_poll_interval

    def get_hardware_lock(self, device_id: int) -> HardwareAccessLock:
        """Get a hardware access lock for the specified device"""
        return HardwareAccessLock(device_id, self.config)

    def is_monitoring_safe(self) -> Tuple[bool, str]:
        """
        Check if hardware monitoring is safe to perform

        Returns:
            (is_safe, reason)
        """
        if self.monitoring_disabled:
            return False, "Monitoring disabled due to PCIe errors"

        if self.pcie_error_detector.should_disable_monitoring():
            return False, f"Too many PCIe errors detected ({self.pcie_error_detector.error_count})"

        return True, "Monitoring is safe"

    def get_workload_summary(self) -> Dict:
        """Get summary of current workload state"""
        with self._state_lock:
            workload_state = self.workload_detector.last_check
            return {
                'active_ml_processes': workload_state.total_ml_processes,
                'total_ml_memory_gb': workload_state.total_ml_memory_gb,
                'high_memory_processes': len(workload_state.high_memory_processes),
                'is_workload_active': workload_state.is_workload_active,
                'safety_mode_enabled': self.safety_mode_enabled,
                'current_poll_interval': self.current_poll_interval,
                'pcie_error_count': self.pcie_error_detector.error_count
            }

    def force_safety_mode(self, enabled: bool):
        """Force safety mode on/off (for CLI control)"""
        with self._state_lock:
            self.safety_mode_enabled = enabled
            if enabled:
                self.current_poll_interval = self.config.workload_poll_interval
                logger.info("Safety mode forced ON - using reduced polling frequency")
            else:
                self.current_poll_interval = self.config.normal_poll_interval
                logger.info("Safety mode forced OFF - using normal polling frequency")

    def set_custom_poll_interval(self, interval: float):
        """Set a custom polling interval (for CLI control)"""
        with self._state_lock:
            self.current_poll_interval = interval
            self.config.normal_poll_interval = interval
            logger.info(f"Custom polling interval set to {interval}s")

# Global safety coordinator instance
_global_coordinator: Optional[HardwareSafetyCoordinator] = None

def get_safety_coordinator(config: Optional[SafetyConfig] = None) -> HardwareSafetyCoordinator:
    """Get or create the global hardware safety coordinator"""
    global _global_coordinator
    if _global_coordinator is None:
        _global_coordinator = HardwareSafetyCoordinator(config)
    return _global_coordinator

def safe_hardware_access(device_id: int):
    """Context manager for safe hardware access with automatic locking"""
    coordinator = get_safety_coordinator()
    return coordinator.get_hardware_lock(device_id)

def get_safe_poll_interval() -> float:
    """Get the current safe polling interval"""
    coordinator = get_safety_coordinator()
    return coordinator.get_safe_poll_interval()

def is_monitoring_safe() -> Tuple[bool, str]:
    """Check if monitoring is currently safe"""
    coordinator = get_safety_coordinator()
    return coordinator.is_monitoring_safe()