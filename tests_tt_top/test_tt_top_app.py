#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for TT-Top main application functionality.

Tests the core TTTopApp class, CLI argument parsing, and application lifecycle.
"""

import sys
import unittest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import argparse
import io

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from tt_top.tt_top_app import TTTopApp, parse_args, tt_top_main, main
    from tt_top.tt_smi_backend import TTSMIBackend
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import TT-Top modules: {e}")
    print("Tests will be skipped. Install dependencies to run tests.")
    IMPORTS_AVAILABLE = False


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestTTTopApp(unittest.TestCase):
    """Test TTTopApp main application class"""

    def setUp(self):
        """Set up test fixtures"""
        # Mock backend to avoid hardware dependencies
        self.mock_backend = Mock(spec=TTSMIBackend)
        self.mock_backend.devices = []
        self.mock_backend.device_telemetrys = []
        self.mock_backend.device_infos = []

    def test_app_initialization(self):
        """Test TTTopApp initialization"""
        app = TTTopApp(backend=self.mock_backend)

        self.assertIsNotNone(app)
        self.assertEqual(app.backend, self.mock_backend)
        self.assertIsNone(app.live_monitor)  # Not created until compose()

    def test_app_title_and_subtitle(self):
        """Test application title and subtitle"""
        app = TTTopApp(backend=self.mock_backend)

        self.assertEqual(app.TITLE, "TT-Top - Tenstorrent Hardware Monitor")
        self.assertEqual(app.SUB_TITLE, "Real-time telemetry and hardware visualization")

    def test_app_bindings_present(self):
        """Test that key bindings are properly defined"""
        app = TTTopApp(backend=self.mock_backend)

        # Check that bindings exist
        self.assertTrue(len(app.BINDINGS) > 0)

        # Check for essential bindings
        binding_keys = [binding.key for binding in app.BINDINGS]
        self.assertIn("q", binding_keys)
        self.assertIn("h", binding_keys)
        self.assertIn("ctrl+c", binding_keys)
        self.assertIn("up", binding_keys)
        self.assertIn("down", binding_keys)

    def test_action_methods_exist(self):
        """Test that action methods are defined"""
        app = TTTopApp(backend=self.mock_backend)

        # Test essential action methods exist
        self.assertTrue(hasattr(app, 'action_quit'))
        self.assertTrue(hasattr(app, 'action_help'))
        self.assertTrue(hasattr(app, 'action_scroll_up'))
        self.assertTrue(hasattr(app, 'action_scroll_down'))
        self.assertTrue(hasattr(app, 'action_page_up'))
        self.assertTrue(hasattr(app, 'action_page_down'))

    @patch('tt_top.tt_top_app.logger')
    def test_on_mount_telemetry_update(self, mock_logger):
        """Test that telemetry is updated on mount"""
        app = TTTopApp(backend=self.mock_backend)

        # Mock successful telemetry update
        self.mock_backend.update_telem.return_value = None

        app.on_mount()

        # Verify telemetry update was called
        self.mock_backend.update_telem.assert_called_once()
        mock_logger.info.assert_called()

    @patch('tt_top.tt_top_app.logger')
    def test_on_mount_telemetry_error(self, mock_logger):
        """Test error handling in on_mount telemetry update"""
        app = TTTopApp(backend=self.mock_backend)

        # Mock telemetry update failure
        self.mock_backend.update_telem.side_effect = Exception("Hardware error")

        app.on_mount()

        # Verify error was logged
        mock_logger.error.assert_called()

    def test_action_quit(self):
        """Test quit action"""
        app = TTTopApp(backend=self.mock_backend)

        # Mock the exit method
        app.exit = Mock()

        app.action_quit()

        # Verify exit was called
        app.exit.assert_called_once()

    @patch('builtins.print')
    @patch('tt_top.tt_top_app.logger')
    def test_action_help(self, mock_logger, mock_print):
        """Test help action"""
        app = TTTopApp(backend=self.mock_backend)

        # Mock bell method
        app.bell = Mock()

        app.action_help()

        # Verify bell was called and help was printed
        app.bell.assert_called_once()
        mock_print.assert_called()
        mock_logger.info.assert_called()

    def test_scroll_actions_with_live_monitor(self):
        """Test scroll actions when live monitor is available"""
        app = TTTopApp(backend=self.mock_backend)

        # Mock live monitor
        app.live_monitor = Mock()

        # Test all scroll actions
        app.action_scroll_up()
        app.live_monitor.action_scroll_up.assert_called_once()

        app.action_scroll_down()
        app.live_monitor.action_scroll_down.assert_called_once()

        app.action_page_up()
        app.live_monitor.action_page_up.assert_called_once()

        app.action_page_down()
        app.live_monitor.action_page_down.assert_called_once()

        app.action_scroll_home()
        app.live_monitor.action_scroll_home.assert_called_once()

        app.action_scroll_end()
        app.live_monitor.action_scroll_end.assert_called_once()

    def test_scroll_actions_without_live_monitor(self):
        """Test scroll actions when live monitor is None"""
        app = TTTopApp(backend=self.mock_backend)

        # Ensure live_monitor is None
        app.live_monitor = None

        # These should not raise exceptions
        app.action_scroll_up()
        app.action_scroll_down()
        app.action_page_up()
        app.action_page_down()
        app.action_scroll_home()
        app.action_scroll_end()


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestCLIArguments(unittest.TestCase):
    """Test CLI argument parsing functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Save original argv
        self.original_argv = sys.argv.copy()

    def tearDown(self):
        """Restore original argv"""
        sys.argv = self.original_argv

    def test_parse_args_defaults(self):
        """Test default argument values"""
        sys.argv = ['tt-top']
        args = parse_args()

        self.assertIsNone(args.device)
        self.assertEqual(args.log_level, 'INFO')
        self.assertFalse(args.no_telemetry_warnings)

    def test_parse_args_device_option(self):
        """Test device option parsing"""
        sys.argv = ['tt-top', '--device', '0']
        args = parse_args()

        self.assertEqual(args.device, 0)

    def test_parse_args_device_option_short(self):
        """Test device option short form"""
        sys.argv = ['tt-top', '-d', '1']
        args = parse_args()

        self.assertEqual(args.device, 1)

    def test_parse_args_log_level(self):
        """Test log level option"""
        sys.argv = ['tt-top', '--log-level', 'DEBUG']
        args = parse_args()

        self.assertEqual(args.log_level, 'DEBUG')

    def test_parse_args_log_level_invalid(self):
        """Test invalid log level raises error"""
        sys.argv = ['tt-top', '--log-level', 'INVALID']

        with self.assertRaises(SystemExit):
            parse_args()

    def test_parse_args_no_telemetry_warnings(self):
        """Test no telemetry warnings flag"""
        sys.argv = ['tt-top', '--no-telemetry-warnings']
        args = parse_args()

        self.assertTrue(args.no_telemetry_warnings)

    def test_parse_args_help(self):
        """Test help option"""
        sys.argv = ['tt-top', '--help']

        with self.assertRaises(SystemExit) as cm:
            parse_args()

        self.assertEqual(cm.exception.code, 0)

    def test_parse_args_version(self):
        """Test version option"""
        sys.argv = ['tt-top', '--version']

        with self.assertRaises(SystemExit) as cm:
            parse_args()

        self.assertEqual(cm.exception.code, 0)

    def test_parse_args_multiple_options(self):
        """Test multiple options together"""
        sys.argv = ['tt-top', '--device', '2', '--log-level', 'WARNING', '--no-telemetry-warnings']
        args = parse_args()

        self.assertEqual(args.device, 2)
        self.assertEqual(args.log_level, 'WARNING')
        self.assertTrue(args.no_telemetry_warnings)


@unittest.skipUnless(IMPORTS_AVAILABLE, "TT-Top modules not available")
class TestMainFunction(unittest.TestCase):
    """Test main entry point functions"""

    def setUp(self):
        """Set up test fixtures"""
        # Save original argv
        self.original_argv = sys.argv.copy()

    def tearDown(self):
        """Restore original argv"""
        sys.argv = self.original_argv

    @patch('tt_top.tt_top_app.TTSMIBackend')
    @patch('tt_top.tt_top_app.TTTopApp')
    @patch('tt_top.tt_top_app.logger')
    def test_tt_top_main_success(self, mock_logger, mock_app_class, mock_backend_class):
        """Test successful tt_top_main execution"""
        sys.argv = ['tt-top']

        # Mock backend
        mock_backend = Mock()
        mock_backend.devices = []
        mock_backend_class.return_value = mock_backend

        # Mock app
        mock_app = Mock()
        mock_app_class.return_value = mock_app

        result = tt_top_main()

        # Verify successful execution
        self.assertEqual(result, 0)
        mock_backend_class.assert_called_once()
        mock_app_class.assert_called_once_with(backend=mock_backend)
        mock_app.run.assert_called_once()

    @patch('tt_top.tt_top_app.TTSMIBackend')
    @patch('tt_top.tt_top_app.logger')
    def test_tt_top_main_backend_error(self, mock_logger, mock_backend_class):
        """Test tt_top_main with backend initialization error"""
        sys.argv = ['tt-top']

        # Mock backend initialization failure
        mock_backend_class.side_effect = Exception("Backend error")

        result = tt_top_main()

        # Verify error handling
        self.assertEqual(result, 1)
        mock_logger.error.assert_called()

    @patch('tt_top.tt_top_app.TTSMIBackend')
    @patch('tt_top.tt_top_app.logger')
    def test_tt_top_main_keyboard_interrupt(self, mock_logger, mock_backend_class):
        """Test tt_top_main with keyboard interrupt"""
        sys.argv = ['tt-top']

        # Mock backend
        mock_backend = Mock()
        mock_backend.devices = []
        mock_backend_class.return_value = mock_backend

        # Mock app to raise KeyboardInterrupt
        with patch('tt_top.tt_top_app.TTTopApp') as mock_app_class:
            mock_app = Mock()
            mock_app.run.side_effect = KeyboardInterrupt()
            mock_app_class.return_value = mock_app

            result = tt_top_main()

            # Verify graceful handling
            self.assertEqual(result, 0)
            mock_logger.info.assert_called_with("TT-Top interrupted by user")

    @patch('tt_top.tt_top_app.TTSMIBackend')
    @patch('tt_top.tt_top_app.logger')
    def test_tt_top_main_device_filtering(self, mock_logger, mock_backend_class):
        """Test device filtering functionality"""
        sys.argv = ['tt-top', '--device', '0']

        # Mock backend with devices
        mock_backend = Mock()
        mock_backend.devices = ['device0', 'device1']
        mock_backend_class.return_value = mock_backend

        with patch('tt_top.tt_top_app.TTTopApp') as mock_app_class:
            mock_app = Mock()
            mock_app_class.return_value = mock_app

            result = tt_top_main()

            # Verify successful execution with device filtering
            self.assertEqual(result, 0)
            mock_logger.info.assert_any_call("Monitoring device 0 only")

    @patch('tt_top.tt_top_app.TTSMIBackend')
    @patch('tt_top.tt_top_app.logger')
    def test_tt_top_main_invalid_device(self, mock_logger, mock_backend_class):
        """Test invalid device index handling"""
        sys.argv = ['tt-top', '--device', '5']

        # Mock backend with fewer devices
        mock_backend = Mock()
        mock_backend.devices = ['device0', 'device1']
        mock_backend_class.return_value = mock_backend

        result = tt_top_main()

        # Verify error handling for invalid device
        self.assertEqual(result, 1)
        mock_logger.error.assert_called()

    @patch('tt_top.tt_top_app.tt_top_main')
    @patch('sys.exit')
    def test_main_entry_point(self, mock_exit, mock_tt_top_main):
        """Test main() entry point function"""
        mock_tt_top_main.return_value = 0

        main()

        mock_tt_top_main.assert_called_once()
        mock_exit.assert_called_once_with(0)


if __name__ == '__main__':
    unittest.main()