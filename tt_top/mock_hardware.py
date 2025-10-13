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

# Mock PCI chip functionality
class MockPciChip:
    def __init__(self, pci_interface=0):
        self.pci_interface = pci_interface

    def as_gs(self):
        return None

    def as_wh(self):
        return None

    def as_bh(self):
        return None

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