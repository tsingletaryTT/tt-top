# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-Top Live Monitor Widget

A real-time hardware monitoring display inspired by htop, Logstalgia, and Orca.
Provides visual representation of Tenstorrent hardware activity with:
- Grid-based chip topology visualization
- Real-time activity indicators
- Process/activity listings
- Animated data flow representations
"""

import time
import random
from typing import Dict, List, Optional, Tuple
from textual.widget import Widget
from textual.widgets import Static, ScrollView, DataTable
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.renderables.gradient import LinearGradient
from rich.text import Text
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.align import Align
from textual.app import ComposeResult
from tt_smi.tt_smi_backend import TTSMIBackend
from tt_smi import constants


class ChipGridVisualizer(Widget):
    """
    Grid-based visualization of chip topology and activity, inspired by Orca's
    character-based programming environment.
    """

    activity_data = reactive({})

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.last_update = time.time()
        self.activity_history = []
        self.animation_frame = 0

    def render(self) -> Panel:
        """Render the chip grid with real-time activity indicators"""
        console = Console(width=60, height=20, legacy_windows=False)

        # Create the grid representation
        grid_content = self._create_chip_grid()

        return Panel(
            grid_content,
            title="[bold yellow]Hardware Topology & Activity[/bold yellow]",
            border_style="cyan",
            padding=(1, 2)
        )

    def _create_chip_grid(self) -> str:
        """Create ASCII art representation of chips and their activity"""
        grid_lines = []

        # Header showing overall system status
        grid_lines.append("┌─ TT-TOP: Real-time Hardware Monitor ─┐")
        grid_lines.append("│                                        │")

        # Display each chip in a visual grid
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)
            board_type = self.backend.device_infos[i].get('board_type', 'Unknown')

            # Get current telemetry for activity indicators
            telem = self.backend.device_telemetrys[i]
            voltage = float(telem.get('voltage', '0.0'))
            current = float(telem.get('current', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))
            power = float(telem.get('power', '0.0'))

            # Create activity symbols based on metrics
            activity_symbol = self._get_activity_symbol(voltage, current, temp, power)
            temp_color = self._get_temp_color(temp)
            power_bar = self._get_power_bar(power)

            # Format the chip representation
            chip_line = f"│ [{i:2}] {device_name:10} {activity_symbol} {temp_color}│"
            grid_lines.append(chip_line)

            # Add a sub-line with detailed metrics in grid style
            detail_line = f"│     {board_type:10} {power_bar} {temp:4.1f}°C │"
            grid_lines.append(detail_line)

            if i < len(self.backend.devices) - 1:
                grid_lines.append("│                                        │")

        # Footer with legend
        grid_lines.append("│                                        │")
        grid_lines.append("│ Legend: ● Active  ○ Idle  ◐ Moderate  │")
        grid_lines.append("│         🔥 Hot    ❄️ Cool   ⚡ High Pwr │")
        grid_lines.append("└────────────────────────────────────────┘")

        return "\n".join(grid_lines)

    def _get_activity_symbol(self, voltage: float, current: float, temp: float, power: float) -> str:
        """Generate activity symbol based on current metrics"""
        # Determine activity level based on power consumption
        if power > 50:
            return "[bold red]●[/bold red]"  # High activity
        elif power > 20:
            return "[bold yellow]◐[/bold yellow]"  # Moderate activity
        elif power > 5:
            return "[bold green]○[/bold green]"  # Low activity
        else:
            return "[dim]○[/dim]"  # Idle

    def _get_temp_color(self, temp: float) -> str:
        """Get temperature indicator with color coding"""
        if temp > 80:
            return "[bold red]🔥[/bold red]"
        elif temp > 60:
            return "[bold yellow]🌡️[/bold yellow]"
        elif temp > 40:
            return "[bold green]🌡️[/bold green]"
        else:
            return "[bold cyan]❄️[/bold cyan]"

    def _get_power_bar(self, power: float) -> str:
        """Create a visual power consumption bar"""
        bar_length = 8
        filled = int((power / 100) * bar_length)  # Assume 100W max for scaling
        bar = "█" * filled + "░" * (bar_length - filled)

        if power > 75:
            return f"[bold red]{bar}[/bold red]"
        elif power > 50:
            return f"[bold yellow]{bar}[/bold yellow]"
        else:
            return f"[bold green]{bar}[/bold green]"


class ActivityFlowWidget(Widget):
    """
    Data flow visualization inspired by Logstalgia's animated request visualization
    """

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.particles = []
        self.animation_frame = 0

    def render(self) -> Panel:
        """Render flowing data streams and activity indicators"""
        content = self._create_flow_visualization()

        return Panel(
            content,
            title="[bold cyan]Live Data Streams[/bold cyan]",
            border_style="blue",
            padding=(1, 2)
        )

    def _create_flow_visualization(self) -> str:
        """Create animated flow representation"""
        flows = []

        flows.append("┌─ Data Flow Streams ────────────────────┐")
        flows.append("│                                        │")

        for i, device in enumerate(self.backend.devices):
            telem = self.backend.device_telemetrys[i]
            current = float(telem.get('current', '0.0'))

            # Create flow indicators based on current draw
            flow_intensity = min(int(current / 10), 10)  # Scale to 0-10

            # Generate animated flow symbols
            flow_chars = self._generate_flow_chars(flow_intensity, i)
            device_name = self.backend.get_device_name(device)[:8]

            flow_line = f"│ {device_name:8} │{flow_chars}│ {current:5.1f}A │"
            flows.append(flow_line)

        flows.append("│                                        │")
        flows.append("└────────────────────────────────────────┘")

        return "\n".join(flows)

    def _generate_flow_chars(self, intensity: int, device_idx: int) -> str:
        """Generate animated flow characters based on intensity"""
        width = 20

        if intensity == 0:
            return " " * width

        # Create animated flow based on intensity and animation frame
        flow_pattern = "▶▷▶▷" if intensity > 5 else "▸▹▸▹"
        pattern_len = len(flow_pattern)

        # Animate by shifting pattern based on frame and device offset
        offset = (self.animation_frame + device_idx * 2) % pattern_len
        extended_pattern = (flow_pattern * (width // pattern_len + 2))[offset:offset + width]

        # Apply intensity-based visibility
        result = ""
        for i, char in enumerate(extended_pattern):
            if i % (11 - intensity) == 0:  # Show more characters for higher intensity
                if intensity > 7:
                    result += f"[bold red]{char}[/bold red]"
                elif intensity > 4:
                    result += f"[bold yellow]{char}[/bold yellow]"
                else:
                    result += f"[bold green]{char}[/bold green]"
            else:
                result += " "

        return result[:width]


class LiveProcessTable(Widget):
    """
    Process/activity table similar to htop's process listing
    """

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.sort_column = "Power"
        self.sort_descending = True

    def render(self) -> Panel:
        """Render the live process/activity table"""
        table = self._create_process_table()

        return Panel(
            table,
            title="[bold green]Live Hardware Processes & Activity[/bold green]",
            border_style="green",
            padding=(1, 1)
        )

    def _create_process_table(self) -> Table:
        """Create a table showing live hardware activity similar to htop"""
        table = Table(show_header=True, header_style="bold magenta")

        # Define columns similar to htop but for hardware
        table.add_column("ID", width=3, justify="center")
        table.add_column("Device", width=10, justify="left")
        table.add_column("Board", width=8, justify="left")
        table.add_column("Voltage", width=8, justify="right")
        table.add_column("Current", width=8, justify="right")
        table.add_column("Power", width=8, justify="right")
        table.add_column("Temp", width=8, justify="right")
        table.add_column("AICLK", width=8, justify="right")
        table.add_column("Status", width=10, justify="center")

        # Add rows for each device
        device_data = []
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)
            board_type = self.backend.device_infos[i].get('board_type', 'N/A')[:8]
            telem = self.backend.device_telemetrys[i]

            voltage = float(telem.get('voltage', '0.0'))
            current = float(telem.get('current', '0.0'))
            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))
            aiclk = int(float(telem.get('aiclk', '0')))

            # Determine status based on activity
            status = self._get_device_status(voltage, current, temp, power)

            device_data.append({
                'id': i,
                'device': device_name,
                'board': board_type,
                'voltage': voltage,
                'current': current,
                'power': power,
                'temp': temp,
                'aiclk': aiclk,
                'status': status
            })

        # Sort by the selected column
        if self.sort_column.lower() in ['power', 'voltage', 'current', 'temp', 'aiclk']:
            device_data.sort(
                key=lambda x: x[self.sort_column.lower()],
                reverse=self.sort_descending
            )

        # Add sorted rows to table
        for data in device_data:
            table.add_row(
                str(data['id']),
                data['device'][:10],
                data['board'],
                f"{data['voltage']:6.2f}V",
                f"{data['current']:6.1f}A",
                f"[bold red]{data['power']:6.1f}W[/bold red]" if data['power'] > 50 else f"{data['power']:6.1f}W",
                f"[bold red]{data['temp']:5.1f}°C[/bold red]" if data['temp'] > 75 else f"{data['temp']:5.1f}°C",
                f"{data['aiclk']:6}MHz",
                data['status']
            )

        return table

    def _get_device_status(self, voltage: float, current: float, temp: float, power: float) -> str:
        """Determine device status based on metrics"""
        if temp > 85:
            return "[bold red]CRITICAL[/bold red]"
        elif temp > 75:
            return "[bold yellow]HOT[/bold yellow]"
        elif power > 75:
            return "[bold yellow]HIGH LOAD[/bold yellow]"
        elif power > 25:
            return "[bold green]ACTIVE[/bold green]"
        elif power > 5:
            return "[bold cyan]IDLE[/bold cyan]"
        else:
            return "[dim]SLEEP[/dim]"


class TTLiveMonitor(Container):
    """
    Main container for the TT-Top live monitoring interface.
    Combines grid visualization, flow indicators, and process table.
    """

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.update_interval = constants.GUI_INTERVAL_TIME
        self.animation_timer = 0

    def compose(self) -> ComposeResult:
        """Compose the live monitor layout"""
        with Vertical():
            # Top section: Grid visualization and flow indicators side by side
            with Horizontal(id="top_section"):
                yield ChipGridVisualizer(backend=self.backend, id="chip_grid")
                yield ActivityFlowWidget(backend=self.backend, id="activity_flow")

            # Bottom section: Process table
            yield LiveProcessTable(backend=self.backend, id="process_table")

    def on_mount(self) -> None:
        """Set up the live monitor when mounted"""
        # Set up automatic updates
        self.set_interval(self.update_interval, self.update_display)

    def update_display(self) -> None:
        """Update all components of the live monitor"""
        try:
            # Update the backend telemetry data
            self.backend.update_telem()

            # Refresh all child widgets
            chip_grid = self.query_one("#chip_grid", ChipGridVisualizer)
            activity_flow = self.query_one("#activity_flow", ActivityFlowWidget)
            process_table = self.query_one("#process_table", LiveProcessTable)

            # Increment animation frame for smooth animations
            self.animation_timer += 1
            activity_flow.animation_frame = self.animation_timer

            # Trigger re-render of components
            chip_grid.refresh()
            activity_flow.refresh()
            process_table.refresh()

        except Exception as e:
            # Handle any errors gracefully to avoid crashing the UI
            pass