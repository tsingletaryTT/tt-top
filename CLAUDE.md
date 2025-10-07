# TT-SMI Live Monitor Development with Claude

## Project Overview

This project added "top" or "htop"-like capabilities to the TT-SMI (Tenstorrent System Management Interface) application, creating a real-time hardware monitoring display inspired by classic tools like Logstalgia and Orca, with a retro BBS terminal aesthetic.

## Original User Request

**Initial Prompt**: "Let's work together! This branch is all about adding "top" or "htop" like capabilities to the visual display this app provides for Tenstorrent hardware. I'd like to take inspiration from Logstalgia for some of the visual components and from Orca for some of the grid-based aesthetic. We can call this new feature 'TT-Top'."

**Key Requirements**:
- Real-time hardware monitoring with information density comparable to htop
- Visual inspiration from Logstalgia (dynamic log visualization) and Orca (grid aesthetics)
- BBS-era terminal aesthetic with "leet ANSI art"
- Borderless table design for authentic terminal feel
- Show hardware insights not available in other tabs

## What Happened: Technical Evolution

### Phase 1: Initial Implementation (Cross-Platform Compatibility)
- **Challenge**: ScrollView import errors on Linux
- **Solution**: Simplified widget architecture using single `TTTopDisplay(Static)` widget
- **Learning**: Cross-platform Textual compatibility requires avoiding deprecated imports

### Phase 2: Rich Markup Conflicts
- **Challenge**: `MarkupError: closing tag '[/bold │ 19.0A │' does not match any open tag`
- **Solution**: Removed all embedded Rich markup from table structures, used plain Unicode
- **Learning**: Table formatting conflicts with Rich markup; separate concerns

### Phase 3: Border Alignment Issues
- **Challenge**: Tables and borders don't align properly despite precise character counting
- **Solution**: Adopted systemic borderless approach - no right borders anywhere
- **Learning**: Sometimes the solution is eliminating the problem entirely rather than fixing it

### Phase 4: Information Density Enhancement
- **Challenge**: User feedback that ASCII art was "not as useful as htop"
- **Solution**: Complete redesign focusing on unique hardware insights:
  - Memory topology with real DDR channel status
  - Temporal activity heatmaps (60-second history)
  - Interconnect bandwidth utilization matrix
  - Process analysis with efficiency metrics and trends
- **Learning**: Aesthetic must serve function, not replace it

### Phase 5: BBS Aesthetic Implementation
- **Challenge**: User shared BBS-era screenshot requesting "something more like this"
- **Solution**: Implemented retro terminal design with:
  - Pixelated hardware avatars in ASCII art
  - "Neural interface" branding
  - Borderless right-side tables for authentic terminal feel
- **Learning**: Visual references are crucial for achieving specific aesthetic goals

### Phase 6: Real Hardware Data Integration
- **Challenge**: Too much static/fake placeholder data
- **Solution**: Integrated real SMBUS telemetry data:
  - DDR training status and speed (get_dram_speed, get_dram_training_status)
  - ARC firmware health monitoring (heartbeat telemetry)
  - Real memory channel visualization based on DDR_STATUS
  - Actual power, temperature, and AICLK averages
- **Learning**: Real data makes displays more valuable and trustworthy

## Technical Architecture

### Key Files Modified
- `tt_smi/tt_top_widget.py` - Main implementation (856 lines)
- `tt_smi/tt_smi.py` - Integration with main app (keyboard binding, tab)
- `tt_smi/constants.py` - Help menu updates
- `test_fixed_widget.py` - Compatibility testing with mock data
- `show_bbs_demo.py` - Demo output script
- `BBS_STYLE_README.md` - Implementation documentation

### Core Methods Implemented
```python
# Real hardware data integration
def _generate_real_ddr_pattern(self, ddr_status: str, channels: int, device_idx: int) -> str:
    """Generate real DDR channel visualization based on actual hardware status"""

# BBS aesthetic components
def _create_bbs_header(self) -> List[str]:
    """Create BBS-style header with pixelated hardware avatar"""

def _create_bbs_main_display(self) -> List[str]:
    """Create main BBS-style display with terminal aesthetic"""

def _create_bbs_heatmap_section(self) -> List[str]:
    """Create BBS-style temporal heatmap"""

def _create_bbs_interconnect_section(self) -> List[str]:
    """Create BBS-style interconnect matrix"""
```

### Real Telemetry Data Sources
- **SMBUS Telemetry**: voltage, current, power, temperature, AICLK, heartbeat
- **DDR Status**: `DDR_SPEED`, `DDR_STATUS`, training status per channel
- **ARC Health**: `ARC0_HEALTH`, `ARC3_HEALTH` heartbeat monitoring
- **Memory Channels**: Real channel status (untrained=◯, training=◐/◑, trained=●, error=✗)

## Best Practices Applied

### Code Documentation
- Comprehensive docstrings explaining hardware-specific terminology
- Inline comments for complex bit manipulation (DDR status parsing)
- Clear method names reflecting real vs. simulated data

### Error Handling
```python
try:
    ddr_speed = self.backend.get_dram_speed(i)
    ddr_trained = self.backend.get_dram_training_status(i)
    ddr_info = self.backend.smbus_telem_info[i].get('DDR_STATUS', '0')
except:
    ddr_speed = "N/A"
    ddr_trained = False
    ddr_info = "0"
```

### Hardware-Specific Logic
- Different memory channel counts per architecture (GS: 4, WH: 8, BH: 12)
- Chip-specific telemetry methods (get_gs_chip_telemetry, get_wh_chip_telemetry, etc.)
- Real DDR status bit field parsing for authentic visualization

## Key Insights Gained

**★ Insight ─────────────────────────────────────**
The most successful approach was treating this as a hardware-specific monitoring tool rather than a generic system monitor. By leveraging real Tenstorrent telemetry data (DDR training status, ARC firmware health, memory topology), we created something unique that other monitoring tools cannot provide. The BBS aesthetic became the delivery mechanism for sophisticated hardware insights, not just decoration.
**─────────────────────────────────────────────────**

## Moments in Development

### Critical Decision Points
1. **ScrollView Deprecation**: Simplified architecture for compatibility
2. **Border Alignment**: Systemic removal instead of precise alignment
3. **Static vs. Real Data**: Complete transition to hardware telemetry
4. **Aesthetic vs. Function**: Balancing visual appeal with information density

### User Feedback Integration
- "Getting closer! New error..." → Confirmed fix direction
- "It's still not quite as useful as htop" → Triggered information density redesign
- "What about something more like this? [BBS screenshot]" → Visual reference guided implementation
- "Any static info that isn't related to hardware -- just remove it" → Real telemetry integration

### Evolution of Visual Design
1. **Complex multi-widget layout** → Single Static widget (compatibility)
2. **Rich markup integration** → Plain Unicode (conflict resolution)
3. **Precise border alignment** → Borderless design (systemic solution)
4. **Generic system monitor** → Hardware-specific insights (value differentiation)
5. **Static demonstrations** → Real telemetry integration (authenticity)

## Final Implementation Features

### Real-Time Hardware Insights
- **Memory Topology**: Live DDR channel status with training state animation
- **ARC Health Monitoring**: Firmware heartbeat tracking across devices
- **Temporal Heatmaps**: 60-second activity history visualization
- **Interconnect Matrix**: Device-to-device bandwidth simulation
- **Process Analysis**: Power efficiency, thermal management, load patterns

### BBS Terminal Aesthetic
- **Pixelated Hardware Avatar**: ASCII art system representation
- **Neural Interface Branding**: "TT-SYSMON v3.0 - NEURAL INTERFACE ONLINE"
- **Borderless Tables**: Authentic terminal aesthetic eliminating alignment issues
- **Unicode Animations**: Flowing data indicators, memory bank patterns
- **Real Hardware Footer**: Live device counts, DDR training status, system metrics

This project successfully bridged nostalgic computing aesthetics with modern hardware monitoring, creating a tool that is both visually engaging and functionally superior for Tenstorrent hardware analysis.