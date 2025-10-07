#!/usr/bin/env python3
"""
Test script for the fixed TT-Top widget without hardware dependencies
"""

import sys
import time
from typing import Dict, List
from textual.widgets import Static
from textual.containers import Container
from textual.app import ComposeResult


class MockConstants:
    GUI_INTERVAL_TIME = 0.1


class MockDevice:
    def __init__(self, device_id: int, device_type: str, board_type: str):
        self.device_id = device_id
        self.device_type = device_type
        self.board_type = board_type
        self.base_power = 20 + device_id * 15

    def get_telemetry(self) -> Dict:
        power_variation = (time.time() * (self.device_id + 1)) % 10
        power = self.base_power + power_variation
        return {
            'voltage': f"{0.8 + power/100:.2f}",
            'current': f"{power/0.8:.1f}",
            'power': f"{power:.1f}",
            'asic_temperature': f"{35 + power/2:.1f}",
            'aiclk': f"{800 + power*5:.0f}",
            'heartbeat': str(int(time.time()) % 4)
        }


class MockTTSMIBackend:
    def __init__(self):
        self.devices = [
            MockDevice(0, "Grayskull", "e75"),
            MockDevice(1, "Wormhole", "n300"),
            MockDevice(2, "Blackhole", "p150a"),
        ]
        self.device_infos = [
            {'board_type': device.board_type, 'bus_id': f"0000:0{i}:00.0"}
            for i, device in enumerate(self.devices)
        ]
        self.update_telem()

    def get_device_name(self, device: MockDevice) -> str:
        return device.device_type

    def update_telem(self):
        self.device_telemetrys = [device.get_telemetry() for device in self.devices]


class TTTopDisplay(Static):
    """Fixed TT-Top display widget"""

    def __init__(self, backend: MockTTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.animation_frame = 0

    def on_mount(self) -> None:
        self.set_interval(MockConstants.GUI_INTERVAL_TIME, self._update_display)

    def _update_display(self) -> None:
        try:
            self.backend.update_telem()
            self.animation_frame += 1
            content = self._render_complete_display()
            self.update(content)
        except Exception as e:
            self.update(f"Error: {e}")

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
        """Create memory topology visualization inspired by Yar's Revenge"""
        lines = []
        lines.append("Memory Topology & Interconnects")
        lines.append("┌──────────────────────────────────────┐")

        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)[:3].upper()
            telem = self.backend.device_telemetrys[i]
            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))
            current = float(telem.get('current', '0.0'))

            # Memory banks visualization (8 memory banks)
            banks = ["◯"] * 8
            activity_level = int((power / 100) * 8)
            frame_offset = (self.animation_frame + i * 2) % 8

            for j in range(min(activity_level, 8)):
                bank_idx = (j + frame_offset) % 8
                banks[bank_idx] = "●"

            memory_pattern = "".join(banks)

            # Interconnect connector
            connector = "┌─" if i == 0 else "└─" if i == len(self.backend.devices) - 1 else "├─"

            # Temperature-based state
            mem_state = "HOT" if temp > 75 else "ACT" if temp > 50 else "IDL"
            mem_char = "█" if temp > 75 else "▓" if temp > 50 else "░"

            line = f"│{connector}{device_name}[{mem_state}] {memory_pattern} {mem_char*3} │"
            lines.append(line)

            # Data flow visualization
            bandwidth = min(int(current / 5), 20)
            if bandwidth > 0:
                flow_chars = "▶▷▸▹"
                flow_density = min(bandwidth // 2, 10)
                offset = (self.animation_frame + i * 3) % 20

                flow_line = list("∙" * 20)
                for j in range(flow_density):
                    pos = (offset + j * 2) % 20
                    char_idx = (j + self.animation_frame // 2) % len(flow_chars)
                    flow_line[pos] = flow_chars[char_idx]

                flow_str = "".join(flow_line)
            else:
                flow_str = "∙" * 20

            lines.append(f"│  {flow_str}           │")

        lines.append("└──────────────────────────────────────┘")
        return lines

    def _create_activity_heatmap(self) -> List[str]:
        """Create real-time activity heatmap"""
        lines = []
        lines.append("Activity Heatmap (Last 60s)")
        lines.append("┌──────────────────────────────────────┐")

        chars = " ▁▂▃▄▅▆▇█"

        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)[:10]
            telem = self.backend.device_telemetrys[i]
            power = float(telem.get('power', '0.0'))

            # Simulate temporal activity pattern
            heatmap = ""
            for t in range(20):  # 20 time points
                base_activity = 30 + i * 15
                variation = 10 * (1 + 0.5 * ((self.animation_frame + t + i * 5) % 20) / 10)
                activity = max(0, base_activity + variation)
                intensity = min(int(activity / 12), len(chars) - 1)
                heatmap += chars[intensity]

            line = f"│{device_name:10} {heatmap} {power:5.1f}W│"
            lines.append(line)

        lines.append("│Time:       60s    30s     10s    now │")
        lines.append("└──────────────────────────────────────┘")
        return lines

    def _create_bandwidth_utilization(self) -> List[str]:
        """Create interconnect bandwidth visualization"""
        lines = []
        lines.append("Interconnect Bandwidth Utilization")
        lines.append("┌─────────────────────────────────────────────────────────────────────────────┐")

        device_labels = [self.backend.get_device_name(d)[:8] for d in self.backend.devices]
        header = "│" + " " * 10 + "│ " + " ".join(f"{name:5}" for name in device_labels) + " │"
        lines.append(header)
        lines.append("│" + "─" * 10 + "┼" + "─" * (len(device_labels) * 6 + len(device_labels) - 1) + "─│")

        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)[:8]
            utilizations = []

            for j in range(len(self.backend.devices)):
                if i == j:
                    utilizations.append("  ──  ")
                else:
                    telem_i = self.backend.device_telemetrys[i]
                    telem_j = self.backend.device_telemetrys[j]
                    current_i = float(telem_i.get('current', '0.0'))
                    current_j = float(telem_j.get('current', '0.0'))

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
            current = float(telem.get('current', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))

            # Calculate unique insights
            efficiency = (power / max(temp - 25, 1)) if temp > 25 else 0

            # Load pattern analysis
            recent_frames = [(self.animation_frame - j + i * 2) % 60 for j in range(5)]
            if max(recent_frames) - min(recent_frames) > 30:
                load_pattern = "SPKY"
            elif all(f > 40 for f in recent_frames):
                load_pattern = "HIGH"
            elif all(f < 20 for f in recent_frames):
                load_pattern = "LOW"
            else:
                load_pattern = "MED"

            # Trend calculation
            trend_factor = (self.animation_frame + i) % 10 - 5
            if trend_factor > 2:
                trend = "UP↗"
            elif trend_factor < -2:
                trend = "DN↘"
            else:
                trend = "STB→"

            thermal_state = "CRIT" if temp > 85 else "WARN" if temp > 75 else "OK"
            memory_util = min(int(current / 2), 99)
            utilization = f"{int((power/100)*100):2d}%"

            line = f"│{i:2d} │{device_name:8} │{power:5.1f}W│{trend:4s}│{load_pattern:4s}│{efficiency:9.2f}│{thermal_state:7}│{memory_util:2d}%   │{utilization:>10}│"
            lines.append(line)

        lines.append("└─────────────────────────────────────────────────────────────────────────────┘")
        lines.append("Efficiency=Power/ThermalRise | Trend=5s avg | Load=Activity pattern")
        return lines

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
        """Create a unified display with sick ASCII art and perfect alignment"""
        lines = []

        # Main container
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

            # Activity indicators
            if power > 50:
                activity = "██████████"
                status_char = "⚡"
            elif power > 25:
                activity = "██████░░░░"
                status_char = "◆"
            elif power > 10:
                activity = "███░░░░░░░"
                status_char = "◇"
            else:
                activity = "░░░░░░░░░░"
                status_char = "○"

            # Temperature status
            temp_status = "🔥CRIT" if temp > 80 else "🌡HOT " if temp > 65 else "🌡WARM" if temp > 45 else "❄COOL"

            # Flow visualization
            flow_intensity = min(int(current / 5), 20)
            flow_chars = ["▹", "▸", "▷", "▶"]
            flow_char = flow_chars[min(flow_intensity // 5, 3)]
            animated_flow = (flow_char * flow_intensity).ljust(20)

            # Device lines
            device_line = f"    ║ [{i:2d}] {device_name:10s} {status_char} {activity} {animated_flow} {temp_status}"
            lines.append(device_line)

            detail_line = f"    ║     ╰─> {board_type:8s} │ {voltage:5.2f}V │ {current:6.1f}A │ {power:6.1f}W │ {temp:5.1f}°C"
            lines.append(detail_line)

            if i < len(self.backend.devices) - 1:
                lines.append("    ║     ∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙∙")

        # Process section
        lines.append("    ╠════════════════════════════════════════════════════════════════════════════════════╣")
        lines.append("    ║ PROCESS MATRIX ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓")
        lines.append("    ╠════════════════════════════════════════════════════════════════════════════════════╣")
        lines.append("    ║ ID │ DEVICE     │ BOARD  │ VOLTAGE │ CURRENT │ POWER   │ TEMP    │ STATUS")
        lines.append("    ║════┼════════════┼════════┼═════════┼═════════┼═════════┼═════════┼════════════════")

        # Process data
        device_data = []
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)
            board_type = self.backend.device_infos[i].get('board_type', 'N/A')[:6]
            telem = self.backend.device_telemetrys[i]

            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))

            status = "🚨 CRITICAL" if temp > 85 else "🔥 OVERHEATING" if temp > 75 else "⚡ HIGH_LOAD" if power > 75 else "🟢 ACTIVE" if power > 25 else "🟡 IDLE" if power > 5 else "💤 SLEEP"

            device_data.append((i, device_name, board_type, float(telem.get('voltage', '0.0')), float(telem.get('current', '0.0')), power, temp, status))

        device_data.sort(key=lambda x: x[5], reverse=True)

        for i, device_name, board_type, voltage, current, power, temp, status in device_data:
            power_blocks = "█" * int(power / 10) + "░" * (10 - int(power / 10))
            line = f"    ║ {i:2d} │ {device_name[:10]:10s} │ {board_type:6s} │ {voltage:7.2f}V │ {current:7.1f}A │ {power:7.1f}W │ {temp:7.1f}°C │ {status}"
            lines.append(line)
            power_line = f"    ║    │            │        │         │         │ {power_blocks} │         │"
            lines.append(power_line)

        # Footer
        lines.append("    ╠════════════════════════════════════════════════════════════════════════════════════╣")
        lines.append("    ║ LEGEND: ⚡High Load  ◆Active  ◇Moderate  ○Idle  🔥Critical  🌡Hot  ❄Cool")
        lines.append("    ║ FLOWS:  ▶High Traffic  ▷Medium  ▸Low  ▹Minimal  ∙Inactive")
        lines.append("    ║ POWER:  ██Full  ░░Empty  │ Real-time refresh every 100ms")
        lines.append("    ╚════════════════════════════════════════════════════════════════════════════════════╝")

        lines.append("")
        lines.append("    ░░▒▒▓▓██ NEURAL LINK ESTABLISHED ██▓▓▒▒░░")
        lines.append(f"    ░░▒▒▓▓██ FRAME: {self.animation_frame:06d} ██▓▓▒▒░░")

        return lines

    def _create_chip_grid(self) -> List[str]:
        grid_lines = []
        grid_lines.append("┌─ Hardware Topology & Activity ────────┐")
        grid_lines.append("│                                        │")

        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)
            board_type = self.backend.device_infos[i].get('board_type', 'Unknown')
            telem = self.backend.device_telemetrys[i]

            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))

            # Simple symbols without markup
            activity_symbol = "●" if power > 30 else "○"
            temp_symbol = "🔥" if temp > 60 else "🌡"

            chip_line = f"│ [{i:2}] {device_name:10} {activity_symbol} {temp_symbol}│"
            detail_line = f"│     {board_type:10} {'█' * min(8, int(power/10))} {temp:4.1f}°C │"

            grid_lines.append(chip_line)
            grid_lines.append(detail_line)

        grid_lines.append("│                                        │")
        grid_lines.append("│ Legend: ● Active  ○ Idle              │")
        grid_lines.append("└────────────────────────────────────────┘")

        return grid_lines

    def _create_process_table(self) -> str:
        lines = []
        lines.append("┌─ Live Hardware Processes & Activity ──────────────────────┐")
        lines.append("│ ID │ Device     │ Board  │ Power   │ Temp    │ Status  │")
        lines.append("├────┼────────────┼────────┼─────────┼─────────┼─────────┤")

        device_data = []
        for i, device in enumerate(self.backend.devices):
            device_name = self.backend.get_device_name(device)
            board_type = self.backend.device_infos[i].get('board_type', 'N/A')[:6]
            telem = self.backend.device_telemetrys[i]

            power = float(telem.get('power', '0.0'))
            temp = float(telem.get('asic_temperature', '0.0'))

            status = "HOT" if temp > 75 else "ACTIVE" if power > 25 else "IDLE"
            device_data.append((i, device_name, board_type, power, temp, status))

        device_data.sort(key=lambda x: x[3], reverse=True)

        for i, device_name, board_type, power, temp, status in device_data:
            line = f"│ {i:2} │ {device_name[:10]:10} │ {board_type:6} │ {power:6.1f}W │ {temp:6.1f}°C │ {status:7} │"
            lines.append(line)

        lines.append("└────┴────────────┴────────┴─────────┴─────────┴─────────┘")
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

        # Terminal-style footer (keep as 3 separate boxes)
        lines.append("")
        lines.append("┌─ NEURAL LINK STATUS ──┐ ┌─ REFRESH CYCLE ──┐ ┌─ CONNECTION ─┐")
        lines.append("│ ◉ MATRIX SYNCHRONIZED │ │ FRAME: {:06d}    │ │ ████████████ │".format(self.animation_frame))
        lines.append("│ ◉ TELEMETRY ACTIVE    │ │ RATE:  10.0 Hz    │ │ SIGNAL: GOOD │")
        lines.append("│ ◉ FLOW TRACKING ON    │ │ LAG:   0.001ms    │ │ UPTIME: {}s │".format(int(self.animation_frame / 10)))
        lines.append("└───────────────────────┘ └───────────────────┘ └──────────────┘")

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


class TTLiveMonitor(Container):
    def __init__(self, backend: MockTTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend

    def compose(self) -> ComposeResult:
        yield TTTopDisplay(backend=self.backend, id="tt_top_display")


def main():
    print("Testing TTTop widget without hardware dependencies...")

    # Test widget creation
    backend = MockTTSMIBackend()
    display = TTTopDisplay(backend)
    print("✓ Widget creation successful")

    # Test display rendering
    try:
        content = display._render_complete_display()
        print("✓ Display rendering successful")
        print("\nSample output:")
        print(content[:300] + "...")
        return True
    except Exception as e:
        print(f"✗ Display rendering failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)