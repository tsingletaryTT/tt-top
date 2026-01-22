#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Chip Grid Visualizer - Beautiful hardware topology visualization

Inspired by the DRAM visualizer, this creates a full-screen display showing:
- Tensix core grids with real activity levels
- Memory hierarchy (DDR → L2 → L1)
- Data flow indicators
- Thermal patterns

All built fresh per frame - NO markup overlay bugs!
"""

import math
import random
from typing import Dict, List, Any, Tuple


# ============================================================================
# SAFE MARKUP HELPER - Copied to avoid circular import
# ============================================================================

def safe_markup_wrap(text: str, color_str: str) -> str:
    """
    Safely wrap text in Rich markup without possibility of malformed tags.

    Args:
        text: Text to wrap
        color_str: Color like 'red', 'bold red', 'bright_cyan'

    Returns:
        Properly nested markup string
    """
    if not text:
        return ''

    # Parse color string
    if not color_str or not isinstance(color_str, str):
        return text

    # Check for corruption
    if '[' in color_str or ']' in color_str or '/' in color_str:
        return text  # Return unwrapped if corrupted

    # Handle 'bold color' pattern
    parts = color_str.strip().split()
    if len(parts) == 2 and parts[0] == 'bold':
        color = parts[1]
        return f'[bold][{color}]{text}[/{color}][/bold]'
    else:
        # Simple color
        return f'[{color_str}]{text}[/{color_str}]'


class ChipGridVisualizer:
    """
    Beautiful grid-based chip visualization showing real hardware topology
    and activity patterns.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.frame = 0

        # Adaptive baseline system
        self.baseline_established = False
        self.baseline_samples = []
        self.baseline_power = {}
        self.baseline_current = {}
        self.baseline_temp = {}
        self.max_baseline_samples = 20

    def update(self, backend: Any, frame: int):
        """Update with new telemetry data"""
        self.frame = frame

        # Update baseline if needed
        if not self.baseline_established:
            self._update_baseline(backend)

    def _update_baseline(self, backend: Any):
        """Learn hardware idle state"""
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
        """Render the complete chip grid visualization"""
        lines = []

        # Add header
        lines.extend(self._render_header(backend))

        # Render each device
        num_devices = len(backend.devices)
        available_height = self.height - 10  # Reserve space for header/footer

        if num_devices == 0:
            lines.append("")
            lines.append("  No devices detected")
            lines.append("")
        elif num_devices == 1:
            # Single device - show detailed view
            lines.extend(self._render_device_detailed(backend, 0))
        else:
            # Multi-device - show compact grid for each
            height_per_device = available_height // num_devices
            for i in range(num_devices):
                lines.extend(self._render_device_compact(backend, i, height_per_device))
                if i < num_devices - 1:
                    lines.append("")  # Spacing between devices

        # Add footer
        lines.extend(self._render_footer(backend))

        return lines

    def _render_header(self, backend: Any) -> List[str]:
        """Render header with system status"""
        lines = []

        # Calculate system metrics
        num_devices = len(backend.devices)
        if num_devices > 0:
            total_power = sum(float(backend.device_telemetrys[i].get('power', '0')) for i in range(num_devices))
            avg_temp = sum(float(backend.device_telemetrys[i].get('asic_temperature', '0')) for i in range(num_devices)) / num_devices
            total_current = sum(float(backend.device_telemetrys[i].get('current', '0')) for i in range(num_devices))
        else:
            total_power = avg_temp = total_current = 0

        # Status determination
        if avg_temp > 80:
            status = safe_markup_wrap('⚠ THERMAL', 'bold red')
        elif total_power > 200:
            status = safe_markup_wrap('⚡ HIGH POWER', 'bold yellow')
        elif total_power > 50:
            status = safe_markup_wrap('● ACTIVE', 'bright_green')
        else:
            status = safe_markup_wrap('○ READY', 'bright_cyan')

        # Baseline status
        if self.baseline_established:
            baseline_status = safe_markup_wrap('✓ BASELINE', 'bright_green')
        else:
            samples = len(self.baseline_samples)
            baseline_status = f"LEARNING {samples}/{self.max_baseline_samples}"

        # Build header
        lines.append("╔═══════════════════════════════════════════════════════════════════╗")
        lines.append(f"║ {safe_markup_wrap('CHIP TOPOLOGY VISUALIZER', 'bold bright_white')} │ {status} │ Devices: {num_devices} │ {baseline_status} ║")
        lines.append(f"║ Power: {safe_markup_wrap(f'{total_power:5.1f}W', 'bright_yellow')} │ Current: {safe_markup_wrap(f'{total_current:5.1f}A', 'bright_green')} │ Temp: {safe_markup_wrap(f'{avg_temp:4.1f}°C', 'orange1')} ║")
        lines.append("╚═══════════════════════════════════════════════════════════════════╝")

        return lines

    def _render_device_detailed(self, backend: Any, device_idx: int) -> List[str]:
        """Render detailed view of a single device"""
        lines = []

        device = backend.devices[device_idx]
        telem = backend.device_telemetrys[device_idx]

        # Get device info
        board_info = backend.device_infos[device_idx]
        board_type = board_info.get('board_type', 'unknown')

        # Get metrics
        power = float(telem.get('power', '0.0'))
        current = float(telem.get('current', '0.0'))
        temp = float(telem.get('asic_temperature', '0.0'))

        # Get activity level (relative to baseline)
        if self.baseline_established and device_idx in self.baseline_power:
            power_change = (power - self.baseline_power[device_idx]) / max(self.baseline_power[device_idx], 1.0)
            current_change = (current - self.baseline_current[device_idx]) / max(self.baseline_current[device_idx], 1.0)
            activity = max(0.0, min((power_change + current_change) / 2, 1.0))
        else:
            activity = 0.3  # Neutral during learning

        # Device header
        lines.append("")
        lines.append(f"┌─ Device 0: {board_type} │ Activity: {activity*100:5.1f}% ─┐")

        # Tensix core grid
        if device.as_gs():
            rows, cols = 10, 12
        elif device.as_wh():
            rows, cols = 8, 10
        elif device.as_bh():
            rows, cols = 14, 16
        else:
            rows, cols = 8, 10

        lines.extend(self._render_tensix_grid(rows, cols, activity, power, temp, device_idx))

        # Memory hierarchy
        lines.append("├─ Memory Hierarchy ─")
        lines.extend(self._render_memory_hierarchy(device_idx, backend, power, current))

        lines.append("└─────────────────────┘")

        return lines

    def _render_device_compact(self, backend: Any, device_idx: int, max_height: int) -> List[str]:
        """Render compact view of a device for multi-device systems"""
        lines = []

        device = backend.devices[device_idx]
        telem = backend.device_telemetrys[device_idx]
        board_info = backend.device_infos[device_idx]
        board_type = board_info.get('board_type', 'unknown')

        power = float(telem.get('power', '0.0'))
        current = float(telem.get('current', '0.0'))
        temp = float(telem.get('asic_temperature', '0.0'))

        # Activity level
        if self.baseline_established and device_idx in self.baseline_power:
            power_change = (power - self.baseline_power[device_idx]) / max(self.baseline_power[device_idx], 1.0)
            activity = max(0.0, min(power_change, 1.0))
        else:
            activity = 0.3

        # Compact header
        lines.append(f"│ Dev{device_idx}: {board_type:7} │ {safe_markup_wrap(f'{power:5.1f}W', 'bright_yellow')} │ {self._render_activity_bar(activity, 20)} │")

        # Compact grid (fewer rows)
        if device.as_gs():
            rows, cols = 5, 12  # Half height
        elif device.as_wh():
            rows, cols = 4, 10
        elif device.as_bh():
            rows, cols = 7, 16
        else:
            rows, cols = 4, 10

        grid_lines = self._render_tensix_grid_compact(rows, cols, activity, temp, device_idx)
        for line in grid_lines:
            lines.append(f"│   {line}")

        return lines

    def _render_tensix_grid(self, rows: int, cols: int, activity: float, power: float, temp: float, device_idx: int) -> List[str]:
        """Render detailed Tensix core grid"""
        lines = []

        for row in range(rows):
            line_parts = []
            for col in range(cols):
                # Calculate core activity (varies across grid)
                core_offset = math.sin((row + col) * 0.5 + self.frame * 0.05) * 0.2
                core_activity = max(0.0, min(activity + core_offset, 1.0))

                # Get block character and color based on activity
                char, color = self._get_activity_block(core_activity, temp)
                line_parts.append(safe_markup_wrap(char, color))

            lines.append("│ " + "".join(line_parts) + " │")

        return lines

    def _render_tensix_grid_compact(self, rows: int, cols: int, activity: float, temp: float, device_idx: int) -> List[str]:
        """Render compact Tensix grid"""
        lines = []

        for row in range(rows):
            line_parts = []
            for col in range(cols):
                core_offset = math.sin((row + col) * 0.3 + self.frame * 0.05) * 0.15
                core_activity = max(0.0, min(activity + core_offset, 1.0))
                char, color = self._get_activity_block(core_activity, temp)
                line_parts.append(safe_markup_wrap(char, color))

            lines.append("".join(line_parts))

        return lines

    def _get_activity_block(self, activity: float, temp: float) -> Tuple[str, str]:
        """Get block character and color for activity level"""
        # Temperature influences color
        if temp > 80:
            color_base = 'red'
        elif temp > 65:
            color_base = 'orange1'
        elif activity > 0.6:
            color_base = 'yellow'
        elif activity > 0.3:
            color_base = 'green'
        else:
            color_base = 'cyan'

        # Activity influences block character
        if activity > 0.8:
            return ('█', f'bold {color_base}')
        elif activity > 0.6:
            return ('▓', f'bright_{color_base}' if 'bright_' not in color_base else color_base)
        elif activity > 0.4:
            return ('▒', color_base)
        elif activity > 0.2:
            return ('░', color_base)
        else:
            return ('·', f'dim white')

    def _render_activity_bar(self, activity: float, width: int) -> str:
        """Render horizontal activity bar"""
        filled = int(activity * width)
        bar_chars = []

        for i in range(width):
            if i < filled:
                if activity > 0.7:
                    bar_chars.append(safe_markup_wrap('█', 'bright_green'))
                elif activity > 0.4:
                    bar_chars.append(safe_markup_wrap('█', 'bright_yellow'))
                else:
                    bar_chars.append(safe_markup_wrap('█', 'bright_cyan'))
            else:
                bar_chars.append('·')

        return ''.join(bar_chars)

    def _render_memory_hierarchy(self, device_idx: int, backend: Any, power: float, current: float) -> List[str]:
        """Render memory hierarchy (DDR → L2 → L1)"""
        lines = []

        # Get DDR info
        try:
            smbus = backend.smbus_telem_info[device_idx]
            ddr_status = smbus.get('DDR_STATUS', '0')
            ddr_speed = smbus.get('DDR_SPEED', 'N/A')
        except:
            ddr_status = '0'
            ddr_speed = 'N/A'

        # DDR channels
        device = backend.devices[device_idx]
        if device.as_gs():
            num_channels = 4
        elif device.as_wh():
            num_channels = 8
        elif device.as_bh():
            num_channels = 12
        else:
            num_channels = 8

        ddr_pattern = self._render_ddr_channels(ddr_status, num_channels, current)
        lines.append(f"│ DDR: {ddr_pattern} {ddr_speed:>6} │")

        # L2 cache (based on power)
        l2_pattern = self._render_l2_cache(power, num_channels)
        lines.append(f"│ L2:  {l2_pattern} │")

        # Data flow
        flow_pattern = self._render_data_flow(current, 30)
        lines.append(f"│ ▼▼▼  {flow_pattern} │")

        return lines

    def _render_ddr_channels(self, ddr_status: str, num_channels: int, current: float) -> str:
        """Render DDR channel status"""
        try:
            status_value = int(ddr_status, 16) if ddr_status != "0" else 0
        except:
            status_value = 0

        channels = []
        for i in range(min(num_channels, 8)):
            channel_status = (status_value >> (4 * i)) & 0xF

            if channel_status == 2:  # Trained
                # Activity based on current
                if current > 50:
                    channels.append(safe_markup_wrap('██', 'bold red'))
                elif current > 30:
                    channels.append(safe_markup_wrap('▓▓', 'bold yellow'))
                else:
                    channels.append(safe_markup_wrap('●●', 'bright_green'))
            elif channel_status == 1:  # Training
                if (self.frame + i) % 4 < 2:
                    channels.append(safe_markup_wrap('◐◐', 'bright_cyan'))
                else:
                    channels.append(safe_markup_wrap('◑◑', 'bright_cyan'))
            elif channel_status >= 3:  # Error
                channels.append(safe_markup_wrap('✗✗', 'red'))
            else:  # Untrained
                channels.append(safe_markup_wrap('◯◯', 'dim white'))

        return " ".join(channels)

    def _render_l2_cache(self, power: float, num_banks: int) -> str:
        """Render L2 cache banks"""
        banks = []
        base_util = min(int(power / 10), 9)

        for i in range(min(num_banks, 8)):
            bank_util = max(0, base_util - abs(i - num_banks//2))

            if bank_util >= 7:
                banks.append(safe_markup_wrap('▓▓', 'bold yellow'))
            elif bank_util >= 4:
                banks.append(safe_markup_wrap('▒▒', 'yellow'))
            elif bank_util >= 2:
                banks.append(safe_markup_wrap('░░', 'bright_cyan'))
            else:
                banks.append(safe_markup_wrap('··', 'dim white'))

        return " ".join(banks)

    def _render_data_flow(self, current: float, width: int) -> str:
        """Render data flow indicator"""
        intensity = min(int(current / 3), width)

        chars = []
        for i in range(width):
            if i < intensity:
                pos = (i + self.frame) % 6
                if pos < 2:
                    chars.append(safe_markup_wrap('▶', 'bright_white'))
                elif pos < 4:
                    chars.append(safe_markup_wrap('▷', 'bright_cyan'))
                else:
                    chars.append(safe_markup_wrap('·', 'cyan'))
            else:
                chars.append('·')

        return ''.join(chars)

    def _render_footer(self, backend: Any) -> List[str]:
        """Render footer with legend"""
        lines = []

        lines.append("╔═══════════════════════════════════════════════════════════════════╗")
        lines.append(f"║ {safe_markup_wrap('ACTIVITY:', 'bold white')} {safe_markup_wrap('█', 'bold red')}80-100% {safe_markup_wrap('▓', 'yellow')}60-80% {safe_markup_wrap('▒', 'green')}40-60% {safe_markup_wrap('░', 'cyan')}20-40% {safe_markup_wrap('·', 'dim white')}<20% ║")
        lines.append(f"║ {safe_markup_wrap('DDR:', 'bold white')} ● Trained ◐◑ Training ◯ Idle ✗ Error │ {safe_markup_wrap('Press v/ESC to exit', 'bright_cyan')} ║")
        lines.append("╚═══════════════════════════════════════════════════════════════════╝")

        return lines
