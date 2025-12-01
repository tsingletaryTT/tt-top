#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-Top - Real-time hardware monitoring for Tenstorrent silicon

A standalone application forked from TT-SMI, focused exclusively on
live hardware visualization and telemetry monitoring.
"""

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from textual.app import App
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.widgets import Footer

from tt_top.json_backend_adapter import JSONBackendAdapter
from tt_top.tt_top_widget import TTLiveMonitor
from tt_top.animated_display import HardwareResponsiveASCII
from tt_top.simple_animated_display import SimpleHardwareDisplay

# Set up logging
import logging
logger = logging.getLogger(__name__)


class TTTopApp(App[None]):
    """
    TT-Top - Standalone real-time hardware monitoring application

    Provides live telemetry visualization for Tenstorrent devices without
    the traditional TT-SMI tab interface. Focused on continuous monitoring
    and real-time hardware insights.
    """

    CSS = """
    Screen {
        background: black;
    }

    TTLiveMonitor {
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
    }

    HardwareResponsiveASCII {
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 0;
        background: black;
        color: white;
        border: none;
        box-sizing: border-box;
    }

    SimpleHardwareDisplay {
        width: 100%;
        height: 100%;
        margin: 0;
        padding: 1;
        background: black;
        color: white;
        border: solid $accent;
    }

    Footer {
        background: $surface;
        color: $text;
        dock: bottom;
    }
    """

    TITLE = "TT-Top - Tenstorrent Hardware Monitor"
    SUB_TITLE = "Real-time telemetry and hardware visualization"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("h", "help", "Help", priority=True),
        Binding("v", "toggle_visualization", "Toggle Visualization", priority=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("escape", "exit_mode", "Exit Mode", show=False),
        # Scrolling bindings for the live monitor
        Binding("up", "scroll_up", "Scroll Up", show=False),
        Binding("down", "scroll_down", "Scroll Down", show=False),
        Binding("page_up", "page_up", "Page Up", show=False),
        Binding("page_down", "page_down", "Page Down", show=False),
        Binding("home", "scroll_home", "Home", show=False),
        Binding("end", "scroll_end", "End", show=False),
    ]

    def __init__(self, backend: JSONBackendAdapter, **kwargs) -> None:
        """Initialize TT-Top application with JSON backend

        Args:
            backend: JSONBackendAdapter instance for device communication
            **kwargs: Additional arguments passed to parent App
        """
        super().__init__(**kwargs)
        self.backend = backend
        self.live_monitor: Optional[TTLiveMonitor] = None
        self.animated_display: Optional[HardwareResponsiveASCII] = None
        self.visualization_mode = False

    def compose(self) -> ComposeResult:
        """Compose the TT-Top application layout

        Creates a full-screen live monitor widget without tabs,
        providing direct access to real-time hardware visualization.
        """
        # Create the live monitor as the primary interface
        self.live_monitor = TTLiveMonitor(backend=self.backend)
        yield self.live_monitor
        yield Footer()

    def on_mount(self) -> None:
        """Handle application mounting

        Set up the application state and begin telemetry updates.
        """
        logger.info("TT-Top application started")

        # Update telemetry immediately on startup
        try:
            self.backend.update_telem()
            logger.info(f"Detected {len(self.backend.devices)} Tenstorrent devices")
        except Exception as e:
            logger.error(f"Failed to initialize telemetry: {e}")

    def action_quit(self) -> None:
        """Handle quit action"""
        logger.info("TT-Top application shutting down")
        # Cleanup backend resources if using JSON adapter
        if hasattr(self.backend, 'cleanup'):
            self.backend.cleanup()
        self.exit()

    def action_toggle_visualization(self) -> None:
        """Toggle between normal monitor and animated visualization"""
        if self.visualization_mode:
            self._exit_visualization_mode()
        else:
            self._enter_visualization_mode()

    def action_exit_mode(self) -> None:
        """Handle escape key - exit current mode or quit"""
        if self.visualization_mode:
            self._exit_visualization_mode()
        else:
            self.action_quit()

    def _enter_visualization_mode(self) -> None:
        """Enter full-screen animated visualization mode"""
        self.visualization_mode = True

        # Hide live monitor
        if self.live_monitor:
            self.live_monitor.display = False

        # Create and mount animated display (back to complex version)
        self.animated_display = HardwareResponsiveASCII(
            backend=self.backend,
            id="animated_display"
        )
        self.mount(self.animated_display)

        # Set focus to animated display to enable 'w' key binding
        self.animated_display.focus()

        # Update subtitle to show mode
        self.sub_title = "Hardware-Responsive Animated Visualization (Press 'v' to exit)"

    def _exit_visualization_mode(self) -> None:
        """Exit visualization mode and return to normal monitor"""
        self.visualization_mode = False

        # Remove animated display
        if self.animated_display:
            self.animated_display.remove()
            self.animated_display = None

        # Show live monitor
        if self.live_monitor:
            self.live_monitor.display = True

        # Restore subtitle
        self.sub_title = "Real-time telemetry and hardware visualization"

    def action_help(self) -> None:
        """Handle help action - show help message"""
        help_text = """
TT-Top Help

TT-Top is a real-time hardware monitoring tool for Tenstorrent devices.

KEYBOARD SHORTCUTS:
  q, Ctrl+C      - Quit application
  h              - Show this help
  v              - Toggle animated visualization mode
  Esc            - Exit current mode (or quit if in normal mode)
  ↑/↓            - Scroll up/down (normal mode)
  Page Up/Down   - Page up/down (normal mode)
  Home/End       - Jump to top/bottom (normal mode)

DISPLAY MODES:
  Normal Mode:
    • Hardware Status - Real-time device telemetry
    • Memory Hierarchy - DDR channel and cache visualization
    • Workload Detection - ML framework and process analysis
    • Event Log - Live hardware event streaming

  Visualization Mode:
    • Hardware-Responsive Starfield - Tensix cores as twinkling stars
    • Memory Activity Patterns - DDR channels as colored blocks
    • Interconnect Data Flows - Streaming patterns between devices
    • Real-time Color Coding - Temperature/power responsive colors

All animations and colors are driven by actual hardware telemetry data.
        """
        self.bell()
        # In a real implementation, you might want to show this in a modal
        # For now, we'll just log it
        logger.info("Help requested - see terminal for help text")
        print(help_text)

    # Forward scroll actions to the live monitor
    def action_scroll_up(self) -> None:
        """Scroll up in live monitor"""
        if self.live_monitor:
            self.live_monitor.action_scroll_up()

    def action_scroll_down(self) -> None:
        """Scroll down in live monitor"""
        if self.live_monitor:
            self.live_monitor.action_scroll_down()

    def action_page_up(self) -> None:
        """Page up in live monitor"""
        if self.live_monitor:
            self.live_monitor.action_page_up()

    def action_page_down(self) -> None:
        """Page down in live monitor"""
        if self.live_monitor:
            self.live_monitor.action_page_down()

    def action_scroll_home(self) -> None:
        """Go to top of live monitor"""
        if self.live_monitor:
            self.live_monitor.action_scroll_home()

    def action_scroll_end(self) -> None:
        """Go to bottom of live monitor"""
        if self.live_monitor:
            self.live_monitor.action_scroll_end()

    def on_key(self, event: events.Key) -> None:
        """Handle additional key events"""
        # The parent App class handles key bindings automatically via BINDINGS
        # We don't need to explicitly call super().on_key() here
        pass


def parse_args() -> argparse.Namespace:
    """Parse command line arguments for TT-Top

    Maintains compatibility with TT-SMI CLI options while focusing
    on the live monitoring functionality.
    """
    parser = argparse.ArgumentParser(
        prog="tt-top",
        description="Real-time hardware monitoring for Tenstorrent silicon",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Standard Usage (requires tt-smi installed):
  tt-top                              # Start monitoring (spawns tt-smi)
  tt-top --device 0                   # Monitor specific device
  tt-top --tt-smi-path /path/to/tt-smi  # Use custom tt-smi location
  tt-top --log-level DEBUG            # Enable debug logging

  # Mock Mode (for testing without hardware):
  tt-top --mock                       # Use simulated mock data
  tt-top --mock --log-level DEBUG     # Mock mode with debug logging

Architecture:
  tt-top is a standalone UNIX-style tool that spawns tt-smi as a subprocess
  and consumes its JSON telemetry output. This provides clean separation
  between data acquisition (tt-smi) and visualization (tt-top).

  Data flow: tt-smi --json --continuous → JSON stream → tt-top → visualization

Requirements:
  - tt-smi must be installed and accessible in PATH (or via --tt-smi-path)
  - tt-smi must support --json --continuous flags for JSON streaming mode

For more information, visit: https://github.com/tenstorrent/tt-top
        """,
    )

    # Device selection options
    parser.add_argument(
        "-d",
        "--device",
        type=int,
        default=None,
        help="Specify device index to monitor (default: all devices)",
    )

    # Logging options
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )

    # Backend options
    parser.add_argument(
        "--tt-smi-path",
        type=str,
        default="tt-smi",
        metavar="PATH",
        help="Path to tt-smi executable (default: 'tt-smi' from PATH)",
    )

    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data mode (for testing without tt-smi or hardware)",
    )

    # Version information
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.0.0",
    )

    return parser.parse_args()


def tt_top_main() -> int:
    """Main entry point for TT-Top application

    Sets up logging, initializes the JSON backend adapter, and launches
    the real-time monitoring interface.

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    try:
        args = parse_args()

        # Configure logging
        import logging
        logging.basicConfig(
            level=getattr(logging, args.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Determine backend mode (JSON or mock)
        if args.mock:
            # Mock mode: Use simulated data for testing
            logger.info("Starting in MOCK mode (simulated data)")
            backend = JSONBackendAdapter(mock_mode=True)
            logger.info(f"Generated mock data for {len(backend.devices)} device(s)")

        else:
            # JSON mode: Spawn tt-smi subprocess and consume JSON
            logger.info("Starting in JSON mode (tt-smi subprocess)")
            logger.info(f"tt-smi path: {args.tt_smi_path}")

            try:
                # Build tt-smi command with appropriate flags
                tt_smi_cmd = f"{args.tt_smi_path} --json --continuous"

                # Add device filtering if specified
                if args.device is not None:
                    tt_smi_cmd += f" --device {args.device}"
                    logger.info(f"Filtering to device {args.device}")

                logger.info(f"Spawning: {tt_smi_cmd}")

                # Create JSON backend adapter
                backend = JSONBackendAdapter(tt_smi_command=tt_smi_cmd)

                # Wait for initial telemetry data
                import time
                max_wait = 5.0
                start_time = time.time()
                while not backend.devices and (time.time() - start_time) < max_wait:
                    backend.update_telem()
                    time.sleep(0.1)

                if not backend.devices:
                    logger.error("Failed to receive telemetry from tt-smi")
                    logger.error("")
                    logger.error("Troubleshooting:")
                    logger.error("  1. Ensure tt-smi is installed: which tt-smi")
                    logger.error("  2. Test tt-smi directly: tt-smi --json")
                    logger.error("  3. Check tt-smi supports continuous mode: tt-smi --help")
                    logger.error("  4. Try mock mode for testing: tt-top --mock")
                    logger.error("")
                    return 1

                logger.info(f"Successfully connected to tt-smi")
                logger.info(f"Detected {len(backend.devices)} device(s)")
                for i, device in enumerate(backend.devices):
                    logger.info(f"  Device {i}: {device.get_architecture_name()} ({device.board_type})")

            except RuntimeError as e:
                logger.error(f"Failed to spawn tt-smi subprocess: {e}")
                logger.error("")
                logger.error("Possible causes:")
                logger.error("  - tt-smi not installed or not in PATH")
                logger.error("  - tt-smi does not support --json --continuous flags")
                logger.error("")
                logger.error("Solutions:")
                logger.error("  - Install tt-smi from Tenstorrent tools")
                logger.error("  - Use --tt-smi-path to specify custom location")
                logger.error("  - Use --mock for testing without hardware")
                logger.error("")
                return 1

        # Launch the TT-Top application
        logger.info("Launching TT-Top visualization interface")
        app = TTTopApp(backend=backend)
        app.run()

        logger.info("TT-Top session completed")
        return 0

    except KeyboardInterrupt:
        logger.info("TT-Top interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"TT-Top failed with error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return 1


def main() -> None:
    """Console script entry point"""
    sys.exit(tt_top_main())


if __name__ == "__main__":
    main()