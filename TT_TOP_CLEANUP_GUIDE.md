# TT-Top Code Cleanup Guide

This guide identifies files and code that can be removed or modified for a clean TT-Top standalone project.

## Files That Can Be Removed (TT-SMI Specific)

### ❌ **Complete Removal Candidates**

```bash
# TT-SMI main interface files (no longer needed for tt-top)
tt_smi/tt_smi.py                    # Main TT-SMI application with tabs
tt_smi/__main__.py                  # TT-SMI module entry point
tt_smi/gui/                         # GUI components (if exists)

# TT-SMI specific widgets (tabs we eliminated)
tt_smi/device_info_widget.py        # Device info tab
tt_smi/telemetry_widget.py          # Telemetry tab
tt_smi/firmware_widget.py           # Firmware tab
tt_smi/help_widget.py               # Help tab

# Build and packaging files for TT-SMI
setup.py                            # Original TT-SMI setup (keep for reference)
pyproject.toml                      # Original TT-SMI config (keep for reference)
```

### ⚠️ **Modification Candidates**

```bash
# Files that need TT-SMI references cleaned up
tt_smi/constants.py                 # Remove TT-SMI specific help text and constants
tt_smi/__init__.py                  # Clean up TT-SMI imports

# Test files that need updating
test_*.py                           # Update to test tt-top instead of tt-smi
tests/                              # Update test directory structure
```

### ✅ **Files to Keep (Backend Dependencies)**

```bash
# Core backend (required for tt-top)
tt_smi/tt_smi_backend.py           # Hardware communication backend
tt_smi/log.py                      # Logging utilities

# Data and configuration
tt_smi/data/                       # Hardware data files
LICENSE                            # License file
README.md                          # Original project README (for reference)
```

## Code Cleanup Within Files

### 1. **tt_smi/constants.py Cleanup**

**Remove TT-SMI specific help text:**
```python
# REMOVE: TT-SMI help menu markdown (lines 199-221)
HELP_MENU_MARKDOWN = """..."""

# REMOVE: Tab-specific header constants
INFO_TABLE_HEADER = [...]
TELEMETRY_TABLE_HEADER = [...]
FIRMWARES_TABLE_HEADER = [...]

# KEEP: Backend constants
SMBUS_TELEMETRY_LIST = [...]
TELEM_LIST = [...]
GUI_INTERVAL_TIME = 0.1
```

### 2. **Root Directory Cleanup**

**Remove or rename conflicting files:**
```bash
# Move original files to archive
mkdir archive_tt_smi/
mv setup.py archive_tt_smi/setup_ttsmi.py
mv pyproject.toml archive_tt_smi/pyproject_ttsmi.toml

# Rename tt-top files to primary
mv setup_tttop.py setup.py
mv pyproject_tttop.toml pyproject.toml
mv README_TTTOP.md README.md
```

### 3. **Import Cleanup in tt_top Package**

**Clean up any remaining tt_smi imports:**
```python
# IN: tt_top/tt_top_widget.py
# CHANGE: from tt_smi.constants import GUI_INTERVAL_TIME
# TO:     from tt_top.constants import GUI_INTERVAL_TIME

# IN: tt_top/tt_top_app.py
# ENSURE: All imports use tt_top.* not tt_smi.*
```

## Cleanup Script

Here's a bash script to automate the cleanup:

```bash
#!/bin/bash
# cleanup_for_tttop.sh

echo "TT-Top Project Cleanup Script"
echo "=============================="

# Create archive directory
mkdir -p archive_tt_smi

# Archive original TT-SMI files
echo "Archiving original TT-SMI files..."
mv setup.py archive_tt_smi/setup_ttsmi.py 2>/dev/null || true
mv pyproject.toml archive_tt_smi/pyproject_ttsmi.toml 2>/dev/null || true
mv README.md archive_tt_smi/README_ttsmi.md 2>/dev/null || true

# Move TT-SMI specific files to archive
mv tt_smi/tt_smi.py archive_tt_smi/ 2>/dev/null || true
mv tt_smi/__main__.py archive_tt_smi/ 2>/dev/null || true

# Promote TT-Top files to primary
echo "Promoting TT-Top files to primary..."
mv setup_tttop.py setup.py
mv pyproject_tttop.toml pyproject.toml
mv README_TTTOP.md README.md
mv .gitignore_tttop .gitignore

# Remove TT-SMI specific test files
echo "Cleaning up test files..."
find . -name "*tt_smi*test*" -exec mv {} archive_tt_smi/ \; 2>/dev/null || true

# Clean up build artifacts
echo "Removing build artifacts..."
rm -rf build/ dist/ *.egg-info/ __pycache__/ */__pycache__/

echo "Cleanup complete! Original TT-SMI files archived in archive_tt_smi/"
echo "TT-Top is now the primary project structure."
```

## Size Impact Analysis

### **Before Cleanup**
```
tt-smi/                     # ~15MB total
├── tt_smi/                 # ~8MB (includes all widgets)
├── tt_top/                 # ~3MB (standalone package)
├── tests/                  # ~1MB
├── docs/                   # ~1MB
└── other files            # ~2MB
```

### **After Cleanup**
```
tt-top/                     # ~8MB total
├── tt_top/                 # ~3MB (standalone package)
├── tests_tt_top/          # ~500KB (focused tests)
├── examples/               # ~100KB
├── archive_tt_smi/         # ~8MB (archived)
└── other files            # ~500KB
```

**Space Savings**: ~7MB in active project, ~47% reduction

## Recommended Cleanup Strategy

### **Phase 1: Safe Archive** (Immediate)
1. Create `archive_tt_smi/` directory
2. Move TT-SMI specific files to archive
3. Promote TT-Top files to primary names
4. Update .gitignore

### **Phase 2: Dependency Cleanup** (After Testing)
1. Remove unused constants from `tt_top/constants.py`
2. Clean up imports in all tt_top files
3. Remove TT-SMI references from documentation

### **Phase 3: Full Separation** (Production Ready)
1. Remove archived files if no longer needed
2. Create separate repository for TT-Top
3. Update all GitHub/documentation links

## Validation Steps

After cleanup, verify TT-Top still works:

```bash
# Test import
python3 -c "from tt_top import main; print('Import successful')"

# Test CLI
tt-top --help

# Test backend
python3 -c "from tt_top.tt_smi_backend import TTSMIBackend; print('Backend working')"

# Run test suite
python3 -m pytest tests_tt_top/
```

---

**Next**: Run cleanup script and create comprehensive test suite for the cleaned TT-Top project.