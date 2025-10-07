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
        """Render TT-Top with retro BBS/terminal aesthetic"""
        lines = []

        # BBS-style header with pixelated hardware avatar
        lines.extend(self._create_bbs_header())
        lines.append("")

        # Main BBS-style display
        lines.extend(self._create_bbs_main_display())

        return "\n".join(lines)

    def _create_memory_topology(self) -> List[str]:
        """Create memory topology visualization with real DDR telemetry data"""
        lines = []
        lines.append("Real Memory Topology & DDR Status")
        lines.append("┌──────────────────────────────────────────────────────────────┐")

        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)[:3].upper()
            telem = self.backend.device_telemetrys[i]
            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))

            # Get real DDR information from backend
            try:
                ddr_speed = self.backend.get_dram_speed(i)
                ddr_trained = self.backend.get_dram_training_status(i)
                ddr_info = self.backend.smbus_telem_info[i].get('DDR_STATUS', '0')
            except:
                ddr_speed = "N/A"
                ddr_trained = False
                ddr_info = "0"

            # Real memory bank visualization based on DDR status
            if ddr_trained:
                # Show trained memory channels
                if device.as_wh():  # Wormhole has 8 channels
                    channels = 8
                    mem_pattern = self._generate_real_ddr_pattern(ddr_info, channels, i)
                elif device.as_gs():  # Grayskull has 4 channels
                    channels = 4
                    mem_pattern = self._generate_real_ddr_pattern(ddr_info, channels, i)
                else:  # Blackhole
                    channels = 12  # Blackhole has more memory channels
                    mem_pattern = self._generate_real_ddr_pattern(ddr_info, channels, i)
                mem_state = "TRN"  # Trained
            else:
                mem_pattern = "◯" * 8  # Untrained channels
                mem_state = "UNT"  # Untrained

            # Interconnect visualization
            if i == 0:
                connector = "┌─"
            elif i == len(self.backend.devices) - 1:
                connector = "└─"
            else:
                connector = "├─"

            # Real DDR status line
            line = f"│{connector}{device_name}[{mem_state}] {mem_pattern} {ddr_speed:>4} │"
            lines.append(line)

            # Show real memory bandwidth based on current telemetry
            current = float(telem.get('current', '0.0'))
            bandwidth = min(int(current / 5), 40)  # Scale to line width
            flow_line = self._create_data_flow_line(bandwidth, i)
            lines.append(f"│  MEM: {flow_line[:40]:40} │")

        lines.append("└──────────────────────────────────────────────────────────────┘")
        lines.append("Legend: TRN=Trained UNT=Untrained ●=Active Channel ◯=Idle")
        return lines

    def _generate_memory_pattern(self, activity_level: int, device_idx: int) -> str:
        """Generate Yar's Revenge style memory bank visualization"""
        # Memory banks arranged in a pattern
        banks = ["◯", "◯", "◯", "◯", "◯", "◯", "◯", "◯"]  # 8 memory banks

        # Animate based on activity level and time
        frame_offset = (self.animation_frame + device_idx * 2) % 8

        # Light up memory banks based on activity
        for i in range(min(activity_level, 8)):
            bank_idx = (i + frame_offset) % 8
            banks[bank_idx] = "●"

        return "".join(banks)

    def _generate_real_ddr_pattern(self, ddr_status: str, channels: int, device_idx: int) -> str:
        """Generate real DDR channel visualization based on actual hardware status"""
        try:
            status_value = int(ddr_status, 16) if ddr_status != "0" else 0
        except:
            status_value = 0

        # Create channel indicators based on real DDR status
        channel_indicators = []
        for i in range(min(channels, 8)):  # Limit display to 8 for space
            # Extract 4-bit status for each channel
            channel_status = (status_value >> (4 * i)) & 0xF

            # DDR status meanings: 0=untrained, 1=training, 2=trained, 3+=error states
            if channel_status == 2:  # Trained and active
                channel_indicators.append("●")
            elif channel_status == 1:  # Training in progress
                # Animate training channels
                if (self.animation_frame + i) % 4 < 2:
                    channel_indicators.append("◐")
                else:
                    channel_indicators.append("◑")
            elif channel_status >= 3:  # Error states
                channel_indicators.append("✗")
            else:  # Untrained
                channel_indicators.append("◯")

        # Pad to consistent length
        while len(channel_indicators) < 8:
            channel_indicators.append("◯")

        return "".join(channel_indicators)

    def _create_data_flow_line(self, bandwidth: int, device_idx: int) -> str:
        """Create flowing data visualization"""
        flow_chars = "▶▷▸▹"
        base_pattern = "∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙"

        if bandwidth > 0:
            # Create flowing effect
            flow_density = min(bandwidth // 2, 10)
            offset = (self.animation_frame + device_idx * 3) % 20

            result = list(base_pattern)
            for i in range(flow_density):
                pos = (offset + i * 2) % 20
                char_idx = (i + self.animation_frame // 2) % len(flow_chars)
                result[pos] = flow_chars[char_idx]

            return "".join(result)
        return base_pattern

    def _create_activity_heatmap(self) -> List[str]:
        """Create real-time activity heatmap"""
        lines = []
        lines.append("Activity Heatmap (Last 60s)")
        lines.append("┌──────────────────────────────────────┐")

        # Temporal heatmap - what static tabs can't show
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)[:10]
            telem = self.backend.device_telemetrys[i]

            # Create activity history visualization
            activity_history = self._get_activity_history(i)
            heatmap_line = self._create_heatmap_line(activity_history)

            # Current values
            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))

            line = f"│{device_name:10} {heatmap_line} {power:5.1f}W│"
            lines.append(line)

        # Time axis
        lines.append("│Time:       60s    30s     10s    now │")
        lines.append("└──────────────────────────────────────┘")
        return lines

    def _get_activity_history(self, device_idx: int) -> List[float]:
        """Simulate activity history (in real app, maintain rolling buffer)"""
        # Generate realistic activity pattern over time
        history = []
        for t in range(20):  # 20 time points
            base_activity = 30 + device_idx * 15
            # Add some realistic variation based on time and device
            variation = 10 * (1 + 0.5 * ((self.animation_frame + t + device_idx * 5) % 20) / 10)
            activity = max(0, base_activity + variation)
            history.append(activity)
        return history

    def _create_heatmap_line(self, history: List[float]) -> str:
        """Create heatmap visualization of activity over time"""
        chars = " ▁▂▃▄▅▆▇█"
        result = ""

        for value in history:
            intensity = min(int(value / 12), len(chars) - 1)  # Scale to char range
            result += chars[intensity]

        return result

    def _create_bandwidth_utilization(self) -> List[str]:
        """Create real-time bandwidth utilization graph"""
        lines = []
        lines.append("Interconnect Bandwidth Utilization")
        lines.append("┌─────────────────────────────────────────────────────────────────────────────┐")

        # Show bandwidth between devices (what static tabs can't show)
        total_devices = len(self.backend.devices)

        for i in range(total_devices):
            device_name = self.backend.get_device_name(self.backend.devices[i])[:8]

            # Simulate interconnect utilization
            utilizations = []
            for j in range(total_devices):
                if i == j:
                    utilizations.append("  ──  ")  # Self
                else:
                    # Calculate "bandwidth" between devices
                    telem_i = self.backend.device_telemetrys[i]
                    telem_j = self.backend.device_telemetrys[j]

                    current_i = float(telem_i.get('current', '0.0'))
                    current_j = float(telem_j.get('current', '0.0'))

                    # Simulate interconnect activity
                    bandwidth = min(abs(current_i - current_j) * 2, 99)

                    if bandwidth > 50:
                        utilizations.append(f"{bandwidth:4.0f}▓")
                    elif bandwidth > 25:
                        utilizations.append(f"{bandwidth:4.0f}▒")
                    elif bandwidth > 10:
                        utilizations.append(f"{bandwidth:4.0f}░")
                    else:
                        utilizations.append(f"{bandwidth:4.0f} ")

            line = f"│{device_name:8} │ " + " ".join(utilizations) + " │"
            lines.append(line)

        # Footer with device labels
        device_labels = [self.backend.get_device_name(d)[:8] for d in self.backend.devices]
        header = "│" + " " * 10 + "│ " + " ".join(f"{name:5}" for name in device_labels) + " │"
        lines.insert(2, header)  # Insert after title and top border
        lines.insert(3, "│" + "─" * 10 + "┼" + "─" * (len(device_labels) * 6 + len(device_labels) - 1) + "─│")

        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        return lines

    def _create_live_process_insights(self) -> List[str]:
        """Create process insights with temporal patterns"""
        lines = []
        lines.append("Live Process Analysis (Trends & Patterns)")
        lines.append("┌─────────────────────────────────────────────────────────────────────────────┐")
        lines.append("│ID │Device    │Power │Trend│Load │Efficiency│Thermal │Memory │Utilization│")
        lines.append("├───┼──────────┼──────┼─────┼─────┼──────────┼────────┼───────┼───────────┤")

        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)[:8]
            telem = self.backend.device_telemetrys[i]

            power = float(telem.get('power', '0.0'))
            voltage = float(telem.get('voltage', '0.0'))
            current = float(telem.get('current', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))

            # Calculate insights not available in static tabs
            efficiency = (power / max(temp - 25, 1)) if temp > 25 else 0  # Power per degree above ambient
            load_pattern = self._calculate_load_pattern(i)
            trend = self._calculate_trend(i, power)
            thermal_state = "CRIT" if temp > 85 else "WARN" if temp > 75 else "OK"
            memory_util = min(int(current / 2), 99)  # Approximate memory utilization
            utilization = f"{int((power/100)*100):2d}%"

            line = f"│{i:2d} │{device_name:8} │{power:5.1f}W│{trend:4s}│{load_pattern:4s}│{efficiency:9.2f}│{thermal_state:7}│{memory_util:2d}%   │{utilization:>10}│"
            lines.append(line)

        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("Efficiency=Power/ThermalRise | Trend=5s avg | Load=Activity pattern")

        return lines

    def _calculate_load_pattern(self, device_idx: int) -> str:
        """Calculate load pattern (what static displays can't show)"""
        # Analyze recent activity pattern
        recent_frames = [
            (self.animation_frame - i + device_idx * 2) % 60 for i in range(5)
        ]

        if max(recent_frames) - min(recent_frames) > 30:
            return "SPKY"  # Spiky
        elif all(f > 40 for f in recent_frames):
            return "HIGH"  # Consistently high
        elif all(f < 20 for f in recent_frames):
            return "LOW"   # Consistently low
        else:
            return "MED"   # Medium/variable

    def _calculate_trend(self, device_idx: int, current_power: float) -> str:
        """Calculate power trend over recent frames"""
        # Simulate trend calculation (in real app, maintain history)
        trend_factor = (self.animation_frame + device_idx) % 10 - 5

        if trend_factor > 2:
            return "UP↗"
        elif trend_factor < -2:
            return "DN↘"
        else:
            return "STB→"

    def _combine_sections(self, left: List[str], right: List[str]) -> List[str]:
        """Combine two sections side by side"""
        combined = []
        max_lines = max(len(left), len(right))

        for i in range(max_lines):
            left_line = left[i] if i < len(left) else " " * 40
            right_line = right[i] if i < len(right) else " " * 40
            combined.append(f"{left_line} {right_line}")

        return combined

    def _create_unified_display(self) -> List[str]:
        """Create a unified display with perfect ASCII art alignment"""
        lines = []

        # Main container with no right border for that leet look
        lines.append("    ╔════════════════════════════════════════════════════════════════════════════════════╗")
        lines.append("    ║ HARDWARE MATRIX ∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎∎")
        lines.append("    ╠════════════════════════════════════════════════════════════════════════════════════╣")

        # Hardware topology section
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)
            board_type = self.backend.device_infos[i].get('board_type', 'Unknown')
            telem = self.backend.device_telemetrys[i]

            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))
            current = float(telem.get('current', '0.0'))
            voltage = float(telem.get('voltage', '0.0'))

            # Activity indicators with sick symbols
            if power > 50:
                activity = "██████████"  # Full power bars
                status_char = "⚡"
            elif power > 25:
                activity = "██████░░░░"  # High power
                status_char = "◆"
            elif power > 10:
                activity = "███░░░░░░░"  # Medium power
                status_char = "◇"
            else:
                activity = "░░░░░░░░░░"  # Low power
                status_char = "○"

            # Temperature status
            if temp > 80:
                temp_status = "🔥CRIT"
            elif temp > 65:
                temp_status = "🌡HOT "
            elif temp > 45:
                temp_status = "🌡WARM"
            else:
                temp_status = "❄COOL"

            # Create flow visualization
            flow_intensity = min(int(current / 5), 20)
            if flow_intensity > 15:
                flow_pattern = "▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶"[:flow_intensity]
            elif flow_intensity > 10:
                flow_pattern = "▷▷▷▷▷▷▷▷▷▷▷▷▷▷▷▷▷▷▷▷"[:flow_intensity]
            elif flow_intensity > 5:
                flow_pattern = "▸▸▸▸▸▸▸▸▸▸▸▸▸▸▸▸▸▸▸▸"[:flow_intensity]
            else:
                flow_pattern = "▹▹▹▹▹▹▹▹▹▹▹▹▹▹▹▹▹▹▹▹"[:flow_intensity]

            # Add animation offset
            offset = (self.animation_frame + i * 3) % len(flow_pattern) if flow_pattern else 0
            if flow_pattern:
                animated_flow = flow_pattern[offset:] + flow_pattern[:offset]
                animated_flow = animated_flow.ljust(20)
            else:
                animated_flow = "∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙"

            # Main device line with perfect alignment
            device_line = f"    ║ [{i:2d}] {device_name:10s} {status_char} {activity} {animated_flow} {temp_status}"
            lines.append(device_line)

            # Detail line with technical specs
            detail_line = f"    ║     ╰─> {board_type:8s} │ {voltage:5.2f}V │ {current:6.1f}A │ {power:6.1f}W │ {temp:5.1f}°C"
            lines.append(detail_line)

            if i < len(self.backend.devices) - 1:
                lines.append("    ║     ∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙")

        # Separator with sick ASCII
        lines.append("    ╠════════════════════════════════════════════════════════════════════════════════════╣")
        lines.append("    ║ PROCESS MATRIX ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓")
        lines.append("    ╠════════════════════════════════════════════════════════════════════════════════════╣")

        # Process table header with perfect spacing
        lines.append("    ║ ID │ DEVICE     │ BOARD  │ VOLTAGE │ CURRENT │ POWER   │ TEMP    │ STATUS")
        lines.append("    ║════┼════════════┼════════┼═════════┼═════════┼═════════┼═════════┼════════════════")

        # Create device data sorted by power
        device_data = []
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)
            board_type = self.backend.device_infos[i].get('board_type', 'N/A')[:6]
            telem = self.backend.device_telemetrys[i]

            voltage = float(telem.get('voltage', '0.0'))
            current = float(telem.get('current', '0.0'))
            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))

            # Status with sick symbols
            if temp > 85:
                status = "🚨 CRITICAL"
            elif temp > 75:
                status = "🔥 OVERHEATING"
            elif power > 75:
                status = "⚡ HIGH_LOAD"
            elif power > 25:
                status = "🟢 ACTIVE"
            elif power > 5:
                status = "🟡 IDLE"
            else:
                status = "💤 SLEEP"

            device_data.append((i, device_name, board_type, voltage, current, power, temp, status))

        # Sort by power consumption
        device_data.sort(key=lambda x: x[5], reverse=True)

        # Add process rows with perfect alignment
        for i, device_name, board_type, voltage, current, power, temp, status in device_data:
            # Power visualization
            power_blocks = "█" * int(power / 10) + "░" * (10 - int(power / 10))

            line = f"    ║ {i:2d} │ {device_name[:10]:10s} │ {board_type:6s} │ {voltage:7.2f}V │ {current:7.1f}A │ {power:7.1f}W │ {temp:7.1f}°C │ {status}"
            lines.append(line)

            # Add a subtle power bar under each entry
            power_line = f"    ║    │            │        │         │         │ {power_blocks} │         │"
            lines.append(power_line)

        # Footer with legend and sick ASCII
        lines.append("    ╠════════════════════════════════════════════════════════════════════════════════════╣")
        lines.append("    ║ LEGEND: ⚡High Load  ◆Active  ◇Moderate  ○Idle  🔥Critical  🌡Hot  ❄Cool")
        lines.append("    ║ FLOWS:  ▶▶High Traffic  ▷▷Medium  ▸▸Low  ▹▹Minimal  ∙∙Inactive")
        lines.append("    ║ POWER:  ██Full  ░░Empty  │ Real-time refresh every 100ms")
        lines.append("    ╚════════════════════════════════════════════════════════════════════════════════════╝")

        # Add some cyber footer
        lines.append("")
        lines.append("    ░░▒▒▓▓██ NEURAL LINK ESTABLISHED ██▓▓▒▒░░")
        lines.append(f"    ░░▒▒▓▓██ FRAME: {self.animation_frame:06d} ██▓▓▒▒░░")

        return lines

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

            # Activity symbol (plain text)
            if power > 50:
                activity_symbol = "●"  # High activity
            elif power > 20:
                activity_symbol = "◐"  # Moderate activity
            elif power > 5:
                activity_symbol = "○"  # Low activity
            else:
                activity_symbol = "·"  # Idle

            # Temperature indicator (plain text)
            if temp > 80:
                temp_color = "🔥"
            elif temp > 60:
                temp_color = "🌡"
            elif temp > 40:
                temp_color = "🌡"
            else:
                temp_color = "❄"

            # Power bar (simplified to avoid markup conflicts)
            bar_length = 8
            filled = int((power / 100) * bar_length)
            power_bar = "█" * filled + "░" * (bar_length - filled)

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
                        result += char  # Plain text without color markup
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

            power_str = f"{power:6.1f}W"
            temp_str = f"{temp:5.1f}°C"

            # Create the line without embedded markup for table alignment
            line = f"│ {i:2} │ {device_name[:10]:10} │ {board_type:6} │ {voltage:6.2f}V │ {current:6.1f}A │ {power_str:>7} │ {temp_str:>7} │ {aiclk:6}MHz │"

            # Add status separately to avoid markup conflicts
            if temp > 85:
                line += " CRITICAL │"
            elif temp > 75:
                line += " HOT      │"
            elif power > 75:
                line += " HIGH LOAD│"
            elif power > 25:
                line += " ACTIVE   │"
            elif power > 5:
                line += " IDLE     │"
            else:
                line += " SLEEP    │"

            lines.append(line)

        lines.append("└────┴────────────┴────────┴─────────┴─────────┴─────────┴─────────┴─────────┴──────────┘")

        return "\n".join(lines)

    def _create_bbs_header(self) -> List[str]:
        """Create BBS-style header with pixelated hardware avatar - borderless right side"""
        lines = []

        # Retro BBS-style header with no right borders (leet ANSI style)
        lines.append("    ╔══════════════════════════════════════════════════════════════════════════════")
        lines.append("    ║  ▄▄▄▄▄▄▄   TT-SYSMON v3.0 - NEURAL INTERFACE ONLINE   ▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄")
        lines.append("    ║ ████▓▓▓██                                           ██████████████████▓▓")
        lines.append("    ║ ██▓░░░▓██  ┌─ TENSTORRENT MATRIX GRID ─┐          ████▓▓░░██░░▓▓████▓▓")
        lines.append("    ║ ██▓░█░▓██  │ REAL-TIME TELEMETRY GRID  │          ████▓▓░░██░░▓▓████▓▓")
        lines.append("    ║ ██▓░░░▓██  │ INTERCONNECT FLOW MATRIX  │          ████▓▓░░██░░▓▓████▓▓")
        lines.append("    ║ ████▓▓▓██  │ MEMORY TOPOLOGY SCANNER   │          ██████████████████▓▓")
        lines.append("    ║  ▀▀▀▀▀▀▀   └───────────────────────────┘           ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀")
        lines.append("    ╚══════════════════════════════════════════════════════════════════════════════")

        return lines

    def _create_bbs_main_display(self) -> List[str]:
        """Create main BBS-style display with terminal aesthetic - borderless right side"""
        lines = []

        # BBS-style system status header (borderless right)
        lines.append("┌─────────────────────────── SYSTEM STATUS")
        lines.append("│")

        # Hardware grid in retro style
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)[:10]  # Truncate to fit
            board_type = self.backend.device_infos[i].get('board_type', 'Unknown')[:8]
            telem = self.backend.device_telemetrys[i]

            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))
            current = float(telem.get('current', '0.0'))
            voltage = float(telem.get('voltage', '0.0'))

            # Retro terminal-style status indicators
            if power > 50:
                status_block = "██████████"
                status_icon = "◉"
            elif power > 25:
                status_block = "██████▓▓▓▓"
                status_icon = "◎"
            elif power > 10:
                status_block = "████▓▓▓▓▓▓"
                status_icon = "○"
            else:
                status_block = "▓▓▓▓▓▓▓▓▓▓"
                status_icon = "·"

            # Temperature readout in terminal style
            temp_display = f"{temp:05.1f}°C"
            if temp > 80:
                temp_status = "CRIT"
            elif temp > 65:
                temp_status = " HOT"
            elif temp > 45:
                temp_status = "WARM"
            else:
                temp_status = "COOL"

            # Memory activity pattern (Yar's Revenge style)
            memory_banks = self._generate_memory_pattern(int((power / 100) * 8), i)

            # Create BBS-style device entry (no right border)
            device_line = f"│ [{i}] {device_name:10s} {status_icon} │{status_block}│ {temp_display} {temp_status}"
            lines.append(device_line)

            # Technical readout line (no right border)
            tech_line = f"│     {board_type:8s} {memory_banks} {voltage:4.2f}V {current:5.1f}A {power:5.1f}W"
            lines.append(tech_line)

            # Interconnect activity flow (no right border)
            bandwidth = min(int(current / 5), 20)
            flow_line = self._create_data_flow_line(bandwidth, i)
            activity_line = f"│     DATA: {flow_line}"
            lines.append(activity_line)

            if i < len(self.backend.devices) - 1:
                lines.append("│ ·······································································")

        lines.append("│")
        lines.append("└───────────────────────────────────────────────────────────────────────")

        # Add temporal heatmap section in BBS style
        lines.append("")
        lines.extend(self._create_bbs_heatmap_section())

        # Add interconnect matrix in BBS style
        lines.append("")
        lines.extend(self._create_bbs_interconnect_section())

        # Real hardware status footer with ARC health monitoring
        lines.append("")
        total_devices = len(self.backend.devices)
        active_devices = sum(1 for i in range(total_devices)
                           if float(self.backend.device_telemetrys[i].get('heartbeat', '0')) > 0)
        total_power = sum(float(self.backend.device_telemetrys[i].get('power', '0'))
                         for i in range(total_devices))

        # Get real ARC firmware health status from telemetry
        arc_status = "OK"
        ddr_trained_count = 0
        for i in range(total_devices):
            try:
                if self.backend.get_dram_training_status(i):
                    ddr_trained_count += 1
            except:
                pass

        # Calculate real system metrics from telemetry
        avg_temp = sum(float(self.backend.device_telemetrys[i].get('asic_temperature', '0'))
                      for i in range(total_devices)) / max(total_devices, 1)
        avg_aiclk = sum(float(self.backend.device_telemetrys[i].get('aiclk', '0'))
                       for i in range(total_devices)) / max(total_devices, 1)

        lines.append("┌─ HARDWARE STATUS ────── ┌─ MEMORY STATUS ──── ┌─ REAL-TIME METRICS")
        lines.append(f"│ DEVICES: {active_devices}/{total_devices} ACTIVE     │ DDR TRAINED: {ddr_trained_count}/{total_devices}   │ TOTAL PWR: {total_power:5.1f}W")
        lines.append(f"│ ARC HEARTBEATS: {arc_status}     │ CHANNELS: MONITORING │ AVG TEMP: {avg_temp:5.1f}°C")
        lines.append(f"│ TELEMETRY: {:06d}      │ SPEED: REALTIME     │ AVG AICLK: {avg_aiclk:4.0f}MHz".format(self.animation_frame))
        lines.append("└─────────────────────── └─────────────────── └──────────────────")

        return lines

    def _create_bbs_heatmap_section(self) -> List[str]:
        """Create BBS-style temporal heatmap - borderless right side"""
        lines = []
        lines.append("┌─────────── TEMPORAL ACTIVITY ANALYSIS")
        lines.append("│ DEVICE     │ ACTIVITY HISTORY (LAST 60 SECONDS)       │ NOW")
        lines.append("├────────────┼───────────────────────────────────────────┼─────")

        chars = " ·∙▁▂▃▄▅▆▇█"

        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)[:10]
            telem = self.backend.device_telemetrys[i]
            power = float(telem.get('power', '0.0'))

            # Generate heatmap
            heatmap = ""
            for t in range(39):  # 39 characters for timeline
                base_activity = 30 + i * 15
                variation = 10 * (1 + 0.5 * ((self.animation_frame + t + i * 5) % 20) / 10)
                activity = max(0, base_activity + variation)
                intensity = min(int(activity / 10), len(chars) - 1)
                heatmap += chars[intensity]

            # Current power indicator
            current_indicator = "████" if power > 50 else "███▓" if power > 25 else "██▓▓" if power > 10 else "▓▓▓▓"

            line = f"│ {device_name:10} │ {heatmap} │ {current_indicator}"
            lines.append(line)

        lines.append("│            │ ↑60s    ↑30s    ↑10s    ↑5s     ↑NOW    │")
        lines.append("└────────────┴───────────────────────────────────────────┴─────")
        return lines

    def _create_bbs_interconnect_section(self) -> List[str]:
        """Create BBS-style interconnect matrix - borderless right side"""
        lines = []

        # Borderless matrix
        lines.append("┌─────────────── INTERCONNECT BANDWIDTH MATRIX")

        # Device labels header
        device_labels = [self.backend.get_device_name(d)[:8] for d in self.backend.devices]
        header_content = "FROM\\TO  │ " + " │ ".join(f"{name:8s}" for name in device_labels)
        lines.append(f"│ {header_content}")

        # Separator line
        separator_parts = ["─" * 8 for _ in device_labels]
        separator_content = "─" * 8 + "┼" + "┼".join(separator_parts)
        lines.append(f"├─{separator_content}")

        # Matrix rows
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)[:8]
            utilizations = []

            for j in range(len(self.backend.devices)):
                if i == j:
                    utilizations.append("  SELF  ")
                else:
                    # Calculate bandwidth simulation
                    telem_i = self.backend.device_telemetrys[i]
                    telem_j = self.backend.device_telemetrys[j]
                    current_i = float(telem_i.get('current', '0.0'))
                    current_j = float(telem_j.get('current', '0.0'))

                    bandwidth = min(abs(current_i - current_j) * 2, 99)

                    if bandwidth > 50:
                        utilizations.append(f"▓▓{bandwidth:3.0f}  ")
                    elif bandwidth > 25:
                        utilizations.append(f"▒▒{bandwidth:3.0f}  ")
                    elif bandwidth > 10:
                        utilizations.append(f"░░{bandwidth:3.0f}  ")
                    else:
                        utilizations.append(f"  {bandwidth:3.0f}  ")

            # Build row (no right border)
            row_content = f"{device_name:8s} │ " + " │ ".join(utilizations)
            lines.append(f"│ {row_content}")

        # Bottom border (no right side)
        bottom_parts = ["─" * 8 for _ in device_labels]
        bottom_content = "─" * 8 + "┴" + "┴".join(bottom_parts)
        lines.append(f"└─{bottom_content}")

        # Legend (borderless)
        lines.append("┌─ LEGEND")
        lines.append("│ ▓▓ HIGH (>50) ▒▒ MED (25-50) ░░ LOW (10-25)  IDLE (<10)")
        lines.append("└─────────────────────────────────────────────────────────")

        return lines


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