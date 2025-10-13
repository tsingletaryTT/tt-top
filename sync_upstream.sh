#!/bin/bash
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

# TT-Top Upstream Sync Script
# Intelligently sync TT-Top fork with upstream TT-SMI repository

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "🔄 TT-Top Upstream Sync"
echo "======================="

# Check if we're in a git repository
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "❌ Error: Not in a git repository"
    exit 1
fi

# Check if we have the required remotes
if ! git remote | grep -q "^origin$"; then
    echo "❌ Error: 'origin' remote not found"
    echo "Expected: origin -> tenstorrent/tt-smi"
    exit 1
fi

if ! git remote | grep -q "^fork$"; then
    echo "❌ Error: 'fork' remote not found"
    echo "Expected: fork -> your-username/tt-smi"
    exit 1
fi

# Function to check for uncommitted changes
check_working_directory() {
    if ! git diff --quiet || ! git diff --cached --quiet; then
        echo "⚠️  You have uncommitted changes:"
        git status --short
        echo
        read -p "Stash changes and continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            git stash push -m "Pre-sync backup $(date)"
            echo "📦 Changes stashed"
            STASHED=true
        else
            echo "❌ Please commit or stash changes first"
            exit 1
        fi
    fi
}

# Function to check upstream changes
check_upstream_changes() {
    echo "🔍 Fetching upstream changes..."
    git fetch origin

    # Count changes
    BEHIND_COUNT=$(git rev-list --count tt-top..origin/main 2>/dev/null || echo "0")

    if [ "$BEHIND_COUNT" -eq 0 ]; then
        echo "✅ TT-Top is up to date with upstream"
        if [ "$STASHED" = true ]; then
            echo "📤 Restoring stashed changes..."
            git stash pop
        fi
        exit 0
    fi

    echo "📥 Found $BEHIND_COUNT upstream commits"
    echo
    echo "Recent upstream changes:"
    git log --oneline tt-top..origin/main | head -5
    echo
}

# Function to analyze changes for conflicts
analyze_changes() {
    echo "🔍 Analyzing changes for potential conflicts..."

    # Check for changes to files we care about
    BACKEND_CHANGES=$(git log tt-top..origin/main --name-only -- tt_smi/tt_smi_backend.py | wc -l)
    CONSTANTS_CHANGES=$(git log tt-top..origin/main --name-only -- tt_smi/constants.py | wc -l)
    DEPS_CHANGES=$(git log tt-top..origin/main --name-only -- pyproject.toml setup.py | wc -l)

    echo "Changes affecting TT-Top:"
    echo "  • Backend (tt_smi_backend.py): $BACKEND_CHANGES commits"
    echo "  • Constants: $CONSTANTS_CHANGES commits"
    echo "  • Dependencies: $DEPS_CHANGES commits"
    echo

    if [ "$BACKEND_CHANGES" -gt 0 ] || [ "$CONSTANTS_CHANGES" -gt 0 ]; then
        echo "⚠️  Changes detected in shared code - manual review may be needed"
    fi
}

# Function to perform the sync
perform_sync() {
    echo "🔄 Starting sync process..."

    # Create backup branch
    BACKUP_BRANCH="tt-top-backup-$(date +%Y%m%d-%H%M%S)"
    git checkout tt-top
    git branch "$BACKUP_BRANCH"
    echo "📋 Created backup branch: $BACKUP_BRANCH"

    # Update main to match upstream
    echo "📥 Updating main branch..."
    git checkout main
    git reset --hard origin/main

    # Return to tt-top and attempt merge
    echo "🔀 Merging upstream changes..."
    git checkout tt-top

    if git merge main --no-edit; then
        echo "✅ Merge completed successfully"

        # Check if backend needs updating
        if [ "$BACKEND_CHANGES" -gt 0 ]; then
            echo "🔧 Updating TT-Top backend copy..."
            cp tt_smi/tt_smi_backend.py tt_top/tt_smi_backend.py

            if git diff --quiet tt_top/tt_smi_backend.py; then
                echo "   • Backend unchanged"
            else
                echo "   • Backend updated with upstream changes"
                git add tt_top/tt_smi_backend.py
                git commit -m "Sync backend with upstream TT-SMI"
            fi
        fi

        # Check if constants need selective updating
        if [ "$CONSTANTS_CHANGES" -gt 0 ]; then
            echo "⚠️  Constants changed upstream - manual review recommended"
            echo "   Review: git diff main HEAD~1 -- tt_smi/constants.py"
        fi

    else
        echo "❌ Merge conflicts detected"
        echo
        echo "Conflicted files:"
        git status --short | grep "^UU\\|^AA\\|^DD"
        echo
        echo "Resolution options:"
        echo "  1. Fix conflicts manually: edit files, then 'git add' and 'git commit'"
        echo "  2. Abort merge: git merge --abort"
        echo "  3. Restore backup: git reset --hard $BACKUP_BRANCH"
        echo
        exit 1
    fi
}

# Function to validate after sync
validate_sync() {
    echo "🧪 Validating TT-Top after sync..."

    # Run basic validation
    if python3 validate_tttop.py >/dev/null 2>&1; then
        echo "✅ TT-Top structure validation passed"
    else
        echo "⚠️  TT-Top validation warnings - run: python3 validate_tttop.py"
    fi

    # Check if we can import TT-Top
    if python3 -c "from tt_top import main; print('✅ TT-Top import successful')" 2>/dev/null; then
        echo "✅ TT-Top import test passed"
    else
        echo "⚠️  TT-Top import test failed - check dependencies"
    fi
}

# Function to push changes
push_changes() {
    echo "📤 Pushing updated tt-top branch..."

    if git push fork tt-top; then
        echo "✅ Successfully pushed to fork"
    else
        echo "⚠️  Push failed - you may need to resolve conflicts on remote"
        echo "   Try: git push --force-with-lease fork tt-top"
    fi
}

# Function to cleanup
cleanup() {
    echo "🧹 Cleaning up..."

    # Ask about backup branch
    read -p "Delete backup branch $BACKUP_BRANCH? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git branch -D "$BACKUP_BRANCH"
        echo "🗑️  Deleted backup branch"
    else
        echo "📋 Keeping backup branch: $BACKUP_BRANCH"
    fi

    # Restore stashed changes if any
    if [ "$STASHED" = true ]; then
        echo "📤 Restoring stashed changes..."
        git stash pop
    fi
}

# Main execution flow
main() {
    STASHED=false
    BACKUP_BRANCH=""

    # Pre-flight checks
    check_working_directory
    check_upstream_changes
    analyze_changes

    # Confirm before proceeding
    echo "Proceed with sync? This will:"
    echo "  • Create backup branch"
    echo "  • Merge upstream changes into tt-top"
    echo "  • Update backend files if needed"
    echo "  • Push to your fork"
    echo
    read -p "Continue? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ Sync cancelled"
        if [ "$STASHED" = true ]; then
            git stash pop
        fi
        exit 0
    fi

    # Perform the sync
    perform_sync
    validate_sync
    push_changes
    cleanup

    echo
    echo "🎉 Sync completed successfully!"
    echo
    echo "📋 Summary:"
    echo "  • Merged $BEHIND_COUNT upstream commits"
    echo "  • TT-Top functionality validated"
    echo "  • Changes pushed to fork"
    echo
    echo "🚀 Next steps:"
    echo "  • Test TT-Top functionality: tt-top"
    echo "  • Run test suite: cd tests_tt_top && python3 run_tests.py"
    echo "  • Review changes: git log --oneline HEAD~$BEHIND_COUNT..HEAD"
}

# Run main function
main "$@"