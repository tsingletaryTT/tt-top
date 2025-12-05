#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Unit tests for DeviceProxy class

Tests architecture detection logic for all Tenstorrent device types:
- Grayskull (GS): e75, e150
- Wormhole (WH): n150, n300
- Blackhole (BH): p150, p300
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import directly from module to avoid __init__.py dependencies
import importlib.util
spec = importlib.util.spec_from_file_location(
    "device_proxy",
    Path(__file__).parent.parent / "tt_top" / "device_proxy.py"
)
device_proxy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(device_proxy)
DeviceProxy = device_proxy.DeviceProxy


class TestDeviceProxyArchitectureDetection(unittest.TestCase):
    """Test architecture detection for all device types"""

    def test_grayskull_e75_detection(self):
        """Test Grayskull e75 board detection"""
        device = DeviceProxy(board_type='e75', bus_id='0000:01:00.0', device_idx=0)

        self.assertTrue(device.as_gs(), "e75 should be detected as Grayskull")
        self.assertFalse(device.as_wh(), "e75 should not be Wormhole")
        self.assertFalse(device.as_bh(), "e75 should not be Blackhole")
        self.assertEqual(device.get_architecture_name(), "Grayskull")

    def test_grayskull_e150_detection(self):
        """Test Grayskull e150 board detection"""
        device = DeviceProxy(board_type='e150', bus_id='0000:01:00.0', device_idx=0)

        self.assertTrue(device.as_gs(), "e150 should be detected as Grayskull")
        self.assertFalse(device.as_wh(), "e150 should not be Wormhole")
        self.assertFalse(device.as_bh(), "e150 should not be Blackhole")
        self.assertEqual(device.get_architecture_name(), "Grayskull")

    def test_wormhole_n150_detection(self):
        """Test Wormhole n150 board detection"""
        device = DeviceProxy(board_type='n150', bus_id='0000:02:00.0', device_idx=0)

        self.assertFalse(device.as_gs(), "n150 should not be Grayskull")
        self.assertTrue(device.as_wh(), "n150 should be detected as Wormhole")
        self.assertFalse(device.as_bh(), "n150 should not be Blackhole")
        self.assertEqual(device.get_architecture_name(), "Wormhole")

    def test_wormhole_n300_detection(self):
        """Test Wormhole n300 board detection"""
        device = DeviceProxy(board_type='n300', bus_id='0000:02:00.0', device_idx=0)

        self.assertFalse(device.as_gs(), "n300 should not be Grayskull")
        self.assertTrue(device.as_wh(), "n300 should be detected as Wormhole")
        self.assertFalse(device.as_bh(), "n300 should not be Blackhole")
        self.assertEqual(device.get_architecture_name(), "Wormhole")

    def test_blackhole_p150_detection(self):
        """Test Blackhole p150 board detection"""
        device = DeviceProxy(board_type='p150', bus_id='0000:03:00.0', device_idx=0)

        self.assertFalse(device.as_gs(), "p150 should not be Grayskull")
        self.assertFalse(device.as_wh(), "p150 should not be Wormhole")
        self.assertTrue(device.as_bh(), "p150 should be detected as Blackhole")
        self.assertEqual(device.get_architecture_name(), "Blackhole")

    def test_blackhole_p300_detection(self):
        """Test Blackhole p300 board detection"""
        device = DeviceProxy(board_type='p300', bus_id='0000:03:00.0', device_idx=0)

        self.assertFalse(device.as_gs(), "p300 should not be Grayskull")
        self.assertFalse(device.as_wh(), "p300 should not be Wormhole")
        self.assertTrue(device.as_bh(), "p300 should be detected as Blackhole")
        self.assertEqual(device.get_architecture_name(), "Blackhole")

    def test_case_insensitive_detection(self):
        """Test that board type detection is case-insensitive"""
        device_upper = DeviceProxy(board_type='N150', bus_id='0000:02:00.0', device_idx=0)
        device_lower = DeviceProxy(board_type='n150', bus_id='0000:02:00.0', device_idx=0)
        device_mixed = DeviceProxy(board_type='N150', bus_id='0000:02:00.0', device_idx=0)

        self.assertTrue(device_upper.as_wh(), "Uppercase N150 should be Wormhole")
        self.assertTrue(device_lower.as_wh(), "Lowercase n150 should be Wormhole")
        self.assertTrue(device_mixed.as_wh(), "Mixed case N150 should be Wormhole")

    def test_unknown_board_type(self):
        """Test handling of unknown board types"""
        device = DeviceProxy(board_type='unknown', bus_id='0000:04:00.0', device_idx=0)

        self.assertFalse(device.as_gs(), "Unknown should not be Grayskull")
        self.assertFalse(device.as_wh(), "Unknown should not be Wormhole")
        self.assertFalse(device.as_bh(), "Unknown should not be Blackhole")
        self.assertEqual(device.get_architecture_name(), "Unknown")


class TestDeviceProxyMemoryChannels(unittest.TestCase):
    """Test memory channel counts for different architectures"""

    def test_grayskull_memory_channels(self):
        """Test Grayskull has 4 DDR channels"""
        device = DeviceProxy(board_type='e150', bus_id='0000:01:00.0', device_idx=0)
        self.assertEqual(device.get_num_ddr_channels(), 4, "Grayskull should have 4 DDR channels")

    def test_wormhole_memory_channels(self):
        """Test Wormhole has 8 DDR channels"""
        device = DeviceProxy(board_type='n150', bus_id='0000:02:00.0', device_idx=0)
        self.assertEqual(device.get_num_ddr_channels(), 8, "Wormhole should have 8 DDR channels")

    def test_blackhole_memory_channels(self):
        """Test Blackhole has 12 DDR channels"""
        device = DeviceProxy(board_type='p150', bus_id='0000:03:00.0', device_idx=0)
        self.assertEqual(device.get_num_ddr_channels(), 12, "Blackhole should have 12 DDR channels")


class TestDeviceProxyTensixGrid(unittest.TestCase):
    """Test Tensix grid dimensions for different architectures"""

    def test_grayskull_tensix_grid(self):
        """Test Grayskull has 10x12 Tensix grid"""
        device = DeviceProxy(board_type='e150', bus_id='0000:01:00.0', device_idx=0)
        rows, cols = device.get_tensix_grid()
        self.assertEqual(rows, 10, "Grayskull should have 10 Tensix rows")
        self.assertEqual(cols, 12, "Grayskull should have 12 Tensix columns")

    def test_wormhole_tensix_grid(self):
        """Test Wormhole has 8x10 Tensix grid"""
        device = DeviceProxy(board_type='n150', bus_id='0000:02:00.0', device_idx=0)
        rows, cols = device.get_tensix_grid()
        self.assertEqual(rows, 8, "Wormhole should have 8 Tensix rows")
        self.assertEqual(cols, 10, "Wormhole should have 10 Tensix columns")

    def test_blackhole_tensix_grid(self):
        """Test Blackhole has 14x16 Tensix grid"""
        device = DeviceProxy(board_type='p150', bus_id='0000:03:00.0', device_idx=0)
        rows, cols = device.get_tensix_grid()
        self.assertEqual(rows, 14, "Blackhole should have 14 Tensix rows")
        self.assertEqual(cols, 16, "Blackhole should have 16 Tensix columns")


class TestDeviceProxyAttributes(unittest.TestCase):
    """Test DeviceProxy attribute storage and retrieval"""

    def test_device_attributes(self):
        """Test that device attributes are stored correctly"""
        device = DeviceProxy(
            board_type='n150',
            bus_id='0000:02:00.0',
            device_idx=5
        )

        self.assertEqual(device.board_type, 'n150')
        self.assertEqual(device.bus_id, '0000:02:00.0')
        self.assertEqual(device.device_idx, 5)

    def test_string_representation(self):
        """Test DeviceProxy string representation"""
        device = DeviceProxy(board_type='n150', bus_id='0000:02:00.0', device_idx=0)
        str_repr = str(device)

        self.assertIn('Wormhole', str_repr, "String representation should include architecture")
        self.assertIn('0000:02:00.0', str_repr, "String representation should include bus_id")


if __name__ == '__main__':
    unittest.main()
