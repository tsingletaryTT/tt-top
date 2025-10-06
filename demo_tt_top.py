#!/usr/bin/env python3
"""
TT-Top Live Monitor Demo

This demo shows the visual design and functionality of the new TT-Top feature
without requiring actual Tenstorrent hardware. It creates mock data to demonstrate
the three key visual components inspired by htop, Logstalgia, and Orca.
"""

import time
import random
from typing import Dict, List
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.layout import Layout


class MockDevice:
    """Mock Tenstorrent device for demonstration"""
    def __init__(self, device_id: int, device_type: str, board_type: str):
        self.device_id = device_id
        self.device_type = device_type  # "Grayskull", "Wormhole", "Blackhole"
        self.board_type = board_type    # "e75", "n300", "p150a", etc.

        # Initialize with random but realistic values
        self.base_voltage = 0.8 + random.uniform(-0.1, 0.1)
        self.base_current = 10 + random.uniform(-5, 15)
        self.base_temp = 35 + random.uniform(-5, 10)
        self.base_aiclk = 800 + random.uniform(-200, 400)

    def get_telemetry(self) -> Dict:
        """Generate realistic telemetry data with some variation"""
        # Add some realistic fluctuation
        voltage_variation = random.uniform(-0.05, 0.05)
        current_variation = random.uniform(-2, 3)
        temp_variation = random.uniform(-1, 2)
        aiclk_variation = random.uniform(-50, 50)

        voltage = max(0.1, self.base_voltage + voltage_variation)
        current = max(0, self.base_current + current_variation)
        temp = max(20, self.base_temp + temp_variation)
        aiclk = max(100, self.base_aiclk + aiclk_variation)
        power = voltage * current  # Simple power calculation

        return {
            'voltage': f"{voltage:.2f}",
            'current': f"{current:.1f}",
            'power': f"{power:.1f}",
            'asic_temperature': f"{temp:.1f}",
            'aiclk': f"{aiclk:.0f}",
            'heartbeat': str(int(time.time()) % 4)  # Simple heartbeat simulation
        }


class MockTTSMIBackend:
    """Mock backend that simulates the real TTSMIBackend interface"""
    def __init__(self):
        # Create some mock devices
        self.devices = [
            MockDevice(0, "Grayskull", "e75"),
            MockDevice(1, "Wormhole", "n300"),
            MockDevice(2, "Blackhole", "p150a"),
            MockDevice(3, "Wormhole", "n300"),
        ]

        self.device_infos = [
            {'board_type': device.board_type, 'bus_id': f"0000:0{i}:00.0"}
            for i, device in enumerate(self.devices)
        ]

        # Initialize telemetry
        self.update_telem()

    def get_device_name(self, device: MockDevice) -> str:
        return device.device_type

    def update_telem(self):
        """Update telemetry data for all devices"""
        self.device_telemetrys = [device.get_telemetry() for device in self.devices]


def create_chip_grid_demo(backend: MockTTSMIBackend) -> Panel:
    """Create the chip grid visualization demo"""
    grid_lines = []

    grid_lines.append("┌─ TT-TOP: Real-time Hardware Monitor ─┐")
    grid_lines.append("│                                        │")

    for i, device in enumerate(backend.devices):
        device_name = backend.get_device_name(device)
        board_type = backend.device_infos[i].get('board_type', 'Unknown')

        # Get current telemetry for activity indicators
        telem = backend.device_telemetrys[i]
        voltage = float(telem.get('voltage', '0.0'))
        current = float(telem.get('current', '0.0'))
        temp = float(telem.get('asic_temperature', '0.0'))
        power = float(telem.get('power', '0.0'))

        # Create activity symbols based on metrics
        if power > 50:
            activity_symbol = "[bold red]●[/bold red]"  # High activity
        elif power > 20:
            activity_symbol = "[bold yellow]◐[/bold yellow]"  # Moderate activity
        elif power > 5:
            activity_symbol = "[bold green]○[/bold green]"  # Low activity
        else:
            activity_symbol = "[dim]○[/dim]"  # Idle

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

        # Format the chip representation
        chip_line = f"│ [{i:2}] {device_name:10} {activity_symbol} {temp_color}│"
        grid_lines.append(chip_line)

        detail_line = f"│     {board_type:10} {power_bar} {temp:4.1f}°C │"
        grid_lines.append(detail_line)

        if i < len(backend.devices) - 1:
            grid_lines.append("│                                        │")

    grid_lines.append("│                                        │")
    grid_lines.append("│ Legend: ● Active  ○ Idle  ◐ Moderate  │")
    grid_lines.append("│         🔥 Hot    ❄️ Cool   ⚡ High Pwr │")
    grid_lines.append("└────────────────────────────────────────┘")

    return Panel(
        "\n".join(grid_lines),
        title="[bold yellow]Hardware Topology & Activity[/bold yellow]",
        border_style="cyan"
    )


def create_flow_visualization_demo(backend: MockTTSMIBackend, animation_frame: int) -> Panel:
    """Create the data flow visualization demo"""
    flows = []

    flows.append("┌─ Data Flow Streams ────────────────────┐")
    flows.append("│                                        │")

    for i, device in enumerate(backend.devices):
        telem = backend.device_telemetrys[i]
        current = float(telem.get('current', '0.0'))

        # Create flow indicators based on current draw
        flow_intensity = min(int(current / 10), 10)

        # Generate animated flow symbols
        width = 20
        if flow_intensity == 0:
            flow_chars = " " * width
        else:
            flow_pattern = "▶▷▶▷" if flow_intensity > 5 else "▸▹▸▹"
            pattern_len = len(flow_pattern)

            offset = (animation_frame + i * 2) % pattern_len
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

        device_name = backend.get_device_name(device)[:8]
        flow_line = f"│ {device_name:8} │{flow_chars}│ {current:5.1f}A │"
        flows.append(flow_line)

    flows.append("│                                        │")
    flows.append("└────────────────────────────────────────┘")

    return Panel(
        "\n".join(flows),
        title="[bold cyan]Live Data Streams[/bold cyan]",
        border_style="blue"
    )


def create_process_table_demo(backend: MockTTSMIBackend) -> Panel:
    """Create the process table demo"""
    table = Table(show_header=True, header_style="bold magenta")

    table.add_column("ID", width=3, justify="center")
    table.add_column("Device", width=10, justify="left")
    table.add_column("Board", width=8, justify="left")
    table.add_column("Voltage", width=8, justify="right")
    table.add_column("Current", width=8, justify="right")
    table.add_column("Power", width=8, justify="right")
    table.add_column("Temp", width=8, justify="right")
    table.add_column("AICLK", width=8, justify="right")
    table.add_column("Status", width=10, justify="center")

    # Sort devices by power consumption (descending)
    device_data = []
    for i, device in enumerate(backend.devices):
        device_name = backend.get_device_name(device)
        board_type = backend.device_infos[i].get('board_type', 'N/A')[:8]
        telem = backend.device_telemetrys[i]

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

    for data in device_data:
        i, device_name, board_type, voltage, current, power, temp, aiclk, status = data
        table.add_row(
            str(i),
            device_name[:10],
            board_type,
            f"{voltage:6.2f}V",
            f"{current:6.1f}A",
            f"[bold red]{power:6.1f}W[/bold red]" if power > 50 else f"{power:6.1f}W",
            f"[bold red]{temp:5.1f}°C[/bold red]" if temp > 75 else f"{temp:5.1f}°C",
            f"{aiclk:6}MHz",
            status
        )

    return Panel(
        table,
        title="[bold green]Live Hardware Processes & Activity[/bold green]",
        border_style="green"
    )


def main():
    """Main demo function"""
    console = Console()
    backend = MockTTSMIBackend()

    console.print("\n[bold blue]TT-SMI Live Monitor (TT-Top) Demo[/bold blue]")
    console.print("[dim]Press Ctrl+C to exit[/dim]\n")

    animation_frame = 0

    try:
        with Live(console=console, refresh_per_second=4) as live:
            while True:
                # Update telemetry data
                backend.update_telem()

                # Create layout
                layout = Layout()
                layout.split_column(
                    Layout(name="top", ratio=3),
                    Layout(name="bottom", ratio=2)
                )

                # Split top section horizontally
                layout["top"].split_row(
                    Layout(create_chip_grid_demo(backend), name="grid"),
                    Layout(create_flow_visualization_demo(backend, animation_frame), name="flow")
                )

                # Bottom section for process table
                layout["bottom"].update(create_process_table_demo(backend))

                # Update display
                live.update(layout)

                animation_frame += 1
                time.sleep(0.25)  # 4 FPS

    except KeyboardInterrupt:
        console.print("\n[bold yellow]Demo stopped.[/bold yellow]")


if __name__ == "__main__":
    main()