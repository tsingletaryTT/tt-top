# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-Top Live Monitor Widget (Cross-compatible version)

A real-time hardware monitoring display inspired by htop, Logstalgia, and Orca.
Simplified for compatibility across different Textual versions.
"""

import time
from typing import Dict, List
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Container
from textual.app import ComposeResult
from tt_smi.tt_smi_backend import TTSMIBackend
from tt_smi import constants


class TTTopDisplay(Static):
    """
    Single static widget that renders all TT-Top components.
    More compatible across Textual versions.
    """

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.animation_frame = 0

    def on_mount(self) -> None:
        """Set up periodic updates when mounted"""
        self.set_interval(constants.GUI_INTERVAL_TIME, self._update_display)

    def _update_display(self) -> None:
        """Update the display with current data"""
        try:
            # Update backend telemetry
            self.backend.update_telem()
            self.animation_frame += 1

            # Generate the complete display
            content = self._render_complete_display()
            self.update(content)

        except Exception as e:
            # Handle errors gracefully
            self.update(f"[red]Error updating display: {e}[/red]")

    def _render_complete_display(self) -> str:
        """Render the complete TT-Top display as a single string"""
        lines = []

        # Header
        lines.append("[bold blue]TT-TOP: Real-time Hardware Monitor[/bold blue]")
        lines.append("")

        # Top section: Grid and Flow side by side
        grid_panel = self._create_chip_grid()
        flow_panel = self._create_flow_visualization()

        # Combine panels horizontally
        lines.extend(self._combine_panels_horizontally(grid_panel, flow_panel))
        lines.append("")

        # Bottom section: Process table
        table_content = self._create_process_table()
        lines.append(table_content)

        return "\n".join(lines)

    def _create_chip_grid(self) -> List[str]:
        """Create the chip grid visualization"""
        grid_lines = []

        grid_lines.append("┌─ Hardware Topology & Activity ────────┐")
        grid_lines.append("│                                        │")

        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)
            board_type = self.backend.device_infos[i].get('board_type', 'Unknown')

            # Get current telemetry
            telem = self.backend.device_telemetrys[i]
            voltage = float(telem.get('voltage', '0.0'))
            current = float(telem.get('current', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))
            power = float(telem.get('power', '0.0'))

            # Activity symbol
            if power > 50:
                activity_symbol = "[bold red]●[/bold red]"
            elif power > 20:
                activity_symbol = "[bold yellow]◐[/bold yellow]"
            elif power > 5:
                activity_symbol = "[bold green]○[/bold green]"
            else:
                activity_symbol = "[dim]○[/dim]"

            # Temperature indicator
            if temp > 80:
                temp_color = "[bold red]🔥[/bold red]"
            elif temp > 60:
                temp_color = "[bold yellow]🌡️[/bold yellow]"
            elif temp > 40:
                temp_color = "[bold green]🌡️[/bold green]"
            else:
                temp_color = "[bold cyan]❄️[/bold cyan]"

            # Power bar
            bar_length = 8
            filled = int((power / 100) * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)
            if power > 75:
                power_bar = f"[bold red]{bar}[/bold red]"
            elif power > 50:
                power_bar = f"[bold yellow]{bar}[/bold yellow]"
            else:
                power_bar = f"[bold green]{bar}[/bold green]"

            # Format lines
            chip_line = f"│ [{i:2}] {device_name:10} {activity_symbol} {temp_color}│"
            detail_line = f"│     {board_type:10} {power_bar} {temp:4.1f}°C │"

            grid_lines.append(chip_line)
            grid_lines.append(detail_line)

            if i < len(self.backend.devices) - 1:
                grid_lines.append("│                                        │")

        grid_lines.append("│                                        │")
        grid_lines.append("│ Legend: ● Active  ○ Idle  ◐ Moderate  │")
        grid_lines.append("│         🔥 Hot    ❄️ Cool   ⚡ High Pwr │")
        grid_lines.append("└────────────────────────────────────────┘")

        return grid_lines

    def _create_flow_visualization(self) -> List[str]:
        """Create the flow visualization"""
        flows = []

        flows.append("┌─ Live Data Streams ────────────────────┐")
        flows.append("│                                        │")

        for i, device in enumerate(self.backend.devices):
            telem = self.backend.device_telemetrys[i]
            current = float(telem.get('current', '0.0'))

            # Create flow indicators
            flow_intensity = min(int(current / 10), 10)

            # Generate animated flow
            width = 20
            if flow_intensity == 0:
                flow_chars = " " * width
            else:
                flow_pattern = "▶▷▶▷" if flow_intensity > 5 else "▸▹▸▹"
                pattern_len = len(flow_pattern)

                offset = (self.animation_frame + i * 2) % pattern_len
                extended_pattern = (flow_pattern * (width // pattern_len + 2))[offset:offset + width]

                result = ""
                for j, char in enumerate(extended_pattern):
                    if j % (11 - flow_intensity) == 0:
                        if flow_intensity > 7:
                            result += f"[bold red]{char}[/bold red]"
                        elif flow_intensity > 4:
                            result += f"[bold yellow]{char}[/bold yellow]"
                        else:
                            result += f"[bold green]{char}[/bold green]"
                    else:
                        result += " "
                flow_chars = result[:width]

            device_name = self.backend.get_device_name(device)[:8]
            flow_line = f"│ {device_name:8} │{flow_chars}│ {current:5.1f}A │"
            flows.append(flow_line)

        flows.append("│                                        │")
        flows.append("└────────────────────────────────────────┘")

        return flows

    def _combine_panels_horizontally(self, left_panel: List[str], right_panel: List[str]) -> List[str]:
        """Combine two panels horizontally"""
        combined = []
        max_lines = max(len(left_panel), len(right_panel))

        for i in range(max_lines):
            left_line = left_panel[i] if i < len(left_panel) else " " * 42
            right_line = right_panel[i] if i < len(right_panel) else " " * 42
            combined.append(f"{left_line}  {right_line}")

        return combined

    def _create_process_table(self) -> str:
        """Create the process table as a formatted string"""
        lines = []

        lines.append("┌─ Live Hardware Processes & Activity ──────────────────────────────────────────────┐")
        lines.append("│ ID │ Device     │ Board  │ Voltage │ Current │ Power   │ Temp    │ AICLK   │ Status   │")
        lines.append("├────┼────────────┼────────┼─────────┼─────────┼─────────┼─────────┼─────────┼──────────┤")

        # Create device data and sort by power
        device_data = []
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)
            board_type = self.backend.device_infos[i].get('board_type', 'N/A')[:6]
            telem = self.backend.device_telemetrys[i]

            voltage = float(telem.get('voltage', '0.0'))
            current = float(telem.get('current', '0.0'))
            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))
            aiclk = int(float(telem.get('aiclk', '0')))

            # Determine status
            if temp > 85:
                status = "[bold red]CRITICAL[/bold red]"
            elif temp > 75:
                status = "[bold yellow]HOT[/bold yellow]"
            elif power > 75:
                status = "[bold yellow]HIGH LOAD[/bold yellow]"
            elif power > 25:
                status = "[bold green]ACTIVE[/bold green]"
            elif power > 5:
                status = "[bold cyan]IDLE[/bold cyan]"
            else:
                status = "[dim]SLEEP[/dim]"

            device_data.append((i, device_name, board_type, voltage, current, power, temp, aiclk, status))

        # Sort by power consumption
        device_data.sort(key=lambda x: x[5], reverse=True)

        # Add rows
        for data in device_data:
            i, device_name, board_type, voltage, current, power, temp, aiclk, status = data

            power_str = f"[bold red]{power:6.1f}W[/bold red]" if power > 50 else f"{power:6.1f}W"
            temp_str = f"[bold red]{temp:5.1f}°C[/bold red]" if temp > 75 else f"{temp:5.1f}°C"

            line = f"│ {i:2} │ {device_name[:10]:10} │ {board_type:6} │ {voltage:6.2f}V │ {current:6.1f}A │ {power_str:>8} │ {temp_str:>8} │ {aiclk:6}MHz │ {status:>9} │"
            lines.append(line)

        lines.append("└────┴────────────┴────────┴─────────┴─────────┴─────────┴─────────┴─────────┴──────────┘")

        return "\n".join(lines)


class TTLiveMonitor(Container):
    """
    Simplified container for the TT-Top live monitoring interface.
    More compatible across Textual versions.
    """

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend

    def compose(self) -> ComposeResult:
        """Compose the live monitor layout"""
        yield TTTopDisplay(backend=self.backend, id="tt_top_display")