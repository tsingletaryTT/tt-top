# TT-Top Installation Guide

## Quick Install (Recommended)

### From Project Directory
```bash
# Install in virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install tt-top in development mode
pip install -e .
```

### System-Wide Install
```bash
# Install dependencies
pip install textual rich pydantic psutil

# Install tt-top
pip install -e .
```

## Minimal Dependencies

TT-Top has minimal dependencies in JSON mode:

- **textual >= 0.59.0** - Terminal UI framework
- **rich >= 13.7.0** - Rich text formatting
- **pydantic >= 1.9.0** - JSON data validation
- **psutil >= 5.9.0** - Process detection

**No hardware dependencies required!** (tt-smi handles all hardware access)

## Running TT-Top

### After Installation
```bash
# Standard mode (requires tt-smi installed)
tt-top

# Mock mode (no tt-smi required, for testing)
tt-top --mock

# Specify custom tt-smi path
tt-top --tt-smi-path /path/to/tt-smi
```

### Without Installation (Development)
```bash
# Run as module (after installing dependencies)
python3 -m tt_top

# Run with mock mode
python3 -m tt_top --mock
```

## Verification

### Test Installation
```bash
# Check tt-top command works
tt-top --version

# Run in mock mode (no hardware needed)
tt-top --mock

# Press 'q' to quit
```

### Run Tests
```bash
# Install dependencies first
pip install pydantic

# Run test suite
python3 tests/run_tests.py

# Expected: ~78 tests, all passing
```

## Requirements by Mode

### JSON Mode (Default)
**TT-Top Requirements**:
- textual, rich, pydantic, psutil (install via requirements.txt)

**System Requirements**:
- tt-smi must be installed and in PATH
- tt-smi must support `--json --continuous` flags

### Mock Mode (Testing)
**Requirements**:
- textual, rich, pydantic, psutil (same as above)

**No additional requirements** - generates simulated data

## Troubleshooting

### "ModuleNotFoundError: No module named 'textual'"
```bash
# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install textual rich pydantic psutil
```

### "Failed to spawn tt-smi subprocess"
```bash
# Check tt-smi is installed
which tt-smi

# Test tt-smi JSON mode
tt-smi --json

# Use custom path if needed
tt-top --tt-smi-path /path/to/tt-smi

# Or use mock mode for testing
tt-top --mock
```

### "No module named 'tt_top.json_backend_adapter'"
This was fixed in the latest version. Update your installation:
```bash
cd /path/to/tt-top
git pull
pip install -e .
```

## Virtual Environment Setup (Recommended)

### Create Virtual Environment
```bash
# From tt-top project directory
python3 -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install tt-top
pip install -e .
```

### Using Virtual Environment
```bash
# Activate before each use
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Run tt-top
tt-top

# Deactivate when done
deactivate
```

## Development Installation

### Full Development Setup
```bash
# Clone repository
git clone https://github.com/tenstorrent/tt-top.git
cd tt-top

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install in editable mode
pip install -e .

# Run tests
python3 tests/run_tests.py

# Run tt-top
tt-top --mock
```

## Uninstall

### Remove TT-Top
```bash
pip uninstall tt-top
```

### Remove Virtual Environment
```bash
# Deactivate first
deactivate

# Remove directory
rm -rf venv
```

---

**Installation Complete!** Run `tt-top --mock` to verify everything works.
