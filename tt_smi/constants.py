# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

########################################
#          BACKEND CONSTANTS
########################################

SMBUS_TELEMETRY_LIST = [
    "BOARD_ID",
    "ENUM_VERSION",
    "DEVICE_ID",
    "ASIC_RO",
    "ASIC_IDD",
    "BOARD_ID_HIGH",
    "BOARD_ID_LOW",
    "ARC0_FW_VERSION",
    "ARC1_FW_VERSION",
    "ARC2_FW_VERSION",
    "ARC3_FW_VERSION",
    "SPIBOOTROM_FW_VERSION",
    "ETH_FW_VERSION",
    "M3_BL_FW_VERSION",
    "M3_APP_FW_VERSION",
    "DDR_SPEED",
    "DDR_STATUS",
    "ETH_STATUS0",
    "ETH_STATUS1",
    "PCIE_STATUS",
    "FAULTS",
    "ARC0_HEALTH",
    "ARC1_HEALTH",
    "ARC2_HEALTH",
    "ARC3_HEALTH",
    "FAN_SPEED",
    "AICLK",
    "AXICLK",
    "ARCCLK",
    "THROTTLER",
    "VCORE",
    "ASIC_TEMPERATURE",
    "VREG_TEMPERATURE",
    "BOARD_TEMPERATURE",
    "TDP",
    "TDC",
    "VDD_LIMITS",
    "THM_LIMITS",
    "WH_FW_DATE",
    "ASIC_TMON0",
    "ASIC_TMON1",
    "MVDDQ_POWER",
    "GDDR_TRAIN_TEMP0",
    "GDDR_TRAIN_TEMP1",
    "BOOT_DATE",
    "RT_SECONDS",
    "AUX_STATUS",
    "ETH_DEBUG_STATUS0",
    "ETH_DEBUG_STATUS1",
    "TT_FLASH_VERSION",
    "FW_BUNDLE_VERSION",
    "THERM_TRIP_COUNT",
    "INPUT_POWER",
    "BOARD_POWER_LIMIT",
]

BH_TELEMETRY_LIST = [
    "TAG_BOARD_ID_HIGH",
    "TAG_BOARD_ID_HIGH",
    "TAG_ASIC_ID",
    "TAG_UPDATE_TELEM_SPEED",
    "TAG_VCORE",
    "TAG_TDP",
    "TAG_TDC",
    "TAG_VDD_LIMITS",
    "TAG_THM_LIMITS",
    "TAG_ASIC_TEMPERATURE",
    "TAG_VREG_TEMPERATURE",
    "TAG_BOARD_TEMPERATURE",
    "TAG_AICLK",
    "TAG_AXICLK",
    "TAG_ARCCLK",
    "TAG_L2CPUCLK0",
    "TAG_L2CPUCLK1",
    "TAG_L2CPUCLK2",
    "TAG_L2CPUCLK3",
    "TAG_ETH_LIVE_STATUS",
    "TAG_DDR_STATUS",
    "TAG_DDR_SPEED",
    "TAG_ETH_FW_VERSION",
    "TAG_DDR_FW_VERSION",
    "TAG_BM_APP_FW_VERSION",
    "TAG_BM_BL_FW_VERSION",
    "TAG_FLASH_BUNDLE_VERSION",
    "TAG_CM_FW_VERSION",
    "TAG_L2CPU_FW_VERSION",
    "TAG_FAN_SPEED",
    "TAG_TIMER_HEARTBEAT",
    "TAG_TELEM_ENUM_COUNT",
]

TELEM_LIST = [
    "voltage",
    "current",
    "aiclk",
    "power",
    "asic_temperature",
    "heartbeat",
]

LIMITS = [
    "vdd_min",
    "vdd_max",
    "tdp_limit",
    "tdc_limit",
    "asic_fmax",
    "therm_trip_l1_limit",
    "thm_limit",
    "bus_peak_limit",
]

FW_LIST = [
    "fw_bundle_version",
    "tt_flash_version",
    "cm_fw",
    "cm_fw_date",
    "eth_fw",
    "bm_bl_fw",
    "bm_app_fw",
]

DEV_INFO_LIST = [
    "bus_id",
    "board_type",
    "board_id",
    "coords",
    "dram_status",
    "dram_speed",
    "pcie_speed",
    "pcie_width",
]

PCI_PROPERTIES = [
    "current_link_speed",
    "max_link_speed",
    "current_link_width",
    "max_link_width",
]

MAX_PCIE_WIDTH = 16
MAX_PCIE_SPEED = 4
GUI_INTERVAL_TIME = 0.1
MAGIC_FW_VERSION = 0x01030000
MSG_TYPE_FW_VERSION = 0xB9

########################################
#       WORKLOAD DETECTION CONSTANTS
########################################

# Chip-specific idle power baselines (in watts)
CHIP_IDLE_POWER = {
    "grayskull": 15.0,   # GS baseline idle consumption
    "wormhole": 25.0,    # WH baseline idle consumption  
    "blackhole": 35.0,   # BH baseline idle consumption
}

# Workload detection thresholds (relative to idle power)
WORKLOAD_DETECTION = {
    "idle_threshold": 3.0,        # Power delta below which considered idle (watts)
    "light_threshold": 10.0,      # Light workload threshold (watts above idle)
    "moderate_threshold": 30.0,   # Moderate workload threshold (watts above idle)
    "heavy_threshold": 60.0,      # Heavy workload threshold (watts above idle)
    "critical_threshold": 100.0,  # Critical load threshold (watts above idle)
    
    # Clock frequency thresholds (MHz)
    "active_aiclk_min": 800,      # Minimum AICLK for active workload
    "boost_aiclk_min": 1000,      # Minimum AICLK for boost mode
    
    # Current draw thresholds (Amps)
    "active_current_min": 15.0,   # Minimum current for active workload
    "high_current_min": 40.0,     # High current draw threshold
    
    # Temperature thresholds (°C)
    "thermal_active_min": 50.0,   # Temperature suggesting processing
    "thermal_warning": 70.0,      # Temperature warning threshold
    "thermal_critical": 85.0,     # Temperature critical threshold
}

# Workload state definitions
WORKLOAD_STATES = {
    "sleep": {"name": "SLEEP", "color": "dim", "description": "minimal activity"},
    "idle": {"name": "IDLE", "color": "bold cyan", "description": "standby"},
    "light": {"name": "LIGHT_LOAD", "color": "bright_green", "description": "light processing"},
    "active": {"name": "ACTIVE_WORKLOAD", "color": "bright_green", "description": "processing"},
    "moderate": {"name": "MODERATE_LOAD", "color": "orange1", "description": "substantial load"},
    "heavy": {"name": "HEAVY_LOAD", "color": "bold orange3", "description": "high utilization"},
    "critical": {"name": "CRITICAL_LOAD", "color": "bold red", "description": "maximum load"},
    "thermal_limit": {"name": "THERMAL_LIMIT", "color": "bold red", "description": "thermal limiting"},
}
########################################
#          GUI CONSTANTS
########################################

INFO_TABLE_HEADER = [
    "#",
    "Bus ID",
    "Board Type",
    "Board ID",
    "Coords",
    "DRAM Trained",
    "DRAM Speed",
    "Link Speed",
    "Link Width",
]

TELEMETRY_TABLE_HEADER = [
    "#",
    "Core Voltage (V)",
    "Core Current (A)",
    "AICLK (MHz)",
    "Core Power (W)",
    "Core Temp (°C)",
    "Heartbeat",
]

FIRMWARES_TABLE_HEADER = [
    "#",
    "FW Bundle Version",
    "TT-Flash Version",
    "CM FW Version",
    "CM FW Date",
    "ETH FW Version",
    "BM BL Version",
    "BM App Version",
]

PCI_PROPERTIES = [
    "current_link_speed",
    "max_link_speed",
    "current_link_width",
    "max_link_width",
]

# HELP MARKDOWN DOCUMENT

HELP_MENU_MARKDOWN = """\
# TT-SMI HELP MENU

TT-SMI is a command-line utility that allows users to look at the telemetry and device information of Tenstorrent devices.

## KEYBOARD SHORTCUTS

Use cursor or keyboard keys to navigate the app. The following table details the keyboard keys that can be used and their functions

|            Action            |    Key           |                     Detailed Description                     |
| :--------------------------: | :--------------: | :----------------------------------------------------------: |
|             Quit             |   q  |        Exit the program       |
|             Help             |   h   |                   Opens up this help menu                   |
|   Go to device(s) info tab  |        1        |          Switch to tab with device info         |
|   Go to device(s) telemetry tab     |        2        |          Switch to tab with telemetry info that is updated every 100ms           |
|   Go to device(s) firmware tab     |        3        |          Switch to tab with all the fw versions on the board(s)          |
|   Go to live monitor tab     |        4        |          Switch to tab with real-time hardware activity visualization (TT-Top)          |
|   Scroll up in TT-Top        |   ↑ / Page Up   |          Scroll up in live monitor (when in tab 4)         |
|   Scroll down in TT-Top      |   ↓ / Page Down |          Scroll down in live monitor (when in tab 4)       |
|   Go to top of TT-Top        |      Home       |          Jump to top of live monitor content               |
|   Go to bottom of TT-Top     |       End       |          Jump to bottom of live monitor content             |

"""
