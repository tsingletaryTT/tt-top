#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Simplified Animated Display - bypass CSS issues

A minimal version of the animated display to isolate display issues.
"""

import time
from typing import List
from textual.widget import Widget
from textual.widgets import Static

class SimpleHardwareDisplay(Static):
    """Simplified hardware display widget with minimal CSS requirements"""

    def __init__(self, backend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.frame_count = 0
        self.start_time = time.time()

    def on_mount(self) -> None:
        """Initialize the simple display"""
        # Start simple animation loop
        self.set_interval(0.5, self._update_simple_display)  # 2 FPS for debugging

    def _update_simple_display(self) -> None:
        """Simple update with basic content"""
        try:
            # Update backend telemetry
            self.backend.update_telem()
            self.frame_count += 1

            # Create simple content
            content = self._create_simple_content()

            # Update the widget
            self.update(content)

        except Exception as e:
            # Show errors clearly
            error_content = f"""
SIMPLE DISPLAY ERROR

Error: {e}
Frame: {self.frame_count}
Time: {time.time() - self.start_time:.1f}s

If you see this, the widget update mechanism is working
but there's an error in content generation.
"""
            self.update(error_content)

    def _create_simple_content(self) -> str:
        """Create very simple content to test display"""
        lines = []

        # Simple header
        lines.append("=" * 60)
        lines.append("SIMPLE HARDWARE DISPLAY TEST")
        lines.append(f"Frame: {self.frame_count} | Time: {time.time() - self.start_time:.1f}s")
        lines.append("=" * 60)
        lines.append("")

        # Device info
        if len(self.backend.devices) > 0:
            for i, device in enumerate(self.backend.devices):
                try:
                    telem = self.backend.device_telemetrys[i]
                    power = float(telem.get('power', '0.0'))
                    current = float(telem.get('current', '0.0'))
                    temp = float(telem.get('asic_temperature', '0.0'))

                    lines.append(f"Device {i}: {power:.1f}W, {current:.1f}A, {temp:.1f}C")

                    # Simple "stars" based on power
                    if power > 20:
                        stars = "*** HIGH POWER ***"
                    elif power > 15:
                        stars = "** medium power **"
                    elif power > 10:
                        stars = "* low power *"
                    else:
                        stars = ". idle ."

                    lines.append(f"  Activity: {stars}")
                    lines.append("")

                except Exception as e:
                    lines.append(f"Device {i}: Error reading telemetry - {e}")
                    lines.append("")
        else:
            lines.append("No devices detected")
            lines.append("")

        # Simple "starfield" using text
        lines.append("SIMPLE STARFIELD:")
        for row in range(8):
            star_line = ""
            for col in range(20):
                # Create simple pattern
                if (row + col + self.frame_count) % 4 == 0:
                    star_line += "* "
                elif (row + col + self.frame_count) % 6 == 0:
                    star_line += "o "
                else:
                    star_line += ". "
            lines.append(star_line)

        lines.append("")
        lines.append("If you see this content, the widget display is working!")
        lines.append("Press 'v' to exit visualization mode")
        lines.append("=" * 60)

        return "\n".join(lines)


def create_simple_display_app():
    """Create a simple test app"""
    from textual.app import App
    from textual.binding import Binding
    from textual.containers import Container
    from tt_top.tt_smi_backend import TTSMIBackend, HARDWARE_AVAILABLE
    from tt_top.safety import SafetyConfig

    class SimpleDisplayApp(App):
        CSS = """
        SimpleHardwareDisplay {
            width: 100%;
            height: 100%;
            background: black;
            color: white;
            padding: 1;
            margin: 0;
            border: none;
        }
        """

        BINDINGS = [
            Binding("q", "quit", "Quit"),
            Binding("escape", "quit", "Quit"),
        ]

        def __init__(self):
            super().__init__()

            # Create backend
            if HARDWARE_AVAILABLE:
                from tt_top.tt_smi_backend import detect_chips_with_callback
                devices = detect_chips_with_callback(print_status=False)
                if not devices:
                    from tt_top.mock_hardware import MockPciChip
                    devices = [MockPciChip(0)]
            else:
                from tt_top.mock_hardware import MockPciChip
                devices = [MockPciChip(0)]

            safety_config = SafetyConfig()
            self.backend = TTSMIBackend(devices=devices, fully_init=True, safety_config=safety_config)

        def compose(self):
            yield SimpleHardwareDisplay(backend=self.backend)

        def action_quit(self):
            self.exit()

    return SimpleDisplayApp()


if __name__ == "__main__":
    app = create_simple_display_app()
    app.run()