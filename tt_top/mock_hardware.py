#!/usr/bin/env python3
"""
Mock hardware components for TT-Top development without full hardware stack
"""

# Mock CMD_LINE_COLOR for tt_tools_common.ui_common.themes
class MockCMDLineColor:
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"

CMD_LINE_COLOR = MockCMDLineColor()

# Mock reset classes
class MockReset:
    def __init__(self, *args, **kwargs):
        pass

    def full_lds_reset(self, *args, **kwargs):
        print("Mock reset executed")

    def warm_reset_mobo(self, *args, **kwargs):
        print("Mock mobo reset executed")

    def tensix_reset(self, *args, **kwargs):
        print("Mock tensix reset executed")

WHChipReset = MockReset
BHChipReset = MockReset
GSTensixReset = MockReset
GalaxyReset = MockReset

# Mock telemetry structure
class MockTelemetryStruct:
    def __init__(self):
        # Mock telemetry attributes
        self.board_id = 0x1234567890ABCDEF
        self.vcore = 850  # mV
        self.tdc = 30000 | (80000 << 16)  # 30A current | 80A limit
        self.tdp = 150 | (200 << 16)  # 150W power | 200W limit
        self.asic_temperature = 0x2D0000  # 45°C in fixed point
        self.aiclk = 800 | (1000 << 16)  # 800MHz | 1000MHz max
        self.arc0_health = 12000  # Heartbeat counter
        self.arc3_health = 15000  # Heartbeat counter
        self.timer_heartbeat = 18000  # BH heartbeat
        self.ddr_speed = 3200
        self.ddr_status = 0x22222222  # All channels trained (state 2)

    def __dir__(self):
        # Get attributes without causing recursion
        return [attr for attr in object.__dir__(self) if not attr.startswith('_') and hasattr(self, attr)]

# Mock chip type implementations
class MockGSChip:
    def get_telemetry(self):
        return MockTelemetryStruct()

class MockWHChip:
    def get_telemetry(self):
        return MockTelemetryStruct()

class MockBHChip:
    def get_telemetry(self):
        return MockTelemetryStruct()

# Mock PCI chip functionality
class MockPciChip:
    def __init__(self, pci_interface=0):
        self.pci_interface = pci_interface
        # Create mock chip types (simulate Grayskull by default)
        self._gs = MockGSChip()
        self._wh = None
        self._bh = None

    def as_gs(self):
        return self._gs

    def as_wh(self):
        return self._wh

    def as_bh(self):
        return self._bh

    def is_remote(self):
        return False

    def get_pci_interface_id(self):
        return f"0000:{self.pci_interface:02d}:00.0"

    def get_pci_bdf(self):
        return f"0000:{self.pci_interface:02d}:00.0"

PciChip = MockPciChip

# Mock utility functions
def get_host_info():
    import platform
    import sys
    return {
        "OS": platform.system(),
        "Distro": "Mock Linux",
        "Kernel": platform.release(),
        "Hostname": platform.node() or "mock-host",
        "Platform": platform.machine(),
        "Python": sys.version.split()[0],
        "Memory": "16GB",
        "Driver": "Mock Driver v1.0"
    }

def hex_to_semver_m3_fw(value):
    return "1.0.0"

def hex_to_date(value, include_time=False):
    return "2024-01-01"

def hex_to_semver_eth(value):
    return "1.0.0"

def init_logging(path):
    import os
    os.makedirs(path, exist_ok=True)

def detect_chips_with_callback(*args, **kwargs):
    return [MockPciChip(0)]

def run_wh_ubb_ipmi_reset(*args, **kwargs):
    print("Mock IPMI reset")

def run_ubb_wait_for_driver_load():
    print("Mock driver load wait")