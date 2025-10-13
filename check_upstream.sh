#!/bin/bash
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

# Quick upstream change checker for TT-Top
# Run this regularly to stay informed about upstream changes

echo "🔍 Checking upstream TT-SMI for changes..."

# Fetch latest from upstream
git fetch origin >/dev/null 2>&1

# Check how many commits we're behind
BEHIND_COUNT=$(git rev-list --count tt-top..origin/main 2>/dev/null || echo "0")

if [ "$BEHIND_COUNT" -eq 0 ]; then
    echo "✅ TT-Top is up to date with upstream"
else
    echo "📥 Upstream has $BEHIND_COUNT new commits since last sync"
    echo
    echo "Recent changes:"
    git log --oneline --date=short --pretty=format:"%C(yellow)%h%C(reset) %C(green)%ad%C(reset) %s" tt-top..origin/main | head -5
    echo

    # Check for changes to important files
    BACKEND_CHANGES=$(git log tt-top..origin/main --name-only -- tt_smi/tt_smi_backend.py | wc -l)
    CONSTANTS_CHANGES=$(git log tt-top..origin/main --name-only -- tt_smi/constants.py | wc -l)

    if [ "$BACKEND_CHANGES" -gt 0 ]; then
        echo "🔧 Backend changes detected ($BACKEND_CHANGES commits)"
    fi

    if [ "$CONSTANTS_CHANGES" -gt 0 ]; then
        echo "📝 Constants changes detected ($CONSTANTS_CHANGES commits)"
    fi

    echo
    echo "💡 To sync: ./sync_upstream.sh"
fi

# Show last sync date (if available)
LAST_SYNC=$(git log --grep="Sync.*upstream" --pretty=format:"%ad" --date=short -1 2>/dev/null)
if [ -n "$LAST_SYNC" ]; then
    echo "📅 Last sync: $LAST_SYNC"
fi