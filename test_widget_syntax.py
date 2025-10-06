#!/usr/bin/env python3
"""
Simple syntax test for the tt_top_widget module without requiring hardware dependencies.
"""

import ast
import sys

def test_syntax():
    """Test the syntax of the tt_top_widget.py file"""
    try:
        with open('/Users/tsingletary/code/tt-smi/tt_smi/tt_top_widget.py', 'r') as f:
            source_code = f.read()

        # Parse the AST to check for syntax errors
        ast.parse(source_code)
        print("✓ Syntax check passed for tt_top_widget.py")
        return True

    except SyntaxError as e:
        print(f"✗ Syntax error in tt_top_widget.py: {e}")
        return False
    except Exception as e:
        print(f"✗ Error checking syntax: {e}")
        return False

if __name__ == "__main__":
    success = test_syntax()
    sys.exit(0 if success else 1)