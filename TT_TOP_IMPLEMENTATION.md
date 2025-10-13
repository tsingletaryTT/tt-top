# TT-Top: Live Hardware Monitor Implementation

## Overview

TT-Top is a real-time hardware monitoring feature for TT-SMI that brings htop/top-like capabilities to Tenstorrent hardware visualization. Taking inspiration from classic system monitoring tools, Logstalgia's dynamic visualizations, and Orca's grid-based aesthetic, TT-Top provides an engaging, informative real-time view of hardware activity.

## Features Implemented

### 1. **Live Monitor Tab (Press '4')**
- Added as the 4th tab in the existing TT-SMI interface
- Integrates seamlessly with the current telemetry system
- Updates at the same 100ms interval as existing telemetry

### 2. **Three-Panel Layout**

#### **Top Left: Hardware Topology & Activity (Orca-inspired)**
```
┌─ TT-TOP: Real-time Hardware Monitor ─┐
│ [ 0] Grayskull   ●  🌡️│
│     e75        ████░░░░  45.2°C │
│ [ 1] Wormhole    ◐  🔥│
│     n300       ██████░░  78.4°C │
└────────────────────────────────────────┘
```
- Grid-based ASCII visualization of chip layout
- Real-time activity indicators: ● (high activity), ◐ (moderate), ○ (idle)
- Temperature indicators: 🔥 (hot), 🌡️ (normal), ❄️ (cool)
- Power consumption bars with color coding

#### **Top Right: Live Data Streams (Logstalgia-inspired)**
```
┌─ Data Flow Streams ────────────────────┐
│ Graysull │▶▷▶▷    ▶▷    │  12.5A │
│ Wormhole │▶▷▶▷▶▷▶▷▶▷▶▷▶▷│  28.7A │
│ Blackhol │▸▹  ▸▹      ▸▹│   5.2A │
└────────────────────────────────────────┘
```
- Animated flow indicators based on current draw
- Different animation patterns for different activity levels
- Color-coded: Red (high), Yellow (medium), Green (low)

#### **Bottom: Process/Activity Table (htop-inspired)**
```
ID | Device     | Board  | Voltage | Current | Power   | Temp    | AICLK   | Status
 1 | Wormhole   | n300   |  0.85V  |  28.7A  |  24.4W  |  78.4°C | 1200MHz | HOT
 0 | Grayskull  | e75    |  0.82V  |  12.5A  |  10.3W  |  45.2°C |  800MHz | ACTIVE
 2 | Blackhole  | p150a  |  0.79V  |   5.2A  |   4.1W  |  38.1°C |  600MHz | IDLE
```
- Sortable columns (default: by power consumption)
- Status indicators: CRITICAL, HOT, HIGH LOAD, ACTIVE, IDLE, SLEEP
- Color-coded critical values (temperature, power)

## Technical Implementation

### File Structure
```
tt_smi/
├── tt_smi.py              # Main app (modified)
├── tt_top_widget.py       # New TT-Top components
├── constants.py           # Updated with help text
└── demo_tt_top.py         # Standalone demo
```

### Key Components

#### **TTLiveMonitor** (`tt_smi/tt_top_widget.py:320`)
Main container that orchestrates all live monitoring components.

#### **ChipGridVisualizer** (`tt_smi/tt_top_widget.py:25`)
Creates the ASCII grid visualization with real-time activity indicators.

#### **ActivityFlowWidget** (`tt_smi/tt_top_widget.py:88`)
Generates animated data flow streams inspired by Logstalgia.

#### **LiveProcessTable** (`tt_smi/tt_top_widget.py:148`)
Displays sortable hardware metrics in htop-style table.

### Integration Points

1. **Main UI Integration** (`tt_smi/tt_smi.py:81,130,150,659,695`)
   - Added keyboard binding: `("4", "tab_four", "Live monitor tab")`
   - Added tab to TabbedContent: `"Live Monitor (4)"`
   - Added TTLiveMonitor widget yield
   - Added action handler for tab switching

2. **Telemetry Integration** (`tt_smi/tt_smi.py:695`)
   - Reuses existing telemetry thread when Live Monitor tab is activated
   - Updates at same 100ms interval as regular telemetry

3. **Help System** (`tt_smi/constants.py:215`)
   - Updated help menu with new keyboard shortcut

## Visual Design Philosophy

### **★ Insight ─────────────────────────────────────**
The TT-Top interface combines three distinct visualization paradigms:

1. **Orca's Grid Aesthetic**: Character-based grid layout provides information density while maintaining clarity
2. **Logstalgia's Flow Dynamics**: Moving particles create visual interest and immediately convey activity levels
3. **htop's Functional Layout**: Familiar table format ensures usability for system administrators

This hybrid approach transforms technical monitoring into an engaging, informative experience.
**─────────────────────────────────────────────────**

## Usage

### Running the Demo
```bash
# Set up environment (first time)
python3 -m venv .venv
source .venv/bin/activate
pip install rich textual setuptools importlib_resources

# Run standalone demo
python3 demo_tt_top.py
```

### Using in TT-SMI
1. Start TT-SMI normally: `tt-smi`
2. Press `4` or click "Live Monitor (4)" tab
3. Watch real-time hardware activity visualization
4. Press `h` for help menu

## Animation System

The interface uses a frame-based animation system:
- **Animation Frame Counter**: Increments every update cycle
- **Flow Animation**: Characters shift position based on frame + device offset
- **Activity Indicators**: Symbols change based on real telemetry values
- **Smooth Updates**: 100ms interval matches existing telemetry system

## Color Coding System

### Activity Levels
- **Red**: High activity (>50W power consumption)
- **Yellow**: Moderate activity (20-50W)
- **Green**: Low activity (5-20W)
- **Gray**: Idle (<5W)

### Temperature Alerts
- **🔥 Red**: >80°C (critical)
- **🌡️ Yellow**: 60-80°C (warm)
- **🌡️ Green**: 40-60°C (normal)
- **❄️ Cyan**: <40°C (cool)

### Status Indicators
- **CRITICAL**: Temperature >85°C
- **HOT**: Temperature >75°C
- **HIGH LOAD**: Power >75W
- **ACTIVE**: Power 25-75W
- **IDLE**: Power 5-25W
- **SLEEP**: Power <5W

## Future Enhancements

1. **Interactive Controls**: Click-to-sort columns, filtering
2. **Historical Graphs**: Mini-sparklines in process table
3. **Alert System**: Visual/audio notifications for critical states
4. **Export Functions**: Save monitoring snapshots
5. **Customizable Layouts**: User-configurable panel arrangements

## Dependencies Added
- No new external dependencies (reuses existing Rich/Textual)
- Self-contained within existing architecture
- Compatible with current build system
- **Cross-compatible**: Works with different Textual versions (no ScrollView dependency)

## Compatibility Notes
- Simplified widget architecture for broad Textual version compatibility
- Single `Static` widget approach instead of complex multi-widget layout
- Removed deprecated `ScrollView` import that caused issues in newer Textual versions
- Uses standard `set_interval` method available across Textual versions

This implementation provides immediate visual feedback about hardware health and activity, making TT-SMI more engaging and informative for real-time monitoring tasks.