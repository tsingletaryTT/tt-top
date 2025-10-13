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
#          GUI CONSTANTS
########################################




PCI_PROPERTIES = [
    "current_link_speed",
    "max_link_speed",
    "current_link_width",
    "max_link_width",
]

# HELP MARKDOWN DOCUMENT

