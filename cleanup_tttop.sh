#!/bin/bash
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

# TT-Top Project Cleanup Script
# Safely transforms TT-SMI project structure into clean TT-Top standalone project

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"

echo "🚀 TT-Top Project Cleanup Script"
echo "=================================="
echo "Project Root: $PROJECT_ROOT"
echo

# Safety check - ensure we're in the right directory
if [[ ! -f "$PROJECT_ROOT/tt_top.py" ]]; then
    echo "❌ Error: tt_top.py not found. Are you in the correct directory?"
    echo "Expected to find TT-Top project files."
    exit 1
fi

if [[ ! -d "$PROJECT_ROOT/tt_top" ]]; then
    echo "❌ Error: tt_top/ directory not found."
    echo "Expected to find TT-Top package directory."
    exit 1
fi

# Confirm with user before making changes
echo "This script will:"
echo "  📁 Archive original TT-SMI files to archive_tt_smi/"
echo "  🔄 Promote TT-Top files to primary positions"
echo "  🧹 Clean up build artifacts and temporary files"
echo "  📝 Update project structure for standalone TT-Top"
echo

read -p "Continue with cleanup? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Cleanup cancelled."
    exit 0
fi

echo "🔄 Starting cleanup process..."
echo

# Create archive directory
ARCHIVE_DIR="$PROJECT_ROOT/archive_tt_smi"
echo "📁 Creating archive directory: $ARCHIVE_DIR"
mkdir -p "$ARCHIVE_DIR"

# Archive original TT-SMI files
echo "📦 Archiving original TT-SMI files..."

# Archive main project files if they exist
if [[ -f "$PROJECT_ROOT/setup.py" ]]; then
    echo "   • setup.py → archive_tt_smi/setup_ttsmi.py"
    mv "$PROJECT_ROOT/setup.py" "$ARCHIVE_DIR/setup_ttsmi.py"
fi

if [[ -f "$PROJECT_ROOT/pyproject.toml" ]]; then
    echo "   • pyproject.toml → archive_tt_smi/pyproject_ttsmi.toml"
    mv "$PROJECT_ROOT/pyproject.toml" "$ARCHIVE_DIR/pyproject_ttsmi.toml"
fi

if [[ -f "$PROJECT_ROOT/README.md" ]]; then
    echo "   • README.md → archive_tt_smi/README_ttsmi.md"
    mv "$PROJECT_ROOT/README.md" "$ARCHIVE_DIR/README_ttsmi.md"
fi

# Archive TT-SMI specific source files
if [[ -f "$PROJECT_ROOT/tt_smi/tt_smi.py" ]]; then
    echo "   • tt_smi/tt_smi.py → archive_tt_smi/"
    mv "$PROJECT_ROOT/tt_smi/tt_smi.py" "$ARCHIVE_DIR/"
fi

if [[ -f "$PROJECT_ROOT/tt_smi/__main__.py" ]]; then
    echo "   • tt_smi/__main__.py → archive_tt_smi/"
    mv "$PROJECT_ROOT/tt_smi/__main__.py" "$ARCHIVE_DIR/"
fi

# Archive any existing test files for TT-SMI
echo "   • Archiving TT-SMI test files..."
find "$PROJECT_ROOT" -name "*tt_smi*test*" -type f 2>/dev/null | while read -r file; do
    if [[ -f "$file" ]]; then
        echo "     - $(basename "$file") → archive_tt_smi/"
        mv "$file" "$ARCHIVE_DIR/"
    fi
done

# Archive any widget files that are TT-SMI specific
if [[ -d "$PROJECT_ROOT/tt_smi" ]]; then
    for widget_file in device_info_widget.py telemetry_widget.py firmware_widget.py help_widget.py; do
        if [[ -f "$PROJECT_ROOT/tt_smi/$widget_file" ]]; then
            echo "   • tt_smi/$widget_file → archive_tt_smi/"
            mv "$PROJECT_ROOT/tt_smi/$widget_file" "$ARCHIVE_DIR/"
        fi
    done
fi

echo

# Promote TT-Top files to primary positions
echo "🔼 Promoting TT-Top files to primary positions..."

if [[ -f "$PROJECT_ROOT/setup_tttop.py" ]]; then
    echo "   • setup_tttop.py → setup.py"
    mv "$PROJECT_ROOT/setup_tttop.py" "$PROJECT_ROOT/setup.py"
fi

if [[ -f "$PROJECT_ROOT/pyproject_tttop.toml" ]]; then
    echo "   • pyproject_tttop.toml → pyproject.toml"
    mv "$PROJECT_ROOT/pyproject_tttop.toml" "$PROJECT_ROOT/pyproject.toml"
fi

if [[ -f "$PROJECT_ROOT/README_TTTOP.md" ]]; then
    echo "   • README_TTTOP.md → README.md"
    mv "$PROJECT_ROOT/README_TTTOP.md" "$PROJECT_ROOT/README.md"
fi

if [[ -f "$PROJECT_ROOT/.gitignore_tttop" ]]; then
    echo "   • .gitignore_tttop → .gitignore"
    mv "$PROJECT_ROOT/.gitignore_tttop" "$PROJECT_ROOT/.gitignore"
fi

echo

# Clean up build artifacts
echo "🧹 Cleaning up build artifacts and temporary files..."

# Remove Python cache directories
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
echo "   • Removed __pycache__ directories"

# Remove build directories
for build_dir in build dist "*.egg-info"; do
    if [[ -d "$PROJECT_ROOT/$build_dir" ]] || [[ -n $(ls -d "$PROJECT_ROOT"/$build_dir 2>/dev/null) ]]; then
        rm -rf "$PROJECT_ROOT"/$build_dir
        echo "   • Removed $build_dir"
    fi
done

# Remove Python compiled files
find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -name "*.pyo" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -name "*.pyd" -delete 2>/dev/null || true
echo "   • Removed compiled Python files"

# Remove temporary files
find "$PROJECT_ROOT" -name "*~" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -name "*.tmp" -delete 2>/dev/null || true
echo "   • Removed temporary files"

echo

# Clean up constants.py if it exists in tt_top
echo "🔧 Cleaning up TT-Top package files..."

TT_TOP_CONSTANTS="$PROJECT_ROOT/tt_top/constants.py"
if [[ -f "$TT_TOP_CONSTANTS" ]]; then
    echo "   • Cleaning tt_top/constants.py (removing TT-SMI specific constants)"

    # Create a backup
    cp "$TT_TOP_CONSTANTS" "$TT_TOP_CONSTANTS.backup"

    # Remove TT-SMI specific sections (help menu, tab headers)
    sed -i.bak '/^HELP_MENU_MARKDOWN/,/^"""$/d' "$TT_TOP_CONSTANTS" 2>/dev/null || true
    sed -i.bak '/^INFO_TABLE_HEADER/,/^\]$/d' "$TT_TOP_CONSTANTS" 2>/dev/null || true
    sed -i.bak '/^TELEMETRY_TABLE_HEADER/,/^\]$/d' "$TT_TOP_CONSTANTS" 2>/dev/null || true
    sed -i.bak '/^FIRMWARES_TABLE_HEADER/,/^\]$/d' "$TT_TOP_CONSTANTS" 2>/dev/null || true

    # Remove the .bak file created by sed
    rm -f "$TT_TOP_CONSTANTS.bak" 2>/dev/null || true
fi

echo

# Create project status summary
echo "📊 Creating project status summary..."

# Count files in different categories
TOTAL_FILES=$(find "$PROJECT_ROOT" -type f | wc -l)
PYTHON_FILES=$(find "$PROJECT_ROOT" -name "*.py" -type f | wc -l)
TEST_FILES=$(find "$PROJECT_ROOT/tests_tt_top" -name "*.py" -type f 2>/dev/null | wc -l)
ARCHIVED_FILES=$(find "$ARCHIVE_DIR" -type f 2>/dev/null | wc -l)

echo "   • Total files in project: $TOTAL_FILES"
echo "   • Python source files: $PYTHON_FILES"
echo "   • Test files: $TEST_FILES"
echo "   • Archived TT-SMI files: $ARCHIVED_FILES"

# Verify TT-Top structure
echo
echo "🔍 Verifying TT-Top project structure..."

STRUCTURE_OK=true

# Check essential files
ESSENTIAL_FILES=(
    "tt_top.py"
    "setup.py"
    "pyproject.toml"
    "README.md"
    "tt_top/__init__.py"
    "tt_top/tt_top_app.py"
    "tt_top/tt_top_widget.py"
)

for file in "${ESSENTIAL_FILES[@]}"; do
    if [[ -f "$PROJECT_ROOT/$file" ]]; then
        echo "   ✅ $file"
    else
        echo "   ❌ Missing: $file"
        STRUCTURE_OK=false
    fi
done

# Check test directory
if [[ -d "$PROJECT_ROOT/tests_tt_top" ]]; then
    echo "   ✅ tests_tt_top/ directory"
else
    echo "   ⚠️  No tests_tt_top/ directory found"
fi

echo

# Final summary
if [[ "$STRUCTURE_OK" == true ]]; then
    echo "✅ TT-Top project cleanup completed successfully!"
    echo
    echo "📋 Summary of changes:"
    echo "   • Original TT-SMI files archived to archive_tt_smi/"
    echo "   • TT-Top files promoted to primary positions"
    echo "   • Build artifacts and temporary files cleaned"
    echo "   • Project structure verified"
    echo
    echo "🚀 Next steps:"
    echo "   1. Test the TT-Top installation:"
    echo "      python3 -c \"from tt_top import main; print('Import successful')\""
    echo
    echo "   2. Run the test suite:"
    echo "      cd tests_tt_top && python3 run_tests.py"
    echo
    echo "   3. Install TT-Top:"
    echo "      pip install -e ."
    echo
    echo "   4. Launch TT-Top:"
    echo "      tt-top"
    echo
else
    echo "⚠️  TT-Top project cleanup completed with warnings!"
    echo "   Some essential files may be missing. Check the structure above."
    echo
fi

echo "📁 Original TT-SMI files preserved in: $ARCHIVE_DIR"
echo "🎯 TT-Top is now the primary project structure."
echo
echo "Cleanup complete! 🎉"