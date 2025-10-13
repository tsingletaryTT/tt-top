# TT-Top Installation Guide

This guide covers installation and setup of TT-Top, the standalone real-time hardware monitor for Tenstorrent silicon.

## Prerequisites

### System Requirements
- **Operating System**: Linux (Ubuntu 20.04+, RHEL 8+, or equivalent)
- **Python**: 3.10 or higher
- **Hardware**: Tenstorrent devices (Grayskull, Wormhole, or Blackhole)
- **Permissions**: Access to hardware devices (usually requires sudo or hardware group membership)

### Python Dependencies
TT-Top requires several Python packages:
- `textual >= 0.59.0` - Terminal user interface framework
- `rich >= 13.7.0` - Rich text and beautiful formatting
- `psutil >= 5.9.0` - System and process utilities
- `pyluwen == 0.7.11` - Tenstorrent hardware communication
- `tt_tools_common == 1.4.29` - Tenstorrent tools common library
- `pydantic >= 1.2` - Data validation
- `distro >= 1.8.0` - Linux distribution detection

## Installation Methods

### Method 1: Development Installation (Recommended)

For development or when building from source:

```bash
# Clone or navigate to the TT-SMI repository
cd /path/to/tt-smi

# Create a virtual environment
python3 -m venv tt_top_env
source tt_top_env/bin/activate

# Install dependencies
pip install textual>=0.59.0 rich>=13.7.0 psutil>=5.9.0

# Install TT-Top in development mode
python setup_tttop.py develop

# Or using pip with the TOML configuration
pip install -e . -c pyproject_tttop.toml
```

### Method 2: Direct Installation

For direct installation without development setup:

```bash
# Navigate to project directory
cd /path/to/tt-smi

# Install using pip
pip install -e . -f setup_tttop.py

# Or install specific wheel if available
pip install tt_top-1.0.0-py3-none-any.whl
```

### Method 3: System-wide Installation

For system-wide installation (requires appropriate permissions):

```bash
# Install with system Python (not recommended for development)
sudo pip3 install -e . -f setup_tttop.py --break-system-packages

# Or use virtual environment with system access
python3 -m venv /opt/tt_top_env
source /opt/tt_top_env/bin/activate
pip install -e . -f setup_tttop.py
```

## Verification

### Test Basic Import
```bash
# Test Python import
python3 -c "from tt_top import main; print('TT-Top import successful')"

# Test CLI help
tt-top --help

# Test device detection (requires hardware)
tt-top --device 0 --log-level DEBUG
```

### Test Hardware Access
```bash
# Check device permissions
ls -la /dev/tenstorrent/

# Test hardware communication
python3 -c "
from tt_top.tt_smi_backend import TTSMIBackend
backend = TTSMIBackend()
print(f'Found {len(backend.devices)} devices')
"
```

## Configuration

### Hardware Permissions

TT-Top requires access to Tenstorrent hardware devices. Ensure proper permissions:

```bash
# Check current user groups
groups

# Add user to hardware group (if available)
sudo usermod -a -G tenstorrent $USER

# Or create udev rules for device access
sudo tee /etc/udev/rules.d/99-tenstorrent.rules << EOF
SUBSYSTEM=="tenstorrent", GROUP="tenstorrent", MODE="0664"
SUBSYSTEM=="tenstorrent", TAG+="uaccess"
EOF

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

### Environment Variables

Optional environment variables for TT-Top:

```bash
# Enable debug logging
export TT_TOP_LOG_LEVEL=DEBUG

# Specify device path (if non-standard)
export TT_DEVICE_PATH=/dev/tenstorrent

# Disable telemetry warnings
export TT_NO_TELEMETRY_WARNINGS=1
```

### Logging Configuration

Configure logging for debugging:

```bash
# Create log directory
mkdir -p ~/.tt_top/logs

# Run with detailed logging
tt-top --log-level DEBUG 2>&1 | tee ~/.tt_top/logs/tt_top.log
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Error: No module named 'textual'
# Solution: Install dependencies
pip install textual rich psutil

# Error: No module named 'pyluwen'
# Solution: Install Tenstorrent tools
pip install pyluwen==0.7.11 tt_tools_common==1.4.29
```

#### Hardware Access Issues
```bash
# Error: Permission denied accessing devices
# Solution: Check device permissions
sudo chmod 666 /dev/tenstorrent/*

# Error: No devices found
# Solution: Check hardware detection
lspci | grep -i tenstorrent
dmesg | grep -i tenstorrent
```

#### Display Issues
```bash
# Error: Terminal too small or display corruption
# Solution: Resize terminal or use scrolling
# Minimum recommended: 120x40 characters
resize -s 40 120

# Use TT-Top scroll commands
tt-top  # Then use Arrow keys, Page Up/Down, Home/End
```

### Debug Mode

For detailed debugging:

```bash
# Run with maximum verbosity
tt-top --log-level DEBUG --no-telemetry-warnings

# Check backend status
python3 -c "
from tt_top.tt_smi_backend import TTSMIBackend
import logging
logging.basicConfig(level=logging.DEBUG)
backend = TTSMIBackend()
backend.update_telem()
for i, device in enumerate(backend.devices):
    print(f'Device {i}: {backend.get_device_name(device)}')
    print(f'Telemetry: {backend.device_telemetrys[i]}')
"
```

### Performance Optimization

For optimal performance:

```bash
# Reduce update frequency if needed (modify constants.py)
export TT_GUI_INTERVAL=0.2  # 200ms instead of 100ms

# Disable specific features if causing issues
export TT_DISABLE_WORKLOAD_DETECTION=1
export TT_DISABLE_MEMORY_MATRIX=1
```

## Uninstall

To remove TT-Top:

```bash
# Remove development installation
pip uninstall tt-top

# Clean up virtual environment
deactivate
rm -rf tt_top_env

# Remove configuration files
rm -rf ~/.tt_top
```

## Support

### Getting Help
- **CLI Help**: `tt-top --help`
- **Examples**: See `examples/basic_usage.py`
- **Documentation**: `README_TTTOP.md`
- **Issues**: GitHub issues for the project

### Reporting Issues
When reporting issues, include:
- TT-Top version: `tt-top --version`
- Python version: `python3 --version`
- Operating system: `uname -a`
- Hardware information: `lspci | grep -i tenstorrent`
- Error logs with `--log-level DEBUG`

---

**TT-Top Installation Guide** - Get up and running with real-time Tenstorrent hardware monitoring