# TT-Top Layout Redesign: Textual-Native Organic Design

## Design Philosophy

**STOP**: Custom ASCII borders, rigid boxes, manual spacing
**START**: Textual's native containers, organic growth, responsive fr units

### Core Principles
1. **Use `height: auto`** - Let containers grow with content
2. **Use VerticalGroup/HorizontalGroup** - Non-expanding, fit-to-content containers
3. **Use Collapsible** - Built-in accordion widget for sections
4. **Use `fr` units** - Responsive fractional space allocation
5. **Use border styles** - Native `round`, `heavy` borders with opacity

---

## New Container Architecture

### Current Problem
```python
# tt_top_widget.py - Custom ASCII art borders
lines.append("┌─────────── SECTION HEADER ────────────┐")
lines.append("│ Content manually padded with spaces   │")
lines.append("└────────────────────────────────────────┘")
```
❌ Rigid width, doesn't adapt
❌ Borders can misalign
❌ Manual padding calculations

### Textual-Native Solution
```python
# Use Collapsible + CSS borders
with Collapsible(title="Device Telemetry"):
    yield DeviceTelemetryPanel()  # Auto-sized content

# CSS:
Collapsible {
    border: round $accent 70%;
    height: auto;  /* Grows with content */
    margin: 1;
}
```
✅ Automatically sized
✅ Borders always correct
✅ No manual calculations

---

## Layout Structure: 3-Column Organic Design

```
┌──────────────────────────────────────────────────────────────────┐
│                    TT-Top Header (Auto)                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ╭─ Device 0: Wormhole n150 ──────╮  ╭─ Device 1: Blackhole ─╮ │
│  │ Power:  43.2W ████████░░░░      │  │ Power:  67.8W ████▓▓ │ │
│  │ Temp:   45.1°C ██████░░░░░      │  │ Temp:   52.3°C █████ │ │
│  │ Current: 19.4A ████████████     │  │ Current: 28.1A █████ │ │
│  │ AICLK:  1200MHz [Turbo]         │  │ AICLK:  1400MHz [OC] │ │
│  ╰─────────────────────────────────╯  ╰──────────────────────╯ │
│                                                                  │
│  ▼ Memory Hierarchy (click to expand)                           │
│  ▼ Workload Intelligence (collapsed)                            │
│  ▼ System Context (lm-sensors)                                  │
│                                                                  │
│  ╭─ Hardware Event Stream (Last 10) ───────────────────────────╮│
│  │ 42:15 │ Dev 0 │ HIGH_CURRENT │ 71.3A │ peak demand          ││
│  │ 42:12 │ Dev 1 │ POWER_RAMP   │ +15W  │ increasing load      ││
│  │ 42:08 │ Dev 0 │ COMPUTE      │ MatMul│ Tensix cores active  ││
│  ╰───────────────────────────────────────────────────────────────╯│
└──────────────────────────────────────────────────────────────────┘
```

---

## Implementation: Component Breakdown

### 1. Multi-Device Grid (Native Grid Container)

```python
from textual.containers import Grid, VerticalGroup
from textual.widgets import Static, Collapsible

class DeviceTelemetryCard(Static):
    """Single device card with auto-height"""

    def compose(self) -> ComposeResult:
        """Telemetry content - grows naturally"""
        with VerticalGroup():  # Fits to content
            yield Static(f"Power:  {power}W")
            yield Static(f"Temp:   {temp}°C")
            yield Static(f"Current: {current}A")
            yield Static(f"AICLK:  {aiclk}MHz")

# CSS:
DeviceTelemetryCard {
    border: round $accent 70%;
    padding: 1;
    height: auto;  /* Key: grows with content */
    width: 1fr;    /* Equal columns */
}

class MultiDeviceGrid(Grid):
    """Responsive grid for N devices"""

    def compose(self) -> ComposeResult:
        num_devices = len(self.backend.devices)

        # Dynamic grid sizing based on device count
        if num_devices <= 3:
            self.styles.grid_size_columns = num_devices
        elif num_devices <= 6:
            self.styles.grid_size_columns = 3
        elif num_devices <= 12:
            self.styles.grid_size_columns = 4
        else:
            self.styles.grid_size_columns = 4

        self.styles.grid_gutter = 1  # Space between cards
        self.styles.grid_size_rows = "auto"  # Rows fit content

        # Yield device cards
        for device in self.backend.devices:
            yield DeviceTelemetryCard(device=device)

# CSS:
MultiDeviceGrid {
    height: auto;  /* Grows with content */
    padding: 1;
}
```

**Why This Works**:
- No manual width calculations
- Grid automatically sizes columns with `fr` units
- `height: auto` makes each card fit its content
- `grid_gutter` provides spacing without manual borders

---

### 2. Collapsible Sections (Built-in Widget)

```python
from textual.widgets import Collapsible

class ExpandableSections(VerticalScroll):
    """Scrollable container with collapsible sections"""

    def compose(self) -> ComposeResult:
        # Device grid - always visible
        yield MultiDeviceGrid(backend=self.backend)

        # Collapsible sections - click to expand
        with Collapsible(title="Memory Hierarchy Matrix", collapsed=False):
            yield MemoryHierarchyPanel(backend=self.backend)

        with Collapsible(title="Workload Intelligence Engine", collapsed=True):
            yield WorkloadDetectionPanel(backend=self.backend)

        with Collapsible(title="System Context (lm-sensors)", collapsed=True):
            yield SystemSensorsPanel(backend=self.backend)

        # Event stream - always visible at bottom
        yield HardwareEventStream(backend=self.backend)

# CSS:
Collapsible {
    border: round $accent 50%;
    margin: 1 0;  /* Vertical spacing only */
    height: auto;
}

Collapsible > Contents {
    padding: 1;
    height: auto;
}
```

**Why This Works**:
- Built-in expand/collapse with keyboard support (Enter)
- No custom border drawing code
- Sections grow/shrink naturally
- Users can hide irrelevant sections

---

### 3. DataTable for Event Stream

```python
from textual.widgets import DataTable

class HardwareEventStream(Static):
    """Live event stream using native DataTable"""

    def compose(self) -> ComposeResult:
        yield DataTable(zebra_stripes=True)

    def on_mount(self) -> None:
        table = self.query_one(DataTable)
        table.add_columns("Time", "Device", "Event", "Value", "Details")
        table.cursor_type = "row"
        table.fixed_rows = 1  # Header stays visible

        # Populate with events
        for event in self.get_recent_events():
            table.add_row(
                event['time'],
                f"Dev {event['device_idx']}",
                event['type'],
                event['value'],
                event['details']
            )

# CSS:
DataTable {
    height: 10;  /* Fixed height */
    border: heavy $accent;
    margin: 1 0;
}

DataTable > .datatable--header {
    background: $accent 30%;
    text-style: bold;
}
```

**Why This Works**:
- Native scrolling support
- Zebra striping built-in
- Row cursor navigation (arrow keys)
- Fixed header support
- Can handle thousands of rows efficiently

---

### 4. Progress Bars (Native Rich Rendering)

```python
from rich.progress import Progress, BarColumn
from textual.widgets import Static

class DeviceMetricBar(Static):
    """Metric with visual bar using Rich"""

    def render(self) -> RenderableType:
        # Use Rich Bar directly
        bar_width = 20
        filled = int(bar_width * (self.value / self.max_value))
        bar = "█" * filled + "░" * (bar_width - filled)

        # Color based on value
        if self.value > 0.8 * self.max_value:
            color = "red"
        elif self.value > 0.6 * self.max_value:
            color = "yellow"
        else:
            color = "green"

        return f"{self.label}: {self.value}{self.unit} [{color}]{bar}[/] {self.percent}%"

# Example usage:
yield DeviceMetricBar(label="Power", value=43.2, max_value=120, unit="W")
# Renders: Power: 43.2W [green]████████░░░░░░░░░░░░[/] 36%
```

---

## CSS Styling Strategy

### theme.tcss (New file)
```css
/* Organic, non-boxy design */

/* Main screen */
Screen {
    background: $surface;
}

/* Container defaults */
VerticalScroll {
    height: 100%;
    scrollbar-gutter: stable;  /* Prevent content shift */
}

VerticalGroup, HorizontalGroup {
    height: auto;  /* Fit content */
    padding: 0;
    margin: 0;
}

/* Device cards */
DeviceTelemetryCard {
    border: round $accent 70%;
    padding: 1;
    height: auto;
    width: 1fr;
    margin: 1;
}

DeviceTelemetryCard:focus {
    border: round $accent;  /* Full opacity on focus */
}

/* Collapsible sections */
Collapsible {
    border: round $primary 50%;
    margin: 1 0;
    height: auto;
}

Collapsible.-collapsed {
    border: dashed $primary 30%;  /* Dimmer when collapsed */
}

Collapsible > Contents {
    padding: 1;
    height: auto;
}

/* DataTable */
DataTable {
    border: heavy $accent;
    height: 10;
    margin: 1 0;
}

DataTable > .datatable--header {
    background: $accent 30%;
    text-style: bold;
}

DataTable > .datatable--cursor {
    background: $secondary 50%;
}

/* Grid layouts */
Grid {
    height: auto;
    padding: 0;
}

Grid > * {
    height: auto;  /* All grid items auto-size */
}

/* No rigid borders - use transparency */
Static {
    border: none;  /* Remove default borders */
    height: auto;
}
```

---

## Responsive Behavior

### 1-3 Devices: Full-Width Cards
```
┌────────────────────────────────────────────────┐
│  ╭─ Device 0 ─────────╮  ╭─ Device 1 ────────╮│
│  │ [Full details]     │  │ [Full details]    ││
│  ╰────────────────────╯  ╰───────────────────╯│
└────────────────────────────────────────────────┘
```

### 4-6 Devices: 3-Column Grid
```
┌────────────────────────────────────────────────┐
│  ╭─ Dev 0 ──╮  ╭─ Dev 1 ──╮  ╭─ Dev 2 ──╮    │
│  │ [Compact]│  │ [Compact]│  │ [Compact]│    │
│  ╰──────────╯  ╰──────────╯  ╰──────────╯    │
│  ╭─ Dev 3 ──╮  ╭─ Dev 4 ──╮  ╭─ Dev 5 ──╮    │
│  │ [Compact]│  │ [Compact]│  │ [Compact]│    │
│  ╰──────────╯  ╰──────────╯  ╰──────────╯    │
└────────────────────────────────────────────────┘
```

### 7-16 Devices: 4-Column Compact Grid
```
┌──────────────────────────────────────────────┐
│  ╭─D0─╮ ╭─D1─╮ ╭─D2─╮ ╭─D3─╮              │
│  │ 43W│ │ 67W│ │ 52W│ │ 38W│              │
│  ╰────╯ ╰────╯ ╰────╯ ╰────╯              │
│  ╭─D4─╮ ╭─D5─╮ ╭─D6─╮ ╭─D7─╮              │
│  │ 29W│ │ 71W│ │ 45W│ │ 58W│              │
│  ╰────╯ ╰────╯ ╰────╯ ╰────╯              │
└──────────────────────────────────────────────┘
```

---

## File Structure Changes

### New Files to Create:
```
tt_top/
├── widgets/
│   ├── __init__.py
│   ├── device_card.py          # DeviceTelemetryCard widget
│   ├── event_stream.py         # HardwareEventStream widget
│   ├── memory_panel.py         # MemoryHierarchyPanel widget
│   ├── workload_panel.py       # WorkloadDetectionPanel widget
│   └── system_panel.py         # SystemSensorsPanel (lm-sensors)
├── layouts/
│   ├── __init__.py
│   ├── multi_device_grid.py    # MultiDeviceGrid container
│   └── main_layout.py          # ExpandableSections container
└── theme.tcss                   # CSS styling

# Modify:
tt_top/tt_top_app.py              # Use new layout system
tt_top/tt_top_widget.py           # Deprecate in favor of widgets/
```

---

## Migration Strategy

### Phase 1: Create New Widget System (Don't break existing)
1. Create `widgets/` directory with new components
2. Create `layouts/` directory with Grid and VerticalScroll containers
3. Create `theme.tcss` with organic styling

### Phase 2: Add Feature Flag Toggle
```python
# tt_top_app.py
BINDINGS = [
    Binding("1", "switch_layout('classic')", "Classic"),
    Binding("2", "switch_layout('organic')", "Organic"),
]
```

### Phase 3: Make Organic Default
- Set `layout_mode = "organic"` as default
- Keep classic mode available via key binding

### Phase 4: Deprecate Classic
- Remove tt_top_widget.py custom ASCII rendering
- Pure Textual widgets only

---

## Benefits Summary

### Before (Custom ASCII):
❌ Manual border calculations
❌ Rigid fixed widths
❌ Border misalignment issues
❌ No collapsing sections
❌ Custom scrolling logic
❌ Reinventing the wheel

### After (Textual Native):
✅ Automatic border sizing
✅ Responsive `fr` units
✅ Always perfect alignment
✅ Built-in Collapsible widget
✅ Native scrolling (VerticalScroll)
✅ Using proven library features

---

## Next Steps

1. ✅ Research Textual features (DONE)
2. ⏳ Create `widgets/device_card.py`
3. ⏳ Create `layouts/multi_device_grid.py`
4. ⏳ Create `theme.tcss`
5. ⏳ Add layout toggle in `tt_top_app.py`
6. ⏳ Test with 1, 3, 8, 16 device configurations

---

**Status**: 🎯 Ready for Implementation
**Date**: December 7, 2025
**Design Philosophy**: Textual-native, organic, non-boxy

## References
- [Textual Containers API](https://textual.textualize.io/api/containers/)
- [Textual Collapsible Widget](https://textual.textualize.io/widgets/collapsible/)
- [Textual Height/Width Auto](https://textual.textualize.io/styles/height/)
- [Fr Units Guide by Darren Burns](https://darren.codes/posts/textual-layout-fr-units/)
- [Textual Border Styles](https://textual.textualize.io/styles/border/)
- [Textual DataTable](https://textual.textualize.io/widgets/data_table/)
