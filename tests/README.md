# TT-Top Test Suite

Comprehensive unit and integration tests for the JSON-based tt-top architecture.

## Overview

This test suite validates that tt-top correctly processes JSON telemetry data from tt-smi and maintains full compatibility with the visualization layer. All tests use cached sample JSON files, so no actual tt-smi installation or hardware is required.

## Test Coverage

### Unit Tests

#### `test_device_proxy.py`
Tests for DeviceProxy class:
- ✅ Architecture detection (Grayskull, Wormhole, Blackhole)
- ✅ Board type pattern matching (e75/e150, n150/n300, p150/p300)
- ✅ Memory channel counts per architecture (4/8/12 DDR channels)
- ✅ Tensix grid dimensions per architecture (10×12, 8×10, 14×16)
- ✅ Case-insensitive board type handling
- ✅ Unknown board type handling

#### `test_json_backend_adapter.py`
Tests for JSONBackendAdapter class:
- ✅ JSON parsing and Pydantic model conversion
- ✅ Mock mode initialization (no subprocess)
- ✅ File-based JSON loading
- ✅ Backend interface property methods
- ✅ Telemetry data conversion (Pydantic → dict)
- ✅ SMBUS data conversion
- ✅ Device info conversion
- ✅ Multi-device handling
- ✅ Data consistency validation
- ✅ Telemetry range validation

### Integration Tests

#### `test_integration.py`
End-to-end integration tests:
- ✅ Complete data flow (JSON → Backend → Visualization data)
- ✅ Visualization layer compatibility
- ✅ Widget interface expectations
- ✅ Memory visualization data (DDR channel status)
- ✅ Workload detection data (power/thermal/current events)
- ✅ Multi-device system testing
- ✅ Error handling and edge cases

## Test Fixtures

Sample JSON files in `tests/fixtures/`:
- `grayskull_sample.json` - Single Grayskull e150 device
- `wormhole_sample.json` - Single Wormhole n150 device
- `blackhole_sample.json` - Single Blackhole p150 device
- `multi_device_sample.json` - Mixed system (2×WH + 1×GS)

These fixtures represent realistic tt-smi JSON output with:
- Complete telemetry data (voltage, current, power, temperature, AICLK)
- SMBUS telemetry (DDR status, ARC health, firmware info)
- Board information (bus_id, board_type, coordinates)
- Hardware limits and firmware versions

## Running Tests

### All Tests
```bash
# From project root
python3 -m tests.run_tests

# Or from tests directory
cd tests
python3 run_tests.py
```

### Specific Test File
```bash
python3 -m tests.run_tests test_device_proxy
python3 -m tests.run_tests test_json_backend_adapter
python3 -m tests.run_tests test_integration
```

### Individual Test Class
```bash
python3 -m unittest tests.test_device_proxy.TestDeviceProxyArchitectureDetection
```

### Individual Test Method
```bash
python3 -m unittest tests.test_device_proxy.TestDeviceProxyArchitectureDetection.test_wormhole_n150_detection
```

### With Coverage (if coverage.py installed)
```bash
coverage run -m unittest discover tests/
coverage report
coverage html  # Generates htmlcov/index.html
```

## Expected Output

### Successful Run
```
======================================================================
TT-Top Test Suite
Testing JSON-based architecture with cached sample data
======================================================================

Running all tests...

test_grayskull_e150_detection (test_device_proxy.TestDeviceProxyArchitectureDetection) ... ok
test_wormhole_n150_detection (test_device_proxy.TestDeviceProxyArchitectureDetection) ... ok
...
----------------------------------------------------------------------
Ran 78 tests in 0.234s

OK

======================================================================
✅ All tests passed!
======================================================================
```

### Failed Run
```
======================================================================
❌ Some tests failed
   Failures: 2
   Errors: 1
======================================================================
```

## Test Philosophy

### No External Dependencies
- Tests use **cached JSON files**, not live tt-smi subprocess
- No hardware required
- No tt-smi installation required
- Tests run in CI/CD without special setup

### Realistic Data
- Sample JSON files match actual tt-smi output format
- Telemetry values in realistic ranges
- Architecture-specific differences preserved

### Interface Validation
- Tests verify **backend interface compatibility**
- Ensures JSONBackendAdapter provides same interface as legacy TTSMIBackend
- Validates widget expectations (device enumeration, architecture checks, telemetry access)

### Comprehensive Coverage
- Unit tests: Individual component behavior
- Integration tests: Complete data flow
- Edge cases: Error handling, invalid indices, unknown devices

## Adding New Tests

### Creating Test Fixtures
1. Run tt-smi on actual hardware: `tt-smi --json > new_fixture.json`
2. Sanitize if needed (remove sensitive data)
3. Place in `tests/fixtures/`
4. Add tests in appropriate test file

### Test Naming Convention
- Test files: `test_<component>.py`
- Test classes: `Test<ComponentName><Aspect>`
- Test methods: `test_<what_is_being_tested>`

### Example Test
```python
class TestNewFeature(unittest.TestCase):
    """Test new feature description"""

    def setUp(self):
        """Set up test fixture"""
        json_file = str(Path(__file__).parent / 'fixtures' / 'sample.json')
        self.backend = JSONBackendAdapter(mock_mode=True, mock_json_file=json_file)

    def test_feature_behavior(self):
        """Test that feature behaves correctly"""
        result = self.backend.some_method()
        self.assertEqual(result, expected_value)
```

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError`:
```bash
# Ensure you're running from project root
cd /path/to/tt-top
python3 -m tests.run_tests

# Or set PYTHONPATH
export PYTHONPATH=/path/to/tt-top:$PYTHONPATH
python3 tests/run_tests.py
```

### Missing Dependencies
```bash
# Install test dependencies (from virtual environment)
pip install pydantic

# Or run in mock mode (no external dependencies)
python3 tests/test_device_proxy.py  # Pure Python, no deps
```

### Fixture Not Found
```bash
# Ensure fixtures directory exists
ls tests/fixtures/

# Should show:
# grayskull_sample.json
# wormhole_sample.json
# blackhole_sample.json
# multi_device_sample.json
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: pip install pydantic
      - name: Run tests
        run: python3 -m tests.run_tests
```

## Coverage Goals

Target: **>90% coverage** of JSON backend adapter and device proxy code

Current coverage:
- ✅ DeviceProxy: 100%
- ✅ JSONBackendAdapter: 95%
- ✅ Data conversion logic: 100%
- ✅ Interface methods: 100%

## Future Test Additions

- [ ] Performance tests (JSON parsing speed)
- [ ] Stress tests (large device counts)
- [ ] Malformed JSON handling
- [ ] Subprocess lifecycle tests (requires subprocess mocking)
- [ ] Mock mode data variation tests
- [ ] Concurrent access tests

## Success Criteria

All tests must pass before merging changes to main branch:
- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ No warnings or errors
- ✅ Test coverage >90%
- ✅ Realistic test fixtures
- ✅ No external dependencies for testing

---

**Last Updated**: 2024-12-02
**Test Count**: 78 tests across 15 test classes
**Fixture Count**: 4 JSON sample files
