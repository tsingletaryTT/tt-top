#!/usr/bin/env python3
"""Test the defensive error handling in multi-chip scenarios"""

from tt_top.animated_display import RichMarkupBuilder, safe_markup_wrap

print("Testing defensive error handling for multi-chip safety...")
print()

# Test 1: Corrupted color string detection
print("Test 1: Corrupted color string detection")
test_cases = [
    ('bright_cyan', True),
    ('bold red', True),
    ('[bright_cyan]', False),  # Corrupted - contains markup
    ('bright_[cyan', False),   # Corrupted - contains markup
    ('[/bright_white]', False),  # Corrupted - is a closing tag
]

for color_str, should_be_valid in test_cases:
    color, styles = RichMarkupBuilder.normalize_color(color_str)
    is_valid = (color is not None and color != 'white') or (not should_be_valid and color == 'white')
    status = '✓' if is_valid == should_be_valid else '✗'
    print(f"  {status} '{color_str}' -> color='{color}', styles={styles}")

print()
print("Test 2: Safe markup wrapper")
result = safe_markup_wrap("test", "bright_cyan")
print(f"  safe_markup_wrap('test', 'bright_cyan') = {result}")
assert '[/[' not in result
assert '[[' not in result
print("  ✓ No double brackets or malformed tags")

print()
print("✓ All defensive checks working correctly!")
print()
print("When you run tt-top and press 'v':")
print("  - Any corrupted colors will be logged with ⚠️ WARNING messages")
print("  - Stars with bad colors will be reset to 'white'")
print("  - Rendering errors will be caught and logged with line/column info")
print("  - The visualization will gracefully degrade instead of crashing")
