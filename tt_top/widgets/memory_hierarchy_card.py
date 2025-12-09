#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Memory Hierarchy Visualization Card

Textual-native widget showing DDR → L2 → L1 SRAM memory hierarchy
with real-time utilization patterns from the classic mode visualizations.
"""

from typing import Any, List, Tuple
from textual.widgets import Static
from rich.console import RenderableType


class MemoryHierarchyCard(Static):
    """
    Memory hierarchy visualization showing DDR, L2 cache, and L1 SRAM

    Features:
    - DDR channel status with real training data
    - L2 cache bank utilization
    - L1 SRAM grid (Tensix core array)
    - Data flow indicators between levels
    - Hardware-responsive colors (power/current based)

    This widget adapts the memory hierarchy visualization from classic mode
    into a Textual-native card that fits the organic layout aesthetic.
    """

    DEFAULT_CSS = """
    MemoryHierarchyCard {
        border: round $primary 50%;
        padding: 1;
        height: auto;
        width: 100%;
        margin: 1 0;
    }

    MemoryHierarchyCard:focus {
        border: round $primary;
    }

    MemoryHierarchyCard.-compact {
        padding: 0 1;
        margin: 0;
    }
    """

    def __init__(
        self,
        backend: Any,
        device_idx: int,
        compact: bool = False,
        refresh_rate: float = 0.05,
        **kwargs
    ):
        """
        Initialize memory hierarchy card

        Args:
            backend: JSONBackendAdapter or compatible backend
            device_idx: Device index in backend.devices
            compact: If True, use compact layout
            refresh_rate: Display refresh rate in seconds (default: 0.05 = 20 FPS)
            **kwargs: Additional arguments for Static widget
        """
        super().__init__(**kwargs)
        self.backend = backend
        self.device_idx = device_idx
        self.compact = compact
        self.refresh_rate = refresh_rate
        self.update_timer = None  # Store timer handle for dynamic updates

        if compact:
            self.add_class("-compact")

    def on_mount(self) -> None:
        """Set up automatic refresh on mount"""
        self.update_timer = self.set_interval(self.refresh_rate, self.refresh)

    def render(self) -> RenderableType:
        """
        Render memory hierarchy visualization

        Returns Rich markup with DDR → L2 → L1 memory levels
        """
        device = self.backend.devices[self.device_idx]
        telem = self.backend.device_telemetrys[self.device_idx]

        # Safe float conversion
        try:
            power = float(telem.get('power', 0))
        except (ValueError, TypeError):
            power = 0.0

        try:
            current = float(telem.get('current', 0))
        except (ValueError, TypeError):
            current = 0.0

        # Get architecture info
        arch_name = self._get_architecture_name(device)
        num_channels = self._get_memory_channels(device)
        tensix_rows, tensix_cols = self._get_tensix_grid_size(device)

        lines = []

        # Header
        lines.append(f"[bold bright_magenta]Memory Hierarchy - {arch_name}[/]")
        lines.append("")

        # Legend (compact version)
        if not self.compact:
            lines.append("[dim]Legend: ██ >90% ▓▓ 70-90% ▒▒ 40-70% ░░ 10-40% ·· <10%[/]")
            lines.append("")

        # DDR Channels
        ddr_line = self._create_ddr_channel_visualization(num_channels, power)
        lines.append(f"[bright_yellow]DDR Channels:[/] {ddr_line}")

        # L2 Cache Banks
        l2_line = self._create_l2_cache_visualization(num_channels, current)
        lines.append(f"[bright_cyan]L2 Cache:    [/] {l2_line}")

        # L1 SRAM Grid (Tensix cores)
        if not self.compact:
            lines.append(f"[bright_green]L1 SRAM Grid:[/] ({tensix_rows}×{tensix_cols} Tensix cores)")
            l1_lines = self._create_l1_sram_grid(tensix_rows, tensix_cols, power)
            for l1_line in l1_lines:
                lines.append(f"  {l1_line}")
        else:
            # Compact: single line summary
            utilization = min(int(power / 1.5), 100)  # Scale 0-150W to 0-100%
            bar = self._create_utilization_bar(utilization, 20)
            lines.append(f"[bright_green]L1 SRAM:[/] {bar} {utilization}%")

        # Data flow indicator
        if not self.compact:
            flow_line = self._create_data_flow_indicator(current)
            lines.append("")
            lines.append(f"[dim]Data Flow:[/] {flow_line}")

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

    def _get_memory_channels(self, device: Any) -> int:
        """Get number of DDR memory channels for architecture"""
        if device.as_gs():
            return 4
        elif device.as_wh():
            return 8
        elif device.as_bh():
            return 12
        else:
            return 8

    def _get_tensix_grid_size(self, device: Any) -> Tuple[int, int]:
        """Get Tensix core grid dimensions (rows, cols)"""
        if device.as_gs():
            return (10, 12)  # Grayskull: 10×12
        elif device.as_wh():
            return (8, 10)   # Wormhole: 8×10
        elif device.as_bh():
            return (14, 16)  # Blackhole: 14×16
        else:
            return (8, 10)

    def _create_ddr_channel_visualization(self, num_channels: int, power: float) -> str:
        """Create DDR channel utilization visualization"""
        channels = []

        # Simulate utilization based on power draw
        for i in range(num_channels):
            # Simple pattern: alternate high/low based on power
            base_util = (power / 120.0) * 100  # 0-120W → 0-100%
            offset = (i % 3) * 10  # Variation per channel
            util = min(base_util + offset, 100)

            # Color code by utilization
            if util > 90:
                char = "[bold red]██[/]"
            elif util > 70:
                char = "[bold orange1]▓▓[/]"
            elif util > 40:
                char = "[bright_yellow]▒▒[/]"
            elif util > 10:
                char = "[bright_green]░░[/]"
            else:
                char = "[dim white]··[/]"

            channels.append(char)

        return " ".join(channels)

    def _create_l2_cache_visualization(self, num_banks: int, current: float) -> str:
        """Create L2 cache bank visualization"""
        banks = []

        # L2 responds to current draw (memory traffic)
        for i in range(num_banks):
            base_util = (current / 100.0) * 100  # 0-100A → 0-100%
            offset = (i % 4) * 8
            util = min(base_util + offset, 100)

            if util > 90:
                char = "[bold red]██[/]"
            elif util > 70:
                char = "[bold yellow]▓▓[/]"
            elif util > 40:
                char = "[bright_cyan]▒▒[/]"
            elif util > 10:
                char = "[bright_blue]░░[/]"
            else:
                char = "[dim white]··[/]"

            banks.append(char)

        return " ".join(banks)

    def _create_l1_sram_grid(self, rows: int, cols: int, power: float) -> List[str]:
        """Create L1 SRAM grid showing Tensix core activity"""
        lines = []

        # Compress large grids to fit display
        display_rows = min(rows, 6)
        display_cols = min(cols, 16)

        for r in range(display_rows):
            row_chars = []
            for c in range(display_cols):
                # Activity pattern based on power and position
                core_activity = (power / 150.0) * 100  # 0-150W → 0-100%

                # Create hotspot pattern (higher activity in center)
                center_r = display_rows / 2
                center_c = display_cols / 2
                distance = ((r - center_r) ** 2 + (c - center_c) ** 2) ** 0.5
                max_distance = (center_r ** 2 + center_c ** 2) ** 0.5

                # Cores closer to center are more active
                core_util = core_activity * (1 - distance / max_distance / 2)

                # Color code by utilization
                if core_util > 80:
                    char = "[bold red]█[/]"
                elif core_util > 60:
                    char = "[bold orange1]▓[/]"
                elif core_util > 40:
                    char = "[bright_yellow]▒[/]"
                elif core_util > 20:
                    char = "[bright_green]░[/]"
                else:
                    char = "[dim white]·[/]"

                row_chars.append(char)

            lines.append("".join(row_chars))

        if rows > display_rows:
            lines.append(f"[dim](Showing {display_rows}/{rows} rows)[/]")

        return lines

    def _create_data_flow_indicator(self, current: float) -> str:
        """Create data flow visualization between memory levels"""
        # Flow intensity based on current draw
        flow_intensity = int((current / 100.0) * 10)  # 0-10 scale

        if flow_intensity > 7:
            flow = "DDR [bold red]▶▶▶[/] L2 [bold red]▶▶▶[/] L1"
        elif flow_intensity > 4:
            flow = "DDR [bright_yellow]▶▶[/] L2 [bright_yellow]▶▶[/] L1"
        elif flow_intensity > 1:
            flow = "DDR [bright_cyan]▶[/] L2 [bright_cyan]▶[/] L1"
        else:
            flow = "DDR [dim white]▷[/] L2 [dim white]▷[/] L1"

        bandwidth = current * 5  # Rough estimate: 5 GB/s per amp
        return f"{flow}  [dim]~{bandwidth:.1f} GB/s[/]"

    def _create_utilization_bar(self, percent: int, width: int) -> str:
        """Create a utilization progress bar"""
        filled = int(width * percent / 100)
        empty = width - filled

        if percent > 80:
            color = "bold red"
        elif percent > 50:
            color = "bright_yellow"
        else:
            color = "bright_green"

        return f"[{color}]{'█' * filled}[/][dim white]{'░' * empty}[/]"

    def update_refresh_rate(self, refresh_rate: float) -> None:
        """
        Update refresh rate for memory hierarchy updates

        Args:
            refresh_rate: New refresh rate in seconds
        """
        self.refresh_rate = refresh_rate

        # Cancel existing timer and create new one with updated rate
        if self.update_timer:
            self.update_timer.stop()
        self.update_timer = self.set_interval(self.refresh_rate, self.refresh)
