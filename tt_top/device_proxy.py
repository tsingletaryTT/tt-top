# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Device Proxy for JSON-based backend

Provides lightweight device objects for architecture detection without
requiring direct hardware access. Used by JSONBackendAdapter to emulate
the device interface expected by visualization widgets.
"""

from typing import Optional


class DeviceProxy:
    """
    Lightweight proxy for Tenstorrent device objects

    Provides architecture detection methods (as_gs, as_wh, as_bh) based on
    board_type string from JSON telemetry. This allows visualization code
    to work identically with both direct hardware access and JSON mode.

    Architecture Detection Strategy:
    - Grayskull: board_type contains 'e75', 'e150', 'grayskull', 'gs'
    - Wormhole: board_type contains 'n150', 'n300', 'wormhole', 'wh'
    - Blackhole: board_type contains 'p150', 'p300', 'blackhole', 'bh'

    Examples:
        >>> device = DeviceProxy(board_type='n150', bus_id='0000:01:00.0')
        >>> device.as_wh()  # Returns True
        >>> device.as_gs()  # Returns False
    """

    def __init__(self, board_type: str, bus_id: str, device_idx: int = 0):
        """
        Initialize device proxy

        Args:
            board_type: Board type string from JSON (e.g., 'n150', 'e75', 'p300')
            bus_id: PCI bus ID string (e.g., '0000:01:00.0')
            device_idx: Device index in system (0-based)
        """
        self.board_type = board_type.lower() if board_type else ''
        self.bus_id = bus_id
        self.device_idx = device_idx

        # Cache architecture detection for performance
        self._is_grayskull: Optional[bool] = None
        self._is_wormhole: Optional[bool] = None
        self._is_blackhole: Optional[bool] = None

        # Detect architecture once on initialization
        self._detect_architecture()

    def _detect_architecture(self) -> None:
        """
        Detect device architecture from board_type string

        Uses pattern matching on board_type to determine chip architecture.
        Results are cached in _is_* instance variables for fast access.
        """
        board_lower = self.board_type.lower()

        # Grayskull patterns: e75, e150, grayskull, gs
        if any(pattern in board_lower for pattern in ['e75', 'e150', 'grayskull', 'gs']):
            self._is_grayskull = True
            self._is_wormhole = False
            self._is_blackhole = False

        # Wormhole patterns: n150, n300, wormhole, wh
        elif any(pattern in board_lower for pattern in ['n150', 'n300', 'wormhole', 'wh']):
            self._is_grayskull = False
            self._is_wormhole = True
            self._is_blackhole = False

        # Blackhole patterns: p150, p300, blackhole, bh
        elif any(pattern in board_lower for pattern in ['p150', 'p300', 'blackhole', 'bh']):
            self._is_grayskull = False
            self._is_wormhole = False
            self._is_blackhole = True

        # Unknown/fallback: set all to False
        else:
            self._is_grayskull = False
            self._is_wormhole = False
            self._is_blackhole = False

    def as_gs(self) -> bool:
        """
        Check if device is Grayskull architecture

        Returns:
            True if device is Grayskull (e75, e150), False otherwise
        """
        return self._is_grayskull

    def as_wh(self) -> bool:
        """
        Check if device is Wormhole architecture

        Returns:
            True if device is Wormhole (n150, n300), False otherwise
        """
        return self._is_wormhole

    def as_bh(self) -> bool:
        """
        Check if device is Blackhole architecture

        Returns:
            True if device is Blackhole (p150, p300), False otherwise
        """
        return self._is_blackhole

    def get_architecture_name(self) -> str:
        """
        Get human-readable architecture name

        Returns:
            Architecture name string: 'Grayskull', 'Wormhole', 'Blackhole', or 'Unknown'
        """
        if self._is_grayskull:
            return 'Grayskull'
        elif self._is_wormhole:
            return 'Wormhole'
        elif self._is_blackhole:
            return 'Blackhole'
        else:
            return 'Unknown'

    def get_num_ddr_channels(self) -> int:
        """
        Get number of DDR memory channels for this architecture

        Returns:
            Number of DDR channels:
            - Grayskull: 4 channels
            - Wormhole: 8 channels
            - Blackhole: 12 channels
            - Unknown: 8 channels (default)
        """
        if self._is_grayskull:
            return 4
        elif self._is_wormhole:
            return 8
        elif self._is_blackhole:
            return 12
        else:
            return 8  # Default fallback

    def get_tensix_grid(self) -> tuple[int, int]:
        """
        Get Tensix core grid dimensions (rows, cols) for this architecture

        Returns:
            Tuple of (rows, cols):
            - Grayskull: (10, 12)
            - Wormhole: (8, 10)
            - Blackhole: (14, 16)
            - Unknown: (8, 10) - default to Wormhole dimensions
        """
        if self._is_grayskull:
            return (10, 12)
        elif self._is_wormhole:
            return (8, 10)
        elif self._is_blackhole:
            return (14, 16)
        else:
            return (8, 10)  # Default fallback

    def __repr__(self) -> str:
        """String representation for debugging"""
        return f"DeviceProxy(board_type='{self.board_type}', bus_id='{self.bus_id}', arch='{self.get_architecture_name()}')"

    def __str__(self) -> str:
        """Human-readable string representation"""
        return f"{self.get_architecture_name()} ({self.board_type}) at {self.bus_id}"
