#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Unified Chip Art Visualizer - Informational Delight

Creates a single, cohesive work of art from all available chips.
Scales beautifully from 1 to 30+ devices.

Visual concept: A living memory wall where all devices contribute to
horizontal bands showing different layers of the system, with activity
flowing like waves across the entire visualization.
"""

import math
from typing import List, Any, Tuple


def safe_markup_wrap(text: str, color_str: str) -> str:
    """Safely wrap text in Rich markup"""
    if not text:
        return ''
    if not color_str or not isinstance(color_str, str):
        return text
    if '[' in color_str or ']' in color_str or '/' in color_str:
        return text

    parts = color_str.strip().split()
    if len(parts) == 2 and parts[0] == 'bold':
        color = parts[1]
        return f'[bold][{color}]{text}[/{color}][/bold]'
    else:
        return f'[{color_str}]{text}[/{color_str}]'


class UnifiedChipArt:
    """
    A unified visualization that integrates all chips into one artistic display.

    Layout:
    - Top: System status banner
    - Main: Horizontal bands showing unified system layers
      * Memory Wall (DDR channels from all devices)
      * Compute Wave (Tensix cores from all devices)
      * Flow Layer (Data movement patterns)
    - Bottom: Thermal spectrum showing all devices
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.frame = 0

        # Adaptive baseline
        self.baseline_established = False
        self.baseline_samples = []
        self.baseline_power = {}
        self.baseline_current = {}
        self.baseline_temp = {}
        self.max_baseline_samples = 20

    def resize(self, width: int, height: int):
        """Handle terminal resize - be adaptive!"""
        self.width = width
        self.height = height

    def update(self, backend: Any, frame: int):
        """Update with new telemetry"""
        self.frame = frame
        if not self.baseline_established:
            self._update_baseline(backend)

    def _update_baseline(self, backend: Any):
        """Learn hardware baseline"""
        if self.baseline_established:
            return

        current_sample = {}
        for i in range(len(backend.devices)):
            try:
                telem = backend.device_telemetrys[i]
                current_sample[i] = {
                    'power': float(telem.get('power', '0.0')),
                    'current': float(telem.get('current', '0.0')),
                    'temp': float(telem.get('asic_temperature', '0.0'))
                }
            except:
                current_sample[i] = {'power': 0.0, 'current': 0.0, 'temp': 0.0}

        self.baseline_samples.append(current_sample)

        if len(self.baseline_samples) >= self.max_baseline_samples:
            for device_idx in range(len(backend.devices)):
                power_samples = [s[device_idx]['power'] for s in self.baseline_samples if device_idx in s]
                current_samples = [s[device_idx]['current'] for s in self.baseline_samples if device_idx in s]
                temp_samples = [s[device_idx]['temp'] for s in self.baseline_samples if device_idx in s]

                if power_samples:
                    self.baseline_power[device_idx] = sum(power_samples) / len(power_samples)
                    self.baseline_current[device_idx] = sum(current_samples) / len(current_samples)
                    self.baseline_temp[device_idx] = sum(temp_samples) / len(temp_samples)

            self.baseline_established = True

    def render(self, backend: Any) -> List[str]:
        """Render the unified artistic visualization"""
        lines = []

        num_devices = len(backend.devices)
        if num_devices == 0:
            return ["", "  No devices detected", ""]

        # Gather all device data
        device_data = self._gather_device_data(backend)

        # Header: System-wide status
        lines.extend(self._render_unified_header(device_data, num_devices))

        # Main visualization area
        available_height = self.height - 10

        # Unified Memory Wall (top third)
        memory_height = available_height // 3
        lines.extend(self._render_memory_wall(device_data, memory_height))

        # Compute Wave (middle third)
        compute_height = available_height // 3
        lines.extend(self._render_compute_wave(device_data, compute_height))

        # Flow Layer (bottom third)
        flow_height = available_height - memory_height - compute_height
        lines.extend(self._render_flow_layer(device_data, flow_height))

        # Footer: Thermal spectrum
        lines.extend(self._render_thermal_spectrum(device_data))

        return lines

    def _gather_device_data(self, backend: Any) -> List[dict]:
        """Gather telemetry from all devices"""
        data = []
        for i in range(len(backend.devices)):
            try:
                device = backend.devices[i]
                telem = backend.device_telemetrys[i]
                board_info = backend.device_infos[i]

                power = float(telem.get('power', '0.0'))
                current = float(telem.get('current', '0.0'))
                temp = float(telem.get('asic_temperature', '0.0'))

                # Calculate activity relative to baseline
                if self.baseline_established and i in self.baseline_power:
                    power_change = (power - self.baseline_power[i]) / max(self.baseline_power[i], 1.0)
                    current_change = (current - self.baseline_current[i]) / max(self.baseline_current[i], 1.0)
                    temp_change = (temp - self.baseline_temp[i]) / max(self.baseline_temp[i], 1.0)
                    activity = max(0.0, min((power_change + current_change) / 2, 2.0))
                else:
                    activity = 0.1
                    power_change = current_change = temp_change = 0.0

                # Get architecture info
                if device.as_gs():
                    arch = 'GS'
                    cores = (10, 12)
                    mem_channels = 4
                elif device.as_wh():
                    arch = 'WH'
                    cores = (8, 10)
                    mem_channels = 8
                elif device.as_bh():
                    arch = 'BH'
                    cores = (14, 16)
                    mem_channels = 12
                else:
                    arch = 'UK'
                    cores = (8, 10)
                    mem_channels = 8

                # Get DDR status
                try:
                    smbus = backend.smbus_telem_info[i]
                    ddr_status = smbus.get('DDR_STATUS', '0')
                except:
                    ddr_status = '0'

                data.append({
                    'idx': i,
                    'arch': arch,
                    'cores': cores,
                    'mem_channels': mem_channels,
                    'power': power,
                    'current': current,
                    'temp': temp,
                    'activity': activity,
                    'power_change': power_change,
                    'current_change': current_change,
                    'temp_change': temp_change,
                    'ddr_status': ddr_status
                })
            except:
                continue

        return data

    def _render_unified_header(self, device_data: List[dict], num_devices: int) -> List[str]:
        """Render unified system header - BORDERLESS RIGHT"""
        lines = []

        # Calculate system totals
        total_power = sum(d['power'] for d in device_data)
        avg_temp = sum(d['temp'] for d in device_data) / max(len(device_data), 1)
        max_activity = max((d['activity'] for d in device_data), default=0.0)

        # Status color
        if avg_temp > 80:
            status = safe_markup_wrap('◆ THERMAL', 'bold red')
        elif max_activity > 0.5:
            status = safe_markup_wrap('◆ ACTIVE', 'bold yellow')
        elif max_activity > 0.1:
            status = safe_markup_wrap('◆ WORKING', 'bright_green')
        else:
            status = safe_markup_wrap('◆ READY', 'bright_cyan')

        # Build header - borderless right
        lines.append("╔═══════════════════════════════════════════════════════════════")

        title = safe_markup_wrap('UNIFIED CHIP ART', 'bold bright_white')
        devices_text = f"{num_devices} device{'s' if num_devices != 1 else ''}"
        power_text = safe_markup_wrap(f'{total_power:.1f}W', 'bright_yellow')
        temp_text = safe_markup_wrap(f'{avg_temp:.1f}°C', 'orange1')

        header_line = f"║ {title} │ {status} │ {devices_text} │ {power_text} │ {temp_text}"
        lines.append(header_line)

        lines.append("╚═══════════════════════════════════════════════════════════════")

        return lines

    def _render_memory_wall(self, device_data: List[dict], height: int) -> List[str]:
        """Render unified memory wall showing all DDR channels

        MEMORY WALL ANIMATION SEMANTICS:
        - Animates based on CURRENT DRAW (directly correlates with DDR bandwidth)
        - HIGH ACTIVITY (>30A): Model loading, weight transfers, large data movement
        - MEDIUM ACTIVITY (15-30A): Inference, activation movement through memory hierarchy
        - LOW ACTIVITY (<15A): Idle, occasional memory accesses

        The wave motion creates a "breathing" effect that shows memory bandwidth demand
        across the entire system. During model loading, you'll see sustained high activity.
        During inference, you'll see burst patterns. Training shows continuous high activity.

        ENHANCED DYNAMICS:
        - Multiple wave layers with different speeds and phases create interference patterns
        - Per-channel shimmer effect adds local variation
        - Ripple propagation shows data movement across channels
        - Uses both absolute current and change rate for maximum sensitivity
        """
        lines = []

        if height < 3:
            return lines

        # Adaptive title based on width - BORDERLESS RIGHT
        title_text = "MEMORY WALL" if self.width > 60 else "MEMORY"
        title = safe_markup_wrap(title_text, "bold bright_magenta")
        lines.append("┌─ " + title + " ─────────────────────────────────")

        # Calculate total memory channels across all devices
        total_channels = sum(d['mem_channels'] for d in device_data)
        chars_per_channel = max(1, (self.width - 4) // max(total_channels, 1))

        # Render memory rows
        for row in range(height - 2):
            row_chars = []
            channel_idx = 0

            for dev in device_data:
                for ch in range(dev['mem_channels']):
                    # Parse DDR status
                    try:
                        status_value = int(dev['ddr_status'], 16) if dev['ddr_status'] != "0" else 0
                        channel_status = (status_value >> (4 * ch)) & 0xF
                    except:
                        channel_status = 0

                    # ULTRA-DYNAMIC MEMORY WALL ACTIVITY CALCULATION
                    # Maximum sensitivity - NO baseline dampening!

                    if channel_status == 2:  # Trained channel
                        # ULTRA SENSITIVE: Even 2A shows visible activity!
                        current_activity = min(dev['current'] / 10.0, 2.0)  # 10A = 1.0, scales to 2.0

                        # Amplified change rate for burst detection
                        change_boost = max(0.0, dev['current_change'] * 5.0)  # 5x amplification!

                        # Power also contributes but scaled aggressively
                        power_activity = min(dev['power'] / 25.0, 1.5)  # 25W = 1.5 activity

                        # Temperature adds dynamic "heat shimmer" effect
                        temp_boost = max(0.0, (dev['temp'] - 30.0) / 50.0)  # Temps above 30°C add activity

                        # Combine ALL signals with no dampening
                        base_activity = current_activity + change_boost + power_activity * 0.5 + temp_boost * 0.3

                    elif channel_status == 1:  # Training
                        base_activity = 1.5  # High activity for training
                    else:
                        base_activity = 0.0  # Truly idle

                    # MULTI-LAYER WAVE SYSTEM - ULTRA DRAMATIC!

                    # Wave 1: Fast primary wave (data streaming) - DOUBLED amplitude!
                    wave_speed_1 = 0.6 + base_activity * 0.8  # Faster: 0.6-1.4 range
                    wave_1 = math.sin((channel_idx * 0.8 + row * 0.5 + self.frame * wave_speed_1) * 0.8) * 0.7

                    # Wave 2: Medium speed wave (burst transfers) - DOUBLED!
                    wave_speed_2 = 0.4 + base_activity * 0.6
                    wave_2 = math.cos((channel_idx * 0.5 - row * 0.7 + self.frame * wave_speed_2) * 0.6) * 0.5

                    # Wave 3: Slow deep wave (background activity) - Larger amplitude
                    wave_3 = math.sin((channel_idx * 0.3 + row * 0.9 + self.frame * 0.2) * 0.4) * 0.4

                    # Wave 4: Ultra-fast flutter for alive feeling
                    wave_4 = math.sin((channel_idx * 1.5 + self.frame * 1.2) * 1.2) * 0.3

                    # Ripple effect: Propagating waves - STRONGER!
                    ripple_distance = abs(channel_idx - (self.frame * 0.8) % total_channels)
                    ripple = math.exp(-ripple_distance / 8.0) * math.sin(ripple_distance * 0.7) * 0.6

                    # Per-channel shimmer: Adds sparkle effect - AMPLIFIED!
                    shimmer_seed = (channel_idx * 7 + row * 13 + self.frame) % 100
                    shimmer = (math.sin(shimmer_seed * 0.628) * 0.5 + 0.5) * 0.3

                    # Interference pattern: Waves interact STRONGLY
                    interference = (wave_1 + wave_2 + wave_4) * (1.5 + wave_3 * 0.8)

                    # Combine all dynamics - NO DAMPENING!
                    total_wave = wave_1 + wave_2 + wave_3 + wave_4 + ripple + shimmer + interference * 0.5

                    # Final activity - base_activity DIRECTLY added, not dampened!
                    activity = max(0.0, base_activity + total_wave)

                    # Get block and color with enhanced activity
                    char, color = self._get_memory_block(activity, dev['temp'], channel_status)

                    # Add to row
                    for _ in range(chars_per_channel):
                        row_chars.append(safe_markup_wrap(char, color))

                    channel_idx += 1

            # Trim to width and add left border only - BORDERLESS RIGHT
            row_str = ''.join(row_chars[:self.width - 4])
            lines.append("│ " + row_str)

        lines.append("└─────────────────────────────────────────────────────")

        return lines

    def _render_compute_wave(self, device_data: List[dict], height: int) -> List[str]:
        """Render unified compute wave showing all Tensix cores

        COMPUTE WAVE ANIMATION SEMANTICS:
        - Animates based on POWER DRAW (directly correlates with compute activity)
        - HIGH ACTIVITY (>50W): Active inference, training, intensive computation
        - MEDIUM ACTIVITY (20-50W): Light inference, model compilation
        - LOW ACTIVITY (<20W): Idle, occasional housekeeping

        The wave creates interference patterns that show compute intensity distribution.
        Phase shifts between rows create a 3D depth effect. During inference, you'll see
        rhythmic pulses. During training, sustained high activity with minimal variation.
        """
        lines = []

        if height < 3:
            return lines

        # Adaptive title based on width - BORDERLESS RIGHT
        title_text = "COMPUTE WAVE" if self.width > 60 else "COMPUTE"
        title = safe_markup_wrap(title_text, "bold bright_yellow")
        lines.append("┌─ " + title + " ─────────────────────────────────")

        # Total core columns across all devices
        total_cols = sum(d['cores'][1] for d in device_data)
        chars_per_col = max(1, (self.width - 4) // max(total_cols, 1))

        # Render compute rows
        for row in range(height - 2):
            row_chars = []
            col_idx = 0

            for dev in device_data:
                dev_cols = dev['cores'][1]
                for col in range(dev_cols):
                    # Calculate core activity with wave
                    base_activity = dev['activity']
                    wave = math.sin((col_idx + row * 0.7 + self.frame * 0.15) * 0.8) * 0.4
                    phase = math.cos((col_idx - row + self.frame * 0.1) * 0.6) * 0.2
                    activity = max(0.0, min(base_activity + wave + phase, 1.0))

                    # Get block and color
                    char, color = self._get_compute_block(activity, dev['temp'])

                    # Add to row
                    for _ in range(chars_per_col):
                        row_chars.append(safe_markup_wrap(char, color))

                    col_idx += 1

            row_str = ''.join(row_chars[:self.width - 4])
            lines.append("│ " + row_str)

        lines.append("└─────────────────────────────────────────────────────")

        return lines

    def _render_flow_layer(self, device_data: List[dict], height: int) -> List[str]:
        """Render data flow patterns across all devices

        DATA FLOW ANIMATION SEMANTICS:
        - Animates based on CURRENT CHANGE (rapid increases = burst transfers)
        - Shows data movement patterns radiating from active devices
        - Flow intensity: Distance from device center affects flow strength
        - Flow direction: Animated characters move left→right showing data direction

        During model loading: Sustained radial flow from all devices
        During inference: Burst patterns from active devices
        During idle: Minimal scattered flow particles
        """
        lines = []

        if height < 3:
            return lines

        # Adaptive title based on width - BORDERLESS RIGHT
        title_text = "DATA FLOW" if self.width > 60 else "FLOW"
        title = safe_markup_wrap(title_text, "bold bright_cyan")
        lines.append("┌─ " + title + " ─────────────────────────────────")

        # Render flow patterns
        for row in range(height - 2):
            row_chars = []

            for x in range(self.width - 4):
                # Calculate flow intensity from device positions
                flow_intensity = 0.0

                device_spacing = (self.width - 4) / max(len(device_data), 1)
                for dev_idx, dev in enumerate(device_data):
                    dev_center = int(dev_idx * device_spacing + device_spacing / 2)
                    distance = abs(x - dev_center)

                    # Flow radiates from active devices
                    if distance < device_spacing / 2:
                        device_flow = dev['current_change'] * (1.0 - distance / (device_spacing / 2))
                        flow_intensity = max(flow_intensity, device_flow)

                # Add wave animation
                wave = math.sin((x + row + self.frame * 0.3) * 0.4) * 0.2
                flow_intensity = max(0.0, min(flow_intensity + wave, 1.0))

                # Choose flow character
                char, color = self._get_flow_char(flow_intensity, x, row)
                row_chars.append(safe_markup_wrap(char, color))

            row_str = ''.join(row_chars[:self.width - 4])
            lines.append("│ " + row_str)

        lines.append("└─────────────────────────────────────────────────────")

        return lines

    def _render_thermal_spectrum(self, device_data: List[dict]) -> List[str]:
        """Render thermal spectrum showing all devices

        THERMAL SPECTRUM SEMANTICS:
        - Static bar showing temperature distribution across all devices
        - Color: Real-time temperature (cyan<35°C → red>80°C)
        - Density: Activity level (█ high activity → ░ idle)
        - Width: Each device gets proportional space (scales for 1-30+ devices)

        This gives you instant visual confirmation of thermal distribution across
        your entire system. Hot spots are immediately visible as red segments.
        """
        lines = []

        # Adaptive title based on width - BORDERLESS RIGHT
        title_text = "THERMAL SPECTRUM" if self.width > 60 else "THERMAL"
        title = safe_markup_wrap(title_text, "bold bright_white")
        lines.append("┌─ " + title + " ─────────────────────────────────")

        # Create thermal bar
        bar_chars = []
        chars_per_device = max(3, (self.width - 4) // max(len(device_data), 1))

        for dev in device_data:
            temp_norm = (dev['temp'] - 20) / 80  # Normalize 20-100°C range

            # Temperature-based color
            if dev['temp'] > 80:
                color = 'bold red'
            elif dev['temp'] > 65:
                color = 'orange1'
            elif dev['temp'] > 50:
                color = 'yellow'
            elif dev['temp'] > 35:
                color = 'bright_green'
            else:
                color = 'bright_cyan'

            # Fill character based on activity
            if dev['activity'] > 0.6:
                char = '█'
            elif dev['activity'] > 0.3:
                char = '▓'
            elif dev['activity'] > 0.1:
                char = '▒'
            else:
                char = '░'

            # Add device segment
            for _ in range(chars_per_device):
                bar_chars.append(safe_markup_wrap(char, color))

        bar_str = ''.join(bar_chars[:self.width - 4])
        lines.append("│ " + bar_str)

        # Legend - BORDERLESS RIGHT
        legend = safe_markup_wrap("█", "bold red") + ">80°C " + \
                safe_markup_wrap("█", "orange1") + "65-80 " + \
                safe_markup_wrap("█", "yellow") + "50-65 " + \
                safe_markup_wrap("█", "bright_green") + "35-50 " + \
                safe_markup_wrap("█", "bright_cyan") + "<35"

        lines.append("│ " + legend)

        lines.append("└─────────────────────────────────────────────────────")

        return lines

    def _get_memory_block(self, activity: float, temp: float, channel_status: int) -> Tuple[str, str]:
        """Get memory block character and color

        Now handles enhanced activity range (0-2.0) with more gradations
        and vibrant colors for maximum visual feedback
        """
        # Training channels get special animation
        if channel_status == 1:
            if (self.frame % 4) < 2:
                return ('◐', 'bright_cyan')
            else:
                return ('◑', 'bright_cyan')

        # Error channels
        if channel_status >= 3:
            return ('✗', 'red')

        # Inactive channels
        if channel_status == 0:
            return ('·', 'dim white')

        # Active channels - enhanced color palette based on activity and temperature
        # Temperature influences base color, activity determines intensity

        # Color selection with more vibrant options
        if temp > 70:
            color_base = 'red'
        elif temp > 55:
            color_base = 'orange1'
        elif activity > 1.0:  # High activity gets bright colors
            color_base = 'bright_magenta'
        else:
            color_base = 'magenta'

        # Character selection with much more sensitive thresholds
        # Activity range is now 0-2.0, so we spread across that range
        if activity > 1.5:  # Extreme activity
            return ('█', f'bold {color_base}')
        elif activity > 1.0:  # Very high activity
            return ('▓', f'bold {color_base}')
        elif activity > 0.6:  # High activity
            return ('▓', color_base)
        elif activity > 0.35:  # Medium activity
            return ('▒', color_base)
        elif activity > 0.15:  # Low-medium activity
            return ('░', color_base)
        elif activity > 0.05:  # Low activity but visible
            return ('░', 'bright_cyan')
        else:  # Very low activity
            return ('·', 'cyan')

    def _get_compute_block(self, activity: float, temp: float) -> Tuple[str, str]:
        """Get compute block character and color"""
        # Temperature influences color
        if temp > 75:
            color_base = 'red'
        elif temp > 60:
            color_base = 'orange1'
        elif activity > 0.5:
            color_base = 'yellow'
        elif activity > 0.2:
            color_base = 'green'
        else:
            color_base = 'cyan'

        # Activity influences character
        if activity > 0.8:
            return ('█', f'bold {color_base}')
        elif activity > 0.6:
            return ('▓', color_base)
        elif activity > 0.4:
            return ('▒', color_base)
        elif activity > 0.2:
            return ('░', color_base)
        else:
            return ('·', 'dim white')

    def _get_flow_char(self, intensity: float, x: int, row: int) -> Tuple[str, str]:
        """Get flow character and color"""
        # Animated flow based on position
        phase = (x + self.frame) % 6

        if intensity > 0.6:
            if phase < 2:
                return ('▶', 'bright_white')
            elif phase < 4:
                return ('▷', 'bright_yellow')
            else:
                return ('▸', 'yellow')
        elif intensity > 0.3:
            if phase < 3:
                return ('▷', 'bright_cyan')
            else:
                return ('▸', 'cyan')
        elif intensity > 0.1:
            return ('·', 'cyan')
        else:
            return ('·', 'dim white')

    def _strip_markup(self, text: str) -> str:
        """Strip Rich markup for length calculation"""
        import re
        return re.sub(r'\[.*?\]', '', text)
