# TT-Top - Real-time Hardware Monitor for Tenstorrent Silicon

TT-Top is a standalone real-time hardware monitoring application for Tenstorrent devices. It follows the UNIX philosophy by consuming JSON telemetry data from tt-smi, providing live visualization and hardware insights without requiring direct hardware access.

## Features

### 🚀 Real-time Hardware Monitoring
- Live telemetry updates every 100ms
- Hardware-responsive visualizations based on actual device state
- Temperature, power, current, and clock frequency monitoring
- ARC firmware health and heartbeat tracking

### 🧠 Intelligent Workload Detection
- Automatic detection of ML frameworks (PyTorch, TensorFlow, JAX, HuggingFace)
- Model type identification (LLM, Computer Vision, Audio/Speech)
- Workload classification (Training, Inference, Evaluation)
- Process correlation with hardware telemetry

### 🔧 Memory Hierarchy Visualization
- DDR channel status and training state
- L2 cache bank utilization patterns
- L1 SRAM grid activity (compressed view)
- Real-time memory bandwidth flow indicators

### 📊 Advanced Analytics
- Temporal activity heatmaps (60-second history)
- Interconnect bandwidth utilization matrix
- Live hardware event logging
- Process efficiency and trend analysis

### 🎨 Terminal Interface
- Clean ASCII art design with cyberpunk color palette
- Hardware-responsive TENSTORRENT branding
- Borderless tables for authentic terminal feel
- Scrollable interface for extended content

## Installation

### From Source
```bash
# Install TT-Top directly
pip install -e . -f setup_tttop.py

# Or using the TOML configuration
pip install -e . -c pyproject_tttop.toml
```

### Dependencies

#### Core Dependencies (Always Required)
- Python 3.10+
- Textual >= 0.59.0
- Rich >= 13.7.0
- psutil >= 5.9.0
- pydantic >= 1.9.0

#### Backend Requirements
**JSON Mode (Default)**:
- tt-smi installed and accessible in PATH
- tt-smi must support `--json --continuous` flags

**Mock Mode (Testing)**:
- No additional dependencies (built-in)

## Usage

### Basic Monitoring

**Standard Usage (requires tt-smi)**:
```bash
# Start live monitoring (spawns tt-smi subprocess)
tt-top

# Monitor specific device
tt-top --device 0

# Use custom tt-smi path
tt-top --tt-smi-path /path/to/tt-smi

# Enable debug logging
tt-top --log-level DEBUG
```

**Mock Mode (testing without hardware)**:
```bash
# Use simulated mock data
tt-top --mock

# Mock mode with debug output
tt-top --mock --log-level DEBUG
```

### Keyboard Shortcuts

| Key | Action | Description |
|-----|--------|-------------|
| `q`, `Ctrl+C`, `Esc` | Quit | Exit application |
| `h` | Help | Show help information |
| `↑`/`↓` | Scroll | Navigate up/down |
| `Page Up`/`Page Down` | Page | Jump by screen |
| `Home`/`End` | Jump | Go to top/bottom |

## Interface Sections

### Hardware Status
- Real-time device telemetry with color-coded status indicators
- Power consumption, temperature, and current draw monitoring
- AICLK frequency and voltage monitoring
- Hardware-responsive visual elements

### Memory Hierarchy Matrix
- **DDR Channels**: Live training status per channel (●=trained, ◐=training, ◯=idle, ✗=error)
- **L2 Cache**: Bank utilization with hotspot detection
- **L1 SRAM**: Compressed Tensix core grid activity
- **Data Flow**: Bandwidth visualization between hierarchy levels

### Workload Intelligence Engine
- **Framework Detection**: PyTorch, TensorFlow, JAX, HuggingFace
- **Model Classification**: LLM, Computer Vision, Audio/Speech
- **Process Analysis**: Memory usage, thread count, hardware correlation
- **Real-time Filtering**: Only displays identified ML workloads

### Hardware Event Log
- Live streaming of hardware events based on telemetry thresholds
- Power state transitions (IDLE → ACTIVE → HIGH_POWER)
- Thermal alerts and warnings
- ARC firmware heartbeat monitoring
- Clock frequency changes and turbo mode activation

## Architecture

### Architecture

**Data Flow**:
```
tt-smi --json --continuous (subprocess)
   ↓
JSON telemetry stream (stdout, line-buffered)
   ↓
JSONBackendAdapter (parse & cache)
   ↓
DeviceProxy objects (architecture detection)
   ↓
Visualization Widgets (unchanged interface)
   ↓
Hardware-responsive terminal display
```

**Key Principles**:
- **UNIX Philosophy**: Composable tools with clean data interfaces
- **Decoupled**: tt-top has zero direct hardware dependencies
- **Subprocess Isolation**: tt-smi handles all hardware access
- **JSON Contract**: All improvements flow through JSON schema
- **Portable**: Works anywhere tt-smi runs (local, remote, containers)
- **Testable**: Mock mode for CI/CD and development

**Backend Modes**:
- **JSON Mode**: Spawns tt-smi subprocess, parses JSON telemetry (default)
- **Mock Mode**: Generates simulated data for testing (`--mock` flag)

### Hardware Support
- **Grayskull**: 4 DDR channels, 10×12 Tensix grid
- **Wormhole**: 8 DDR channels, 8×10 Tensix grid
- **Blackhole**: 12 DDR channels, 14×16 Tensix grid

## Development

### Project Structure
```
tt_top/
├── __init__.py                 # Package initialization
├── tt_top_app.py               # Main application (backend mode selection)
├── tt_top_widget.py            # Live monitoring widget
├── json_backend_adapter.py     # JSON backend adapter (core)
├── device_proxy.py             # Architecture detection (GS/WH/BH)
├── animated_display.py         # Hardware-responsive visualization
├── simple_animated_display.py  # Alternative visualization mode
├── constants.py                # Configuration constants
├── log.py                      # Pydantic models for JSON parsing
└── workload_config.py          # ML framework detection patterns
```

### Key Design Principles
- **UNIX Philosophy**: Tools communicate via standard formats (JSON over stdout)
- **Clean Separation**: Data acquisition (tt-smi) vs visualization (tt-top)
- **Zero Hardware Dependencies**: tt-top never touches hardware directly
- **JSON Contract**: All features flow through JSON schema evolution
- **Hybrid Workload Detection**: tt-smi provides telemetry, tt-top scans /proc
- **Mock-Friendly**: Built-in mock mode for development and CI/CD

### Contributing
Contributions should focus on:
- Enhanced visualizations using JSON telemetry
- Improved ML framework detection and correlation
- JSON schema extensions (propose to tt-smi project)
- Performance optimizations in parsing/rendering
- Alternative backend adapters (file replay, network streaming)
- Cross-platform compatibility

## License

Apache License 2.0 - See LICENSE file for details.

## Support

For issues and feature requests:
- GitHub Issues: https://github.com/tenstorrent/tt-top/issues
- Documentation: https://github.com/tenstorrent/tt-top

---

**TT-Top** - Real-time insights into Tenstorrent silicon performance