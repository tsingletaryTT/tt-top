#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-Top Project Validation Script

Validates the TT-Top project structure, imports, and basic functionality
without requiring hardware dependencies.
"""

import sys
import os
from pathlib import Path
import importlib.util


class TTTopValidator:
    """TT-Top project structure and functionality validator"""

    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.errors = []
        self.warnings = []
        self.successes = []

    def log_success(self, message):
        """Log a successful validation"""
        self.successes.append(message)
        print(f"✅ {message}")

    def log_warning(self, message):
        """Log a validation warning"""
        self.warnings.append(message)
        print(f"⚠️  {message}")

    def log_error(self, message):
        """Log a validation error"""
        self.errors.append(message)
        print(f"❌ {message}")

    def validate_file_structure(self):
        """Validate essential file structure"""
        print("🔍 Validating file structure...")

        # Essential files
        essential_files = {
            'tt_top.py': 'Main executable entry point',
            'setup.py': 'Installation script',
            'pyproject.toml': 'Project configuration',
            'README.md': 'Project documentation',
            'tt_top/__init__.py': 'Package initialization',
            'tt_top/tt_top_app.py': 'Main application class',
            'tt_top/tt_top_widget.py': 'Live monitoring widget',
            'tt_top/tt_smi_backend.py': 'Hardware communication backend',
            'tt_top/constants.py': 'Configuration constants',
            'tt_top/log.py': 'Logging utilities'
        }

        for file_path, description in essential_files.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                self.log_success(f"{file_path} - {description}")
            else:
                self.log_error(f"Missing {file_path} - {description}")

        # Optional but recommended files
        optional_files = {
            'tt_top/version.py': 'Version information',
            'tests_tt_top/': 'Test directory',
            'examples/': 'Usage examples',
            'INSTALL_TTTOP.md': 'Installation guide'
        }

        for file_path, description in optional_files.items():
            full_path = self.project_root / file_path
            if full_path.exists():
                self.log_success(f"{file_path} - {description}")
            else:
                self.log_warning(f"Optional {file_path} not found - {description}")

    def validate_imports(self):
        """Validate Python imports"""
        print("\n🐍 Validating Python imports...")

        # Add project root to path
        sys.path.insert(0, str(self.project_root))

        # Test basic imports
        imports_to_test = [
            ('tt_top', 'TT-Top package'),
            ('tt_top.tt_top_app', 'Main application module'),
            ('tt_top.tt_smi_backend', 'Backend module'),
            ('tt_top.constants', 'Constants module'),
            ('tt_top.log', 'Logging module')
        ]

        for module_name, description in imports_to_test:
            try:
                module = importlib.import_module(module_name)
                self.log_success(f"Import {module_name} - {description}")
            except ImportError as e:
                self.log_error(f"Import failed {module_name} - {description}: {e}")
            except Exception as e:
                self.log_warning(f"Import warning {module_name} - {description}: {e}")

    def validate_application_structure(self):
        """Validate application class structure"""
        print("\n🏗️  Validating application structure...")

        try:
            from tt_top.tt_top_app import TTTopApp, parse_args, tt_top_main, main

            # Check class exists
            self.log_success("TTTopApp class imported successfully")

            # Check essential methods exist
            essential_methods = [
                'compose', 'on_mount', 'action_quit', 'action_help',
                'action_scroll_up', 'action_scroll_down'
            ]

            for method_name in essential_methods:
                if hasattr(TTTopApp, method_name):
                    self.log_success(f"TTTopApp.{method_name} method exists")
                else:
                    self.log_error(f"TTTopApp.{method_name} method missing")

            # Check CLI functions exist
            cli_functions = [parse_args, tt_top_main, main]
            for func in cli_functions:
                if callable(func):
                    self.log_success(f"{func.__name__} function exists")
                else:
                    self.log_error(f"{func.__name__} function not callable")

        except ImportError as e:
            self.log_error(f"Could not import application components: {e}")

    def validate_widget_structure(self):
        """Validate widget class structure"""
        print("\n🖼️  Validating widget structure...")

        try:
            from tt_top.tt_top_widget import TTTopDisplay, TTLiveMonitor

            # Check classes exist
            self.log_success("TTTopDisplay class imported successfully")
            self.log_success("TTLiveMonitor class imported successfully")

            # Check essential methods in TTTopDisplay
            display_methods = [
                '_update_display', '_render_complete_display',
                '_create_bbs_main_display', '_get_status_color',
                '_create_memory_hierarchy_matrix', '_create_workload_detection_section'
            ]

            for method_name in display_methods:
                if hasattr(TTTopDisplay, method_name):
                    self.log_success(f"TTTopDisplay.{method_name} method exists")
                else:
                    self.log_warning(f"TTTopDisplay.{method_name} method missing")

            # Check TTLiveMonitor scroll methods
            monitor_methods = [
                'action_scroll_up', 'action_scroll_down',
                'action_page_up', 'action_page_down'
            ]

            for method_name in monitor_methods:
                if hasattr(TTLiveMonitor, method_name):
                    self.log_success(f"TTLiveMonitor.{method_name} method exists")
                else:
                    self.log_error(f"TTLiveMonitor.{method_name} method missing")

        except ImportError as e:
            self.log_error(f"Could not import widget components: {e}")

    def validate_cli_functionality(self):
        """Validate CLI argument parsing"""
        print("\n⌨️  Validating CLI functionality...")

        try:
            from tt_top.tt_top_app import parse_args

            # Save original argv
            original_argv = sys.argv.copy()

            # Test basic argument parsing
            test_cases = [
                (['tt-top'], "Basic invocation"),
                (['tt-top', '--device', '0'], "Device selection"),
                (['tt-top', '--log-level', 'DEBUG'], "Log level setting"),
                (['tt-top', '--no-telemetry-warnings'], "Telemetry warning disable")
            ]

            for test_argv, description in test_cases:
                try:
                    sys.argv = test_argv
                    args = parse_args()
                    self.log_success(f"CLI parsing: {description}")
                except SystemExit:
                    # Help or version requests cause SystemExit - this is expected
                    self.log_success(f"CLI parsing: {description} (help/version)")
                except Exception as e:
                    self.log_error(f"CLI parsing failed: {description} - {e}")
                finally:
                    sys.argv = original_argv

        except ImportError as e:
            self.log_error(f"Could not import CLI functions: {e}")

    def validate_project_metadata(self):
        """Validate project metadata files"""
        print("\n📋 Validating project metadata...")

        # Check setup.py content
        setup_py = self.project_root / 'setup.py'
        if setup_py.exists():
            try:
                content = setup_py.read_text()
                if 'tt-top' in content:
                    self.log_success("setup.py contains tt-top branding")
                else:
                    self.log_warning("setup.py may not contain tt-top branding")

                if 'tt_top:main' in content:
                    self.log_success("setup.py has correct entry point")
                else:
                    self.log_warning("setup.py may have incorrect entry point")
            except Exception as e:
                self.log_warning(f"Could not validate setup.py content: {e}")

        # Check pyproject.toml content
        pyproject_toml = self.project_root / 'pyproject.toml'
        if pyproject_toml.exists():
            try:
                content = pyproject_toml.read_text()
                if 'name = "tt-top"' in content:
                    self.log_success("pyproject.toml has correct project name")
                else:
                    self.log_warning("pyproject.toml may have incorrect project name")

                required_deps = ['textual', 'rich', 'psutil']
                for dep in required_deps:
                    if dep in content:
                        self.log_success(f"pyproject.toml includes {dep} dependency")
                    else:
                        self.log_warning(f"pyproject.toml may be missing {dep} dependency")
            except Exception as e:
                self.log_warning(f"Could not validate pyproject.toml content: {e}")

    def validate_test_structure(self):
        """Validate test structure"""
        print("\n🧪 Validating test structure...")

        tests_dir = self.project_root / 'tests_tt_top'
        if tests_dir.exists():
            self.log_success("Test directory exists")

            # Check for test files
            test_files = list(tests_dir.glob('test_*.py'))
            if test_files:
                self.log_success(f"Found {len(test_files)} test files")
                for test_file in test_files:
                    self.log_success(f"  - {test_file.name}")
            else:
                self.log_warning("No test files found in tests_tt_top/")

            # Check for test runner
            runner = tests_dir / 'run_tests.py'
            if runner.exists():
                self.log_success("Test runner script exists")
            else:
                self.log_warning("Test runner script not found")
        else:
            self.log_warning("Test directory not found")

    def validate_documentation(self):
        """Validate documentation completeness"""
        print("\n📚 Validating documentation...")

        # Check README content
        readme = self.project_root / 'README.md'
        if readme.exists():
            try:
                content = readme.read_text()
                required_sections = [
                    '# TT-Top', 'Installation', 'Usage', 'Features'
                ]
                for section in required_sections:
                    if section in content:
                        self.log_success(f"README contains {section} section")
                    else:
                        self.log_warning(f"README may be missing {section} section")
            except Exception as e:
                self.log_warning(f"Could not validate README content: {e}")

        # Check for additional documentation
        doc_files = {
            'INSTALL_TTTOP.md': 'Installation guide',
            'TT_TOP_CLEANUP_GUIDE.md': 'Cleanup guide',
            'TT_TOP_PROJECT_SUMMARY.md': 'Project summary'
        }

        for doc_file, description in doc_files.items():
            if (self.project_root / doc_file).exists():
                self.log_success(f"{doc_file} - {description}")
            else:
                self.log_warning(f"{doc_file} not found - {description}")

    def run_all_validations(self):
        """Run all validation checks"""
        print("🚀 TT-Top Project Validation")
        print("=" * 50)

        validations = [
            self.validate_file_structure,
            self.validate_imports,
            self.validate_application_structure,
            self.validate_widget_structure,
            self.validate_cli_functionality,
            self.validate_project_metadata,
            self.validate_test_structure,
            self.validate_documentation
        ]

        for validation in validations:
            try:
                validation()
            except Exception as e:
                self.log_error(f"Validation failed: {validation.__name__}: {e}")

        # Summary
        print("\n📊 Validation Summary")
        print("=" * 30)
        print(f"✅ Successes: {len(self.successes)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        print(f"❌ Errors: {len(self.errors)}")

        if not self.errors:
            print("\n🎉 All critical validations passed!")
            print("TT-Top project structure is ready for use.")
            return True
        else:
            print(f"\n💥 {len(self.errors)} critical errors found.")
            print("Please fix errors before using TT-Top.")
            return False


def main():
    """Main validation entry point"""
    # Determine project root
    script_dir = Path(__file__).parent
    project_root = script_dir

    # Run validation
    validator = TTTopValidator(project_root)
    success = validator.run_all_validations()

    if success:
        print("\n🚀 Next steps:")
        print("  1. Install dependencies: pip install textual rich psutil")
        print("  2. Install TT-Top: pip install -e .")
        print("  3. Run tests: cd tests_tt_top && python3 run_tests.py")
        print("  4. Launch TT-Top: tt-top")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())