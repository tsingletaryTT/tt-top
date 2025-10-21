#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Hardware-Responsive Animated ASCII Art Display

A full-screen animated visualization that draws its colors, twinkling effects,
and patterns directly from real Tenstorrent hardware activity. Unlike static
or cosmetic animations, every visual element reflects actual telemetry data.
"""

import time
import random
import math
from typing import Dict, List, Tuple, Optional
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Container
from textual.app import ComposeResult
from textual.binding import Binding
from tt_top.tt_smi_backend import TTSMIBackend


class HardwareStarfield:
    """
    A dynamic starfield where each 'star' represents a hardware component
    and its behavior is driven by real telemetry data.
    """

    def __init__(self, width: int, height: int, num_stars: int = 200):
        """Initialize hardware-responsive starfield

        Args:
            width: Display width in characters
            height: Display height in characters
            num_stars: Maximum number of stars (limited by available hardware data points)
        """
        self.width = width
        self.height = height
        self.num_stars = num_stars
        self.stars = []
        self.time_offset = 0

    def initialize_stars(self, backend: TTSMIBackend) -> None:
        """Initialize stars based on actual hardware topology

        Creates stars that correspond to real hardware elements:
        - Device cores (positioned based on grid layout)
        - Memory channels (clustered around devices)
        - Interconnect nodes (between devices)
        - Telemetry data points (distributed across field)
        """
        self.stars = []
        star_id = 0

        # Create device-based star clusters
        num_devices = len(backend.devices)
        if num_devices == 0:
            return

        # Distribute devices across screen space
        device_spacing_x = self.width // max(num_devices, 1)
        device_spacing_y = self.height // 3  # Use top 2/3 for devices

        for device_idx, device in enumerate(backend.devices):
            # Device center position
            center_x = device_spacing_x * device_idx + device_spacing_x // 2
            center_y = device_spacing_y + (device_idx % 2) * 10  # Stagger vertically

            # Create core grid based on architecture
            if device.as_gs():
                grid_rows, grid_cols = 10, 12  # Grayskull
                cluster_size = 15
            elif device.as_wh():
                grid_rows, grid_cols = 8, 10   # Wormhole
                cluster_size = 12
            elif device.as_bh():
                grid_rows, grid_cols = 14, 16  # Blackhole
                cluster_size = 20
            else:
                grid_rows, grid_cols = 8, 10   # Default
                cluster_size = 12

            # Create stars for Tensix cores
            for row in range(min(grid_rows, 6)):  # Limit for screen space
                for col in range(min(grid_cols, 8)):
                    if star_id >= self.num_stars:
                        break

                    # Position relative to device center
                    star_x = center_x + (col - grid_cols//2) * 2
                    star_y = center_y + (row - grid_rows//2)

                    # Ensure star is within bounds
                    if 0 <= star_x < self.width and 0 <= star_y < self.height:
                        star = {
                            'id': star_id,
                            'x': star_x,
                            'y': star_y,
                            'device_idx': device_idx,
                            'component_type': 'tensix_core',
                            'grid_pos': (row, col),
                            'brightness': 0.5,
                            'color': 'bright_cyan',
                            'twinkle_phase': random.random() * 2 * math.pi,
                            'twinkle_speed': 0.1 + random.random() * 0.3
                        }
                        self.stars.append(star)
                        star_id += 1

            # Create memory channel stars
            memory_channels = 4 if device.as_gs() else 8 if device.as_wh() else 12
            for channel in range(min(memory_channels, 8)):
                if star_id >= self.num_stars:
                    break

                # Position memory stars around device perimeter
                angle = 2 * math.pi * channel / memory_channels
                radius = 15
                star_x = int(center_x + radius * math.cos(angle))
                star_y = int(center_y + radius * math.sin(angle))

                if 0 <= star_x < self.width and 0 <= star_y < self.height:
                    star = {
                        'id': star_id,
                        'x': star_x,
                        'y': star_y,
                        'device_idx': device_idx,
                        'component_type': 'memory_channel',
                        'channel_idx': channel,
                        'brightness': 0.3,
                        'color': 'bright_magenta',
                        'twinkle_phase': random.random() * 2 * math.pi,
                        'twinkle_speed': 0.05 + random.random() * 0.15
                    }
                    self.stars.append(star)
                    star_id += 1

        # Add interconnect stars between devices
        for i in range(num_devices):
            for j in range(i + 1, num_devices):
                if star_id >= self.num_stars:
                    break

                # Position between device centers
                device_i_x = device_spacing_x * i + device_spacing_x // 2
                device_j_x = device_spacing_x * j + device_spacing_x // 2
                interconnect_x = (device_i_x + device_j_x) // 2
                interconnect_y = self.height * 2 // 3  # Lower part of screen

                if 0 <= interconnect_x < self.width and 0 <= interconnect_y < self.height:
                    star = {
                        'id': star_id,
                        'x': interconnect_x,
                        'y': interconnect_y,
                        'device_idx': i,  # Primary device
                        'connected_device': j,
                        'component_type': 'interconnect',
                        'brightness': 0.2,
                        'color': 'bright_green',
                        'twinkle_phase': random.random() * 2 * math.pi,
                        'twinkle_speed': 0.02 + random.random() * 0.08
                    }
                    self.stars.append(star)
                    star_id += 1

    def update_from_telemetry(self, backend: TTSMIBackend, frame_count: int) -> None:
        """Update star properties based on real hardware telemetry

        This is what makes the visualization hardware-responsive rather than
        just cosmetic animation. Each star's brightness, color, and twinkle
        rate directly corresponds to actual hardware activity.
        """
        self.time_offset = frame_count * 0.1

        for star in self.stars:
            device_idx = star['device_idx']

            # Skip if device doesn't exist
            if device_idx >= len(backend.devices):
                continue

            # Get current telemetry for this device
            try:
                telem = backend.device_telemetrys[device_idx]
                power = float(telem.get('power', '0.0'))
                temp = float(telem.get('asic_temperature', '0.0'))
                current = float(telem.get('current', '0.0'))
                voltage = float(telem.get('voltage', '0.0'))
                aiclk = float(telem.get('aiclk', '0.0'))
            except:
                power = temp = current = voltage = aiclk = 0.0

            # Update star based on component type and real telemetry
            if star['component_type'] == 'tensix_core':
                # Core activity based on power consumption
                core_activity = min(power / 100.0, 1.0)  # Normalize to 0-1
                star['brightness'] = 0.2 + core_activity * 0.8

                # Color based on temperature
                if temp > 80:
                    star['color'] = 'bold red'
                elif temp > 65:
                    star['color'] = 'orange1'
                elif temp > 45:
                    star['color'] = 'bright_yellow'
                elif power > 25:
                    star['color'] = 'bright_green'
                else:
                    star['color'] = 'bright_cyan'

                # Twinkle speed based on current draw (activity frequency)
                star['twinkle_speed'] = 0.05 + (current / 100.0) * 0.4

            elif star['component_type'] == 'memory_channel':
                # Memory activity based on current draw
                memory_activity = min(current / 50.0, 1.0)
                star['brightness'] = 0.1 + memory_activity * 0.7

                # Memory channels pulse with different colors based on utilization
                if current > 40:
                    star['color'] = 'bright_magenta'
                elif current > 20:
                    star['color'] = 'magenta'
                elif current > 10:
                    star['color'] = 'bright_blue'
                else:
                    star['color'] = 'blue'

                star['twinkle_speed'] = 0.02 + memory_activity * 0.15

            elif star['component_type'] == 'interconnect':
                # Interconnect activity based on power difference between connected devices
                try:
                    connected_idx = star['connected_device']
                    if connected_idx < len(backend.device_telemetrys):
                        connected_telem = backend.device_telemetrys[connected_idx]
                        connected_power = float(connected_telem.get('power', '0.0'))
                        power_diff = abs(power - connected_power)

                        # Activity increases with power difference (data flow)
                        interconnect_activity = min(power_diff / 50.0, 1.0)
                        star['brightness'] = 0.1 + interconnect_activity * 0.6

                        # Color indicates traffic intensity
                        if power_diff > 40:
                            star['color'] = 'bright_white'
                        elif power_diff > 20:
                            star['color'] = 'bright_green'
                        elif power_diff > 10:
                            star['color'] = 'green'
                        else:
                            star['color'] = 'dim white'

                        star['twinkle_speed'] = 0.01 + interconnect_activity * 0.1
                except:
                    star['brightness'] = 0.1
                    star['color'] = 'dim white'
                    star['twinkle_speed'] = 0.01

            # Update twinkle phase based on hardware-responsive speed
            star['twinkle_phase'] += star['twinkle_speed']
            if star['twinkle_phase'] > 2 * math.pi:
                star['twinkle_phase'] -= 2 * math.pi

    def render_starfield(self) -> List[str]:
        """Render the hardware-responsive starfield to ASCII art

        Creates a colorful display where each position represents actual
        hardware component state. The resulting art is both beautiful and
        informationally dense.
        """
        # Initialize blank field
        field = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        color_field = [['dim white' for _ in range(self.width)] for _ in range(self.height)]

        # Render each star
        for star in self.stars:
            x, y = star['x'], star['y']

            # Skip stars outside bounds
            if not (0 <= x < self.width and 0 <= y < self.height):
                continue

            # Calculate current brightness with twinkling
            base_brightness = star['brightness']
            twinkle_factor = 0.3 * math.sin(star['twinkle_phase'])
            current_brightness = base_brightness + twinkle_factor
            current_brightness = max(0.0, min(1.0, current_brightness))

            # Choose character based on brightness and component type
            if star['component_type'] == 'tensix_core':
                if current_brightness > 0.8:
                    char = '●'
                elif current_brightness > 0.6:
                    char = '◉'
                elif current_brightness > 0.4:
                    char = '○'
                elif current_brightness > 0.2:
                    char = '∘'
                else:
                    char = '·'
            elif star['component_type'] == 'memory_channel':
                if current_brightness > 0.7:
                    char = '█'
                elif current_brightness > 0.5:
                    char = '▓'
                elif current_brightness > 0.3:
                    char = '▒'
                elif current_brightness > 0.1:
                    char = '░'
                else:
                    char = '·'
            elif star['component_type'] == 'interconnect':
                if current_brightness > 0.6:
                    char = '✦'
                elif current_brightness > 0.4:
                    char = '✧'
                elif current_brightness > 0.2:
                    char = '✩'
                else:
                    char = '·'
            else:
                char = '*'

            field[y][x] = char
            color_field[y][x] = star['color']

        # Convert to markup strings
        lines = []
        for row_idx, (char_row, color_row) in enumerate(zip(field, color_field)):
            line_parts = []
            current_color = None

            for char, color in zip(char_row, color_row):
                if color != current_color:
                    if current_color is not None:
                        line_parts.append(f'[/{current_color}]')
                    if char != ' ':  # Don't add color markup for spaces
                        line_parts.append(f'[{color}]')
                        current_color = color
                    else:
                        current_color = None
                line_parts.append(char)

            # Close final color tag if needed
            if current_color is not None:
                line_parts.append(f'[/{current_color}]')

            lines.append(''.join(line_parts))

        return lines


class FlowingDataStreams:
    """
    Animated data streams that flow across the screen, representing
    actual data movement between hardware components.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.streams = []

    def update_streams(self, backend: TTSMIBackend, frame_count: int) -> None:
        """Update data streams based on real interconnect activity"""
        self.streams = []

        # Create streams between active devices
        num_devices = len(backend.devices)
        if num_devices < 2:
            return

        for i in range(num_devices):
            for j in range(i + 1, num_devices):
                try:
                    # Get power levels to simulate data flow
                    telem_i = backend.device_telemetrys[i]
                    telem_j = backend.device_telemetrys[j]
                    power_i = float(telem_i.get('power', '0.0'))
                    power_j = float(telem_j.get('power', '0.0'))

                    # Only create streams if there's significant activity
                    if power_i > 10 or power_j > 10:
                        stream_intensity = (power_i + power_j) / 200.0

                        # Stream flows from higher power to lower power device
                        if power_i > power_j:
                            start_x = i * self.width // num_devices
                            end_x = j * self.width // num_devices
                            flow_direction = 1
                        else:
                            start_x = j * self.width // num_devices
                            end_x = i * self.width // num_devices
                            flow_direction = -1

                        stream_y = self.height // 2 + (i - j) * 3

                        if 0 <= stream_y < self.height:
                            stream = {
                                'start_x': start_x,
                                'end_x': end_x,
                                'y': stream_y,
                                'intensity': stream_intensity,
                                'direction': flow_direction,
                                'phase': (frame_count * 0.2 + i * 0.5) % (2 * math.pi)
                            }
                            self.streams.append(stream)
                except:
                    continue

    def render_streams(self, base_field: List[str]) -> List[str]:
        """Render flowing data streams over the base starfield"""
        lines = list(base_field)  # Copy base field

        for stream in self.streams:
            y = stream['y']
            if not (0 <= y < len(lines)):
                continue

            start_x = stream['start_x']
            end_x = stream['end_x']
            intensity = stream['intensity']
            phase = stream['phase']

            # Create flowing pattern
            stream_length = abs(end_x - start_x)
            if stream_length == 0:
                continue

            flow_chars = ['·', '▸', '▶', '▶', '▸', '·'] if stream['direction'] > 0 else ['·', '◂', '◀', '◀', '◂', '·']
            pattern_length = len(flow_chars)

            # Determine color based on intensity
            if intensity > 0.7:
                stream_color = 'bright_white'
            elif intensity > 0.5:
                stream_color = 'bright_yellow'
            elif intensity > 0.3:
                stream_color = 'orange1'
            else:
                stream_color = 'bright_cyan'

            # Build the stream line
            line_chars = list(lines[y]) if y < len(lines) else [' '] * self.width

            for offset in range(0, stream_length, 2):  # Sample every 2 characters
                x = start_x + offset if stream['direction'] > 0 else start_x - offset
                if not (0 <= x < len(line_chars)):
                    continue

                # Calculate which flow character to use based on phase
                pattern_pos = int((offset / 2 + phase) % pattern_length)
                flow_char = flow_chars[pattern_pos]

                # Only place character if it's not a space/dot or if it would overwrite a space
                if flow_char not in ' ·' or line_chars[x] == ' ':
                    # Insert colored character
                    line_chars[x] = f'[{stream_color}]{flow_char}[/{stream_color}]'

            lines[y] = ''.join(line_chars)

        return lines


class HardwareResponsiveASCII(Static):
    """
    Hardware-Responsive Animated ASCII Art Display Widget

    A full-screen animated visualization where every pixel responds to
    real hardware telemetry data, creating beautiful art that's also
    informationally dense.
    """

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.frame_count = 0
        self.start_time = time.time()

        # Initialize display dimensions (will be updated on mount)
        self.display_width = 120
        self.display_height = 40

        # Initialize animation systems
        self.starfield = HardwareStarfield(self.display_width, self.display_height)
        self.data_streams = FlowingDataStreams(self.display_width, self.display_height)

    def on_mount(self) -> None:
        """Initialize hardware-responsive animation systems"""
        # Get actual display size
        self.display_width = self.size.width
        self.display_height = self.size.height - 2  # Account for borders

        # Reinitialize systems with correct size
        self.starfield = HardwareStarfield(self.display_width, self.display_height)
        self.data_streams = FlowingDataStreams(self.display_width, self.display_height)

        # Initialize starfield based on actual hardware
        self.starfield.initialize_stars(self.backend)

        # Start animation loop
        self.set_interval(0.1, self._update_animation)  # 10 FPS for smooth animation

    def _update_animation(self) -> None:
        """Update animation frame with hardware-responsive data"""
        try:
            # Update backend telemetry
            self.backend.update_telem()
            self.frame_count += 1

            # Update animation systems with real hardware data
            self.starfield.update_from_telemetry(self.backend, self.frame_count)
            self.data_streams.update_streams(self.backend, self.frame_count)

            # Render the complete visualization
            content = self._render_complete_visualization()
            self.update(content)

        except Exception as e:
            # Handle errors gracefully
            self.update(f"[red]Animation Error: {e}[/red]")

    def _render_complete_visualization(self) -> str:
        """Render the complete hardware-responsive visualization"""
        lines = []

        # Add header with hardware status
        header = self._create_visualization_header()
        lines.extend(header)

        # Render starfield
        starfield_lines = self.starfield.render_starfield()

        # Add flowing data streams over starfield
        enhanced_lines = self.data_streams.render_streams(starfield_lines)

        lines.extend(enhanced_lines)

        # Add footer with legend
        footer = self._create_visualization_footer()
        lines.extend(footer)

        return "\n".join(lines)

    def _create_visualization_header(self) -> List[str]:
        """Create header showing system status and animation info"""
        lines = []

        # System metrics
        total_devices = len(self.backend.devices)
        if total_devices > 0:
            total_power = sum(float(self.backend.device_telemetrys[i].get('power', '0'))
                            for i in range(total_devices))
            avg_temp = sum(float(self.backend.device_telemetrys[i].get('asic_temperature', '0'))
                          for i in range(total_devices)) / total_devices

            # Color-code system status
            if avg_temp > 80:
                status_color = 'bold red'
                status_text = 'THERMAL WARNING'
            elif avg_temp > 65:
                status_color = 'orange1'
                status_text = 'ELEVATED TEMP'
            elif total_power > 200:
                status_color = 'bright_yellow'
                status_text = 'HIGH POWER'
            elif total_power > 50:
                status_color = 'bright_green'
                status_text = 'ACTIVE'
            else:
                status_color = 'bright_cyan'
                status_text = 'READY'
        else:
            total_power = avg_temp = 0
            status_color = 'dim white'
            status_text = 'NO DEVICES'

        # Animated header line
        elapsed_time = time.time() - self.start_time
        pulse_char = '●' if int(elapsed_time * 2) % 2 else '○'

        lines.append(f"[bright_cyan]╔══════════════════════════════════════════════════════════════════════════════════════════╗[/bright_cyan]")
        lines.append(f"[bright_cyan]║[/bright_cyan] [bold bright_magenta]{pulse_char}[/bold bright_magenta] [bold bright_white]HARDWARE-RESPONSIVE VISUALIZATION[/bold bright_white] [dim white]│[/dim white] [{status_color}]{status_text}[/{status_color}] [dim white]│[/dim white] [bright_white]Devices:[/bright_white] {total_devices} [dim white]│[/dim white] [bright_white]Power:[/bright_white] [orange1]{total_power:5.1f}W[/orange1] [bright_cyan]║[/bright_cyan]")
        lines.append(f"[bright_cyan]╚══════════════════════════════════════════════════════════════════════════════════════════╝[/bright_cyan]")

        return lines

    def _create_visualization_footer(self) -> List[str]:
        """Create footer with legend and controls"""
        lines = []

        lines.append(f"[bright_cyan]╔══════════════════════════════════════════════════════════════════════════════════════════╗[/bright_cyan]")
        lines.append(f"[bright_cyan]║[/bright_cyan] [bold bright_white]LEGEND:[/bold bright_white] [bright_cyan]●◉○∘·[/bright_cyan] Tensix Cores [dim white]│[/dim white] [bright_magenta]█▓▒░·[/bright_magenta] Memory [dim white]│[/dim white] [bright_green]✦✧✩[/bright_green] Interconnect [dim white]│[/dim white] [bright_yellow]▶◀[/bright_yellow] Data Flow [bright_cyan]║[/bright_cyan]")
        lines.append(f"[bright_cyan]║[/bright_cyan] [bold bright_white]COLORS:[/bold bright_white] [bold red]Red[/bold red] Critical [dim white]│[/dim white] [orange1]Orange[/orange1] Hot [dim white]│[/dim white] [bright_yellow]Yellow[/bright_yellow] Warm [dim white]│[/dim white] [bright_green]Green[/bright_green] Active [dim white]│[/dim white] [bright_cyan]Cyan[/bright_cyan] Idle [bright_cyan]║[/bright_cyan]")
        lines.append(f"[bright_cyan]║[/bright_cyan] [dim bright_white]Press 'v' to toggle visualization mode • All animations driven by real hardware telemetry[/dim bright_white] [bright_cyan]║[/bright_cyan]")
        lines.append(f"[bright_cyan]╚══════════════════════════════════════════════════════════════════════════════════════════╝[/bright_cyan]")

        return lines


class AnimatedDisplayContainer(Container):
    """
    Container for the animated display that can be toggled on/off
    """

    BINDINGS = [
        Binding("v", "toggle_visualization", "Toggle Visualization", show=True),
        Binding("escape", "exit_visualization", "Exit Visualization", show=False),
    ]

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.is_visualization_mode = False
        self.animated_display = None

    def compose(self) -> ComposeResult:
        """Compose the animated display container"""
        # Initially empty - display is created on toggle
        pass

    def action_toggle_visualization(self) -> None:
        """Toggle between normal monitor and animated visualization"""
        if self.is_visualization_mode:
            self.action_exit_visualization()
        else:
            self.enter_visualization_mode()

    def enter_visualization_mode(self) -> None:
        """Enter full-screen animated visualization mode"""
        self.is_visualization_mode = True

        # Clear current content
        for child in self.children:
            child.remove()

        # Create and mount animated display
        self.animated_display = HardwareResponsiveASCII(
            backend=self.backend,
            id="animated_display"
        )
        self.mount(self.animated_display)

        # Focus the animated display
        self.animated_display.focus()

    def action_exit_visualization(self) -> None:
        """Exit visualization mode and return to normal monitor"""
        self.is_visualization_mode = False

        # Remove animated display
        if self.animated_display:
            self.animated_display.remove()
            self.animated_display = None

        # Signal parent to restore normal view
        self.post_message_no_wait(self.VisualizationToggled(False))

    class VisualizationToggled:
        """Message sent when visualization is toggled"""
        def __init__(self, enabled: bool):
            self.enabled = enabled