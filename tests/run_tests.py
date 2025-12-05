#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Test runner for TT-Top test suite

Runs all unit and integration tests, providing summary and detailed output.
"""

import unittest
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def run_all_tests():
    """Run all tests and return results"""
    # Discover and run all tests
    loader = unittest.TestLoader()
    start_dir = Path(__file__).parent
    suite = loader.discover(start_dir, pattern='test_*.py')

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


def run_specific_test_file(test_file: str):
    """Run tests from a specific file"""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName(test_file)

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return result


if __name__ == '__main__':
    print("=" * 70)
    print("TT-Top Test Suite")
    print("Testing JSON-based architecture with cached sample data")
    print("=" * 70)
    print()

    if len(sys.argv) > 1:
        # Run specific test file
        test_file = sys.argv[1]
        print(f"Running tests from: {test_file}")
        print()
        result = run_specific_test_file(test_file)
    else:
        # Run all tests
        print("Running all tests...")
        print()
        result = run_all_tests()

    print()
    print("=" * 70)

    # Print summary
    if result.wasSuccessful():
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Some tests failed")
        print(f"   Failures: {len(result.failures)}")
        print(f"   Errors: {len(result.errors)}")
        sys.exit(1)
