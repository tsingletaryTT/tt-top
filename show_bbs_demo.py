#!/usr/bin/env python3
"""
Quick demonstration of the new BBS-style TT-Top display
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from test_fixed_widget import MockTTSMIBackend, TTTopDisplay

def main():
    print("BBS-Style TT-Top Demo Output:")
    print("=" * 80)

    # Create mock backend and display
    backend = MockTTSMIBackend()
    display = TTTopDisplay(backend)

    # Render and show output
    content = display._render_complete_display()
    print(content)

    print("\n" + "=" * 80)
    print("This is the new BBS/retro terminal aesthetic for TT-Top!")

if __name__ == "__main__":
    main()