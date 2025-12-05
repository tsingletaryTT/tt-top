# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
JSON Backend Adapter for TT-Top

Provides a backend interface that consumes JSON telemetry data from tt-smi
instead of accessing hardware directly. This follows the UNIX philosophy of
composable tools with clean data interfaces.

Architecture:
    tt-smi --json --continuous (subprocess)
        ↓
    JSON stream to stdout
        ↓
    JSONBackendAdapter (parse & cache)
        ↓
    Widgets (same interface as TTSMIBackend)
"""

import json
import subprocess
import time
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    # Try relative imports first (when used as package)
    from .device_proxy import DeviceProxy
    from .log import TTSMILog, TTSMIDeviceLog
except ImportError:
    # Fallback to direct imports (for standalone testing)
    from device_proxy import DeviceProxy
    from log import TTSMILog, TTSMIDeviceLog

# Set up logging
logger = logging.getLogger(__name__)


class JSONSafetyCoordinator:
    """
    Simplified safety coordinator for JSON mode

    Manages adaptive polling intervals based on subprocess health.
    Unlike the hardware safety coordinator, this focuses on subprocess
    stability rather than PCIe error detection.
    """

    def __init__(self, base_interval: float = 0.1, max_interval: float = 2.0):
        """
        Initialize safety coordinator

        Args:
            base_interval: Normal polling interval in seconds (default: 100ms)
            max_interval: Maximum backoff interval on errors (default: 2s)
        """
        self.base_interval = base_interval
        self.max_interval = max_interval
        self.current_interval = base_interval

        # Error tracking for adaptive backoff
        self.consecutive_errors = 0
        self.last_success_time = time.time()

    def get_safe_poll_interval(self) -> float:
        """
        Get recommended polling interval

        Returns gradually increasing intervals if errors occur,
        returns to base interval after successful reads.

        Returns:
            Polling interval in seconds
        """
        return self.current_interval

    def report_json_success(self) -> None:
        """
        Report successful JSON read

        Resets error counter and returns to base polling interval.
        """
        self.consecutive_errors = 0
        self.current_interval = self.base_interval
        self.last_success_time = time.time()

    def report_json_error(self) -> None:
        """
        Report JSON read error

        Increases polling interval with exponential backoff to avoid
        hammering a failed subprocess.
        """
        self.consecutive_errors += 1

        # Exponential backoff: 0.1s -> 0.2s -> 0.4s -> 0.8s -> 1.6s -> 2.0s (max)
        backoff_multiplier = min(2 ** self.consecutive_errors, self.max_interval / self.base_interval)
        self.current_interval = min(self.base_interval * backoff_multiplier, self.max_interval)

        logger.warning(
            f"JSON error #{self.consecutive_errors}, backing off to {self.current_interval:.2f}s interval"
        )


class JSONBackendAdapter:
    """
    Backend adapter that consumes tt-smi JSON output

    Provides the same interface as TTSMIBackend but gets data from
    tt-smi subprocess instead of direct hardware access.

    Features:
    - Subprocess lifecycle management (spawn, monitor, restart)
    - JSON parsing with error handling
    - Data caching compatible with widget expectations
    - Architecture detection via DeviceProxy
    - Adaptive polling with safety coordinator
    """

    def __init__(
        self,
        tt_smi_command: str = "tt-smi --json --continuous",
        mock_mode: bool = False,
        mock_json_file: Optional[str] = None,
    ):
        """
        Initialize JSON backend adapter

        Args:
            tt_smi_command: Command to spawn tt-smi (default: "tt-smi --json --continuous")
            mock_mode: If True, use mock data instead of subprocess
            mock_json_file: Path to JSON file for mock mode
        """
        self.tt_smi_command = tt_smi_command
        self.mock_mode = mock_mode
        self.mock_json_file = mock_json_file

        # Subprocess management
        self.process: Optional[subprocess.Popen] = None
        self.subprocess_running = False

        # Safety coordinator for adaptive polling
        self.safety_coordinator = JSONSafetyCoordinator()

        # Cached data (compatible with TTSMIBackend interface)
        self._devices: List[DeviceProxy] = []
        self._device_telemetrys: List[Dict[str, str]] = []
        self._smbus_telem_info: List[Dict[str, str]] = []
        self._device_infos: List[Dict[str, str]] = []

        # Last successful JSON log
        self._last_log: Optional[TTSMILog] = None
        self._last_update_time = 0.0

        # Initialize (spawn subprocess or load mock data)
        self._initialize()

    def _initialize(self) -> None:
        """
        Initialize backend adapter

        Spawns tt-smi subprocess in continuous JSON mode, or loads mock data
        if in mock mode. Performs initial data read to populate device list.
        """
        if self.mock_mode:
            logger.info("Initializing in mock mode")
            if self.mock_json_file:
                self._load_mock_data()
            else:
                self._generate_mock_data()
        else:
            logger.info(f"Spawning tt-smi subprocess: {self.tt_smi_command}")
            self._spawn_subprocess()
            # Perform initial read to populate device list
            self.update_telem()

    def _spawn_subprocess(self) -> None:
        """
        Spawn tt-smi subprocess for continuous JSON output

        Configures subprocess with:
        - stdout capture for JSON streaming
        - stderr capture for error logging
        - Line-buffered output for real-time reads
        """
        try:
            # Split command string into args
            cmd_args = self.tt_smi_command.split()

            # Spawn subprocess with stdout/stderr capture
            self.process = subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line-buffered
            )

            self.subprocess_running = True
            logger.info(f"tt-smi subprocess spawned with PID {self.process.pid}")

        except FileNotFoundError as e:
            logger.error(f"tt-smi command not found: {self.tt_smi_command}")
            logger.error("Please ensure tt-smi is installed and in PATH")
            raise RuntimeError("tt-smi not found") from e

        except Exception as e:
            logger.error(f"Failed to spawn tt-smi subprocess: {e}")
            raise

    def _restart_subprocess(self) -> None:
        """
        Restart tt-smi subprocess after crash or error

        Performs cleanup of old process, waits briefly, then spawns new process.
        """
        logger.warning("Restarting tt-smi subprocess")

        # Cleanup old process
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logger.error(f"Error cleaning up old subprocess: {e}")

        # Wait before restart
        time.sleep(0.5)

        # Spawn new process
        try:
            self._spawn_subprocess()
            logger.info("Subprocess restarted successfully")
        except Exception as e:
            logger.error(f"Failed to restart subprocess: {e}")
            self.subprocess_running = False

    def update_telem(self) -> None:
        """
        Update telemetry data from tt-smi JSON output

        Reads next line of JSON from subprocess stdout, parses it,
        and updates cached data structures. Handles errors gracefully
        with automatic subprocess restart.
        """
        if self.mock_mode:
            # In mock mode, just refresh the mock data
            self._refresh_mock_data()
            return

        # Check subprocess health
        if not self.subprocess_running or not self.process:
            logger.error("Subprocess not running, attempting restart")
            self.safety_coordinator.report_json_error()
            self._restart_subprocess()
            return

        try:
            # Read next line of JSON from stdout
            json_line = self.process.stdout.readline()

            if not json_line:
                # Empty read - subprocess may have died
                logger.warning("Empty read from subprocess, checking health")
                if self.process.poll() is not None:
                    # Process has terminated
                    logger.error(f"Subprocess terminated with code {self.process.returncode}")
                    self.safety_coordinator.report_json_error()
                    self._restart_subprocess()
                return

            # Parse JSON
            json_data = json.loads(json_line)

            # Parse into Pydantic model
            log = TTSMILog(**json_data)

            # Update cached data
            self._update_from_log(log)

            # Report success to safety coordinator
            self.safety_coordinator.report_json_success()
            self._last_update_time = time.time()

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            logger.debug(f"Malformed JSON line: {json_line[:200]}")
            self.safety_coordinator.report_json_error()

        except Exception as e:
            logger.error(f"Error updating telemetry: {e}")
            self.safety_coordinator.report_json_error()

    def _update_from_log(self, log: TTSMILog) -> None:
        """
        Update cached data structures from parsed TTSMILog

        Args:
            log: Parsed TTSMILog object from JSON
        """
        self._last_log = log

        # Update device list (create DeviceProxy objects)
        if not self._devices or len(self._devices) != len(log.device_info):
            self._devices = []
            for idx, device_log in enumerate(log.device_info):
                board_type = device_log.board_info.board_type or 'Unknown'
                bus_id = device_log.board_info.bus_id or f'unknown:{idx}'
                proxy = DeviceProxy(board_type=board_type, bus_id=bus_id, device_idx=idx)
                self._devices.append(proxy)
                logger.debug(f"Created {proxy}")

        # Update telemetry dictionaries (convert Pydantic models to dicts)
        self._device_telemetrys = []
        self._smbus_telem_info = []
        self._device_infos = []

        for device_log in log.device_info:
            # Telemetry dict (matches backend.device_telemetrys[i] format)
            telem_dict = {
                'voltage': device_log.telemetry.voltage or '0.0',
                'current': device_log.telemetry.current or '0.0',
                'power': device_log.telemetry.power or '0.0',
                'asic_temperature': device_log.telemetry.asic_temperature or '0.0',
                'aiclk': device_log.telemetry.aiclk or '0',
                # Add heartbeat from SMBUS if available
                'heartbeat': device_log.smbus_telem.ARC0_HEALTH or '0',
            }
            self._device_telemetrys.append(telem_dict)

            # SMBUS telemetry dict (matches backend.smbus_telem_info[i] format)
            smbus_dict = {
                'DDR_STATUS': device_log.smbus_telem.DDR_STATUS or '0',
                'DDR_SPEED': device_log.smbus_telem.DDR_SPEED or '0',
                'ARC0_HEALTH': device_log.smbus_telem.ARC0_HEALTH or '0',
                'ARC3_HEALTH': device_log.smbus_telem.ARC3_HEALTH or '0',
                'AICLK': device_log.smbus_telem.AICLK or '0',
                'ASIC_TEMPERATURE': device_log.smbus_telem.ASIC_TEMPERATURE or '0',
                'BOARD_ID': device_log.smbus_telem.BOARD_ID or '0',
            }
            self._smbus_telem_info.append(smbus_dict)

            # Device info dict (matches backend.device_infos[i] format)
            info_dict = {
                'board_type': device_log.board_info.board_type or 'Unknown',
                'bus_id': device_log.board_info.bus_id or 'unknown',
                'dram_status': device_log.board_info.dram_status or 'Unknown',
                'dram_speed': device_log.board_info.dram_speed or '0',
                'coords': device_log.board_info.coords or '(0,0)',
            }
            self._device_infos.append(info_dict)

    def _load_mock_data(self) -> None:
        """Load mock data from JSON file"""
        try:
            with open(self.mock_json_file, 'r') as f:
                json_data = json.load(f)
                log = TTSMILog(**json_data)
                self._update_from_log(log)
                logger.info(f"Loaded mock data from {self.mock_json_file}")
        except Exception as e:
            logger.error(f"Failed to load mock data: {e}")
            self._generate_mock_data()

    def _generate_mock_data(self) -> None:
        """Generate simple mock data for testing without tt-smi"""
        # Create a simple mock device
        proxy = DeviceProxy(board_type='n150', bus_id='0000:01:00.0', device_idx=0)
        self._devices = [proxy]

        self._device_telemetrys = [{
            'voltage': '0.85',
            'current': '25.5',
            'power': '45.2',
            'asic_temperature': '52.3',
            'aiclk': '1000',
            'heartbeat': '1',
        }]

        self._smbus_telem_info = [{
            'DDR_STATUS': '255',  # All channels trained
            'DDR_SPEED': '6400',
            'ARC0_HEALTH': '1',
            'ARC3_HEALTH': '1',
            'AICLK': '1000',
            'ASIC_TEMPERATURE': '52.3',
            'BOARD_ID': '0',
        }]

        self._device_infos = [{
            'board_type': 'n150',
            'bus_id': '0000:01:00.0',
            'dram_status': 'Trained',
            'dram_speed': '6400',
            'coords': '(0,0)',
        }]

        logger.info("Generated mock data for 1 Wormhole device")

    def _refresh_mock_data(self) -> None:
        """Refresh mock data with simulated changes"""
        # Add some variation to simulate real hardware
        import random
        for telem in self._device_telemetrys:
            # Add random variation to power/current
            base_power = float(telem['power'])
            telem['power'] = f"{base_power + random.uniform(-5, 5):.1f}"

            base_current = float(telem['current'])
            telem['current'] = f"{base_current + random.uniform(-2, 2):.1f}"

            base_temp = float(telem['asic_temperature'])
            telem['asic_temperature'] = f"{base_temp + random.uniform(-1, 1):.1f}"

    # Backend interface methods (compatibility with TTSMIBackend)

    @property
    def devices(self) -> List[DeviceProxy]:
        """Get list of device proxies"""
        return self._devices

    @property
    def device_telemetrys(self) -> List[Dict[str, str]]:
        """Get list of telemetry dictionaries"""
        return self._device_telemetrys

    @property
    def smbus_telem_info(self) -> List[Dict[str, str]]:
        """Get list of SMBUS telemetry dictionaries"""
        return self._smbus_telem_info

    @property
    def device_infos(self) -> List[Dict[str, str]]:
        """Get list of device info dictionaries"""
        return self._device_infos

    def get_device_name(self, device: DeviceProxy) -> str:
        """
        Get device name from device proxy

        Args:
            device: DeviceProxy object

        Returns:
            Device name string (e.g., 'Wormhole-0')
        """
        return f"{device.get_architecture_name()}-{device.device_idx}"

    def get_dram_speed(self, device_idx: int) -> str:
        """
        Get DDR speed for device

        Args:
            device_idx: Device index

        Returns:
            DDR speed string (e.g., '6400')
        """
        try:
            return self._smbus_telem_info[device_idx].get('DDR_SPEED', '0')
        except (IndexError, KeyError):
            return '0'

    def get_dram_training_status(self, device_idx: int) -> bool:
        """
        Get DDR training status for device

        Args:
            device_idx: Device index

        Returns:
            True if DDR is trained, False otherwise
        """
        try:
            ddr_status = self._smbus_telem_info[device_idx].get('DDR_STATUS', '0')
            # Non-zero DDR_STATUS means at least some channels are trained
            return int(ddr_status) > 0
        except (IndexError, KeyError, ValueError):
            return False

    def detect_workload_state(self, device_idx: int) -> str:
        """
        Detect workload state based on telemetry thresholds

        Args:
            device_idx: Device index

        Returns:
            Workload state string: 'idle', 'active', 'high'
        """
        try:
            telem = self._device_telemetrys[device_idx]
            power = float(telem.get('power', '0'))

            if power > 75:
                return 'high'
            elif power > 25:
                return 'active'
            else:
                return 'idle'
        except (IndexError, KeyError, ValueError):
            return 'idle'

    def get_workload_event_text(self, device_idx: int, event_type: str) -> str:
        """
        Get workload event description text

        Args:
            device_idx: Device index
            event_type: Event type ('power', 'thermal', 'current', 'clock')

        Returns:
            Event description string
        """
        try:
            telem = self._device_telemetrys[device_idx]

            if event_type == 'power':
                power = float(telem.get('power', '0'))
                if power > 75:
                    return f"HIGH_POWER_STATE {power:.1f}W (maximum load)"
                elif power > 50:
                    return f"ACTIVE_WORKLOAD {power:.1f}W (processing)"
                else:
                    return f"IDLE_STATE {power:.1f}W (low power)"

            elif event_type == 'thermal':
                temp = float(telem.get('asic_temperature', '0'))
                if temp > 80:
                    return f"THERMAL_ALERT {temp:.1f}°C (critical)"
                elif temp > 65:
                    return f"TEMP_WARNING {temp:.1f}°C (elevated)"
                else:
                    return f"TEMP_NORMAL {temp:.1f}°C"

            elif event_type == 'current':
                current = float(telem.get('current', '0'))
                if current > 50:
                    return f"HIGH_CURRENT {current:.1f}A (peak demand)"
                else:
                    return f"CURRENT_DRAW {current:.1f}A"

            elif event_type == 'clock':
                aiclk = float(telem.get('aiclk', '0'))
                if aiclk > 1000:
                    return f"AICLK_BOOST {aiclk:.0f}MHz (turbo mode)"
                else:
                    return f"AICLK_ACTIVE {aiclk:.0f}MHz"

        except (IndexError, KeyError, ValueError):
            pass

        return f"{event_type.upper()}_UNKNOWN"

    def cleanup(self) -> None:
        """
        Cleanup resources (terminate subprocess)

        Should be called on application shutdown.
        """
        if self.process:
            logger.info("Terminating tt-smi subprocess")
            try:
                self.process.terminate()
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                logger.warning("Subprocess did not terminate, killing")
                self.process.kill()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

            self.subprocess_running = False

    def __del__(self):
        """Destructor - ensure subprocess is terminated"""
        self.cleanup()
