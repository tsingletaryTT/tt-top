#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Multi-Device Grid Layout

Responsive grid container that adapts to number of devices using Textual's
native Grid container with fr units. No custom border calculations needed.
"""

from typing import Any
from textual.containers import Grid
from textual.app import ComposeResult
from tt_top.widgets.device_card import DeviceTelemetryCard


class MultiDeviceGrid(Grid):
    """
    Responsive grid layout for multiple Tenstorrent devices

    Automatically adjusts columns and compactness based on device count:
    - 1-3 devices: Full-width cards (1-3 columns)
    - 4-6 devices: 3 columns with moderate detail
    - 7-12 devices: 4 columns with compact cards
    - 13+ devices: 4 columns with ultra-compact cards

    Uses Textual's Grid container with:
    - Automatic column sizing with fr units
    - Auto-height rows (fit content)
    - Grid gutter for spacing (no manual borders)
    - Responsive card sizing based on count
    """

    DEFAULT_CSS = """
    MultiDeviceGrid {
        height: auto;  /* Grows with content */
        padding: 1;
        grid-gutter: 1;  /* Space between cards */
    }

    MultiDeviceGrid > DeviceTelemetryCard {
        width: 1fr;   /* Equal column widths */
        height: auto; /* Each card fits its content */
    }
    """

    def __init__(self, backend: Any, refresh_rate: float = 0.05, **kwargs):
        """
        Initialize multi-device grid

        Args:
            backend: JSONBackendAdapter or compatible backend
            refresh_rate: Display refresh rate in seconds (default: 0.05 = 20 FPS)
            **kwargs: Additional arguments for Grid container
        """
        super().__init__(**kwargs)
        self.backend = backend
        self.refresh_rate = refresh_rate
        self.update_timer = None  # Store timer handle for dynamic updates

    def compose(self) -> ComposeResult:
        """
        Compose grid with device cards

        Automatically determines grid sizing and card compactness
        based on number of devices detected.
        """
        num_devices = len(self.backend.devices)

        # Configure grid layout based on device count
        if num_devices == 0:
            # No devices detected
            from textual.widgets import Static
            yield Static("No Tenstorrent devices detected")
            return

        # Determine grid columns
        if num_devices == 1:
            columns = 1
            compact = False
        elif num_devices == 2:
            columns = 2
            compact = False
        elif num_devices == 3:
            columns = 3
            compact = False
        elif num_devices <= 6:
            columns = 3
            compact = False
        elif num_devices <= 12:
            columns = 4
            compact = True
        else:
            # 13+ devices: ultra-compact 4-column grid
            columns = 4
            compact = True

        # Apply grid sizing
        self.styles.grid_size_columns = columns
        # Calculate rows based on device count and columns
        rows = (num_devices + columns - 1) // columns  # Ceiling division
        self.styles.grid_size_rows = rows

        # Yield device cards
        for i in range(num_devices):
            yield DeviceTelemetryCard(
                backend=self.backend,
                device_idx=i,
                compact=compact,
                id=f"device_card_{i}"
            )

    def on_mount(self) -> None:
        """Update telemetry on mount"""
        self.update_timer = self.set_interval(self.refresh_rate, self._update_telemetry)

    def on_unmount(self) -> None:
        """Cleanup timer when widget is unmounted"""
        if self.update_timer:
            self.update_timer.stop()
            self.update_timer = None

    def _update_telemetry(self) -> None:
        """Update all device cards with latest telemetry"""
        try:
            # Update backend telemetry
            self.backend.update_telem()

            # Refresh all cards
            for card in self.query("DeviceTelemetryCard"):
                card.refresh()

        except Exception:
            # Silently continue on errors (backend handles logging)
            pass

    def update_refresh_rate(self, refresh_rate: float) -> None:
        """
        Update refresh rate for telemetry updates

        Args:
            refresh_rate: New refresh rate in seconds
        """
        self.refresh_rate = refresh_rate

        # Cancel existing timer and create new one with updated rate
        if self.update_timer:
            self.update_timer.stop()
        self.update_timer = self.set_interval(self.refresh_rate, self._update_telemetry)
