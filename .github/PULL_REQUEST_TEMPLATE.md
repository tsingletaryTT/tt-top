# Pull Request: TT-Top JSON Architecture

## Description
Complete refactoring and cleanup to make TT-Top a standalone UNIX-style tool.

## Changes Made

### Architecture Transformation
- ✅ Decoupled from tt-smi internal code
- ✅ JSON-only backend using subprocess communication
- ✅ Removed all direct hardware access code
- ✅ Clean UNIX philosophy implementation

### Files Added
- `tt_top/json_backend_adapter.py` - JSON backend with subprocess management
- `tt_top/device_proxy.py` - Lightweight architecture detection
- `DECOUPLING_COMPLETE.md` - Architecture documentation
- `CLEANUP_SUMMARY.md` - Cleanup details

### Files Removed
- Entire `tt_smi/` directory (legacy integration code)
- `tt_top/tt_smi_backend.py` (direct hardware backend)
- `tt_top/safety.py` (hardware safety coordinator)
- `tt_top/mock_hardware.py` (replaced with JSON mock mode)
- All obsolete test and demo files
- All fork maintenance documentation and scripts
- ~160KB+ of legacy code

### Documentation Updated
- `README.md` - New architecture, usage, dependencies
- `CLAUDE.md` - Complete development history
- All references to direct mode removed

## Benefits

### Zero Coupling
- No imports of tt-smi internal modules
- No shared code paths
- Changes in tt-smi internals cannot break tt-top
- Only dependency: JSON format contract

### Simplified Distribution
- Minimal dependencies: textual, rich, pydantic, psutil
- No pyluwen or tt_tools_common required
- Works on any machine with tt-smi installed
- Mock mode for testing without hardware

### Clear Separation
- **tt-smi**: Hardware access, safety, telemetry acquisition
- **tt-top**: Visualization, workload detection, UI
- **Interface**: JSON schema (versioned, backward-compatible)

## Testing

### Tested Scenarios
- ✅ Mock mode works without any dependencies
- ✅ JSON backend adapter spawns subprocess correctly
- ✅ Device proxy detects all architectures (GS/WH/BH)
- ✅ All visualization features unchanged
- ✅ Error handling and recovery works

### Test Commands
```bash
# Mock mode (no dependencies)
tt-top --mock

# JSON mode (requires tt-smi)
tt-top

# Custom tt-smi path
tt-top --tt-smi-path /path/to/tt-smi
```

## Migration Guide

### For Users
Previously:
```bash
tt-top --direct-mode  # No longer supported
```

Now:
```bash
tt-top                # Uses tt-smi JSON (default)
tt-top --mock         # Testing without hardware
```

### For Developers
- Direct hardware access removed
- All improvements through JSON schema
- New features require tt-smi JSON updates
- Tests use mock mode (no hardware needed)

## Checklist

- [x] Code compiles and runs
- [x] Documentation updated
- [x] Legacy code removed
- [x] Mock mode works
- [x] Architecture documented
- [x] Breaking changes noted
- [x] Migration path clear

## Related Issues
Closes #[issue-number] - Decouple from tt-smi internal code

## Additional Notes
This is a significant architectural change that completes the transformation of TT-Top from a tightly-coupled fork to a standalone UNIX-style tool. All future improvements will flow through the JSON interface, ensuring intentional and backward-compatible evolution.
