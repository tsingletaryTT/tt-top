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

    def __init__(self, backend: Any, **kwargs):
        """
        Initialize multi-device grid

        Args:
            backend: JSONBackendAdapter or compatible backend
            **kwargs: Additional arguments for Grid container
        """
        super().__init__(**kwargs)
        self.backend = backend

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
        self.styles.grid_size_rows = "auto"  # Rows fit content

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
        self.set_interval(0.1, self._update_telemetry)  # 10 FPS

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
