#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
TT-Top Test Runner

Comprehensive test runner for TT-Top application with various test categories
and reporting options.
"""

import sys
import os
import unittest
import time
from pathlib import Path
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Test discovery patterns
TEST_PATTERNS = {
    'all': 'test_*.py',
    'app': 'test_tt_top_app.py',
    'widget': 'test_tt_top_widget.py',
    'backend': 'test_backend_integration.py',
    'performance': 'test_performance.py',
    'safety': 'test_safety_*.py',
    'safety_core': 'test_safety_core.py',
    'safety_measures': 'test_safety_measures.py'
}


def check_dependencies():
    """Check if TT-Top dependencies are available"""
    missing_deps = []

    try:
        import textual
    except ImportError:
        missing_deps.append('textual')

    try:
        import rich
    except ImportError:
        missing_deps.append('rich')

    try:
        from tt_top import main
    except ImportError:
        missing_deps.append('tt-top package')

    return missing_deps


def run_test_suite(pattern='all', verbosity=2, failfast=False):
    """Run test suite with specified parameters"""
    print("TT-Top Test Suite")
    print("=" * 50)

    # Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        print("⚠️  Warning: Missing dependencies:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nSome tests will be skipped. Install dependencies for full test coverage.")
        print()

    # Test directory
    test_dir = Path(__file__).parent

    # Discover tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    if pattern == 'all':
        # Load all tests
        discovered_tests = loader.discover(test_dir, pattern=TEST_PATTERNS['all'])
        suite.addTest(discovered_tests)
    else:
        # Load specific test pattern
        test_pattern = TEST_PATTERNS.get(pattern, pattern)
        if test_pattern.endswith('.py'):
            # Single test file
            test_module = test_pattern[:-3]  # Remove .py
            try:
                module = __import__(test_module)
                suite.addTest(loader.loadTestsFromModule(module))
            except ImportError as e:
                print(f"❌ Could not import test module {test_module}: {e}")
                return False
        else:
            # Pattern-based discovery
            discovered_tests = loader.discover(test_dir, pattern=test_pattern)
            suite.addTest(discovered_tests)

    # Configure test runner
    runner = unittest.TextTestRunner(
        verbosity=verbosity,
        failfast=failfast,
        stream=sys.stdout,
        buffer=True
    )

    # Run tests
    print(f"Running tests with pattern: {pattern}")
    print(f"Test directory: {test_dir}")
    print()

    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()

    # Print summary
    print()
    print("Test Summary")
    print("=" * 30)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Time: {end_time - start_time:.2f}s")

    if result.failures:
        print(f"\n❌ {len(result.failures)} test(s) failed")

    if result.errors:
        print(f"\n💥 {len(result.errors)} test(s) had errors")

    if result.wasSuccessful():
        print("\n✅ All tests passed!")
        return True
    else:
        print(f"\n❌ {len(result.failures + result.errors)} test(s) failed")
        return False


def run_specific_tests():
    """Run specific test categories with descriptions"""
    categories = {
        'quick': {
            'pattern': 'app',
            'description': 'Quick app functionality tests',
            'time': '~30 seconds'
        },
        'functionality': {
            'pattern': 'widget',
            'description': 'Widget and display functionality tests',
            'time': '~60 seconds'
        },
        'integration': {
            'pattern': 'backend',
            'description': 'Backend integration tests',
            'time': '~45 seconds'
        },
        'performance': {
            'pattern': 'performance',
            'description': 'Performance and stress tests',
            'time': '~90 seconds'
        },
        'safety': {
            'pattern': 'safety',
            'description': 'Hardware safety coordination tests',
            'time': '~60 seconds'
        },
        'full': {
            'pattern': 'all',
            'description': 'Complete test suite',
            'time': '~4 minutes'
        }
    }

    print("\nAvailable test categories:")
    print("-" * 40)
    for name, info in categories.items():
        print(f"{name:12} - {info['description']} ({info['time']})")

    return categories


def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(
        description="TT-Top Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Categories:
  quick       - Quick app functionality tests (~30s)
  functionality - Widget and display tests (~60s)
  integration - Backend integration tests (~45s)
  performance - Performance and stress tests (~90s)
  safety      - Hardware safety coordination tests (~60s)
  full        - Complete test suite (~4min)

Examples:
  python run_tests.py                    # Run all tests
  python run_tests.py quick              # Quick tests only
  python run_tests.py safety             # Safety tests only
  python run_tests.py --verbose          # Detailed output
  python run_tests.py performance --failfast  # Stop on first failure
        """
    )

    parser.add_argument(
        'category',
        nargs='?',
        default='full',
        choices=['quick', 'functionality', 'integration', 'performance', 'safety', 'full'],
        help='Test category to run (default: full)'
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output (show individual test results)'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Quiet output (minimal information)'
    )

    parser.add_argument(
        '--failfast',
        action='store_true',
        help='Stop on first failure'
    )

    parser.add_argument(
        '--list',
        action='store_true',
        help='List available test categories and exit'
    )

    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies and exit'
    )

    args = parser.parse_args()

    if args.list:
        categories = run_specific_tests()
        return 0

    if args.check_deps:
        missing_deps = check_dependencies()
        if missing_deps:
            print("Missing dependencies:")
            for dep in missing_deps:
                print(f"  - {dep}")
            return 1
        else:
            print("✅ All dependencies available")
            return 0

    # Determine verbosity
    if args.quiet:
        verbosity = 0
    elif args.verbose:
        verbosity = 2
    else:
        verbosity = 1

    # Map category to pattern
    category_map = {
        'quick': 'app',
        'functionality': 'widget',
        'integration': 'backend',
        'performance': 'performance',
        'safety': 'safety',
        'full': 'all'
    }

    pattern = category_map.get(args.category, args.category)

    # Run tests
    success = run_test_suite(
        pattern=pattern,
        verbosity=verbosity,
        failfast=args.failfast
    )

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())