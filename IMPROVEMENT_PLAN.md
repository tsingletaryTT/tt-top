# TT-Top Enhancement Plan: World-Class Monitoring Tool

## Vision Statement
Transform tt-top from a functional monitoring tool into a world-class TUI that combines:
- **Logstalgia's visual beauty**: Flowing, color-coded animations that tell a story
- **htop's information density**: Every pixel serves a purpose, no wasted space
- **Engineering precision**: All visualizations driven by real data, no decorations

---

## 1. CRITICAL ISSUES TO RESOLVE

### 1.1 Process Detection (/proc monitoring) - FIX OR REMOVE

**Current Problem**: Workload detection using psutil/ps//proc doesn't show active loads on devices.

**Root Cause Analysis Needed**:
- psutil is NOT in current dependencies (missing from requirements.txt line 12)
- Process detection has 3 fallback methods but may not be correlating correctly with hardware
- Pattern matching may be too specific (looking for "python.*torch" but actual processes may be different)

**Decision Matrix**:

| Option | Pros | Cons | Recommendation |
|--------|------|------|----------------|
| **Fix it properly** | Provides valuable context about what's running | Complex correlation logic, platform-specific | ✅ **RECOMMENDED** |
| **Remove entirely** | Simplifies codebase | Loses valuable workload context | ❌ Not recommended |
| **Make it opt-in** | Works when it works, doesn't clutter when broken | Hidden feature, users won't discover it | ⚠️ Consider |

**Proposed Fix**:
```python
# 1. Add psutil to dependencies properly
# 2. Expand detection patterns to catch real workloads:
#    - Look for ANY Python process with high memory (>1GB) + GPU-related env vars
#    - Check for device file access (/dev/tenstorrent/*)
#    - Monitor processes with tt-smi, tt-kmd, ttnn in cmdline
# 3. Add debug logging: "Detected N processes, M matched patterns, K correlated with telemetry"
# 4. Show detection statistics in UI (with toggle to show details)
```

---

## 2. ARCHITECTURAL IMPROVEMENTS

### 2.1 Multi-Device Layout Strategy

**Current Problem**: Multiple cards "jumble" in visualization mode.

**Engineering Solution**: Use Textual's Grid and Container system properly.

#### **For 1-4 Devices**: Horizontal layout (current approach works)
```
┌─────────────────────────────────────────────────────┐
│  Device 0    │  Device 1    │  Device 2    │  Dev 3 │
│  [starfield] │  [starfield] │  [starfield] │  [*]   │
│  ●◉○✦★      │  ●◉○✦★      │  ●◉○✦★      │  ●◉○   │
└─────────────────────────────────────────────────────┘
```

#### **For 5-8 Devices**: 2×4 Grid layout
```
┌─────────────────────────────────────────────────────┐
│  Dev 0  │  Dev 1  │  Dev 2  │  Dev 3                │
│  ●◉○✦  │  ●◉○✦  │  ●◉○✦  │  ●◉○✦                 │
├─────────────────────────────────────────────────────┤
│  Dev 4  │  Dev 5  │  Dev 6  │  Dev 7                │
│  ●◉○✦  │  ●◉○✦  │  ●◉○✦  │  ●◉○✦                 │
└─────────────────────────────────────────────────────┘
```

#### **For 9-16 Devices**: 4×4 Grid layout with compact mode
```
┌─────────────────────────────────────────────┐
│ D0 │ D1 │ D2 │ D3 │ D4 │ D5 │ D6 │ D7 │     │
│ ●◉ │ ●◉ │ ●◉ │ ●◉ │ ●◉ │ ●◉ │ ●◉ │ ●◉ │     │
├─────────────────────────────────────────────┤
│ D8 │ D9 │D10 │D11 │D12 │D13 │D14 │D15 │     │
│ ●◉ │ ●◉ │ ●◉ │ ●◉ │ ●◉ │ ●◉ │ ●◉ │ ●◉ │     │
└─────────────────────────────────────────────┘
```

**Implementation**:
```python
# Use Textual's Grid container with dynamic sizing
from textual.containers import Grid

class MultiDeviceGrid(Grid):
    def __init__(self, num_devices: int):
        if num_devices <= 4:
            # Horizontal layout
            self.styles.grid_size_columns = num_devices
            self.styles.grid_size_rows = 1
        elif num_devices <= 8:
            # 2×4 grid
            self.styles.grid_size_columns = 4
            self.styles.grid_size_rows = 2
        else:
            # 4×4 grid (compact)
            self.styles.grid_size_columns = 4
            self.styles.grid_size_rows = (num_devices + 3) // 4
```

### 2.2 Expand Information Display (Stop Shortening!)

**Current Problem**: Text is abbreviated, condensed, shortened to fit.

**Solution**: Use Textual's layout system to EXPAND intelligently.

#### **Stop This**:
```
│ Dev 0: WOR │ Pwr: 43W │ Cur: 19A │ Tmp: 45C │
```

#### **Do This Instead**:
```
╔═══════════════════════ DEVICE 0: WORMHOLE n150 ═══════════════════════╗
║ Power Consumption  │ 43.2W  (35% of TDP)    [████████░░░░░░░░░░░░] ║
║ Current Draw       │ 19.4A  (High activity)  [████████████░░░░░░░░] ║
║ Temperature        │ 45.1°C (Nominal)        [██████░░░░░░░░░░░░░░] ║
║ AICLK Frequency    │ 1200MHz (Turbo)         [████████████████░░░░] ║
║ ARC Firmware       │ ❤️ Healthy (beat: 1.2s) [✓ ARC0] [✓ ARC3]   ║
╚═══════════════════════════════════════════════════════════════════════╝
```

**Use Visual Encoding**:
- Bar graphs for utilization (like htop CPU bars)
- Color gradients for temperature (blue → green → yellow → red)
- Status symbols (✓✗⚠❤) for health checks
- Full names, not abbreviations

### 2.3 Larger Grid Visualizations

**Current Problem**: Grids are compressed (14×16 → 8×6 displayed).

**Solution**: Use scrollable containers and multiple view modes.

#### **Full Grid View Mode** (new key binding: `g`)
```
┌─────────── FULL TENSIX GRID: BLACKHOLE (14×16 = 224 cores) ────────────┐
│                                                                         │
│   0  1  2  3  4  5  6  7  8  9  A  B  C  D  E  F                      │
│ 0 ██ ██ ▓▓ ▒▒ ░░ ·· ·· ·· ·· ·· ·· ·· ▒▒ ▓▓ ██ ██   Row 0: 87% active │
│ 1 ██ ▓▓ ▓▓ ▒▒ ░░ ·· ·· ·· ·· ·· ░░ ▒▒ ▓▓ ▓▓ ██ ██   Row 1: 75% active │
│ 2 ▓▓ ▓▓ ▒▒ ▒▒ ░░ ░░ ·· ·· ·· ░░ ░░ ▒▒ ▒▒ ▓▓ ▓▓ ██   Row 2: 62% active │
│ 3 ▒▒ ▒▒ ▒▒ ░░ ░░ ·· ·· ·· ·· ·· ░░ ░░ ▒▒ ▒▒ ▒▒ ▓▓   Row 3: 45% active │
│ ...scrollable...                                                       │
│ D ██ ██ ▓▓ ▒▒ ░░ ·· ·· ·· ·· ·· ░░ ▒▒ ▓▓ ██ ██ ██   Row 13: 81% activ│
│                                                                         │
│ Column stats: [Press 'c' to see column-by-column breakdown]           │
│ Hottest core: Row 0, Col 0 (92% util) │ Coldest: Row 6, Col 8 (3%)   │
└─────────────────────────────────────────────────────────────────────────┘
```

**Implementation Strategy**:
- Use `VerticalScroll` container for full grid
- Add core-level details on hover (if mouse enabled)
- Color code by activity level (current power-based)
- Show row/column statistics

---

## 3. NEW DATA SOURCES

### 3.1 lm-sensors Integration

**Goal**: Add motherboard/system context to Tenstorrent hardware monitoring.

**What lm-sensors Provides**:
```bash
# sensors -j outputs JSON like:
{
  "coretemp-isa-0000": {
    "Package id 0": {
      "temp1_input": 45.0,
      "temp1_max": 100.0
    },
    "Core 0": {"temp2_input": 42.0},
    "Core 1": {"temp3_input": 43.0}
  },
  "k10temp-pci-00c3": {
    "Tdie": {"temp1_input": 55.0}
  },
  "iwlwifi_1-virtual-0": {
    "temp1": {"temp1_input": 42.0}
  }
}
```

**What to Display**:
```
╔═══════════════════ SYSTEM CONTEXT (lm-sensors) ═══════════════════╗
║ CPU Package      │ 45°C ████░░░░░░  (8 cores avg: 43°C)         ║
║ Motherboard      │ 38°C ██░░░░░░░░  (PCH chipset)               ║
║ PCIe Slot 1 Temp │ 52°C ██████░░░░  (TT Device 0 slot)          ║
║ VRM Temperature  │ 61°C ████████░░  (Power delivery)            ║
║ Case Fan 1       │ 1240 RPM        (intake, front)              ║
║ Case Fan 2       │ 980 RPM         (exhaust, rear)              ║
║ PSU Fan          │ 0 RPM           (fanless mode)               ║
╚═══════════════════════════════════════════════════════════════════╝
```

**Why This Matters**:
- Correlate TT device temperatures with ambient/case temps
- Detect thermal throttling due to inadequate cooling
- Monitor power delivery (VRM) temperatures under load
- Identify PCIe slot thermal issues

**Implementation**:
```python
import json
import subprocess

class LMSensorsAdapter:
    """Parse lm-sensors data for system context"""

    def get_sensors_data(self) -> Dict:
        """Get sensor data using JSON output"""
        try:
            result = subprocess.run(
                ['sensors', '-j'],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except (FileNotFoundError, json.JSONDecodeError, subprocess.TimeoutExpired):
            # Fallback to -u (raw) output parsing if -j not available
            return self._parse_raw_output()
        return {}

    def get_system_context(self) -> Dict[str, float]:
        """Extract relevant system temperatures and fan speeds"""
        data = self.get_sensors_data()
        context = {
            'cpu_package_temp': self._extract_cpu_temp(data),
            'motherboard_temp': self._extract_mb_temp(data),
            'vrm_temp': self._extract_vrm_temp(data),
            'pcie_slot_temps': self._extract_pcie_temps(data),
            'fan_speeds': self._extract_fan_speeds(data),
        }
        return context
```

### 3.2 Expand tt-smi JSON Consumption

**Current JSON Fields Used**:
- Basic telemetry: voltage, current, power, temperature, aiclk
- SMBUS: DDR_STATUS, DDR_SPEED, ARC_HEALTH
- Board info: board_type, bus_id

**Available but UNUSED Fields** (research tt-smi schema):
- Firmware versions
- PCIe link speed/width
- Memory ECC error counts
- Thermal history
- Power limit violations
- Clock throttling events

**Action Items**:
1. Document full tt-smi JSON schema (reverse engineer from tt-smi source)
2. Add all available fields to log.py Pydantic models
3. Create visualizations for previously ignored data

---

## 4. ADVANCED TEXTUAL FEATURES

### 4.1 DataTable for Detailed Views

**Use Case**: Detailed per-device statistics table.

**Example Implementation**:
```python
from textual.widgets import DataTable

class DeviceStatsTable(DataTable):
    """Scrollable table of device statistics"""

    def populate_devices(self, backend):
        self.clear()
        self.add_columns("Device", "Type", "Power", "Temp", "AICLK", "DDR", "ARC", "Status")

        for i, device in enumerate(backend.devices):
            telem = backend.get_device_telemetry(i)
            ddr_status = "✓ Trained" if backend.get_dram_training_status(i) else "⚠ Training"
            arc_health = "❤ Healthy" if telem.get('heartbeat', 0) > 0 else "✗ Timeout"

            self.add_row(
                f"Device {i}",
                device.board_type,
                f"{telem['power']:.1f}W",
                f"{telem['asic_temperature']:.1f}°C",
                f"{telem['aiclk']}MHz",
                ddr_status,
                arc_health,
                self._get_status_icon(telem)
            )
```

**Binding**: Press `t` for table view, `Esc` to return.

### 4.2 Screen System for Multiple Views

**Goal**: Multiple full-screen modes, not just toggle between 2 states.

**View Modes**:
1. **Dashboard View** (current default): Compact multi-device overview
2. **Detailed View** (new): Single device, full stats, large grid
3. **Table View** (new): DataTable with all devices, sortable columns
4. **Visualization View** (current 'v' mode): Starfield animation
5. **Flow View** (new): Logstalgia-style data flow visualization
6. **System View** (new): Full system context (TT devices + lm-sensors)

**Implementation**:
```python
from textual.screen import Screen

class DashboardScreen(Screen):
    """Multi-device compact overview"""
    pass

class DetailedScreen(Screen):
    """Single device deep-dive"""
    pass

class FlowScreen(Screen):
    """Logstalgia-style flowing data visualization"""
    pass

# In TTTopApp:
SCREENS = {
    "dashboard": DashboardScreen,
    "detailed": DetailedScreen,
    "table": TableScreen,
    "visualization": VisualizationScreen,
    "flow": FlowScreen,
    "system": SystemScreen,
}

BINDINGS = [
    Binding("1", "switch_screen('dashboard')", "Dashboard"),
    Binding("2", "switch_screen('detailed')", "Detailed"),
    Binding("3", "switch_screen('table')", "Table"),
    Binding("4", "switch_screen('visualization')", "Viz"),
    Binding("5", "switch_screen('flow')", "Flow"),
    Binding("6", "switch_screen('system')", "System"),
]
```

### 4.3 Grid Layout for Complex Compositions

**Example: Dashboard with 4 panels**
```python
class DashboardLayout(Container):
    """4-panel dashboard using Grid layout"""

    def compose(self) -> ComposeResult:
        with Grid():
            yield DeviceSummaryPanel()      # Top-left
            yield SystemContextPanel()      # Top-right
            yield MemoryHierarchyPanel()    # Bottom-left
            yield ProcessActivityPanel()    # Bottom-right

# CSS:
Grid {
    grid-size: 2 2;
    grid-gutter: 1;
}
```

---

## 5. LOGSTALGIA-INSPIRED FLOW VISUALIZATION

### 5.1 Data Flow Particles

**Concept**: Show data movement as flowing particles between memory hierarchy levels.

**Visual Design**:
```
          DDR DRAM (12 channels)
         ↓↓↓ ← flowing particles
      ╔══════════════════════╗
      ║    L2 CACHE          ║
      ║  ◉ ◉ ◉ → → ◉ ◉      ║  ← particles flowing right
      ╚══════════════════════╝
         ↓↓↓
      ╔══════════════════════╗
      ║  L1 SRAM (Tensix)    ║
      ║  ● ● ◉ ◉ ○ ○ ○ ●    ║  ← cores consuming data
      ╚══════════════════════╝
         ↓↓↓
        PCIe Host
```

**Particle Properties** (Logstalgia-inspired):
- **Color**: Encode data type (read=blue, write=red, compute=green)
- **Size**: Encode data volume (small=KB, medium=MB, large=GB)
- **Speed**: Encode bandwidth (slow=10MB/s, fast=100GB/s)
- **Path**: Follow memory hierarchy (DDR → L2 → L1 → Compute)

**Implementation**:
```python
class FlowParticle:
    def __init__(self, source, dest, data_type, volume, bandwidth):
        self.x, self.y = source
        self.target_x, self.target_y = dest
        self.color = self._get_color(data_type)  # Blue/red/green
        self.char = self._get_char(volume)       # ·○◉●
        self.speed = bandwidth / 100.0           # Pixels per frame
        self.trail = []                          # Recent positions

    def update(self):
        """Move particle toward destination"""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        distance = math.sqrt(dx**2 + dy**2)

        if distance > self.speed:
            # Move toward target
            self.x += (dx / distance) * self.speed
            self.y += (dy / distance) * self.speed
            self.trail.append((int(self.x), int(self.y)))
            if len(self.trail) > 5:
                self.trail.pop(0)
        else:
            # Arrived at destination
            return True  # Particle complete
        return False
```

### 5.2 Real-Time Event Stream

**Concept**: Show hardware events flowing up the screen (like log lines in Logstalgia).

```
┌─────────────────── LIVE EVENT STREAM ──────────────────────┐
│                                                             │
│ ↑ [42:15] Dev 0 │ DDR Read Burst   │ 8.2GB/s │ Channel 3 ↑│
│ ↑ [42:15] Dev 1 │ L2 Cache Hit     │ 95% hit │ Hot data  ↑│
│ ↑ [42:14] Dev 0 │ Compute Start    │ MatMul  │ Tensix 0  ↑│
│ ↑ [42:14] Dev 2 │ Power Spike      │ +15W    │ Training  ↑│
│ ↑ [42:13] Dev 0 │ ARC Heartbeat    │ 1.2s    │ Healthy   ↑│
│   [older events scroll up and fade out...]                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Implementation**: Use scrolling buffer with fade-out effect.

---

## 6. HTOP-LEVEL INFORMATION DENSITY

### 6.1 Dense Layout Principles

**htop Lessons**:
1. **No wasted space**: Every character serves a purpose
2. **Visual hierarchy**: Color coding replaces lengthy labels
3. **Compact notation**: Use symbols (✓✗⚠) instead of words
4. **Bar graphs**: Show proportions visually (████░░░░)
5. **Column alignment**: Right-align numbers, left-align text
6. **Smart scrolling**: Only what doesn't fit

**Apply to tt-top**:

#### **Before** (current, too much whitespace):
```
Device 0: Wormhole
Power: 43.2W
Current: 19.4A
Temperature: 45°C
```

#### **After** (htop-dense):
```
 0 WOR │ 43.2W ████░░ 35% │ 19.4A ████████░░ 64% │ 45°C ███░░░ 45% │ ✓
```

### 6.2 Header Bar Design

**htop-style header** (always visible, dense info):
```
┌─────────────────────────────────────────────────────────────────────┐
│ TT-Top │ 3 devices │ Sys: 48°C │ Total: 127W │ ↑15.2GB/s │ ⚡Active │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.3 Footer Bar Design

**htop-style footer** (function keys):
```
┌─────────────────────────────────────────────────────────────────────┐
│ 1Dash 2Detail 3Table 4Viz 5Flow 6System │ t:Sort g:Grid q:Quit    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 7. IMPLEMENTATION ROADMAP

### Phase 1: Fix Critical Issues (Week 1)
- [ ] Fix psutil import in requirements.txt
- [ ] Debug workload detection with verbose logging
- [ ] Add detection statistics display
- [ ] Improve multi-device grid layout (5-16 devices)

### Phase 2: Expand Information Display (Week 2)
- [ ] Remove abbreviations, use full names
- [ ] Add visual progress bars (power, temp, utilization)
- [ ] Expand device info panels
- [ ] Add full grid view mode (`g` key)
- [ ] Implement scrollable containers properly

### Phase 3: Add lm-sensors Integration (Week 3)
- [ ] Create LMSensorsAdapter class
- [ ] Parse JSON output from `sensors -j`
- [ ] Add system context panel
- [ ] Correlate system temps with TT device temps
- [ ] Add fan speed monitoring

### Phase 4: Advanced Textual Features (Week 4)
- [ ] Implement Screen system (6 view modes)
- [ ] Add DataTable for detailed stats
- [ ] Create Grid-based dashboard layout
- [ ] Add proper navigation (number keys 1-6)
- [ ] Implement htop-style header/footer

### Phase 5: Flow Visualization (Week 5-6)
- [ ] Design particle system architecture
- [ ] Implement DDR→L2→L1 data flow particles
- [ ] Add color/size/speed encoding
- [ ] Create event stream view
- [ ] Add particle trails and fade effects

### Phase 6: Polish & Optimization (Week 7)
- [ ] Optimize rendering performance
- [ ] Add configuration file support
- [ ] Implement user preferences
- [ ] Add color theme support
- [ ] Performance profiling and optimization

---

## 8. TECHNICAL SPECIFICATIONS

### 8.1 Dependencies to Add
```toml
# Add to pyproject.toml dependencies:
dependencies = [
  'pydantic>=1.9.0',
  'rich>=13.7.0',
  'textual>=0.59.0',
  'psutil>=5.9.0',  # Already listed but ensure it's working
]
```

### 8.2 New Files to Create
```
tt_top/
├── lm_sensors_adapter.py       # lm-sensors integration
├── screens/
│   ├── __init__.py
│   ├── dashboard.py            # Multi-device overview
│   ├── detailed.py             # Single device deep-dive
│   ├── table.py                # DataTable view
│   ├── visualization.py        # Starfield (existing)
│   ├── flow.py                 # Flow particles (new)
│   └── system.py               # Full system context (new)
├── widgets/
│   ├── __init__.py
│   ├── device_panel.py         # Expanded device info
│   ├── system_panel.py         # lm-sensors data
│   ├── grid_view.py            # Full Tensix grid
│   ├── flow_particles.py       # Particle system
│   └── stats_table.py          # DataTable implementation
└── layouts/
    ├── __init__.py
    ├── multi_device_grid.py    # Smart grid for N devices
    └── dashboard_grid.py       # 4-panel dashboard
```

### 8.3 Performance Targets
- **Refresh rate**: Maintain 10 FPS (100ms updates)
- **CPU usage**: <5% on modern CPU (single core)
- **Memory**: <50MB for 16 devices
- **Latency**: <10ms from tt-smi JSON to display update

---

## 9. DESIGN PHILOSOPHY

### Core Principles
1. **Every pixel has a purpose**: No decorative elements
2. **Real data drives everything**: All animations reflect actual hardware state
3. **Information density over whitespace**: Make every character count
4. **Beautiful AND useful**: Aesthetics serve function
5. **Engineering truth**: No marketing speak, precise measurements only

### Visual Hierarchy
1. **Critical alerts**: Bold red, can't be missed
2. **Warnings**: Yellow/orange, noticeable
3. **Normal operation**: Green/cyan, calm
4. **Inactive/idle**: Dim gray, background
5. **Context**: White, informational

### Color Palette (Cyberpunk Engineering)
```python
COLORS = {
    'critical': 'bold red',        # >80°C, errors, failures
    'warning': 'bold yellow',      # >65°C, elevated power
    'active': 'bright_green',      # Normal active operation
    'idle': 'bright_cyan',         # Low power, ready state
    'inactive': 'dim white',       # Background, disabled
    'accent': 'bright_magenta',    # Highlights, borders
    'info': 'bright_white',        # Labels, text
}
```

---

## 10. SUCCESS METRICS

### Usability Goals
- [ ] Engineers can diagnose hardware issues in <30 seconds
- [ ] All abbreviations eliminated, full context available
- [ ] Multi-device systems display clearly without "jumbling"
- [ ] Workload detection shows running processes accurately
- [ ] System context (lm-sensors) provides thermal correlation

### Technical Goals
- [ ] 2000+ lines of dense information visible simultaneously
- [ ] 6 different view modes accessible via number keys
- [ ] Particle flow visualization running at 10 FPS
- [ ] Full Tensix grid (14×16) displayable and scrollable
- [ ] DataTable supporting 100+ devices without lag

### Beauty Goals
- [ ] As visually striking as Logstalgia
- [ ] As information-dense as htop
- [ ] As engineering-precise as oscilloscope display
- [ ] Users say "wow" on first launch, then use it daily for real work

---

## References

### Documentation Sources
- [lm-sensors manual](https://manpages.debian.org/unstable/lm-sensors/sensors.1.en.html)
- [lm-sensors GitHub Issue #18: JSON Output](https://github.com/lm-sensors/lm-sensors/issues/18)
- [Textual Layout Guide](https://textual.textualize.io/guide/layout/)
- [Textual Grid Container](https://textual.textualize.io/styles/grid/)
- [Textual DataTable Widget](https://textual.textualize.io/widgets/data_table/)
- [htop source code](https://github.com/htop-dev/htop)
- [Logstalgia visualization design](https://portalzine.de/website-traffic-visualization-with-logstalgia/)
- [Terminal UI Design Principles (2025)](https://www.blog.brightcoding.dev/2025/09/07/beyond-the-gui-the-ultimate-guide-to-modern-terminal-user-interface-applications-and-development-libraries/)

### Engineering Principles
- [UNIX Philosophy](https://en.wikipedia.org/wiki/Unix_philosophy): Do one thing well, compose via clean interfaces
- [Data Visualization Principles](https://dasycenter.org/datavis-toolkit/animations/): Animations should enhance understanding, not distract
- [Information Density](https://www.blog.brightcoding.dev/2025/09/07/beyond-the-gui-the-ultimate-guide-to-modern-terminal-user-interface-applications-and-development-libraries/): Maximize useful information per screen area

---

**Document Version**: 1.0
**Date**: December 7, 2025
**Status**: 🎯 Ready for Implementation
