# Intelligent Workload Detection in TT-SMI

## Overview

The TT-SMI system now features **intelligent workload detection** that provides more accurate determination of device activity states, replacing the previous hardcoded power thresholds that led to false "ACTIVE_WORKLOAD" readings on idle devices.

## The Problem

Previously, TT-SMI used simple absolute power thresholds:
- `> 75W`: High power state
- `> 50W`: Power ramp up  
- `> 5W`: **ACTIVE_WORKLOAD**
- `≤ 5W`: Idle

This approach had significant issues:

1. **Chip Architecture Differences**: Different TT chips (Grayskull, Wormhole, Blackhole) have different idle power consumption
2. **Static Power Ignored**: All chips consume baseline power even when completely idle (10-35W depending on architecture)
3. **False Positives**: Any chip consuming >5W would show as "ACTIVE_WORKLOAD" even when doing nothing

## The Solution

### 1. Chip-Specific Idle Power Baselines

The system now recognizes that different architectures have different idle power consumption:

```python
CHIP_IDLE_POWER = {
    "grayskull": 15.0,   # GS baseline idle consumption  
    "wormhole": 25.0,    # WH baseline idle consumption
    "blackhole": 35.0,   # BH baseline idle consumption
}
```

### 2. Multi-Signal Workload Detection

Instead of relying solely on absolute power, the system now uses multiple telemetry signals:

- **Power Delta**: Power consumption relative to chip-specific idle baseline
- **Clock Frequency (AICLK)**: Higher frequencies indicate active processing
- **Current Draw**: Correlates with actual computation load
- **Temperature**: Heat generation suggests processing activity

### 3. Intelligent State Classification

The new system provides more granular and accurate workload states:

| State | Condition | Description |
|-------|-----------|-------------|
| **SLEEP** | < 50% of idle power | Minimal activity, deep power saving |
| **IDLE** | < 3W above idle | Standby state, ready for work |
| **LIGHT_LOAD** | 3-10W above idle + supporting signals | Light processing tasks |
| **ACTIVE_WORKLOAD** | 10-30W above idle + activity signals | Active computation |
| **MODERATE_LOAD** | 30-60W above idle | Substantial workload |
| **HEAVY_LOAD** | 60-100W above idle | High utilization |
| **CRITICAL_LOAD** | >100W above idle | Maximum load |
| **THERMAL_LIMIT** | Temperature > 85°C | Thermal throttling |

### 4. Confidence Scoring

Each detection includes a confidence score (0-1) based on how well multiple signals agree, helping identify uncertain classifications.

## Configuration

### Default Configuration

The system works out-of-the-box with sensible defaults, but can be customized for specific deployments.

### Auto-Calibration

For maximum accuracy, you can auto-calibrate idle power baselines for your specific hardware:

```bash
# Ensure no workloads are running, then:
python configure_workload.py --calibrate --calibrate-duration 60
```

This measures actual idle power consumption and sets appropriate baselines.

### Manual Configuration  

You can manually adjust thresholds for your environment:

```bash
# Set custom idle power for Wormhole chips
python configure_workload.py --set-idle wormhole 28.5

# Adjust sensitivity for light workload detection  
python configure_workload.py --set-threshold light_threshold 12.0

# View current configuration
python configure_workload.py --show
```

### Configuration Persistence

Settings are saved to `~/.tt-smi/workload_config.json` and can be exported/imported for deployment across multiple systems.

## Benefits

### ✅ Accurate Detection
- **No more false ACTIVE_WORKLOAD** events on idle devices
- Proper differentiation between idle and actually active states
- Architecture-aware detection logic

### ✅ Better Monitoring  
- More informative event logs showing actual device activity
- Gradual state transitions (idle → light → active → heavy)
- Thermal limiting detection for overheating scenarios

### ✅ Customizable
- Auto-calibration for unknown hardware configurations
- Manually tunable thresholds for specialized environments  
- Exportable configurations for team deployments

### ✅ Backward Compatible
- Existing TT-SMI interfaces work unchanged
- Same visual output with improved accuracy
- No breaking changes to scripts or automation

## Technical Details

### Algorithm Overview

1. **Read Telemetry**: Collect power, temperature, current, and clock data
2. **Calculate Delta**: Compute power consumption above architecture-specific idle baseline  
3. **Analyze Signals**: Cross-reference with clock frequency, current draw, and temperature
4. **Classify State**: Determine workload state using configurable thresholds
5. **Assign Confidence**: Score the reliability of the classification

### Signal Correlation

The system uses multiple signals to improve accuracy:

- **High Power + Low Clock**: May indicate power inefficiency or measurement error
- **Moderate Power + High Clock**: Strong indicator of active computation  
- **High Temperature + High Power**: Confirms heavy workload
- **Low Current + High Power**: May indicate power delivery issues

### Thermal Management

Temperature monitoring provides additional context:

- **> 85°C**: Thermal limiting state (red alert)
- **> 70°C**: Thermal warning (elevated temperature)
- **> 50°C**: Active processing temperature range

## Migration

### From Previous Versions

Existing TT-SMI installations will automatically:
- Use new intelligent detection
- Fall back to default idle power baselines  
- Maintain backward compatibility

### Recommended Actions

1. **Run calibration** on representative idle workloads
2. **Verify thresholds** match your environment's expectations
3. **Monitor for 24-48 hours** to ensure appropriate classifications
4. **Fine-tune** thresholds if needed for your specific use case

## Troubleshooting

### Still Seeing False Positives?

1. Check if your "idle" state actually has background activity
2. Run auto-calibration with truly idle system
3. Manually adjust idle power baselines upward
4. Increase `idle_threshold` for less sensitive detection

### Missing Active Workloads?

1. Check if workloads are actually increasing power consumption
2. Lower `light_threshold` for more sensitive detection  
3. Verify clock frequencies are changing during workloads
4. Consider architecture-specific behavior differences

### Configuration Issues?

```bash
# Reset to defaults
python configure_workload.py --reset

# Show current settings
python configure_workload.py --show --help
```

## Future Enhancements

- **Machine Learning**: Adaptive thresholds based on historical patterns
- **Workload Classification**: Identify specific types of workloads (inference vs training)
- **Performance Correlation**: Link workload detection to actual throughput metrics
- **Cluster-wide Coordination**: Aggregate workload detection across multiple devices