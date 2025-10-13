# TT-Top - Real-time Hardware Monitor for Tenstorrent Silicon

TT-Top is a standalone real-time hardware monitoring application for Tenstorrent devices, forked from TT-SMI to focus exclusively on live telemetry visualization and hardware insights.

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
- Python 3.10+
- Textual >= 0.59.0
- Rich >= 13.7.0
- psutil >= 5.9.0
- pyluwen == 0.7.11
- tt_tools_common == 1.4.29

## Usage

### Basic Monitoring
```bash
# Start live monitoring (all devices)
tt-top

# Monitor specific device
tt-top --device 0

# Enable debug logging
tt-top --log-level DEBUG
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

### Backend Integration
TT-Top uses the same backend as TT-SMI for hardware communication:
- **TTSMIBackend**: Device discovery and telemetry collection
- **SMBUS Integration**: Direct hardware telemetry access
- **Cross-platform**: Linux and other UNIX-like systems

### Hardware Support
- **Grayskull**: 4 DDR channels, 10×12 Tensix grid
- **Wormhole**: 8 DDR channels, 8×10 Tensix grid
- **Blackhole**: 12 DDR channels, 14×16 Tensix grid

## Development

### Project Structure
```
tt_top/
├── __init__.py              # Package initialization
├── tt_top_app.py           # Main application class
├── tt_top_widget.py        # Live monitoring widget
├── tt_smi_backend.py       # Hardware communication backend
├── constants.py            # Configuration constants
└── log.py                  # Logging utilities
```

### Key Differences from TT-SMI
- **Standalone Application**: No tab interface, direct to live monitoring
- **Focused Scope**: Exclusively real-time visualization
- **Enhanced Analytics**: Advanced workload detection and memory visualization
- **Performance Optimized**: 100ms refresh rate for responsive monitoring

### Contributing
TT-Top is forked from TT-SMI and maintains compatibility with the underlying hardware abstraction layer. Contributions should focus on:
- Enhanced visualization techniques
- Advanced analytics and insights
- Performance optimizations
- Cross-platform compatibility

## License

Apache License 2.0 - See LICENSE file for details.

## Support

For issues and feature requests:
- GitHub Issues: https://github.com/tenstorrent/tt-top/issues
- Documentation: https://github.com/tenstorrent/tt-top

---

**TT-Top** - Real-time insights into Tenstorrent silicon performance