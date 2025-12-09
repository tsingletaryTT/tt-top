#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Hero Cursor Hardware Visualization

Roguelike-inspired hardware monitor where a "hero cursor" (▶) moves between
devices to show active workload location. Each device is isolated in its own
container to prevent Rich markup errors from propagating.

Design Philosophy:
- Markup isolation: Each device has independent rendering
- Visual clarity: Hero shows WHERE activity is happening
- Roguelike aesthetic: Like @ moving in classic roguelikes
- Error containment: Markup issues localized to individual devices
"""

import time
import math
from typing import Any, List, Tuple, Optional
from textual.app import ComposeResult
from textual.containers import Grid, Container, VerticalScroll
from textual.widgets import Static
from textual.binding import Binding


class DeviceVisualizationCard(Static):
    """
    Individual device visualization card with isolated markup rendering

    Shows:
    - Device index and architecture
    - Activity pattern (dots/stars based on power)
    - Current telemetry readings
    - Hero cursor (▶) when device is most active
    """

    DEFAULT_CSS = """
    DeviceVisualizationCard {
        border: round $primary 50%;
        padding: 1;
        height: auto;
        width: 1fr;
        margin: 0 1;
        background: $surface;
    }

    DeviceVisualizationCard.hero-active {
        border: round $accent;
        background: $panel;
    }
    """

    def __init__(self, backend: Any, device_idx: int, **kwargs):
        """
        Initialize device visualization card

        Args:
            backend: JSONBackendAdapter or compatible backend
            device_idx: Device index in backend.devices
            **kwargs: Additional arguments for Static widget
        """
        super().__init__(**kwargs)
        self.backend = backend
        self.device_idx = device_idx
        self.is_hero_location = False

    def render(self) -> str:
        """
        Render device visualization with isolated markup

        Returns plain text with minimal Rich markup to avoid errors.
        Each device renders independently - errors don't propagate.
        """
        try:
            device = self.backend.devices[self.device_idx]
            telem = self.backend.device_telemetrys[self.device_idx]

            # Safe float conversion
            try:
                power = float(telem.get('power', 0))
                current = float(telem.get('current', 0))
                temp = float(telem.get('asic_temperature', 0))
            except (ValueError, TypeError):
                power = current = temp = 0.0

            # Get architecture name
            if device.as_gs():
                arch = "GS"
            elif device.as_wh():
                arch = "WH"
            elif device.as_bh():
                arch = "BH"
            else:
                arch = "??"

            lines = []

            # Header with hero cursor if active
            if self.is_hero_location:
                lines.append(f"[bold bright_yellow]▶ Device {self.device_idx} ({arch}) ◀[/]")
            else:
                lines.append(f"[dim]Device {self.device_idx} ({arch})[/]")

            # Activity visualization (3x3 grid of dots/stars)
            # More power = more filled dots
            activity_level = min(int((power / 30.0) * 9), 9)  # 0-30W mapped to 0-9 dots

            activity_chars = []
            for i in range(9):
                if i < activity_level:
                    activity_chars.append('●')
                else:
                    activity_chars.append('○')

            # 3x3 grid
            lines.append("")
            lines.append(f"  {activity_chars[0]} {activity_chars[1]} {activity_chars[2]}")
            lines.append(f"  {activity_chars[3]} {activity_chars[4]} {activity_chars[5]}")
            lines.append(f"  {activity_chars[6]} {activity_chars[7]} {activity_chars[8]}")

            # Telemetry readings
            lines.append("")
            lines.append(f"[bright_yellow]{power:5.1f}W[/]")
            lines.append(f"[bright_green]{current:5.1f}A[/]")
            lines.append(f"[bright_cyan]{temp:4.1f}°C[/]")

            return '\n'.join(lines)

        except Exception as e:
            # Error in THIS device only - doesn't affect others
            return f"[red]Device {self.device_idx}\\nError: {str(e)[:30]}[/]"


class HeroCursor:
    """
    Hero cursor that tracks and moves to the most active device

    Like the @ symbol in roguelikes, this shows where the "action" is happening.
    Moves based on real hardware activity (power/current changes).
    """

    def __init__(self, num_devices: int):
        """Initialize hero cursor"""
        self.num_devices = num_devices
        self.current_device = 0  # Hero starts at device 0
        self.previous_power = [0.0] * num_devices
        self.activity_score = [0.0] * num_devices

    def update_position(self, backend: Any) -> int:
        """
        Update hero position based on hardware activity

        Args:
            backend: JSONBackendAdapter with current telemetry

        Returns:
            Device index where hero should be located
        """
        # Calculate activity score for each device
        for i in range(self.num_devices):
            try:
                telem = backend.device_telemetrys[i]
                power = float(telem.get('power', 0))
                current = float(telem.get('current', 0))

                # Activity = power change + current level
                power_change = abs(power - self.previous_power[i])
                self.activity_score[i] = power_change * 2 + current * 0.1

                self.previous_power[i] = power

            except:
                self.activity_score[i] = 0.0

        # Find device with highest activity
        if max(self.activity_score) > 0:
            self.current_device = self.activity_score.index(max(self.activity_score))

        return self.current_device


class HeroVisualizationDisplay(Container):
    """
    Hardware visualization with hero cursor showing active device

    Uses Grid layout with isolated device cards. Hero cursor (▶) appears on
    the most active device based on real telemetry changes.

    Benefits:
    - No markup bleeding between devices
    - Clear visual indication of activity location
    - Roguelike aesthetic (nostalgic, game-like)
    - Easy debugging (can identify problematic device)
    """

    DEFAULT_CSS = """
    HeroVisualizationDisplay {
        width: 100%;
        height: 100%;
        background: $surface;
    }

    HeroVisualizationDisplay VerticalScroll {
        width: 100%;
        height: 100%;
        overflow-y: auto;
    }

    #hero_header {
        width: 100%;
        padding: 1 2;
        background: $panel;
        border: solid $accent;
    }

    #device_grid {
        width: 100%;
        padding: 2;
        grid-gutter: 1;
    }

    #hero_footer {
        width: 100%;
        padding: 1 2;
        background: $panel;
    }
    """

    BINDINGS = [
        Binding("v", "exit_visualization", "Exit Visualization", show=True),
        Binding("escape", "exit_visualization", "Exit Visualization", show=False),
    ]

    def __init__(self, backend: Any, refresh_rate: float = 0.05, **kwargs):
        """
        Initialize hero visualization display

        Args:
            backend: JSONBackendAdapter or compatible backend
            refresh_rate: Display refresh rate in seconds
            **kwargs: Additional arguments for Container
        """
        super().__init__(**kwargs)
        self.backend = backend
        self.refresh_rate = refresh_rate
        self.update_timer = None

        # Hero cursor tracker
        num_devices = len(backend.devices) if backend.devices else 1
        self.hero = HeroCursor(num_devices)

        # Device cards
        self.device_cards: List[DeviceVisualizationCard] = []

    def compose(self) -> ComposeResult:
        """Compose the hero visualization layout"""
        # Store grid configuration for on_mount
        num_devices = len(self.backend.devices) if self.backend.devices else 1

        # Determine grid columns
        if num_devices <= 2:
            self.grid_columns = num_devices
        elif num_devices <= 4:
            self.grid_columns = 2
        elif num_devices <= 9:
            self.grid_columns = 3
        else:
            self.grid_columns = 4

        self.grid_rows = (num_devices + self.grid_columns - 1) // self.grid_columns

        with VerticalScroll():
            # Header
            yield Static(
                "[bold bright_magenta]HARDWARE ACTIVITY MONITOR[/]\n"
                "[dim]Hero cursor (▶) shows most active device[/]",
                id="hero_header"
            )

            # Device grid
            with Grid(id="device_grid") as grid:
                # Create device cards
                for i in range(num_devices):
                    card = DeviceVisualizationCard(
                        backend=self.backend,
                        device_idx=i,
                        id=f"device_{i}"
                    )
                    self.device_cards.append(card)
                    yield card

            # Footer legend
            yield Static(
                "\n[dim]Legend: ▶ Hero (active) │ ● Activity │ ○ Idle[/]\n"
                "[dim]Press 'v' to exit visualization[/]",
                id="hero_footer"
            )

    def on_mount(self) -> None:
        """Start animation updates and apply grid styling"""
        # Apply grid styling after mount
        try:
            grid = self.query_one("#device_grid", Grid)
            grid.styles.grid_size_columns = self.grid_columns
            grid.styles.grid_size_rows = self.grid_rows
        except:
            pass  # Silently continue if grid not found

        # Start hero cursor updates
        self.update_timer = self.set_interval(self.refresh_rate, self._update_hero_display)

    def _update_hero_display(self) -> None:
        """Update hero position and refresh device displays"""
        try:
            # Update backend telemetry
            self.backend.update_telem()

            # Update hero cursor position
            hero_device = self.hero.update_position(self.backend)

            # Update device cards with hero location
            for i, card in enumerate(self.device_cards):
                card.is_hero_location = (i == hero_device)

                # Add/remove hero-active CSS class
                if card.is_hero_location:
                    card.add_class("hero-active")
                else:
                    card.remove_class("hero-active")

                card.refresh()

            # Update header with hero location
            header = self.query_one("#hero_header", Static)
            device = self.backend.devices[hero_device]
            arch_name = "Grayskull" if device.as_gs() else "Wormhole" if device.as_wh() else "Blackhole" if device.as_bh() else "Unknown"

            header.update(
                f"[bold bright_magenta]HARDWARE ACTIVITY MONITOR[/]\n"
                f"[bright_yellow]Hero Location:[/] Device {hero_device} ({arch_name})"
            )

        except Exception as e:
            # Gracefully handle errors
            pass

    def update_refresh_rate(self, refresh_rate: float) -> None:
        """
        Update refresh rate dynamically

        Args:
            refresh_rate: New refresh rate in seconds
        """
        self.refresh_rate = refresh_rate

        if self.update_timer:
            self.update_timer.stop()
        self.update_timer = self.set_interval(self.refresh_rate, self._update_hero_display)

    def action_exit_visualization(self) -> None:
        """Exit visualization mode"""
        self.app.action_toggle_visualization()
