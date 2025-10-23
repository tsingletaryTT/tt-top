#!/usr/bin/env python3
# SPDX-FileCopyrightText: © 2023 Tenstorrent Inc.
# SPDX-License-Identifier: Apache-2.0

"""
Hardware-Responsive Animated ASCII Art Display

A full-screen animated visualization that draws its colors, twinkling effects,
and patterns directly from real Tenstorrent hardware activity. Unlike static
or cosmetic animations, every visual element reflects actual telemetry data.
"""

import time
import random
import math
from typing import Dict, List, Tuple, Optional
from textual.widget import Widget
from textual.widgets import Static
from textual.containers import Container
from textual.app import ComposeResult
from textual.binding import Binding
from tt_top.tt_smi_backend import TTSMIBackend


def generate_leet_hello_world_ascii(frame: int = 0, width: int = 80, hardware_data: Dict = None) -> List[str]:
    """
    Generate animated ASCII art for l33t 'HELLO WORLD!' that responds to hardware activity

    Args:
        frame: Animation frame number for base effects
        width: Display width to center the art
        hardware_data: Dict with hardware telemetry for responsive effects
                      Expected keys: 'power', 'temp', 'current', 'power_change', 'temp_change'

    Returns:
        List of strings representing the ASCII art lines
    """
    # L33t speak ASCII art for "HELLO WORLD!"
    base_art = [
        "██   ██ ███████ ██      ██       ██████      ██     ██  ██████  ██████  ██      ██████  ██ ",
        "██   ██ ██      ██      ██      ██    ██     ██     ██ ██    ██ ██   ██ ██      ██   ██ ██ ",
        "███████ █████   ██      ██      ██    ██     ██  █  ██ ██    ██ ██████  ██      ██   ██ ██ ",
        "██   ██ ██      ██      ██      ██    ██     ██ ███ ██ ██    ██ ██   ██ ██      ██   ██    ",
        "██   ██ ███████ ███████ ███████  ██████       ███ ███   ██████  ██   ██ ███████ ██████  ██ "
    ]
    
    # L33t character replacements
    leet_replacements = {
        'A': ['4', '@', 'Λ'],
        'E': ['3', '€', 'Ξ'],
        'L': ['1', '|', '£'],
        'O': ['0', '◯', 'Ø'],
        'S': ['5', '$', 'Ş'],
        'T': ['7', '+', '†'],
        'I': ['!', '1', '|'],
        'G': ['6', '&', 'Ğ']
    }
    
    # Extract hardware values for animation responsiveness
    if hardware_data:
        power_change = hardware_data.get('power_change', 0.0)
        temp_change = hardware_data.get('temp_change', 0.0)
        current_change = hardware_data.get('current_change', 0.0)
        power = hardware_data.get('power', 50.0)
        temp = hardware_data.get('temp', 50.0)

        # Hardware-responsive animation factors
        morph_rate = 0.1 + min(power_change * 0.5, 1.0)  # More power = faster morphing
        pulse_intensity = 0.3 + min(temp_change * 0.4, 0.5)  # Higher temp = more pulsing
        glitch_frequency = max(5, 30 - int(current_change * 20))  # More current = more glitches
    else:
        # Fallback to time-based animation when no hardware data available
        morph_rate = 0.1
        pulse_intensity = 0.3
        glitch_frequency = 30

    # Apply l33t transformations and hardware-responsive animation effects
    animated_art = []
    for line_idx, line in enumerate(base_art):
        animated_line = ""
        for char_idx, char in enumerate(line):
            # Hardware-responsive pulsing effect
            pulse_phase = (frame * morph_rate + line_idx * 0.3 + char_idx * 0.1) % (2 * math.pi)
            should_transform = math.sin(pulse_phase) > pulse_intensity

            if char.upper() in leet_replacements and should_transform:
                # Hardware-responsive l33t variation cycling
                if hardware_data:
                    # Use power level to influence transformation variety
                    variant_speed = max(5, 20 - int(power_change * 10))
                    variant_idx = (frame // variant_speed + char_idx) % len(leet_replacements[char.upper()])
                else:
                    variant_idx = (frame // 10 + char_idx) % len(leet_replacements[char.upper()])

                transformed_char = leet_replacements[char.upper()][variant_idx]
                animated_line += transformed_char
            else:
                animated_line += char

        animated_art.append(animated_line)
    
    # Add hardware-responsive glitch effects
    if frame % glitch_frequency < 5:  # Hardware determines glitch frequency
        glitch_line = random.randint(0, len(animated_art) - 1)
        line = list(animated_art[glitch_line])
        
        # Add some random glitch characters
        for _ in range(random.randint(1, 3)):
            pos = random.randint(0, len(line) - 1)
            glitch_chars = ['▓', '▒', '░', '█', '▀', '▄', '▌', '▐', '▖', '▗', '▘', '▙', '▚', '▛', '▜', '▝', '▞', '▟']
            line[pos] = random.choice(glitch_chars)
            
        animated_art[glitch_line] = ''.join(line)
    
    # Center the art horizontally
    max_line_length = max(len(line) for line in animated_art) if animated_art else 0
    padding = max(0, (width - max_line_length) // 2)
    
    centered_art = []
    for line in animated_art:
        centered_line = ' ' * padding + line
        centered_art.append(centered_line)
    
    return centered_art


def generate_workload_celebration_effects(frame: int, width: int, height: int) -> List[str]:
    """
    Generate additional celebration effects around the ASCII art
    
    Args:
        frame: Animation frame number
        width: Display width
        height: Display height
        
    Returns:
        List of effect strings to overlay
    """
    effects = []
    
    # Particle explosion effect
    particles = ['*', '✦', '✧', '✩', '★', '☆', '◆', '◇', '●', '○']
    
    for i in range(height):
        effect_line = [' '] * width
        
        # Add random particles
        for _ in range(random.randint(0, 3)):
            x = random.randint(0, width - 1)
            if random.random() < 0.3:  # 30% chance per position
                particle = random.choice(particles)
                effect_line[x] = particle
        
        effects.append(''.join(effect_line))
    
    return effects


class HardwareStarfield:
    """
    A dynamic starfield where each 'star' represents a hardware component
    and its behavior is driven by real telemetry data with adaptive baseline scaling.
    """

    def __init__(self, width: int, height: int, num_stars: int = 200):
        """Initialize hardware-responsive starfield

        Args:
            width: Display width in characters
            height: Display height in characters
            num_stars: Maximum number of stars (limited by available hardware data points)
        """
        self.width = width
        self.height = height
        self.num_stars = num_stars
        self.stars = []
        self.time_offset = 0

        # Adaptive baseline system
        self.baseline_samples = []
        self.baseline_established = False
        self.baseline_power = {}
        self.baseline_current = {}
        self.baseline_temp = {}
        self.max_baseline_samples = 20  # Learn baseline over first 20 updates
        
        # Workload detection system
        self.workload_detected = False
        self.workload_detection_time = None
        self.workload_celebration_duration = 40  # Show celebration for 40 frames (~4 seconds at 10 FPS)
        self.workload_celebration_frame = 0
        self.previous_activity_state = {}  # Track previous activity state per device
        self.workload_threshold = 0.20  # 20% increase from baseline triggers workload detection

    def initialize_stars(self, backend: TTSMIBackend) -> None:
        """Initialize stars based on actual hardware topology

        Creates stars that correspond to real hardware elements:
        - Device cores (positioned based on grid layout)
        - Memory channels (clustered around devices)
        - Interconnect nodes (between devices)
        - Telemetry data points (distributed across field)
        """
        self.stars = []
        star_id = 0

        # Create device-based star clusters
        num_devices = len(backend.devices)
        if num_devices == 0:
            return

        # Distribute devices across screen space
        device_spacing_x = self.width // max(num_devices, 1)
        device_spacing_y = self.height // 2  # Use middle of screen as baseline

        for device_idx, device in enumerate(backend.devices):
            # Device center position - spread devices across full screen
            center_x = device_spacing_x * device_idx + device_spacing_x // 2
            # Stagger devices vertically across the middle portion of screen
            vertical_offset = (device_idx % 2) * (self.height // 6) - (self.height // 12)
            center_y = device_spacing_y + vertical_offset

            # Create core grid based on architecture
            if device.as_gs():
                grid_rows, grid_cols = 10, 12  # Grayskull
                cluster_size = 15
            elif device.as_wh():
                grid_rows, grid_cols = 8, 10   # Wormhole
                cluster_size = 12
            elif device.as_bh():
                grid_rows, grid_cols = 14, 16  # Blackhole
                cluster_size = 20
            else:
                grid_rows, grid_cols = 8, 10   # Default
                cluster_size = 12

            # Create stars for Tensix cores - distribute across more screen area
            max_rows = min(grid_rows, self.height // 3)  # Use up to 1/3 of screen height per device
            max_cols = min(grid_cols, self.width // 4)   # Use up to 1/4 of screen width per device

            for row in range(max_rows):
                for col in range(max_cols):
                    if star_id >= self.num_stars:
                        break

                    # Position relative to device center with more spread
                    star_x = center_x + (col - max_cols//2) * 3  # Wider horizontal spacing
                    star_y = center_y + (row - max_rows//2) * 2  # Taller vertical spacing

                    # Ensure star is within bounds
                    if 0 <= star_x < self.width and 0 <= star_y < self.height:
                        star = {
                            'id': star_id,
                            'x': star_x,
                            'y': star_y,
                            'device_idx': device_idx,
                            'component_type': 'tensix_core',
                            'grid_pos': (row, col),
                            'brightness': 0.5,
                            'color': 'bright_cyan',
                            'twinkle_phase': random.random() * 2 * math.pi,
                            'twinkle_speed': 0.1 + random.random() * 0.3
                        }
                        self.stars.append(star)
                        star_id += 1

            # Create memory channel stars (closer to device)
            memory_channels = 4 if device.as_gs() else 8 if device.as_wh() else 12
            for channel in range(min(memory_channels, 8)):
                if star_id >= self.num_stars:
                    break

                # Position memory stars around device perimeter with better spacing
                angle = 2 * math.pi * channel / memory_channels
                radius = max(8, min(self.width // 8, self.height // 4))  # Adaptive radius
                star_x = int(center_x + radius * math.cos(angle))
                star_y = int(center_y + radius * math.sin(angle))

                if 0 <= star_x < self.width and 0 <= star_y < self.height:
                    star = {
                        'id': star_id,
                        'x': star_x,
                        'y': star_y,
                        'device_idx': device_idx,
                        'component_type': 'memory_channel',
                        'channel_idx': channel,
                        'brightness': 0.3,
                        'color': 'bright_magenta',
                        'twinkle_phase': random.random() * 2 * math.pi,
                        'twinkle_speed': 0.05 + random.random() * 0.15
                    }
                    self.stars.append(star)
                    star_id += 1

            # Create memory hierarchy "planets" (larger visual elements)
            hierarchy_levels = ['L1_cache', 'L2_cache', 'DDR_controller']
            for level_idx, level in enumerate(hierarchy_levels):
                if star_id >= self.num_stars:
                    break

                # Position at different radii around device center with better spread
                base_radius = max(12, min(self.width // 6, self.height // 3))
                radius = base_radius + level_idx * 6
                angle = 2 * math.pi * level_idx / 3  # 3 levels, evenly spaced
                planet_x = int(center_x + radius * math.cos(angle))
                planet_y = int(center_y + radius * math.sin(angle))

                if 0 <= planet_x < self.width and 0 <= planet_y < self.height:
                    planet = {
                        'id': star_id,
                        'x': planet_x,
                        'y': planet_y,
                        'device_idx': device_idx,
                        'component_type': 'memory_planet',
                        'hierarchy_level': level,
                        'level_index': level_idx,
                        'brightness': 0.4,
                        'color': ['bright_blue', 'bright_yellow', 'bright_red'][level_idx],
                        'twinkle_phase': random.random() * 2 * math.pi,
                        'twinkle_speed': 0.03 + random.random() * 0.1
                    }
                    self.stars.append(planet)
                    star_id += 1

        # Add interconnect stars between devices
        for i in range(num_devices):
            for j in range(i + 1, num_devices):
                if star_id >= self.num_stars:
                    break

                # Position between device centers with better distribution
                device_i_x = device_spacing_x * i + device_spacing_x // 2
                device_j_x = device_spacing_x * j + device_spacing_x // 2
                interconnect_x = (device_i_x + device_j_x) // 2
                # Vary interconnect vertical position based on device pair
                interconnect_y = self.height // 2 + ((i + j) % 3 - 1) * (self.height // 8)

                if 0 <= interconnect_x < self.width and 0 <= interconnect_y < self.height:
                    star = {
                        'id': star_id,
                        'x': interconnect_x,
                        'y': interconnect_y,
                        'device_idx': i,  # Primary device
                        'connected_device': j,
                        'component_type': 'interconnect',
                        'brightness': 0.2,
                        'color': 'bright_green',
                        'twinkle_phase': random.random() * 2 * math.pi,
                        'twinkle_speed': 0.02 + random.random() * 0.08
                    }
                    self.stars.append(star)
                    star_id += 1

    def _update_baseline(self, backend: TTSMIBackend) -> None:
        """Update the adaptive baseline from current telemetry readings"""
        if self.baseline_established:
            return

        # Collect current sample
        current_sample = {}
        for i, device in enumerate(backend.devices):
            try:
                telem = backend.device_telemetrys[i]
                current_sample[i] = {
                    'power': float(telem.get('power', '0.0')),
                    'current': float(telem.get('current', '0.0')),
                    'temp': float(telem.get('asic_temperature', '0.0'))
                }
            except:
                current_sample[i] = {'power': 0.0, 'current': 0.0, 'temp': 0.0}

        self.baseline_samples.append(current_sample)

        # Establish baseline after enough samples
        if len(self.baseline_samples) >= self.max_baseline_samples:
            for device_idx in range(len(backend.devices)):
                # Calculate average baseline values
                power_samples = [s[device_idx]['power'] for s in self.baseline_samples if device_idx in s]
                current_samples = [s[device_idx]['current'] for s in self.baseline_samples if device_idx in s]
                temp_samples = [s[device_idx]['temp'] for s in self.baseline_samples if device_idx in s]

                if power_samples:
                    self.baseline_power[device_idx] = sum(power_samples) / len(power_samples)
                    self.baseline_current[device_idx] = sum(current_samples) / len(current_samples)
                    self.baseline_temp[device_idx] = sum(temp_samples) / len(temp_samples)

            self.baseline_established = True
            print(f"✓ Baseline established for {len(backend.devices)} devices:")
            for i in range(len(backend.devices)):
                if i in self.baseline_power:
                    print(f"  Device {i}: {self.baseline_power[i]:.1f}W, {self.baseline_current[i]:.1f}A, {self.baseline_temp[i]:.1f}°C")

    def _get_relative_change(self, current_value: float, baseline_value: float) -> float:
        """Calculate relative change from baseline as a percentage

        Returns:
            float: Relative change where 0.0 = baseline, 1.0 = 100% increase, -0.5 = 50% decrease
        """
        if baseline_value <= 0:
            return 0.0

        return (current_value - baseline_value) / baseline_value

    def _detect_new_workload(self, backend: TTSMIBackend) -> bool:
        """
        Detect if a new workload has started based on significant activity increase from baseline
        
        Returns:
            bool: True if a new workload is detected
        """
        if not self.baseline_established:
            return False
            
        current_activity_state = {}
        new_workload_detected = False
        
        for device_idx in range(len(backend.devices)):
            if device_idx not in self.baseline_power:
                continue
                
            try:
                telem = backend.device_telemetrys[device_idx]
                power = float(telem.get('power', '0.0'))
                current = float(telem.get('current', '0.0'))
                
                # Calculate relative changes from baseline
                power_change = self._get_relative_change(power, self.baseline_power[device_idx])
                current_change = self._get_relative_change(current, self.baseline_current[device_idx])
                
                # Determine if device is now active (above workload threshold)
                is_active = (power_change > self.workload_threshold or 
                            current_change > self.workload_threshold)
                
                # Check if this is a transition from inactive to active (new workload)
                was_active = self.previous_activity_state.get(device_idx, False)
                
                if is_active and not was_active:
                    new_workload_detected = True
                    print(f"🚀 New workload detected on device {device_idx}: "
                          f"Power +{power_change*100:.1f}%, Current +{current_change*100:.1f}%")
                
                current_activity_state[device_idx] = is_active
                
            except Exception as e:
                current_activity_state[device_idx] = False
                print(f"Error checking workload for device {device_idx}: {e}")
        
        # Update previous state
        self.previous_activity_state = current_activity_state
        
        return new_workload_detected

    def update_from_telemetry(self, backend: TTSMIBackend, frame_count: int) -> None:
        """Update star properties based on real hardware telemetry with adaptive baseline scaling

        This is what makes the visualization hardware-responsive rather than
        just cosmetic animation. Each star's brightness, color, and twinkle
        rate directly corresponds to actual hardware activity relative to learned baseline.
        """
        self.time_offset = frame_count * 0.1

        # Update baseline if not established
        if not self.baseline_established:
            self._update_baseline(backend)
        else:
            # Check for new workload detection
            if self._detect_new_workload(backend):
                self.workload_detected = True
                self.workload_detection_time = time.time()
                self.workload_celebration_frame = 0
                print("🎉 WORKLOAD CELEBRATION ACTIVATED!")
        
        # Update celebration frame counter if celebrating
        if self.workload_detected:
            self.workload_celebration_frame += 1
            if self.workload_celebration_frame >= self.workload_celebration_duration:
                self.workload_detected = False
                self.workload_celebration_frame = 0
                print("✨ Workload celebration ended")

        for star in self.stars:
            device_idx = star['device_idx']

            # Skip if device doesn't exist
            if device_idx >= len(backend.devices):
                continue

            # Get current telemetry for this device
            try:
                telem = backend.device_telemetrys[device_idx]
                power = float(telem.get('power', '0.0'))
                temp = float(telem.get('asic_temperature', '0.0'))
                current = float(telem.get('current', '0.0'))
                voltage = float(telem.get('voltage', '0.0'))
                aiclk = float(telem.get('aiclk', '0.0'))
            except:
                power = temp = current = voltage = aiclk = 0.0

            # Update star based on component type and RELATIVE telemetry changes
            if star['component_type'] == 'tensix_core':
                if self.baseline_established and device_idx in self.baseline_power:
                    # Use relative changes from baseline
                    power_change = self._get_relative_change(power, self.baseline_power[device_idx])
                    current_change = self._get_relative_change(current, self.baseline_current[device_idx])
                    temp_change = self._get_relative_change(temp, self.baseline_temp[device_idx])

                    # Core activity based on relative power change (much more sensitive!)
                    # 0% change = 0.3 brightness, 50% increase = 1.0 brightness
                    core_activity = max(0, min(power_change, 2.0))  # Cap at 200% increase
                    star['brightness'] = 0.3 + core_activity * 0.7

                    # Color based on relative temperature change
                    if temp_change > 0.3:  # 30% temp increase
                        star['color'] = 'bold red'
                    elif temp_change > 0.15:  # 15% temp increase
                        star['color'] = 'orange1'
                    elif temp_change > 0.05:  # 5% temp increase
                        star['color'] = 'bright_yellow'
                    elif power_change > 0.1:  # 10% power increase
                        star['color'] = 'bright_green'
                    else:
                        star['color'] = 'bright_cyan'

                    # Twinkle speed based on relative current change
                    twinkle_activity = max(0, min(current_change, 1.0))
                    star['twinkle_speed'] = 0.05 + twinkle_activity * 0.4
                else:
                    # Learning baseline - show neutral state
                    star['brightness'] = 0.3
                    star['color'] = 'dim white'
                    star['twinkle_speed'] = 0.05

            elif star['component_type'] == 'memory_channel':
                if self.baseline_established and device_idx in self.baseline_current:
                    # Memory activity based on relative current change
                    current_change = self._get_relative_change(current, self.baseline_current[device_idx])
                    memory_activity = max(0, min(current_change, 1.5))  # Cap at 150% increase
                    star['brightness'] = 0.2 + memory_activity * 0.8

                    # Memory channels pulse with different colors based on activity level
                    if current_change > 0.5:  # 50% increase
                        star['color'] = 'bright_magenta'
                    elif current_change > 0.25:  # 25% increase
                        star['color'] = 'magenta'
                    elif current_change > 0.1:  # 10% increase
                        star['color'] = 'bright_blue'
                    else:
                        star['color'] = 'blue'

                    star['twinkle_speed'] = 0.03 + memory_activity * 0.2
                else:
                    # Learning baseline
                    star['brightness'] = 0.2
                    star['color'] = 'dim blue'
                    star['twinkle_speed'] = 0.03

            elif star['component_type'] == 'memory_planet':
                if self.baseline_established and device_idx in self.baseline_power:
                    # Memory hierarchy planets show combined metrics
                    power_change = self._get_relative_change(power, self.baseline_power[device_idx])
                    current_change = self._get_relative_change(current, self.baseline_current[device_idx])

                    # Different hierarchy levels respond to different metrics
                    level_idx = star['level_index']
                    if level_idx == 0:  # L1 cache - responds to power
                        activity = max(0, min(power_change, 1.0))
                        base_color = 'bright_blue'
                    elif level_idx == 1:  # L2 cache - responds to current
                        activity = max(0, min(current_change, 1.0))
                        base_color = 'bright_yellow'
                    else:  # DDR controller - responds to average
                        activity = max(0, min((power_change + current_change) / 2, 1.0))
                        base_color = 'bright_red'

                    star['brightness'] = 0.4 + activity * 0.6

                    # Planet colors intensify with activity
                    if activity > 0.3:
                        # Use proper compound color name instead of string concatenation
                        color_part = base_color.split("_")[1] if "_" in base_color else base_color
                        star['color'] = f'bold {color_part}'
                    elif activity > 0.1:
                        star['color'] = base_color
                    else:
                        star['color'] = base_color.replace('bright_', 'dim ')

                    star['twinkle_speed'] = 0.02 + activity * 0.15
                else:
                    # Learning baseline
                    star['brightness'] = 0.4
                    star['color'] = 'dim white'
                    star['twinkle_speed'] = 0.02

            elif star['component_type'] == 'interconnect':
                # Interconnect activity based on power difference between connected devices
                try:
                    connected_idx = star['connected_device']
                    if connected_idx < len(backend.device_telemetrys):
                        connected_telem = backend.device_telemetrys[connected_idx]
                        connected_power = float(connected_telem.get('power', '0.0'))
                        power_diff = abs(power - connected_power)

                        # Activity increases with power difference (real hardware: 0-50W diff)
                        interconnect_activity = min(power_diff / 30.0, 1.0)  # 30W max difference
                        star['brightness'] = 0.05 + interconnect_activity * 0.7

                        # Color indicates traffic intensity
                        if power_diff > 20:
                            star['color'] = 'bright_white'
                        elif power_diff > 10:
                            star['color'] = 'bright_green'
                        elif power_diff > 5:
                            star['color'] = 'green'
                        else:
                            star['color'] = 'dim white'

                        star['twinkle_speed'] = 0.005 + interconnect_activity * 0.1
                except:
                    star['brightness'] = 0.1
                    star['color'] = 'dim white'
                    star['twinkle_speed'] = 0.01

            # Update twinkle phase based on hardware-responsive speed
            star['twinkle_phase'] += star['twinkle_speed']
            if star['twinkle_phase'] > 2 * math.pi:
                star['twinkle_phase'] -= 2 * math.pi

    def render_starfield(self) -> List[str]:
        """Render the hardware-responsive starfield to ASCII art

        Creates a colorful display where each position represents actual
        hardware component state. The resulting art is both beautiful and
        informationally dense.
        """
        # Initialize blank field
        field = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        color_field = [['dim white' for _ in range(self.width)] for _ in range(self.height)]

        # Always render starfield (celebration will be added below if active)

        # Render each star
        for star in self.stars:
            x, y = star['x'], star['y']

            # Skip stars outside bounds
            if not (0 <= x < self.width and 0 <= y < self.height):
                continue

            # Calculate current brightness with twinkling
            base_brightness = star['brightness']
            twinkle_factor = 0.3 * math.sin(star['twinkle_phase'])
            current_brightness = base_brightness + twinkle_factor
            current_brightness = max(0.0, min(1.0, current_brightness))

            # Choose character based on brightness and component type
            if star['component_type'] == 'tensix_core':
                if current_brightness > 0.8:
                    char = '●'
                elif current_brightness > 0.6:
                    char = '◉'
                elif current_brightness > 0.4:
                    char = '○'
                elif current_brightness > 0.2:
                    char = '∘'
                else:
                    char = '·'
            elif star['component_type'] == 'memory_channel':
                if current_brightness > 0.7:
                    char = '█'
                elif current_brightness > 0.5:
                    char = '▓'
                elif current_brightness > 0.3:
                    char = '▒'
                elif current_brightness > 0.1:
                    char = '░'
                else:
                    char = '·'
            elif star['component_type'] == 'memory_planet':
                # Larger, more distinctive characters for memory hierarchy
                level_idx = star['level_index']
                if current_brightness > 0.8:
                    chars = ['◆', '◇', '♦']  # L1, L2, DDR
                elif current_brightness > 0.6:
                    chars = ['◈', '◊', '♢']
                elif current_brightness > 0.4:
                    chars = ['◊', '◌', '◯']
                elif current_brightness > 0.2:
                    chars = ['◦', '○', '◯']
                else:
                    chars = ['·', '·', '·']
                char = chars[min(level_idx, 2)]
            elif star['component_type'] == 'interconnect':
                if current_brightness > 0.6:
                    char = '✦'
                elif current_brightness > 0.4:
                    char = '✧'
                elif current_brightness > 0.2:
                    char = '✩'
                else:
                    char = '·'
            else:
                char = '*'

            field[y][x] = char
            color_field[y][x] = star['color']

        # Convert to markup strings
        lines = []
        for row_idx, (char_row, color_row) in enumerate(zip(field, color_field)):
            line_parts = []
            current_color = None

            for char, color in zip(char_row, color_row):
                if color != current_color:
                    # Close previous color/bold tags
                    if current_color is not None:
                        if current_color.startswith('bold '):
                            base_color = current_color.replace('bold ', '')
                            line_parts.append(f'[/{base_color}]')
                            line_parts.append('[/bold]')
                        else:
                            line_parts.append(f'[/{current_color}]')

                    # Open new color/bold tags
                    if char != ' ':  # Don't add color markup for spaces
                        if color.startswith('bold '):
                            base_color = color.replace('bold ', '')
                            line_parts.append('[bold]')
                            line_parts.append(f'[{base_color}]')
                        else:
                            line_parts.append(f'[{color}]')
                        current_color = color
                    else:
                        current_color = None
                line_parts.append(char)

            # Close final color tag if needed
            if current_color is not None:
                if current_color.startswith('bold '):
                    base_color = current_color.replace('bold ', '')
                    line_parts.append(f'[/{base_color}]')
                    line_parts.append('[/bold]')
                else:
                    line_parts.append(f'[/{current_color}]')

            lines.append(''.join(line_parts))

        return lines

    def _render_workload_celebration(self) -> List[str]:
        """
        Render the celebration mode with l33t HELLO WORLD ASCII art and effects
        
        Returns:
            List of strings with celebration visualization
        """
        print(f"🎨 DEBUG: _render_workload_celebration called! Frame: {self.workload_celebration_frame}, Size: {self.width}x{self.height}")
        lines = []
        
        # Collect hardware data for responsive animations
        hardware_data = self._collect_hardware_data_for_celebration()

        # Generate the hardware-responsive animated ASCII art
        ascii_art = generate_leet_hello_world_ascii(self.workload_celebration_frame, self.width, hardware_data)
        
        # Calculate vertical position to center the ASCII art
        ascii_height = len(ascii_art)
        vertical_padding = max(0, (self.height - ascii_height) // 2)
        
        # Add padding lines at top
        for _ in range(vertical_padding):
            lines.append(' ' * self.width)
        
        # Add the ASCII art with colors and effects
        for line_idx, art_line in enumerate(ascii_art):
            # Hardware-responsive color cycling and pulsing
            if hardware_data and hardware_data.get('temp_change', 0) > 0.15:
                # High temperature - use warmer colors
                color_cycle = ['bright_red', 'orange1', 'bright_yellow', 'yellow',
                              'bright_magenta', 'magenta', 'bright_white']
            elif hardware_data and hardware_data.get('power_change', 0) > 0.3:
                # High power - use energetic colors
                color_cycle = ['bright_green', 'bright_cyan', 'bright_blue', 'bright_magenta',
                              'bright_yellow', 'bright_white', 'bright_red']
            else:
                # Normal/baseline - standard rainbow
                color_cycle = ['bright_red', 'bright_yellow', 'bright_green', 'bright_cyan',
                              'bright_blue', 'bright_magenta', 'bright_white']

            # Hardware-responsive color wave speed
            if hardware_data:
                color_speed = max(1, 5 - int(hardware_data.get('current_change', 0) * 3))
            else:
                color_speed = 3

            color_offset = (self.workload_celebration_frame // color_speed + line_idx) % len(color_cycle)
            line_color = color_cycle[color_offset]

            # Hardware-responsive pulsing effect
            if hardware_data:
                pulse_rate = 0.2 + min(hardware_data.get('power_change', 0) * 0.3, 0.4)
                pulse_threshold = 0.7 - min(hardware_data.get('temp_change', 0) * 0.2, 0.3)
            else:
                pulse_rate = 0.2
                pulse_threshold = 0.7

            pulse_intensity = abs(math.sin(self.workload_celebration_frame * pulse_rate))
            use_bold = pulse_intensity > pulse_threshold

            # Create the colored line with proper Rich markup nesting
            if art_line.strip():  # Only color non-empty lines
                if use_bold:
                    colored_line = f'[bold][{line_color}]{art_line}[/{line_color}][/bold]'
                else:
                    colored_line = f'[{line_color}]{art_line}[/{line_color}]'
            else:
                colored_line = art_line
                
            lines.append(colored_line)
        
        # Add padding lines at bottom
        remaining_lines = self.height - len(lines)
        for _ in range(remaining_lines):
            lines.append(' ' * self.width)
            
        # Add particle effects overlay
        if self.workload_celebration_frame % 5 == 0:  # Update particles every 5 frames
            lines = self._add_celebration_particles(lines)
        
        return lines

    def _collect_hardware_data_for_celebration(self) -> Dict[str, float]:
        """Collect hardware telemetry data for responsive celebration animations

        Returns:
            Dict with averaged hardware values and relative changes from baseline
        """
        if not hasattr(self, 'starfield') or not self.starfield or not self.starfield.baseline_established:
            # No hardware data available or baseline not established
            return {}

        try:
            total_power = total_temp = total_current = 0.0
            total_power_change = total_temp_change = total_current_change = 0.0
            device_count = 0

            # Average hardware values across all devices
            for device_idx in range(len(self.backend.devices)):
                if device_idx not in self.starfield.baseline_power:
                    continue

                try:
                    telem = self.backend.device_telemetrys[device_idx]
                    power = float(telem.get('power', '0.0'))
                    temp = float(telem.get('asic_temperature', '0.0'))
                    current = float(telem.get('current', '0.0'))

                    # Calculate relative changes from baseline
                    power_change = self.starfield._get_relative_change(power, self.starfield.baseline_power[device_idx])
                    temp_change = self.starfield._get_relative_change(temp, self.starfield.baseline_temp[device_idx])
                    current_change = self.starfield._get_relative_change(current, self.starfield.baseline_current[device_idx])

                    total_power += power
                    total_temp += temp
                    total_current += current
                    total_power_change += power_change
                    total_temp_change += temp_change
                    total_current_change += current_change
                    device_count += 1

                except (ValueError, KeyError):
                    continue

            if device_count == 0:
                return {}

            # Return averaged values for celebration animation
            return {
                'power': total_power / device_count,
                'temp': total_temp / device_count,
                'current': total_current / device_count,
                'power_change': total_power_change / device_count,
                'temp_change': total_temp_change / device_count,
                'current_change': total_current_change / device_count,
                'device_count': device_count
            }

        except Exception as e:
            print(f"🔧 DEBUG: Error collecting hardware data for celebration: {e}")
            return {}

    def _add_celebration_particles(self, base_lines: List[str]) -> List[str]:
        """
        Add animated particle effects over the celebration display
        
        Args:
            base_lines: Base lines to add particles to
            
        Returns:
            Modified lines with particle effects
        """
        enhanced_lines = []
        
        for line_idx, line in enumerate(base_lines):
            line_chars = list(line) if isinstance(line, str) else [' '] * self.width
            
            # Add random celebration particles
            particles = ['✦', '✧', '✩', '★', '☆', '◆', '◇', '●', '○', '▲', '▼', '♦', '♠', '♣', '♥']
            particle_colors = ['bright_yellow', 'bright_red', 'bright_green', 'bright_blue', 
                              'bright_magenta', 'bright_cyan', 'bright_white']
            
            # Hardware-responsive particle density
            # Collect hardware data for particles
            hardware_data = self._collect_hardware_data_for_celebration()

            # Base density from celebration progress
            celebration_progress = self.workload_celebration_frame / self.workload_celebration_duration
            if celebration_progress < 0.3 or celebration_progress > 0.7:
                base_density = 0.15  # Higher density during intro and outro
            else:
                base_density = 0.05  # Lower density during main display

            # Hardware modulation of particle density
            if hardware_data:
                power_boost = min(hardware_data.get('power_change', 0) * 0.1, 0.1)
                current_boost = min(hardware_data.get('current_change', 0) * 0.05, 0.05)
                particle_density = base_density + power_boost + current_boost
            else:
                particle_density = base_density
            
            for char_idx in range(len(line_chars)):
                if random.random() < particle_density:
                    particle = random.choice(particles)
                    particle_color = random.choice(particle_colors)
                    
                    # Only add particle if position is empty (space)
                    if char_idx < len(line_chars) and line_chars[char_idx] == ' ':
                        line_chars[char_idx] = f'[{particle_color}]{particle}[/{particle_color}]'
            
            enhanced_lines.append(''.join(line_chars))
        
        return enhanced_lines


class FlowingDataStreams:
    """
    Animated data streams that flow across the screen, representing
    actual data movement between hardware components.
    """

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.streams = []

    def update_streams(self, backend: TTSMIBackend, frame_count: int) -> None:
        """Update data streams based on real interconnect activity"""
        self.streams = []

        # Create streams between active devices
        num_devices = len(backend.devices)
        if num_devices < 2:
            return

        for i in range(num_devices):
            for j in range(i + 1, num_devices):
                try:
                    # Get power levels to simulate data flow
                    telem_i = backend.device_telemetrys[i]
                    telem_j = backend.device_telemetrys[j]
                    power_i = float(telem_i.get('power', '0.0'))
                    power_j = float(telem_j.get('power', '0.0'))

                    # Only create streams if there's significant activity (lowered threshold)
                    if power_i > 5 or power_j > 5:  # Lower threshold for real hardware
                        stream_intensity = (power_i + power_j) / 100.0  # Adjusted for real power levels

                        # Stream flows from higher power to lower power device
                        if power_i > power_j:
                            start_x = i * self.width // num_devices
                            end_x = j * self.width // num_devices
                            flow_direction = 1
                        else:
                            start_x = j * self.width // num_devices
                            end_x = i * self.width // num_devices
                            flow_direction = -1

                        stream_y = self.height // 2 + (i - j) * 3

                        if 0 <= stream_y < self.height:
                            stream = {
                                'start_x': start_x,
                                'end_x': end_x,
                                'y': stream_y,
                                'intensity': stream_intensity,
                                'direction': flow_direction,
                                'phase': (frame_count * 0.2 + i * 0.5) % (2 * math.pi)
                            }
                            self.streams.append(stream)
                except:
                    continue

    def render_streams(self, base_field: List[str]) -> List[str]:
        """Render flowing data streams over the base starfield"""
        lines = list(base_field)  # Copy base field

        for stream in self.streams:
            y = stream['y']
            if not (0 <= y < len(lines)):
                continue

            start_x = stream['start_x']
            end_x = stream['end_x']
            intensity = stream['intensity']
            phase = stream['phase']

            # Create flowing pattern
            stream_length = abs(end_x - start_x)
            if stream_length == 0:
                continue

            flow_chars = ['·', '▸', '▶', '▶', '▸', '·'] if stream['direction'] > 0 else ['·', '◂', '◀', '◀', '◂', '·']
            pattern_length = len(flow_chars)

            # Determine color based on intensity (adjusted for real hardware)
            if intensity > 0.4:  # Lower thresholds for real hardware
                stream_color = 'bright_white'
            elif intensity > 0.25:
                stream_color = 'bright_yellow'
            elif intensity > 0.1:
                stream_color = 'orange1'
            else:
                stream_color = 'bright_cyan'

            # Build the stream line
            line_chars = list(lines[y]) if y < len(lines) else [' '] * self.width

            for offset in range(0, stream_length, 2):  # Sample every 2 characters
                x = start_x + offset if stream['direction'] > 0 else start_x - offset
                if not (0 <= x < len(line_chars)):
                    continue

                # Calculate which flow character to use based on phase
                pattern_pos = int((offset / 2 + phase) % pattern_length)
                flow_char = flow_chars[pattern_pos]

                # Only place character if it's not a space/dot or if it would overwrite a space
                if flow_char not in ' ·' or line_chars[x] == ' ':
                    # Insert colored character
                    line_chars[x] = f'[{stream_color}]{flow_char}[/{stream_color}]'

            lines[y] = ''.join(line_chars)

        return lines


class HardwareResponsiveASCII(Static):
    """
    Hardware-Responsive Animated ASCII Art Display Widget

    A full-screen animated visualization where every pixel responds to
    real hardware telemetry data, creating beautiful art that's also
    informationally dense.
    """

    BINDINGS = [
        Binding("w", "trigger_celebration", "Trigger Workload Celebration", show=True),
        Binding("v", "exit_visualization", "Exit Visualization", show=True),
        Binding("escape", "exit_visualization", "Exit Visualization", show=False),
    ]

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.frame_count = 0
        self.start_time = time.time()

        # Initialize display dimensions (will be updated on mount)
        self.display_width = 120
        self.display_height = 40

        # Initialize animation systems
        self.starfield = HardwareStarfield(self.display_width, self.display_height)
        self.data_streams = FlowingDataStreams(self.display_width, self.display_height)

    def on_mount(self) -> None:
        """Initialize hardware-responsive animation systems"""
        # Get actual display size with fallback
        self.display_width = max(self.size.width, 80) if hasattr(self, 'size') and self.size else 80
        self.display_height = max(self.size.height - 2, 25) if hasattr(self, 'size') and self.size else 25

        # DEBUG: Show initialization info
        init_debug = f"""
[bright_yellow]INITIALIZING HARDWARE VISUALIZATION[/bright_yellow]
Display Size: {self.display_width} x {self.display_height}
Backend Devices: {len(self.backend.devices)}
Initialization: Starting...
"""
        self.update(init_debug)

        # Reinitialize systems with correct size
        self.starfield = HardwareStarfield(self.display_width, self.display_height)
        self.data_streams = FlowingDataStreams(self.display_width, self.display_height)

        # Initialize starfield based on actual hardware
        try:
            self.starfield.initialize_stars(self.backend)
            init_debug += f"Stars: {len(self.starfield.stars)} created\n"
        except Exception as e:
            init_debug += f"Star creation error: {e}\n"

        self.update(init_debug + "[green]Starting animation loop...[/green]")

        # Start animation loop
        self.set_interval(0.1, self._update_animation)  # 10 FPS for smooth animation

    def _update_animation(self) -> None:
        """Update animation frame with hardware-responsive data"""
        try:
            # Update backend telemetry
            self.backend.update_telem()
            self.frame_count += 1

            # Update animation systems with real hardware data
            self.starfield.update_from_telemetry(self.backend, self.frame_count)
            self.data_streams.update_streams(self.backend, self.frame_count)

            # Render the complete visualization
            content = self._render_complete_visualization()

            # DEBUG: Add content length info at start of content
            content_lines = content.split('\n')
            debug_info = f"[dim white]DEBUG: {len(content_lines)} lines, {len(content)} chars, Frame {self.frame_count}[/dim white]"

            # Insert debug info after header
            lines = content.split('\n')
            if len(lines) > 5:  # After header
                lines.insert(5, debug_info)
                content = '\n'.join(lines)

            self.update(content)

        except Exception as e:
            # Handle errors gracefully with more debug info
            import traceback
            error_details = traceback.format_exc()
            self.update(f"[red]Animation Error: {e}[/red]\n\nDebug info:\n{error_details}")

    def action_trigger_celebration(self) -> None:
        """Trigger workload celebration manually"""
        print("🔧 DEBUG: 'w' key pressed on HardwareResponsiveASCII widget!")
        if hasattr(self, 'starfield') and self.starfield:
            self.starfield.workload_detected = True
            self.starfield.workload_detection_time = time.time()
            self.starfield.workload_celebration_frame = 0
            print("🎉 Workload celebration triggered from widget!")
            print(f"🔧 DEBUG: Celebration state - detected: {self.starfield.workload_detected}")
        else:
            print("❌ Starfield not available for celebration trigger")

    def action_exit_visualization(self) -> None:
        """Exit visualization mode"""
        print("🔧 DEBUG: Exit visualization called from widget")
        # Signal parent to exit visualization mode
        self.app.exit()

    def _render_complete_visualization(self) -> str:
        """Render the complete hardware-responsive visualization"""
        try:
            lines = []

            # Add header with hardware status
            header = self._create_visualization_header()
            lines.extend(header)

            # Render starfield
            starfield_lines = self.starfield.render_starfield()

            if not starfield_lines or len(starfield_lines) == 0:
                # Fallback to simple text starfield
                starfield_lines = self._render_simple_fallback_starfield()

            # Add flowing data streams over starfield
            enhanced_lines = self.data_streams.render_streams(starfield_lines)

            lines.extend(enhanced_lines)

            # If workload celebration is active, add it below the starfield (unobtrusive)
            if hasattr(self, 'starfield') and self.starfield and self.starfield.workload_detected:
                print(f"🎨 DEBUG: Adding celebration below starfield! Frame: {self.starfield.workload_celebration_frame}")

                # Add a separator line before celebration
                lines.append("")
                lines.append("[dim white]" + "─" * self.starfield.width + "[/dim white]")

                # Get celebration content from starfield (but limit height to keep it unobtrusive)
                celebration_lines = self.starfield._render_workload_celebration()
                # Limit celebration to bottom portion of screen (max 8 lines)
                max_celebration_lines = min(8, len(celebration_lines))
                lines.extend(celebration_lines[:max_celebration_lines])

                # Add simple multi-color "Hello!" text below celebration
                hello_text = self._create_simple_hello_text(self.starfield.workload_celebration_frame)
                lines.append("")  # Spacing
                lines.append(hello_text)

            # Add footer with legend
            footer = self._create_visualization_footer()
            lines.extend(footer)

            return "\n".join(lines)

        except Exception as e:
            # Complete fallback
            return f"""
[red]VISUALIZATION RENDERING ERROR[/red]

Error: {e}
Frame: {self.frame_count}
Display: {self.display_width}x{self.display_height}
Stars: {len(self.starfield.stars) if hasattr(self.starfield, 'stars') else 'unknown'}

[yellow]SIMPLE FALLBACK STARFIELD:[/yellow]

{self._render_simple_fallback_starfield_as_text()}

Press 'v' to exit visualization mode
"""

    def _render_simple_fallback_starfield(self) -> List[str]:
        """Render a simple text-based starfield as fallback"""
        lines = []

        # Create simple starfield
        for row in range(self.display_height):
            line = ""
            for col in range(self.display_width):
                # Simple pattern based on frame and position
                if (row + col + self.frame_count) % 12 == 0:
                    line += "●"
                elif (row + col + self.frame_count) % 8 == 0:
                    line += "○"
                elif (row + col + self.frame_count) % 15 == 0:
                    line += "◉"
                else:
                    line += " "
            lines.append(line)

        return lines

    def _render_simple_fallback_starfield_as_text(self) -> str:
        """Render simple starfield as plain text"""
        lines = []
        for row in range(10):  # Smaller for error display
            line = ""
            for col in range(40):
                if (row + col + self.frame_count) % 8 == 0:
                    line += "*"
                elif (row + col + self.frame_count) % 12 == 0:
                    line += "o"
                else:
                    line += "."
            lines.append(line)
        return "\n".join(lines)

    def _create_visualization_header(self) -> List[str]:
        """Create header showing system status and animation info"""
        lines = []

        # System metrics
        total_devices = len(self.backend.devices)
        if total_devices > 0:
            total_power = sum(float(self.backend.device_telemetrys[i].get('power', '0'))
                            for i in range(total_devices))
            avg_temp = sum(float(self.backend.device_telemetrys[i].get('asic_temperature', '0'))
                          for i in range(total_devices)) / total_devices
            total_current = sum(float(self.backend.device_telemetrys[i].get('current', '0'))
                              for i in range(total_devices))

            # Color-code system status (adjusted thresholds for real hardware)
            if avg_temp > 80:
                status_color = 'bold red'
                status_text = 'THERMAL WARNING'
            elif avg_temp > 65:
                status_color = 'orange1'
                status_text = 'ELEVATED TEMP'
            elif total_power > 100:  # Lowered from 200W
                status_color = 'bright_yellow'
                status_text = 'HIGH POWER'
            elif total_power > 20:  # Lowered from 50W
                status_color = 'bright_green'
                status_text = 'ACTIVE'
            else:
                status_color = 'bright_cyan'
                status_text = 'READY'
        else:
            total_power = avg_temp = total_current = 0
            status_color = 'dim white'
            status_text = 'NO DEVICES'

        # Animated header line
        elapsed_time = time.time() - self.start_time
        pulse_char = '●' if int(elapsed_time * 2) % 2 else '○'

        # Show baseline status and relative changes
        if hasattr(self, 'starfield') and hasattr(self.starfield, 'baseline_established'):
            # Check if in celebration mode
            if hasattr(self.starfield, 'workload_detected') and self.starfield.workload_detected:
                celebration_progress = (self.starfield.workload_celebration_frame / 
                                      self.starfield.workload_celebration_duration * 100)
                baseline_status = f"[bold bright_green]🚀 WORKLOAD CELEBRATION MODE![/bold bright_green]"
                change_info = f"[bright_white]Progress:[/bright_white] [bright_magenta]{celebration_progress:.1f}%[/bright_magenta] [dim white]│[/dim white] [bright_yellow]Frame:[/bright_yellow] [bright_cyan]{self.starfield.workload_celebration_frame}[/bright_cyan]"
            elif self.starfield.baseline_established:
                baseline_status = "[bright_green]BASELINE ESTABLISHED[/bright_green]"
                # Calculate relative changes from baseline
                if total_devices > 0:
                    baseline_total_power = sum(self.starfield.baseline_power.get(i, total_power/total_devices)
                                             for i in range(total_devices))
                    baseline_total_current = sum(self.starfield.baseline_current.get(i, total_current/total_devices)
                                               for i in range(total_devices))

                    power_change = ((total_power - baseline_total_power) / baseline_total_power * 100) if baseline_total_power > 0 else 0
                    current_change = ((total_current - baseline_total_current) / baseline_total_current * 100) if baseline_total_current > 0 else 0

                    change_info = f"[bright_white]Δ Power:[/bright_white] [{'bright_green' if power_change >= 0 else 'orange1'}]{power_change:+5.1f}%[/{'bright_green' if power_change >= 0 else 'orange1'}] [dim white]│[/dim white] [bright_white]Δ Current:[/bright_white] [{'bright_green' if current_change >= 0 else 'orange1'}]{current_change:+5.1f}%[/{'bright_green' if current_change >= 0 else 'orange1'}]"
                else:
                    change_info = "[dim white]No devices detected[/dim white]"
            else:
                baseline_samples = len(self.starfield.baseline_samples) if hasattr(self.starfield, 'baseline_samples') else 0
                baseline_status = f"[bright_yellow]LEARNING BASELINE[/bright_yellow] [dim white]({baseline_samples}/{self.starfield.max_baseline_samples})[/dim white]"
                change_info = "[dim white]Establishing baseline values...[/dim white]"
        else:
            baseline_status = "[bright_yellow]INITIALIZING[/bright_yellow]"
            change_info = "[dim white]Starting visualization...[/dim white]"

        lines.append(f"[bright_cyan]╔═══════════════════════════════════════════════════════════════════════════════════════════╗[/bright_cyan]")
        lines.append(f"[bright_cyan]║[/bright_cyan] [bold bright_magenta]{pulse_char}[/bold bright_magenta] [bold bright_white]ADAPTIVE HARDWARE VISUALIZATION[/bold bright_white] [dim white]│[/dim white] [{status_color}]{status_text}[/{status_color}] [dim white]│[/dim white] [bright_white]Devices:[/bright_white] {total_devices} [bright_cyan]║[/bright_cyan]")
        lines.append(f"[bright_cyan]║[/bright_cyan] {baseline_status} [dim white]│[/dim white] {change_info}")
        lines.append(f"[bright_cyan]║[/bright_cyan] [bright_white]Absolute:[/bright_white] [orange1]{total_power:5.1f}W[/orange1] [bright_green]{total_current:5.1f}A[/bright_green] [bright_yellow]{avg_temp:4.1f}°C[/bright_yellow] [dim white]│[/dim white] [bright_white]Frame:[/bright_white] [bright_magenta]{self.frame_count}[/bright_magenta] [bright_cyan]║[/bright_cyan]")
        lines.append(f"[bright_cyan]╚═══════════════════════════════════════════════════════════════════════════════════════════╝[/bright_cyan]")

        return lines

    def _create_visualization_footer(self) -> List[str]:
        """Create footer with legend and controls"""
        lines = []

        lines.append(f"[bright_cyan]╔═══════════════════════════════════════════════════════════════════════════════════════════╗[/bright_cyan]")
        lines.append(f"[bright_cyan]║[/bright_cyan] [bold bright_white]COMPONENTS:[/bold bright_white] [bright_cyan]●◉○∘·[/bright_cyan] Tensix Cores [dim white]│[/dim white] [bright_magenta]█▓▒░·[/bright_magenta] Memory Ch [dim white]│[/dim white] [bright_blue]◆[/bright_blue] L1 [bright_yellow]◇[/bright_yellow] L2 [bright_red]♦[/bright_red] DDR [dim white]│[/dim white] [bright_green]✦✧✩[/bright_green] Links [bright_cyan]║[/bright_cyan]")
        lines.append(f"[bright_cyan]║[/bright_cyan] [bold bright_white]WORKLOAD DETECTION:[/bold bright_white] Says [bold bright_magenta]🚀 hello[/bold bright_magenta] when activity +{int(hasattr(self, 'starfield') and getattr(self.starfield, 'workload_threshold', 0.20) * 100)}% above baseline")
        lines.append(f"[bright_cyan]║[/bright_cyan] [bold bright_white]CONTROLS:[/bold bright_white] Press 'v' to exit [dim white]│[/dim white] Press 'w' to test celebration [dim white]│[/dim white] [bright_green]+10%[/bright_green] [bright_yellow]+25%[/bright_yellow] [orange1]+50%[/orange1] triggers celebration [bright_cyan]║[/bright_cyan]")
        lines.append(f"[bright_cyan]╚═══════════════════════════════════════════════════════════════════════════════════════════╝[/bright_cyan]")

        return lines

    def _create_simple_hello_text(self, frame: int) -> str:
        """Create simple multi-color 'Hello!' text for celebration

        Args:
            frame: Current celebration frame for color cycling

        Returns:
            Formatted hello text with hardware-responsive colors
        """
        # Multi-color palette that cycles through the celebration
        colors = ['bright_red', 'bright_yellow', 'bright_green', 'bright_cyan',
                  'bright_blue', 'bright_magenta', 'bright_white']

        # Create "Hello!" with each letter in a different color
        hello_letters = ['H', 'e', 'l', 'l', 'o', '!']
        colored_letters = []

        for i, letter in enumerate(hello_letters):
            # Cycle through colors based on frame and letter position
            color_index = (frame // 5 + i) % len(colors)
            color = colors[color_index]
            colored_letters.append(f'[{color}]{letter}[/{color}]')

        # Center the text
        hello_text = ''.join(colored_letters)
        centered_text = hello_text.center(80)  # Assume 80-character width

        return centered_text


class AnimatedDisplayContainer(Container):
    """
    Container for the animated display that can be toggled on/off
    """

    BINDINGS = [
        Binding("v", "toggle_visualization", "Toggle Visualization", show=True),
        Binding("escape", "exit_visualization", "Exit Visualization", show=False),
        Binding("w", "trigger_workload_celebration", "Test Workload Celebration", show=True),
    ]

    def __init__(self, backend: TTSMIBackend, **kwargs):
        super().__init__(**kwargs)
        self.backend = backend
        self.is_visualization_mode = False
        self.animated_display = None

    def compose(self) -> ComposeResult:
        """Compose the animated display container"""
        # Initially empty - display is created on toggle
        pass

    def action_toggle_visualization(self) -> None:
        """Toggle between normal monitor and animated visualization"""
        if self.is_visualization_mode:
            self.action_exit_visualization()
        else:
            self.enter_visualization_mode()

    def enter_visualization_mode(self) -> None:
        """Enter full-screen animated visualization mode"""
        self.is_visualization_mode = True

        # Clear current content
        for child in self.children:
            child.remove()

        # Create and mount animated display
        self.animated_display = HardwareResponsiveASCII(
            backend=self.backend,
            id="animated_display"
        )
        self.mount(self.animated_display)

        # Focus the animated display
        self.animated_display.focus()

    def action_exit_visualization(self) -> None:
        """Exit visualization mode and return to normal monitor"""
        self.is_visualization_mode = False

        # Remove animated display
        if self.animated_display:
            self.animated_display.remove()
            self.animated_display = None

        # Signal parent to restore normal view
        self.post_message_no_wait(self.VisualizationToggled(False))

    def action_trigger_workload_celebration(self) -> None:
        """Manually trigger workload celebration for testing"""
        print(f"🔧 DEBUG: 'w' key pressed! Visualization mode: {self.is_visualization_mode}")
        print(f"🔧 DEBUG: Animated display exists: {self.animated_display is not None}")
        
        if self.is_visualization_mode and self.animated_display and hasattr(self.animated_display, 'starfield'):
            # Manually trigger the celebration
            starfield = self.animated_display.starfield
            starfield.workload_detected = True
            starfield.workload_detection_time = time.time()
            starfield.workload_celebration_frame = 0
            print("🎉 Manual workload celebration triggered!")
            print(f"🔧 DEBUG: Starfield celebration state set - detected: {starfield.workload_detected}, frame: {starfield.workload_celebration_frame}")
        else:
            print("❌ Cannot trigger celebration - not in visualization mode or display not available")
            if not self.is_visualization_mode:
                print("   Hint: Press 'v' first to enter visualization mode")
            if not self.animated_display:
                print("   Hint: Animated display not initialized")

    class VisualizationToggled:
        """Message sent when visualization is toggled"""
        def __init__(self, enabled: bool):
            self.enabled = enabled