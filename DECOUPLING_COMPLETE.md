# TT-Top Decoupling Complete

## Summary

TT-Top has been fully decoupled from tt-smi internal code and now operates as a standalone UNIX-style tool that consumes JSON telemetry data.

## What Changed

### Code Removed
- ✅ All `TTSMIBackend` imports and usage
- ✅ All `tt_smi_backend` module dependencies
- ✅ All `SafetyConfig` and hardware safety coordinator code
- ✅ `--direct-mode` CLI flag and implementation
- ✅ Legacy CLI flags: `--safe-mode`, `--poll-interval`, `--max-errors`, `--workload-check-interval`, `--lock-timeout`, `--max-retries`, `--no-telemetry-warnings`
- ✅ Hardware detection and device initialization code
- ✅ pyluwen and tt_tools_common import paths

### Architecture Transformation

**Before**:
```
tt-top → TTSMIBackend → pyluwen → hardware (direct access)
```

**After**:
```
tt-top → tt-smi subprocess → JSON stream → JSONBackendAdapter → Visualization
```

### Only Two Modes

1. **JSON Mode (default)**: `tt-top` - Spawns tt-smi subprocess, consumes JSON
2. **Mock Mode (testing)**: `tt-top --mock` - Uses simulated data

### Files Added

- `tt_top/json_backend_adapter.py` (684 lines) - JSON backend adapter with subprocess management
- `tt_top/device_proxy.py` (159 lines) - Lightweight architecture detection

### Files Modified

- `tt_top/tt_top_app.py` - Simplified to JSON-only with better error messages
- `README.md` - Updated architecture, dependencies, usage examples
- `CLAUDE.md` - Documented complete decoupling rationale

### Unused Legacy Files

These files remain in the repository from the fork but are **NOT used by tt-top**:
- `tt_top/tt_smi_backend.py` (legacy, not imported)
- `tt_top/safety.py` (legacy, not imported)
- `tt_smi/` directory (entire directory unused)

**Note**: These files can be removed in a future cleanup, but are kept for now for historical reference.

## Benefits Achieved

### 1. Zero Code Coupling
- tt-top cannot import any tt-smi internal modules
- No shared code paths or internal APIs
- Changes in tt-smi internals cannot break tt-top
- Only dependency: JSON format contract

### 2. Intentional Evolution
- tt-smi JSON changes require explicit schema updates
- tt-top maintainers review JSON format changes
- Backward compatibility managed at JSON layer
- No accidental breakage from refactoring

### 3. Distribution Simplicity
- tt-top has minimal dependencies: textual, rich, pydantic, psutil
- No hardware stack dependencies: pyluwen, tt_tools_common
- Can be pip-installed on any machine
- Works on systems without hardware access

### 4. Clear Separation of Concerns

**tt-smi Responsibilities**:
- Hardware detection and initialization
- Safety coordination and error handling
- SMBUS telemetry collection
- DDR training status monitoring
- ARC firmware health checking
- JSON serialization

**tt-top Responsibilities**:
- JSON parsing and validation
- Device architecture detection (from board_type)
- Visualization rendering
- /proc filesystem scanning for workload detection
- User interface and keyboard handling
- Mock data generation

### 5. Testing Independence
- tt-top tests don't need hardware
- tt-top tests don't need tt-smi internals
- Mock mode provides complete test coverage
- CI/CD runs without hardware dependencies

## Usage Examples

### Standard Usage
```bash
# Start monitoring (requires tt-smi installed)
tt-top

# Monitor specific device
tt-top --device 0

# Custom tt-smi path
tt-top --tt-smi-path /usr/local/bin/tt-smi

# Debug logging
tt-top --log-level DEBUG
```

### Mock Mode
```bash
# Testing without hardware
tt-top --mock

# Mock with debug output
tt-top --mock --log-level DEBUG
```

## JSON Contract

### Interface Boundary
The JSON schema defines the exact data contract between tt-smi and tt-top:

```json
{
  "time": "2024-12-01T12:00:00Z",
  "host_info": { ... },
  "host_sw_vers": { ... },
  "device_info": [
    {
      "smbus_telem": {
        "DDR_STATUS": "255",
        "DDR_SPEED": "6400",
        "ARC0_HEALTH": "1",
        "AICLK": "1000",
        "ASIC_TEMPERATURE": "52.3",
        ...
      },
      "board_info": {
        "board_type": "n150",
        "bus_id": "0000:01:00.0",
        "dram_status": "Trained",
        ...
      },
      "telemetry": {
        "voltage": "0.85",
        "current": "25.5",
        "power": "45.2",
        "asic_temperature": "52.3",
        "aiclk": "1000"
      },
      "firmwares": { ... },
      "limits": { ... }
    }
  ]
}
```

### Schema Versioning (Future)
```json
{
  "schema_version": "1.0",
  "time": "2024-12-01T12:00:00Z",
  "device_info": [...]
}
```

## Migration from Direct Mode

If you previously used `tt-top --direct-mode`:
1. Install tt-smi and ensure it supports `--json --continuous`
2. Run `tt-top` (JSON mode is now default)
3. All visualization features work identically

## Requirements

### tt-smi Requirements
- Must be installed and accessible in PATH (or via `--tt-smi-path`)
- Must support `--json` flag for single JSON output
- Must support `--json --continuous` for streaming mode (~100ms intervals)
- JSON format: One TTSMILog object per line (JSONL)

### tt-top Dependencies
```
textual >= 0.59.0
rich >= 13.7.0
pydantic >= 1.9.0
psutil >= 5.9.0
```

**No hardware dependencies required!**

## Troubleshooting

### "Failed to spawn tt-smi subprocess"
- Ensure tt-smi is installed: `which tt-smi`
- Test tt-smi directly: `tt-smi --json`
- Check tt-smi supports JSON mode: `tt-smi --help | grep json`
- Use custom path: `tt-top --tt-smi-path /path/to/tt-smi`
- Try mock mode: `tt-top --mock`

### "Failed to receive telemetry from tt-smi"
- Verify tt-smi outputs JSON: `tt-smi --json --continuous | head -1`
- Check for errors: `tt-smi --json --continuous 2>&1 | head`
- Ensure continuous mode works: `tt-smi --help | grep continuous`

## Future Enhancements

### Proposed JSON Schema Extensions
- **Historical data**: Add `history` array with last N samples
- **Workload hints**: Process correlation data from tt-smi
- **Alerts**: Threshold violations flagged in JSON
- **Calculated metrics**: Efficiency, utilization
- **Topology**: Multi-device interconnect information

### Alternative Backend Adapters
- **File-based**: Read JSON from log files for playback
- **Network streaming**: Consume JSON from remote tt-smi over TCP
- **Multi-source**: Aggregate data from multiple tt-smi instances
- **Recording mode**: Capture JSON streams for analysis

## Success Criteria

✅ tt-top launches successfully using tt-smi subprocess
✅ All visualization features work identically to previous version
✅ Performance remains at ~100ms refresh rate
✅ Workload detection continues functioning
✅ Architecture detection works for all chip types (GS/WH/BH)
✅ Graceful error handling for tt-smi subprocess issues
✅ Mock mode works without any dependencies
✅ Documentation updated and clear
✅ Zero coupling to tt-smi internals

## Conclusion

The decoupling is complete! TT-Top is now a true UNIX-style monitoring tool that follows the principle of composability through clean data interfaces. All improvements to monitoring capabilities will flow through the JSON schema, ensuring intentional and backward-compatible evolution.
