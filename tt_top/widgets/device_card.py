#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Device Telemetry Card Widget

Textual-native widget for displaying single device telemetry in a compact card.
Uses auto-height, native borders, and Rich rendering for progress bars.
"""

from typing import Any
from textual.widgets import Static
from textual.app import ComposeResult
from rich.text import Text
from rich.console import RenderableType


class DeviceTelemetryCard(Static):
    """
    Single device telemetry card with organic auto-sizing

    Features:
    - Auto-height based on content (no rigid boxes)
    - Native Textual borders (round style with transparency)
    - Rich-rendered progress bars for metrics
    - Color-coded status (green/yellow/red based on thresholds)
    - Responsive sizing with fr units

    The card displays:
    - Device name and architecture
    - Power consumption with visual bar
    - Temperature with visual bar
    - Current draw with visual bar
    - AICLK frequency with status
    - ARC firmware health with heartbeat
    - DDR training status summary
    """

    DEFAULT_CSS = """
    DeviceTelemetryCard {
        border: round $accent 70%;
        padding: 1;
        height: auto;  /* Key: grows with content */
        width: 1fr;    /* Equal columns in grid */
        margin: 1;
    }

    DeviceTelemetryCard:focus {
        border: round $accent;  /* Full opacity on focus */
    }

    DeviceTelemetryCard.-compact {
        padding: 0 1;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        backend: Any,
        device_idx: int,
        compact: bool = False,
        **kwargs
    ):
        """
        Initialize device card

        Args:
            backend: JSONBackendAdapter or compatible backend
            device_idx: Device index in backend.devices
            compact: If True, use compact layout for many devices
            **kwargs: Additional arguments for Static widget
        """
        super().__init__(**kwargs)
        self.backend = backend
        self.device_idx = device_idx
        self.compact = compact

        # Apply compact class if needed
        if compact:
            self.add_class("-compact")

    def render(self) -> RenderableType:
        """
        Render device telemetry with Rich markup

        Returns Rich Text object with formatted device info
        """
        # Get device and telemetry data
        device = self.backend.devices[self.device_idx]
        telem = self.backend.get_device_telemetry(self.device_idx)

        # Extract values
        power = telem.get('power', 0)
        temp = telem.get('asic_temperature', 0)
        current = telem.get('current', 0)
        aiclk = telem.get('aiclk', 0)
        voltage = telem.get('voltage', 0)

        # Get architecture name
        arch_name = self._get_architecture_name(device)

        # Build card content
        lines = []

        # Header with device name
        if self.compact:
            lines.append(f"[bold bright_cyan]Dev {self.device_idx}[/] {arch_name}")
        else:
            lines.append(f"[bold bright_cyan]Device {self.device_idx}: {arch_name}[/]")
            lines.append("")  # Spacing

        # Power consumption with bar
        power_bar = self._create_metric_bar(power, 120, "power")  # Assume 120W max
        power_status = self._get_power_status(power)
        lines.append(f"Power:   {power:5.1f}W {power_bar} {power_status}")

        # Temperature with bar
        temp_bar = self._create_metric_bar(temp, 100, "temp")  # 100°C max
        temp_status = self._get_temp_status(temp)
        lines.append(f"Temp:    {temp:5.1f}°C {temp_bar} {temp_status}")

        if not self.compact:
            # Current draw with bar
            current_bar = self._create_metric_bar(current, 100, "current")  # 100A max
            lines.append(f"Current: {current:5.1f}A {current_bar}")

            # AICLK with status
            aiclk_status = self._get_aiclk_status(aiclk)
            lines.append(f"AICLK:   {aiclk}MHz {aiclk_status}")

            # ARC firmware health
            arc_status = self._get_arc_status()
            lines.append(f"ARC:     {arc_status}")

            # DDR training status
            ddr_status = self._get_ddr_status()
            lines.append(f"DDR:     {ddr_status}")

        return "\n".join(lines)

    def _get_architecture_name(self, device: Any) -> str:
        """Get human-readable architecture name"""
        if device.as_gs():
            return "Grayskull"
        elif device.as_wh():
            return "Wormhole"
        elif device.as_bh():
            return "Blackhole"
        else:
            return "Unknown"

    def _create_metric_bar(self, value: float, max_value: float, metric_type: str) -> str:
        """
        Create visual progress bar for metric

        Args:
            value: Current value
            max_value: Maximum value for scale
            metric_type: Type of metric ('power', 'temp', 'current')

        Returns:
            Colored progress bar string with Rich markup
        """
        bar_width = 12 if not self.compact else 8
        filled = int(bar_width * min(value / max_value, 1.0))
        empty = bar_width - filled

        # Choose color based on value and type
        if metric_type == "temp":
            if value > 80:
                color = "bold red"
            elif value > 65:
                color = "bold yellow"
            elif value > 45:
                color = "bright_green"
            else:
                color = "bright_cyan"
        elif metric_type == "power":
            if value > 100:
                color = "bold red"
            elif value > 75:
                color = "bold yellow"
            elif value > 25:
                color = "bright_green"
            else:
                color = "bright_cyan"
        else:  # current
            if value > 70:
                color = "bold red"
            elif value > 50:
                color = "bold yellow"
            else:
                color = "bright_green"

        return f"[{color}]{'█' * filled}[/][dim white]{'░' * empty}[/]"

    def _get_power_status(self, power: float) -> str:
        """Get power status text"""
        if power < 10:
            return "[dim white](Idle)[/]"
        elif power < 25:
            return "[bright_cyan](Low)[/]"
        elif power < 75:
            return "[bright_green](Active)[/]"
        elif power < 100:
            return "[bold yellow](High)[/]"
        else:
            return "[bold red](Peak)[/]"

    def _get_temp_status(self, temp: float) -> str:
        """Get temperature status text"""
        if temp < 45:
            return "[bright_cyan](Cool)[/]"
        elif temp < 65:
            return "[bright_green](Nominal)[/]"
        elif temp < 80:
            return "[bold yellow](Elevated)[/]"
        else:
            return "[bold red](Hot!)[/]"

    def _get_aiclk_status(self, aiclk: int) -> str:
        """Get AICLK status indicator"""
        if aiclk > 1000:
            return "[bold yellow][Turbo][/]"
        elif aiclk > 800:
            return "[bright_green][Active][/]"
        else:
            return "[dim white][Standard][/]"

    def _get_arc_status(self) -> str:
        """Get ARC firmware health status"""
        try:
            telem = self.backend.get_device_telemetry(self.device_idx)
            heartbeat = telem.get('heartbeat', 0)
            if heartbeat > 0:
                return "[bright_green]❤ Healthy[/]"
            else:
                return "[bold red]✗ Timeout[/]"
        except:
            return "[dim white]Unknown[/]"

    def _get_ddr_status(self) -> str:
        """Get DDR training status summary"""
        try:
            trained = self.backend.get_dram_training_status(self.device_idx)
            if trained:
                return "[bright_green]✓ Trained[/]"
            else:
                return "[bold yellow]◐ Training[/]"
        except:
            return "[dim white]Unknown[/]"
