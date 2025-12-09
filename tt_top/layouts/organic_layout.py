#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Organic Layout Container

Main container for the organic (Textual-native) layout combining
device telemetry cards and memory hierarchy visualizations.
"""

from typing import Any

# Try to import VerticalScroll (added in newer Textual versions)
try:
    from textual.containers import VerticalScroll
except ImportError:
    # Fallback for older Textual versions: use Container with CSS overflow
    from textual.containers import Container as VerticalScroll

from textual.app import ComposeResult
from textual.widgets import Static

from tt_top.layouts.multi_device_grid import MultiDeviceGrid
from tt_top.widgets.memory_hierarchy_card import MemoryHierarchyCard


class OrganicLayout(VerticalScroll):
    """
    Organic layout container with Textual-native widgets

    Combines:
    - Device telemetry grid (power, temp, current, voltage)
    - Memory hierarchy visualizations (DDR, L2, L1 SRAM)
    - Auto-refresh at 10 FPS
    - Scrollable content
    """

    DEFAULT_CSS = """
    OrganicLayout {
        height: 100%;
        overflow-y: auto;
        padding: 1;
    }
    """

    def __init__(self, backend: Any, refresh_rate: float = 0.05, **kwargs):
        """
        Initialize organic layout

        Args:
            backend: JSONBackendAdapter or compatible backend
            refresh_rate: Display refresh rate in seconds (default: 0.05 = 20 FPS)
            **kwargs: Additional arguments for VerticalScroll
        """
        super().__init__(**kwargs)
        self.backend = backend
        self.refresh_rate = refresh_rate

    def compose(self) -> ComposeResult:
        """
        Compose organic layout with device cards and memory visualizations

        Yields:
            - MultiDeviceGrid: Responsive grid of device telemetry cards
            - Section header: Memory hierarchy title
            - MemoryHierarchyCard: One per device showing DDR/L2/L1 SRAM
        """
        # Add multi-device telemetry grid
        yield MultiDeviceGrid(backend=self.backend, refresh_rate=self.refresh_rate, id="device_grid")

        # Add section header for memory hierarchy
        yield Static(
            "[bold bright_magenta]Memory Hierarchy & SRAM Visualization[/]",
            classes="section-header"
        )

        # Add memory hierarchy cards for each device
        num_devices = len(self.backend.devices)
        for i in range(num_devices):
            yield MemoryHierarchyCard(
                backend=self.backend,
                device_idx=i,
                compact=(num_devices > 2),  # Compact if more than 2 devices
                refresh_rate=self.refresh_rate,
                id=f"memory_card_{i}"
            )

    def update_refresh_rate(self, refresh_rate: float) -> None:
        """
        Update refresh rate for all child widgets

        Args:
            refresh_rate: New refresh rate in seconds
        """
        self.refresh_rate = refresh_rate

        # Update MultiDeviceGrid
        device_grid = self.query_one("#device_grid", MultiDeviceGrid)
        if device_grid and hasattr(device_grid, 'update_refresh_rate'):
            device_grid.update_refresh_rate(refresh_rate)

        # Update all MemoryHierarchyCards
        num_devices = len(self.backend.devices)
        for i in range(num_devices):
            memory_card = self.query_one(f"#memory_card_{i}", MemoryHierarchyCard)
            if memory_card and hasattr(memory_card, 'update_refresh_rate'):
                memory_card.update_refresh_rate(refresh_rate)
