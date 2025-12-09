#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Hero Cursor Hardware Visualization with Conway's Game of Life

Roguelike-inspired hardware monitor where a "hero cursor" (▶) moves between
devices to show active workload location. Each device runs Conway's Game of Life
simulation driven by real hardware telemetry - more activity = faster simulation,
more cell births, more color intensity.

Design Philosophy:
- Markup isolation: Each device has independent rendering
- Visual clarity: Hero shows WHERE activity is happening
- Living simulation: Conway's Game of Life driven by hardware state
- Hardware-responsive: Simulation speed, density, colors reflect real telemetry
- Error containment: Markup issues localized to individual devices
"""

import time
import math
import random
from typing import Any, List, Tuple, Optional
from textual.app import ComposeResult
from textual.containers import Grid, Container, VerticalScroll
from textual.widgets import Static
from textual.binding import Binding


class ConwayGameOfLife:
    """
    Conway's Game of Life simulation driven by hardware telemetry

    Rules (modified for hardware responsiveness):
    - Standard Conway rules for cell survival/birth
    - Simulation speed based on power consumption
    - Cell birth probability based on current draw
    - Cell colors based on temperature (blue→cyan→yellow→red)
    - Random seeding on power spikes
    """

    def __init__(self, width: int = 30, height: int = 15):
        """Initialize Game of Life grid"""
        self.width = width
        self.height = height
        self.grid = [[False for _ in range(width)] for _ in range(height)]
        self.age = [[0 for _ in range(width)] for _ in range(height)]  # Track cell age for colors
        self.generation = 0

    def seed_random(self, density: float = 0.3):
        """Seed grid with random cells"""
        for y in range(self.height):
            for x in range(self.width):
                if random.random() < density:
                    self.grid[y][x] = True
                    self.age[y][x] = 0

    def seed_glider(self, x: int, y: int):
        """Seed a glider pattern (classic Conway shape)"""
        pattern = [
            [False, True, False],
            [False, False, True],
            [True, True, True]
        ]
        for dy, row in enumerate(pattern):
            for dx, cell in enumerate(row):
                ny, nx = (y + dy) % self.height, (x + dx) % self.width
                self.grid[ny][nx] = cell
                if cell:
                    self.age[ny][nx] = 0

    def step(self, activity_boost: float = 0.0):
        """
        Advance simulation by one generation

        Args:
            activity_boost: 0.0-1.0, increases birth probability based on hardware activity
        """
        new_grid = [[False for _ in range(self.width)] for _ in range(self.height)]
        new_age = [[0 for _ in range(self.width)] for _ in range(self.height)]

        for y in range(self.height):
            for x in range(self.width):
                # Count live neighbors
                neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dy == 0 and dx == 0:
                            continue
                        ny, nx = (y + dy) % self.height, (x + dx) % self.width
                        if self.grid[ny][nx]:
                            neighbors += 1

                # Conway's rules (modified with activity boost)
                if self.grid[y][x]:
                    # Cell is alive
                    if neighbors in [2, 3]:
                        new_grid[y][x] = True
                        new_age[y][x] = self.age[y][x] + 1  # Age increases
                else:
                    # Cell is dead
                    birth_threshold = 3
                    # Activity boost increases chance of birth with 2 neighbors
                    if neighbors == birth_threshold or (neighbors == 2 and random.random() < activity_boost):
                        new_grid[y][x] = True
                        new_age[y][x] = 0

        self.grid = new_grid
        self.age = new_age
        self.generation += 1

    def render_colorful(self, temp: float, hero_location: bool = False) -> str:
        """
        Render Game of Life grid with hardware-responsive colors

        Args:
            temp: Temperature in Celsius (affects cell colors)
            hero_location: If True, add hero cursor indicator

        Returns:
            Rich-formatted string with colored cells
        """
        lines = []

        # Color palette based on temperature
        if temp > 75:
            alive_colors = ['red', 'orange1', 'bright_yellow']
        elif temp > 60:
            alive_colors = ['orange1', 'bright_yellow', 'yellow']
        elif temp > 45:
            alive_colors = ['bright_yellow', 'bright_green', 'bright_cyan']
        else:
            alive_colors = ['bright_cyan', 'bright_blue', 'cyan']

        for y in range(self.height):
            line_parts = []
            for x in range(self.width):
                if self.grid[y][x]:
                    # Alive cell - color based on age and temperature
                    age = min(self.age[y][x], len(alive_colors) - 1)
                    color = alive_colors[age % len(alive_colors)]

                    # Use different characters for visual variety
                    if self.age[y][x] > 5:
                        char = '█'  # Old cells
                    elif self.age[y][x] > 2:
                        char = '●'  # Middle-aged cells
                    else:
                        char = '○'  # Young cells

                    line_parts.append(f'[{color}]{char}[/{color}]')
                else:
                    # Dead cell
                    line_parts.append('[dim white]·[/]')

            lines.append(''.join(line_parts))

        # Add hero indicator at top if this is hero location
        if hero_location:
            hero_line = '[bold bright_yellow]' + '▶' * self.width + '[/]'
            lines.insert(0, hero_line)

        return '\n'.join(lines)


class DeviceVisualizationCard(Static):
    """
    Individual device visualization card with Conway's Game of Life

    Shows:
    - Device index and architecture
    - Conway's Game of Life simulation (hardware-responsive)
    - Current telemetry readings
    - Hero cursor (▶) when device is most active

    Hardware Response:
    - Simulation speed: Based on power consumption
    - Cell birth rate: Based on current draw
    - Colors: Based on temperature (blue→cyan→yellow→red)
    - Pattern seeding: Power spikes trigger glider injection
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

    def __init__(self, backend: Any, device_idx: int, grid_width: int = 30, grid_height: int = 15, **kwargs):
        """
        Initialize device visualization card

        Args:
            backend: JSONBackendAdapter or compatible backend
            device_idx: Device index in backend.devices
            grid_width: Width of Game of Life grid
            grid_height: Height of Game of Life grid
            **kwargs: Additional arguments for Static widget
        """
        super().__init__(**kwargs)
        self.backend = backend
        self.device_idx = device_idx
        self.is_hero_location = False

        # Conway's Game of Life simulation
        self.game = ConwayGameOfLife(width=grid_width, height=grid_height)
        self.game.seed_random(density=0.35)  # Initial seeding

        # Track power for spike detection
        self.previous_power = 0.0
        self.simulation_skip_counter = 0  # Skip frames when power is low

    def render(self) -> str:
        """
        Render device visualization with Conway's Game of Life simulation

        Returns Conway's Game of Life grid with hardware-responsive behavior:
        - Simulation speed based on power consumption
        - Cell birth rate based on current draw
        - Colors based on temperature (blue→cyan→yellow→red)
        - Glider injection on power spikes

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

            # Calculate activity boost from current draw (0-100A mapped to 0-1)
            # Higher current = more cell births in Conway simulation
            activity_boost = min(current / 100.0, 1.0)

            # Detect power spikes and inject glider patterns
            power_change = abs(power - self.previous_power)
            if power_change > 5.0:  # 5W spike threshold
                # Inject glider at random position when activity spikes
                glider_x = random.randint(0, self.game.width - 3)
                glider_y = random.randint(0, self.game.height - 3)
                self.game.seed_glider(glider_x, glider_y)
            self.previous_power = power

            # Step simulation based on power level
            # Skip frames when device is idle for performance
            if power > 10.0:  # Device is active - run simulation
                self.game.step(activity_boost)
            else:  # Device idle - slow down simulation
                self.simulation_skip_counter += 1
                if self.simulation_skip_counter >= 5:  # Step every 5 frames when idle
                    self.game.step(0.0)  # No activity boost when idle
                    self.simulation_skip_counter = 0

            # Render Game of Life with temperature-responsive colors
            game_display = self.game.render_colorful(temp, self.is_hero_location)

            lines = []

            # Header with hero cursor if active
            if self.is_hero_location:
                lines.append(f"[bold bright_yellow]▶ Device {self.device_idx} ({arch}) ◀[/]")
            else:
                lines.append(f"[dim]Device {self.device_idx} ({arch})[/]")

            lines.append("")

            # Conway's Game of Life grid (30×15 cells)
            lines.append(game_display)

            lines.append("")

            # Telemetry readings with generation count
            lines.append(f"[bright_yellow]{power:5.1f}W[/] [bright_green]{current:5.1f}A[/] [bright_cyan]{temp:4.1f}°C[/]")
            lines.append(f"[dim]Generation: {self.game.generation}[/]")

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
