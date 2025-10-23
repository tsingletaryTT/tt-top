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

from tt_top.tt_smi_backend import TTSMIBackend
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

    def __init__(self, backend: TTSMIBackend, **kwargs) -> None:
        """Initialize TT-Top application with hardware backend

        Args:
            backend: TTSMIBackend instance for device communication
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
  tt-top                              # Start live monitoring with auto safety
  tt-top --device 0                   # Monitor specific device
  tt-top --safe-mode on               # Force safe polling (2s intervals)
  tt-top --safe-mode off              # Disable safety (may interfere with workloads)
  tt-top --poll-interval 0.5          # Custom 500ms polling (overrides safety)
  tt-top --max-errors 5               # Allow 5 PCIe errors before disabling
  tt-top --workload-check-interval 2  # Check for ML workloads every 2 seconds
  tt-top --log-level DEBUG            # Enable debug logging

Safety Modes:
  auto (default) - Automatically detect workloads and adjust polling
  on             - Force safe polling intervals (2s) regardless of workloads
  off            - Use fast polling (100ms) - WARNING: may cause PCIe errors

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

    # Hardware safety options
    parser.add_argument(
        "--safe-mode",
        choices=["auto", "on", "off"],
        default="auto",
        help="Hardware safety mode (auto: workload detection, on: force safe polling, off: disable safety)",
    )

    parser.add_argument(
        "--poll-interval",
        type=float,
        default=None,
        metavar="SECONDS",
        help="Override polling interval in seconds (bypasses dynamic adjustment)",
    )

    parser.add_argument(
        "--max-errors",
        type=int,
        default=3,
        metavar="COUNT",
        help="Maximum PCIe errors before disabling monitoring (default: 3)",
    )

    parser.add_argument(
        "--workload-check-interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="How often to check for active workloads in seconds (default: 1.0)",
    )

    parser.add_argument(
        "--lock-timeout",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Maximum time to wait for hardware access lock in seconds (default: 1.0)",
    )

    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        metavar="COUNT",
        help="Maximum telemetry read retry attempts with exponential backoff (default: 3)",
    )

    # Backend options
    parser.add_argument(
        "--no-telemetry-warnings",
        action="store_true",
        help="Suppress telemetry warnings for unsupported features",
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

    Sets up logging, initializes the hardware backend, and launches
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

        # Initialize backend with device detection
        logger.info("Initializing TT-Top hardware monitoring")

        # Import the device detection functionality
        try:
            from tt_top.tt_smi_backend import detect_chips_with_callback, HARDWARE_AVAILABLE
            if HARDWARE_AVAILABLE:
                logger.info("Detecting Tenstorrent devices...")
                devices = detect_chips_with_callback(print_status=False)
                if not devices:
                    logger.warning("No Tenstorrent devices detected")
                    return 1
                logger.info(f"Found {len(devices)} Tenstorrent device(s)")
            else:
                logger.info("Using mock hardware for development")
                from tt_top.mock_hardware import MockPciChip
                devices = [MockPciChip(i) for i in range(1)]  # Create one mock device
        except Exception as e:
            logger.error(f"Failed to detect devices: {e}")
            return 1

        # Apply device filtering if specified
        if args.device is not None:
            if args.device >= len(devices):
                logger.error(f"Device {args.device} not found. Available devices: 0-{len(devices)-1}")
                return 1
            devices = [devices[args.device]]  # Filter to single device
            logger.info(f"Monitoring device {args.device} only")

        # Configure hardware safety based on CLI arguments
        from tt_top.safety import SafetyConfig
        safety_config = SafetyConfig(
            max_errors_before_disable=args.max_errors,
            workload_check_interval=args.workload_check_interval,
            max_lock_wait_time=args.lock_timeout,
            # Set polling intervals based on CLI arguments
            normal_poll_interval=args.poll_interval if args.poll_interval else 0.1,
            workload_poll_interval=args.poll_interval if args.poll_interval else 2.0,
            critical_poll_interval=args.poll_interval if args.poll_interval else 5.0,
        )

        # Initialize backend with detected devices and safety configuration
        backend = TTSMIBackend(devices=devices, fully_init=True, safety_config=safety_config)

        # Configure retry behavior based on CLI arguments
        backend.max_retries = args.max_retries

        # Apply CLI safety mode overrides
        if args.safe_mode == "on":
            logger.info("Forcing hardware safety mode ON via --safe-mode")
            backend.safety_coordinator.force_safety_mode(True)
        elif args.safe_mode == "off":
            logger.warning("Hardware safety mode DISABLED via --safe-mode - monitoring may interfere with workloads")
            backend.safety_coordinator.force_safety_mode(False)
        else:  # auto mode
            logger.info("Hardware safety mode AUTO - will detect workloads automatically")

        # Apply custom polling interval override if specified
        if args.poll_interval:
            logger.info(f"Using custom polling interval: {args.poll_interval}s (overrides dynamic adjustment)")
            backend.safety_coordinator.set_custom_poll_interval(args.poll_interval)

        # Launch the TT-Top application
        app = TTTopApp(backend=backend)
        app.run()

        logger.info("TT-Top session completed")
        return 0

    except KeyboardInterrupt:
        logger.info("TT-Top interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"TT-Top failed with error: {e}")
        return 1


def main() -> None:
    """Console script entry point"""
    sys.exit(tt_top_main())


if __name__ == "__main__":
    main()