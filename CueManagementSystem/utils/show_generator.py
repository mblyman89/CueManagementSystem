"""
Professional Firework Show Generator
====================================

Advanced show generator implementing industry best practices for creating comprehensive firework shows.

Features:
- Industry best practices implementation
- Extensive validation
- Expert show design logic
- Multiple show sections (intro, buildup, climax, finale)
- Effect sequencing
- Timing optimization
- Safety validation
- Comprehensive show structure

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import random
import math
from typing import List, Dict, Any, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class TimingZone(Enum):
    """Timing patterns for dynamic show pacing"""
    BURST = "burst"  # 0.1-0.3s - Rapid fire excitement
    RAPID = "rapid"  # 0.3-0.8s - Fast energetic
    MODERATE = "moderate"  # 0.8-2.0s - Steady rhythm
    SLOW = "slow"  # 2.0-4.0s - Building anticipation
    PAUSE = "pause"  # 3.0-6.0s - Dramatic silence


class ShowIntensity(Enum):
    """Show intensity levels for professional pacing"""
    CALM = 1
    BUILDING = 2
    MODERATE = 3
    HIGH = 4
    CLIMAX = 5


@dataclass
class CueData:
    """Represents a single firework cue"""
    cue_number: int
    cue_type: str
    outputs: str
    delay: float
    execute_time: str
    intensity: ShowIntensity = ShowIntensity.MODERATE
    zone_type: Optional[TimingZone] = None

    def to_table_row(self) -> List[Any]:
        """Convert to format expected by cue table"""
        return [
            self.cue_number,
            self.cue_type,
            self.outputs,
            self.delay,
            self.execute_time
        ]


@dataclass
class ActMetrics:
    """Metrics for validating act generation"""
    name: str
    target_outputs: int
    actual_outputs: int
    target_duration: float
    actual_duration: float
    start_time: float
    end_time: float
    num_cues: int
    intensity_progression: List[float] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if act metrics are within acceptable ranges"""
        output_match = abs(self.actual_outputs - self.target_outputs) <= 5
        duration_match = abs(self.actual_duration - self.target_duration) <= 5.0
        return output_match and duration_match


@dataclass
class ShowMetrics:
    """Overall show metrics for validation"""
    total_cues: int
    total_outputs_used: int
    target_outputs: int
    total_duration: float
    target_duration: float
    acts: List[ActMetrics] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Validate entire show meets requirements"""
        outputs_valid = self.total_outputs_used == self.target_outputs
        duration_valid = abs(self.total_duration - self.target_duration) <= 2.0
        acts_valid = all(act.is_valid() for act in self.acts)
        return outputs_valid and duration_valid and acts_valid


class SpecialEffectPatterns:
    """Professional special effect timing patterns"""

    PATTERNS = {
        "Trot": {
            "description": "Steady horse gait rhythm",
            "base_delays": [0.7, 0.7, 0.7],
            "min_outputs": 3,
            "max_outputs": 6,
            "variation": 0.1,
            "intensity_multiplier": 1.2
        },
        "Gallop": {
            "description": "Fast triplet with pause",
            "base_delays": [0.15, 0.15, 0.15, 0.5],
            "min_outputs": 4,
            "max_outputs": 8,
            "variation": 0.05,
            "intensity_multiplier": 1.5
        },
        "Step": {
            "description": "Walking rhythm pattern",
            "base_delays": [1.0, 0.5, 1.0, 0.5],
            "min_outputs": 4,
            "max_outputs": 8,
            "variation": 0.1,
            "intensity_multiplier": 1.1
        },
        "Rock Ballad": {
            "description": "Classic rock drum beat",
            "base_delays": [0.8, 0.4, 0.8, 0.4],
            "min_outputs": 4,
            "max_outputs": 8,
            "variation": 0.08,
            "intensity_multiplier": 1.3
        },
        "Metal Ballad": {
            "description": "Double bass drum pattern",
            "base_delays": [0.25, 0.25, 0.5, 0.25, 0.25, 0.5],
            "min_outputs": 6,
            "max_outputs": 12,
            "variation": 0.06,
            "intensity_multiplier": 1.6
        },
        "Chase": {
            "description": "LED chase sequence",
            "base_delays": [0.3, 0.3, 0.3, 0.3, 0.3],
            "min_outputs": 5,
            "max_outputs": 10,
            "variation": 0.03,
            "intensity_multiplier": 1.4
        },
        "Random": {
            "description": "Random varied delays",
            "base_delays": "random",
            "min_outputs": 3,
            "max_outputs": 8,
            "variation": 0.2,
            "intensity_multiplier": 1.2
        },
        "False Finale": {
            "description": "Dramatic false ending with gap and explosive real finale",
            "base_delays": "special",
            "min_outputs": 50,
            "max_outputs": 1000,
            "variation": 0.0,
            "intensity_multiplier": 2.0
        }
    }

    @classmethod
    def generate_effect_delays(cls, effect_name: str, num_outputs: int,
                               intensity: float = 1.0) -> List[float]:
        """
        Generate delays for a special effect with intensity scaling

        Args:
            effect_name: Name of the effect
            num_outputs: Number of outputs in sequence
            intensity: Intensity multiplier (0.5-2.0)
        """
        if effect_name not in cls.PATTERNS:
            return [0.5] * (num_outputs - 1)

        pattern = cls.PATTERNS[effect_name]

        if pattern["base_delays"] == "random":
            base_range = (0.2, 1.0)
            # Adjust range based on intensity
            min_delay = base_range[0] / intensity
            max_delay = base_range[1] / intensity
            return [random.uniform(min_delay, max_delay) for _ in range(num_outputs - 1)]

        base_delays = pattern["base_delays"]
        variation = pattern["variation"]

        delays = []
        for i in range(num_outputs - 1):
            base = base_delays[i % len(base_delays)]
            # Apply intensity scaling (higher intensity = faster)
            scaled = base / intensity
            # Add variation
            varied = scaled * (1 + random.uniform(-variation, variation))
            # Round to 0.05s precision
            varied = round(varied / 0.05) * 0.05
            delays.append(max(0.05, varied))

        return delays


class IntensityCurve:
    """Manages intensity progression throughout the show"""

    @staticmethod
    def calculate_act_intensity(act_name: str, progress: float) -> float:
        """
        Calculate intensity at a given point in an act

        Args:
            act_name: Name of the act (opening, buildup, finale)
            progress: Progress through act (0.0 to 1.0)

        Returns:
            Intensity value (0.5 to 2.0)
        """
        if act_name == "opening":
            # Gradual build from calm to moderate
            # Starts at 0.6, ends at 1.2
            return 0.6 + (0.6 * progress)

        elif act_name == "buildup":
            # Accelerating curve from moderate to high
            # Starts at 1.2, ends at 1.7
            # Uses exponential curve for acceleration feel
            return 1.2 + (0.5 * (progress ** 1.5))

        else:  # finale
            # High intensity with peaks and valleys
            # Base intensity 1.7-2.0 with waves
            base = 1.7 + (0.3 * progress)
            # Add wave pattern for dramatic effect
            wave = 0.15 * math.sin(progress * math.pi * 3)
            return base + wave

    @staticmethod
    def get_zone_probabilities(act_name: str, intensity: float) -> Dict[TimingZone, float]:
        """
        Get timing zone probabilities based on act and intensity

        Higher intensity favors faster zones (BURST, RAPID)
        Lower intensity favors slower zones (SLOW, MODERATE)
        """
        if act_name == "opening":
            if intensity < 0.8:
                return {
                    TimingZone.SLOW: 0.5,
                    TimingZone.MODERATE: 0.3,
                    TimingZone.PAUSE: 0.15,
                    TimingZone.RAPID: 0.05
                }
            else:
                return {
                    TimingZone.SLOW: 0.3,
                    TimingZone.MODERATE: 0.4,
                    TimingZone.RAPID: 0.2,
                    TimingZone.PAUSE: 0.1
                }

        elif act_name == "buildup":
            if intensity < 1.4:
                return {
                    TimingZone.MODERATE: 0.35,
                    TimingZone.RAPID: 0.35,
                    TimingZone.BURST: 0.15,
                    TimingZone.SLOW: 0.1,
                    TimingZone.PAUSE: 0.05
                }
            else:
                return {
                    TimingZone.RAPID: 0.4,
                    TimingZone.BURST: 0.3,
                    TimingZone.MODERATE: 0.2,
                    TimingZone.PAUSE: 0.1
                }

        else:  # finale
            if intensity < 1.8:
                return {
                    TimingZone.BURST: 0.35,
                    TimingZone.RAPID: 0.45,
                    TimingZone.MODERATE: 0.2
                }
            else:
                return {
                    TimingZone.BURST: 0.6,
                    TimingZone.RAPID: 0.35,
                    TimingZone.MODERATE: 0.05
                }


class ShowValidator:
    """Comprehensive validation system for show generation"""

    @staticmethod
    def validate_configuration(config: Dict) -> Tuple[bool, List[str]]:
        """Validate input configuration"""
        errors = []

        if config.get("total_outputs", 0) <= 0:
            errors.append("Total outputs must be greater than 0")

        if config.get("total_duration", 0) <= 0:
            errors.append("Total duration must be greater than 0")

        if config.get("total_outputs", 0) > 10000:
            errors.append("Total outputs exceeds maximum (10000)")

        if config.get("total_duration", 0) > 3600:
            errors.append("Total duration exceeds maximum (1 hour)")

        return len(errors) == 0, errors

    @staticmethod
    def validate_output_usage(cues: List[CueData], total_outputs: int) -> Tuple[bool, Dict]:
        """Validate all outputs are used exactly once"""
        used_outputs = set()
        duplicate_outputs = []

        for cue in cues:
            outputs_str = cue.outputs
            for output_str in outputs_str.split(","):
                try:
                    output = int(output_str.strip())
                    if output in used_outputs:
                        duplicate_outputs.append(output)
                    used_outputs.add(output)
                except:
                    pass

        missing_outputs = set(range(1, total_outputs + 1)) - used_outputs

        return {
            "valid": len(used_outputs) == total_outputs and len(duplicate_outputs) == 0,
            "used_count": len(used_outputs),
            "target_count": total_outputs,
            "missing": sorted(list(missing_outputs)),
            "duplicates": sorted(duplicate_outputs)
        }

    @staticmethod
    def validate_timing(cues: List[CueData], target_duration: float) -> Tuple[bool, Dict]:
        """Validate timing is correct and sequential"""
        if not cues:
            return False, {"error": "No cues generated"}

        # Check timing is sequential
        prev_time = -1.0
        timing_errors = []

        for i, cue in enumerate(cues):
            current_time = ShowValidator._parse_time(cue.execute_time)
            if current_time < prev_time:
                timing_errors.append(f"Cue {i + 1}: Time goes backwards")
            prev_time = current_time

        # Check duration
        final_time = ShowValidator._parse_time(cues[-1].execute_time)
        duration_diff = abs(final_time - target_duration)

        return {
            "valid": len(timing_errors) == 0 and duration_diff <= 2.0,
            "final_duration": final_time,
            "target_duration": target_duration,
            "duration_diff": duration_diff,
            "timing_errors": timing_errors
        }

    @staticmethod
    def _parse_time(time_str: str) -> float:
        """Parse MM:SS.SSSSSSSS format to seconds"""
        parts = time_str.split(":")
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds


class ShowGenerator:
    """
    Professional firework show generator with comprehensive validation
    and industry best practices
    """

    def __init__(self):
        self.cues: List[CueData] = []
        self.current_cue_number = 1
        self.output_index = 0
        self.all_outputs: List[int] = []
        self.sequential_cues = True
        self.current_time = 0.0  # Track global time across acts
        self.act_metrics: List[ActMetrics] = []
        self.used_outputs: Set[int] = set()

    def generate_random_show(self, config_data) -> List[List[Any]]:
        """
        Main entry point for professional show generation

        Args:
            config_data: Configuration from dialog

        Returns:
            List of cue rows (lists) for table display
        """
        print("\n" + "=" * 80)
        print("PROFESSIONAL FIREWORK SHOW GENERATOR v5.0 - Expert Edition")
        print("=" * 80)

        # Phase 1: Extract and validate configuration
        print("\n📋 Phase 1: Configuration")
        print("-" * 80)
        self._extract_configuration(config_data)

        is_valid, errors = ShowValidator.validate_configuration({
            "total_outputs": self.total_outputs,
            "total_duration": self.total_duration
        })

        if not is_valid:
            print("❌ Configuration validation failed:")
            for error in errors:
                print(f"   - {error}")
            return []

        print("✅ Configuration validated")

        # Phase 2: Generate show structure
        print("\n🎆 Phase 2: Show Generation")
        print("-" * 80)
        self._generate_professional_show()

        # Phase 3: Validate and adjust
        print("\n🔍 Phase 3: Validation & Adjustment")
        print("-" * 80)
        self._validate_and_adjust()

        # Phase 4: Final verification
        print("\n✅ Phase 4: Final Verification")
        print("-" * 80)
        self._final_verification()

        print("\n" + "=" * 80)
        print("🎆 SHOW GENERATION COMPLETE")
        print("=" * 80 + "\n")

        # Convert to table rows
        return [cue.to_table_row() for cue in self.cues]

    def _extract_configuration(self, config_data):
        """Extract and display configuration"""
        self.total_outputs = config_data.num_outputs
        self.total_duration = config_data.total_seconds
        self.sequential_cues = config_data.sequential_cues
        self.act_config = config_data.act_config

        # Initialize output pool
        self.all_outputs = list(range(1, self.total_outputs + 1))
        if not self.sequential_cues:
            random.shuffle(self.all_outputs)
            print(f"   Output Mode: RANDOM (shuffled)")
        else:
            print(f"   Output Mode: SEQUENTIAL (1 → {self.total_outputs})")

        print(f"   Total Outputs: {self.total_outputs}")
        print(f"   Total Duration: {self.total_duration}s ({self.total_duration / 60:.1f} minutes)")
        print(f"   Acts: {len(self.act_config)}")

    def _generate_professional_show(self):
        """Generate complete show with professional structure"""
        # Calculate act distribution
        acts = self._calculate_professional_act_distribution()

        # Generate each act sequentially
        for act in acts:
            self._generate_professional_act(act)

    def _calculate_professional_act_distribution(self) -> List[Dict]:
        """Calculate precise act distribution with remainder handling"""
        acts = []
        act_keys = ["opening", "buildup", "finale"]

        # Calculate base allocations
        output_allocations = []
        duration_allocations = []

        for act_key in act_keys:
            act_data = self.act_config.get(act_key, {})

            # Dialog passes "percentage" which should apply to BOTH outputs and duration
            # This ensures 20% opening = 20% of outputs AND 20% of duration
            percentage = act_data.get("percentage", 33) / 100.0

            # DEBUG: Print what we're reading from config
            print(f"   DEBUG {act_key}: percentage={percentage * 100:.0f}%")

            num_outputs = int(self.total_outputs * percentage)
            duration = self.total_duration * percentage

            output_allocations.append(num_outputs)
            duration_allocations.append(duration)

        # Distribute output remainder to finale
        total_allocated = sum(output_allocations)
        output_remainder = self.total_outputs - total_allocated
        output_allocations[2] += output_remainder

        # Distribute duration remainder to finale
        total_duration_allocated = sum(duration_allocations)
        duration_remainder = self.total_duration - total_duration_allocated
        duration_allocations[2] += duration_remainder

        # Create act definitions
        print("\n   Act Distribution:")
        for i, act_key in enumerate(act_keys):
            act_data = self.act_config.get(act_key, {})

            acts.append({
                "name": act_key,
                "num_outputs": output_allocations[i],
                "duration": duration_allocations[i],
                "config": act_data,
                "start_time": self.current_time
            })

            print(f"\n   🎭 {act_key.upper()} Act:")
            print(f"      Start Time: {self._format_time(self.current_time)}")
            print(f"      Duration: {duration_allocations[i]:.1f}s")
            print(f"      Outputs: {output_allocations[i]}")

            # Update current time for next act
            self.current_time += duration_allocations[i]

        # Reset current time for actual generation
        self.current_time = 0.0

        return acts

    def _generate_professional_act(self, act: Dict):
        """Generate a single act with professional pacing"""
        act_name = act["name"]
        num_outputs = act["num_outputs"]
        duration = act["duration"]
        start_time = act["start_time"]
        config = act["config"]

        print(f"\n      🔧 Generating {act_name} cues...")

        # Track act start
        act_start_time = self.current_time
        act_start_output = self.output_index

        # Get configuration
        shot_types = config.get("shot_types", {})
        special_effects = config.get("special_effects", {})
        enabled_effects = [name for name, enabled in special_effects.items() if enabled]

        # Check for False Finale (only in finale act)
        has_false_finale = act_name == "finale" and "False Finale" in enabled_effects

        if has_false_finale:
            print(f"         🎭 FALSE FINALE ENABLED - Creating dramatic structure...")
            self._generate_false_finale_act(act, config, enabled_effects)
            return

        # Calculate shot type distribution
        type_counts = self._calculate_shot_type_distribution(shot_types, num_outputs)

        # Generate timing zones with intensity progression
        zones = self._create_professional_timing_zones(act_name, num_outputs, duration)

        # Generate cues following zones
        act_cues = []
        outputs_used = 0

        for zone in zones:
            if outputs_used >= num_outputs:
                break

            zone_cues = self._generate_zone_cues(
                zone, type_counts, enabled_effects,
                num_outputs - outputs_used, act_name
            )

            act_cues.extend(zone_cues)
            outputs_used += len([c for c in zone_cues if not c.get("skip_count", False)])

        # Use any remaining outputs
        while outputs_used < num_outputs:
            cue = self._create_single_shot()
            act_cues.append(cue)
            outputs_used += 1

        # Assign timing to cues
        self._assign_professional_timing(act_cues, zones, duration, act_name)

        # Add to main cue list
        self.cues.extend([c for c in act_cues if isinstance(c, CueData)])

        # Record act metrics
        act_end_time = self.current_time
        act_outputs_used = self.output_index - act_start_output

        metrics = ActMetrics(
            name=act_name,
            target_outputs=num_outputs,
            actual_outputs=act_outputs_used,
            target_duration=duration,
            actual_duration=act_end_time - act_start_time,
            start_time=act_start_time,
            end_time=act_end_time,
            num_cues=len([c for c in act_cues if isinstance(c, CueData)])
        )

        self.act_metrics.append(metrics)

        print(f"         ✓ Generated {metrics.num_cues} cues")
        print(f"         ✓ Used {act_outputs_used} outputs")
        print(f"         ✓ Duration: {metrics.actual_duration:.1f}s")
        print(f"         ✓ End time: {self._format_time(act_end_time)}")

    def _generate_false_finale_act(self, act: Dict, config: Dict, enabled_effects: List[str]):
        """
        Generate finale act with false finale structure

        Structure:
        1. False Finale (20s, 27% outputs) - Rapid buildup to apparent climax
        2. The Gap (12s, 2% outputs) - Silence with 1-3 scattered singles
        3. Real Finale (remaining, 71% outputs) - Explosive spectacular finish
        """
        act_name = act["name"]
        total_outputs = act["num_outputs"]
        total_duration = act["duration"]
        shot_types = config.get("shot_types", {})

        # Remove "False Finale" from enabled effects for actual effect generation
        effect_list = [e for e in enabled_effects if e != "False Finale"]

        # Calculate allocations
        false_finale_outputs = int(total_outputs * 0.27)
        gap_outputs = min(5, int(total_outputs * 0.02))
        real_finale_outputs = total_outputs - false_finale_outputs - gap_outputs

        false_finale_duration = 20.0
        gap_duration = 12.0
        real_finale_duration = total_duration - false_finale_duration - gap_duration

        print(f"         📊 False Finale Structure:")
        print(f"            Part 1 - False Finale: {false_finale_duration:.0f}s, {false_finale_outputs} outputs")
        print(f"            Part 2 - The Gap: {gap_duration:.0f}s, {gap_outputs} outputs")
        print(f"            Part 3 - Real Finale: {real_finale_duration:.0f}s, {real_finale_outputs} outputs")

        act_start_time = self.current_time
        act_start_output = self.output_index

        # PART 1: FALSE FINALE
        print(f"\n         🎆 Generating FALSE FINALE (apparent climax)...")
        false_finale_cues = self._generate_false_finale_section(
            false_finale_outputs, false_finale_duration, shot_types, effect_list
        )
        self.cues.extend(false_finale_cues)

        # PART 2: THE GAP
        print(f"         ⏸️  Generating THE GAP (dramatic silence)...")
        gap_cues = self._generate_gap_section(gap_outputs, gap_duration)
        self.cues.extend(gap_cues)

        # PART 3: REAL FINALE
        print(f"         💥 Generating REAL FINALE (spectacular explosion)...")
        real_finale_cues = self._generate_real_finale_section(
            real_finale_outputs, real_finale_duration, shot_types, effect_list
        )
        self.cues.extend(real_finale_cues)

        # Record metrics
        act_end_time = self.current_time
        act_outputs_used = self.output_index - act_start_output
        total_cues = len(false_finale_cues) + len(gap_cues) + len(real_finale_cues)

        metrics = ActMetrics(
            name=act_name,
            target_outputs=total_outputs,
            actual_outputs=act_outputs_used,
            target_duration=total_duration,
            actual_duration=act_end_time - act_start_time,
            start_time=act_start_time,
            end_time=act_end_time,
            num_cues=total_cues
        )

        self.act_metrics.append(metrics)

        print(f"         ✓ Generated {total_cues} cues with FALSE FINALE structure")
        print(f"         ✓ Used {act_outputs_used} outputs")
        print(f"         ✓ Duration: {metrics.actual_duration:.1f}s")
        print(f"         ✓ End time: {self._format_time(act_end_time)}")

    def _generate_false_finale_section(self, num_outputs: int, duration: float,
                                       shot_types: Dict, enabled_effects: List[str]) -> List[CueData]:
        """Generate the false finale section - rapid buildup to apparent climax"""
        cues = []
        type_counts = self._calculate_shot_type_distribution(shot_types, num_outputs)

        zones = []
        outputs_allocated = 0
        progress = 0.0

        while outputs_allocated < num_outputs:
            intensity = 1.5 + (progress * 1.0)

            if random.random() < 0.8:
                zone_type = TimingZone.BURST
                zone_size = random.randint(5, 10)
            else:
                zone_type = TimingZone.RAPID
                zone_size = random.randint(8, 15)

            zone_size = min(zone_size, num_outputs - outputs_allocated)

            zones.append({
                "type": zone_type,
                "num_cues": zone_size,
                "intensity": intensity
            })

            outputs_allocated += zone_size
            progress = outputs_allocated / num_outputs

        outputs_used = 0
        for zone in zones:
            if outputs_used >= num_outputs:
                break

            zone_cues = self._generate_zone_cues(
                zone, type_counts, enabled_effects,
                num_outputs - outputs_used, "finale"
            )
            cues.extend(zone_cues)
            outputs_used += len([c for c in zone_cues if not c.get("skip_count", False)])

        self._assign_professional_timing(cues, zones, duration, "false_finale")

        return [c for c in cues if isinstance(c, CueData)]

    def _generate_gap_section(self, num_outputs: int, duration: float) -> List[CueData]:
        """Generate the gap section - dramatic silence with 1-3 scattered singles"""
        cues = []

        if num_outputs == 0:
            self.current_time += duration
            return cues

        time_per_shot = duration / num_outputs if num_outputs > 0 else duration

        for i in range(num_outputs):
            if self.output_index >= len(self.all_outputs):
                break

            output = self.all_outputs[self.output_index]
            self.used_outputs.add(output)
            self.output_index += 1

            shot_time = self.current_time + (i * time_per_shot) + random.uniform(1.0, 2.0)

            cue = CueData(
                cue_number=self.current_cue_number,
                cue_type="SINGLE SHOT",
                outputs=str(output),
                delay=0.0,
                execute_time=self._format_time(shot_time),
                zone_type=TimingZone.PAUSE
            )

            cues.append(cue)
            self.current_cue_number += 1

        self.current_time += duration

        return cues

    def _generate_real_finale_section(self, num_outputs: int, duration: float,
                                      shot_types: Dict, enabled_effects: List[str]) -> List[CueData]:
        """Generate the real finale section - explosive spectacular finish"""
        cues = []
        type_counts = self._calculate_shot_type_distribution(shot_types, num_outputs)

        zones = []
        outputs_allocated = 0
        progress = 0.0

        while outputs_allocated < num_outputs:
            intensity = 2.5 + (progress * 0.5)

            if random.random() < 0.7:
                zone_type = TimingZone.BURST
                zone_size = random.randint(8, 15)
            else:
                zone_type = TimingZone.RAPID
                zone_size = random.randint(10, 20)

            zone_size = min(zone_size, num_outputs - outputs_allocated)

            zones.append({
                "type": zone_type,
                "num_cues": zone_size,
                "intensity": intensity
            })

            outputs_allocated += zone_size
            progress = outputs_allocated / num_outputs

        outputs_used = 0
        for zone in zones:
            if outputs_used >= num_outputs:
                break

            zone_cues = self._generate_zone_cues(
                zone, type_counts, enabled_effects,
                num_outputs - outputs_used, "finale"
            )
            cues.extend(zone_cues)
            outputs_used += len([c for c in zone_cues if not c.get("skip_count", False)])

        self._assign_professional_timing(cues, zones, duration, "real_finale")

        return [c for c in cues if isinstance(c, CueData)]

    def _calculate_shot_type_distribution(self, shot_types: Dict, total_outputs: int) -> Dict:
        """Calculate output allocation for each shot type"""
        distribution = {}

        for shot_type, config in shot_types.items():
            if config.get("checkbox", False):
                percentage = config.get("percentage", 0)
                count = int(total_outputs * (percentage / 100.0))
                distribution[shot_type] = count

        return distribution

    def _create_professional_timing_zones(self, act_name: str,
                                          num_outputs: int,
                                          duration: float) -> List[Dict]:
        """Create timing zones with intensity progression"""
        zones = []
        outputs_allocated = 0
        progress = 0.0

        while outputs_allocated < num_outputs:
            # Calculate current intensity
            intensity = IntensityCurve.calculate_act_intensity(act_name, progress)

            # Get zone probabilities based on intensity
            zone_probs = IntensityCurve.get_zone_probabilities(act_name, intensity)

            # Select zone type
            zone_type = random.choices(
                list(zone_probs.keys()),
                weights=list(zone_probs.values())
            )[0]

            # Determine zone size
            zone_size = self._calculate_zone_size(zone_type, num_outputs - outputs_allocated)

            zones.append({
                "type": zone_type,
                "num_cues": zone_size,
                "intensity": intensity
            })

            outputs_allocated += zone_size
            progress = outputs_allocated / num_outputs

        return zones

    def _calculate_zone_size(self, zone_type: TimingZone, remaining: int) -> int:
        """Calculate appropriate size for a timing zone"""
        if zone_type == TimingZone.BURST:
            size = random.randint(3, 8)
        elif zone_type == TimingZone.PAUSE:
            size = 1
        elif zone_type == TimingZone.RAPID:
            size = random.randint(5, 15)
        elif zone_type == TimingZone.MODERATE:
            size = random.randint(8, 20)
        else:  # SLOW
            size = random.randint(3, 10)

        return min(size, remaining)

    def _generate_zone_cues(self, zone: Dict, type_counts: Dict,
                            enabled_effects: List[str], remaining: int,
                            act_name: str) -> List[Dict]:
        """Generate cues for a timing zone"""
        cues = []
        target_outputs = min(zone["num_cues"], remaining)
        intensity = zone.get("intensity", 1.0)
        outputs_used = 0

        # Generate cues until we've used target_outputs
        while outputs_used < target_outputs:
            # Select shot type
            shot_type = self._select_shot_type(type_counts)

            if shot_type == "SINGLE SHOT":
                cue = self._create_single_shot()
                cue["zone_type"] = zone["type"]
                cue["intensity"] = intensity
                cues.append(cue)
                outputs_used += 1

            elif shot_type == "DOUBLE SHOT":
                if target_outputs - outputs_used >= 2:
                    double_cues = self._create_double_shot()
                    for dc in double_cues:
                        dc["zone_type"] = zone["type"]
                        dc["intensity"] = intensity
                    cues.extend(double_cues)
                    outputs_used += 2
                else:
                    # Not enough room for double, make single
                    cue = self._create_single_shot()
                    cue["zone_type"] = zone["type"]
                    cue["intensity"] = intensity
                    cues.append(cue)
                    outputs_used += 1

            elif shot_type == "SPECIAL EFFECTS":
                if enabled_effects and target_outputs - outputs_used >= 3:
                    # Select effect with better distribution (avoid too much chase)
                    effect = self._select_effect_with_variety(enabled_effects, cues)
                    pattern = SpecialEffectPatterns.PATTERNS.get(effect, {})

                    min_out = pattern.get("min_outputs", 3)
                    max_out = pattern.get("max_outputs", 6)
                    remaining_in_zone = target_outputs - outputs_used
                    seq_length = min(random.randint(min_out, max_out), remaining_in_zone)

                    if seq_length >= min_out:
                        effect_cues = self._create_special_effect(effect, seq_length, intensity)
                        for ec in effect_cues:
                            ec["zone_type"] = zone["type"]
                        cues.extend(effect_cues)
                        outputs_used += seq_length
                    else:
                        # Not enough for effect, make single
                        cue = self._create_single_shot()
                        cue["zone_type"] = zone["type"]
                        cue["intensity"] = intensity
                        cues.append(cue)
                        outputs_used += 1
                else:
                    # No effects or not enough room
                    cue = self._create_single_shot()
                    cue["zone_type"] = zone["type"]
                    cue["intensity"] = intensity
                    cues.append(cue)
                    outputs_used += 1

        return cues

    def _select_shot_type(self, type_counts: Dict) -> str:
        """Select shot type based on remaining counts"""
        available = [t for t, c in type_counts.items() if c > 0]

        if not available:
            return "SINGLE SHOT"

        # Weight by remaining count
        weights = [type_counts[t] for t in available]
        total_weight = sum(weights)

        if total_weight == 0:
            return random.choice(available) if available else "SINGLE SHOT"

        selected = random.choices(available, weights=weights)[0]
        type_counts[selected] -= 1

        return selected

    def _select_effect_with_variety(self, enabled_effects: List[str], recent_cues: List[Dict]) -> str:
        """
        Select an effect with variety - avoid repeating same effect too much
        Reduces chase dominance by tracking recent effects
        """
        if not enabled_effects:
            return "Chase"

        # Look at last 10 cues to see what effects were used
        recent_effects = []
        for cue in recent_cues[-10:]:
            if isinstance(cue, dict) and cue.get("effect"):
                recent_effects.append(cue["effect"])

        # Count recent effect usage
        effect_counts = {effect: recent_effects.count(effect) for effect in enabled_effects}

        # If Chase has been used a lot recently, reduce its probability
        if "Chase" in effect_counts and effect_counts["Chase"] >= 2:
            # Remove Chase temporarily if it's been used 2+ times in last 10 cues
            available = [e for e in enabled_effects if e != "Chase"]
            if available:
                return random.choice(available)

        # Otherwise, prefer effects that haven't been used recently
        min_count = min(effect_counts.values()) if effect_counts else 0
        least_used = [e for e, c in effect_counts.items() if c == min_count]

        return random.choice(least_used) if least_used else random.choice(enabled_effects)

    def _create_single_shot(self) -> Dict:
        """Create a single shot cue"""
        if self.output_index >= len(self.all_outputs):
            self.output_index = len(self.all_outputs) - 1

        output = self.all_outputs[self.output_index]
        self.used_outputs.add(output)
        self.output_index += 1

        return {
            "type": "SINGLE SHOT",
            "outputs": [output],
            "timing_delay": None
        }

    def _create_double_shot(self) -> List[Dict]:
        """Create double shot (2 simultaneous singles)"""
        cues = []

        for i in range(2):
            if self.output_index >= len(self.all_outputs):
                break

            output = self.all_outputs[self.output_index]
            self.used_outputs.add(output)
            self.output_index += 1

            cues.append({
                "type": "SINGLE SHOT",
                "outputs": [output],
                "timing_delay": None,
                "simultaneous": i > 0  # Second cue is simultaneous
            })

        return cues

    def _create_special_effect(self, effect_name: str, num_outputs: int,
                               intensity: float) -> List[Dict]:
        """Create special effect sequence"""
        cues = []
        delays = SpecialEffectPatterns.generate_effect_delays(
            effect_name, num_outputs, intensity
        )

        for i in range(num_outputs):
            if self.output_index >= len(self.all_outputs):
                break

            output = self.all_outputs[self.output_index]
            self.used_outputs.add(output)
            self.output_index += 1

            cues.append({
                "type": "SINGLE SHOT",
                "outputs": [output],
                "timing_delay": delays[i] if i < len(delays) else 0.5,
                "effect": effect_name
            })

        return cues

    def _assign_professional_timing(self, cues: List[Dict], zones: List[Dict],
                                    duration: float, act_name: str):
        """Assign execution times with professional pacing"""
        if not cues:
            return

        # Start from current global time
        local_time = 0.0
        cue_index = 0

        for zone in zones:
            zone_type = zone["type"]
            num_cues = zone["num_cues"]
            intensity = zone.get("intensity", 1.0)

            # Get delay range for zone
            delay_range = self._get_zone_delay_range(zone_type, intensity)

            # Process cues in zone
            for i in range(num_cues):
                if cue_index >= len(cues):
                    break

                cue = cues[cue_index]

                # Create CueData object
                # IMPORTANT: delay is ALWAYS 0.0 for single shots
                # Timing differences come from execute_time values
                cue_data = CueData(
                    cue_number=self.current_cue_number,
                    cue_type=cue["type"],
                    outputs=", ".join(str(o) for o in cue["outputs"]),
                    delay=0.0,  # Always 0.0 for single shots!
                    execute_time=self._format_time(self.current_time + local_time),
                    zone_type=zone_type
                )

                # Replace dict with CueData
                cues[cue_index] = cue_data
                self.current_cue_number += 1
                cue_index += 1

                # Calculate delay to next cue (for execute_time spacing)
                if cue_index < len(cues):
                    next_cue = cues[cue_index]

                    if isinstance(next_cue, dict) and next_cue.get("simultaneous", False):
                        # Double shot - no delay between simultaneous cues
                        delay = 0.0
                    elif isinstance(cue, dict) and cue.get("effect"):
                        # Special effect - use the effect's timing pattern
                        delay = cue.get("timing_delay", random.uniform(*delay_range))
                    else:
                        # Regular single shot - use zone timing
                        delay = random.uniform(*delay_range)

                    local_time += delay

        # Handle remaining cues
        while cue_index < len(cues):
            cue = cues[cue_index]
            if isinstance(cue, dict):
                cue_data = CueData(
                    cue_number=self.current_cue_number,
                    cue_type=cue["type"],
                    outputs=", ".join(str(o) for o in cue["outputs"]),
                    delay=0.0,
                    execute_time=self._format_time(self.current_time + local_time)
                )
                cues[cue_index] = cue_data
                self.current_cue_number += 1
            cue_index += 1
            local_time += 0.5

        # Scale timing to match target duration
        if local_time > 0 and duration > 0:
            scale_factor = duration / local_time

            # Rescale all cue times in this act
            for cue in cues:
                if isinstance(cue, CueData):
                    # Parse current time
                    current_seconds = self._parse_time(cue.execute_time)
                    # Get time relative to act start
                    relative_time = current_seconds - self.current_time
                    # Scale it
                    scaled_relative = relative_time * scale_factor
                    # Set new absolute time
                    cue.execute_time = self._format_time(self.current_time + scaled_relative)

        # Update global time by target duration (not actual generated time)
        self.current_time += duration

    def _get_zone_delay_range(self, zone_type: TimingZone, intensity: float) -> Tuple[float, float]:
        """Get delay range for zone type adjusted by intensity"""
        base_ranges = {
            TimingZone.BURST: (0.1, 0.3),
            TimingZone.RAPID: (0.3, 0.8),
            TimingZone.MODERATE: (0.8, 2.0),
            TimingZone.SLOW: (2.0, 4.0),
            TimingZone.PAUSE: (3.0, 6.0)
        }

        base_min, base_max = base_ranges.get(zone_type, (0.5, 1.5))

        # Adjust by intensity (higher intensity = faster)
        adjusted_min = base_min / intensity
        adjusted_max = base_max / intensity

        return (max(0.05, adjusted_min), max(0.1, adjusted_max))

    def _validate_and_adjust(self):
        """Validate show and make adjustments"""
        print("\n   Validating output usage...")
        output_validation = ShowValidator.validate_output_usage(self.cues, self.total_outputs)

        if output_validation["valid"]:
            print(f"   ✅ All {self.total_outputs} outputs used correctly")
        else:
            print(f"   ⚠️  Output usage issues:")
            print(f"      Used: {output_validation['used_count']}/{output_validation['target_count']}")
            if output_validation["missing"]:
                print(f"      Missing: {len(output_validation['missing'])} outputs")
            if output_validation["duplicates"]:
                print(f"      Duplicates: {len(output_validation['duplicates'])} outputs")

        print("\n   Validating timing...")
        timing_validation = ShowValidator.validate_timing(self.cues, self.total_duration)

        if timing_validation["valid"]:
            print(f"   ✅ Timing validated")
        else:
            print(f"   ⚠️  Timing issues detected")

        print(f"      Current duration: {timing_validation['final_duration']:.1f}s")
        print(f"      Target duration: {timing_validation['target_duration']:.1f}s")
        print(f"      Difference: {timing_validation['duration_diff']:.1f}s")

        # Adjust timing if needed
        if timing_validation["duration_diff"] > 2.0:
            print("\n   🔧 Adjusting timing to match target duration...")
            self._adjust_timing_to_target()

    def _adjust_timing_to_target(self):
        """Adjust all timing to match target duration precisely"""
        if not self.cues:
            return

        current_duration = self._get_total_duration()
        if current_duration == 0:
            return

        scale_factor = self.total_duration / current_duration

        print(f"      Scale factor: {scale_factor:.4f}")

        # Scale all execution times
        for cue in self.cues:
            current_seconds = self._parse_time(cue.execute_time)
            new_seconds = current_seconds * scale_factor
            cue.execute_time = self._format_time(new_seconds)

        final_duration = self._get_total_duration()
        print(f"      Adjusted duration: {final_duration:.1f}s")

    def _final_verification(self):
        """Final verification and reporting"""
        # Output usage
        used_outputs = len(self.used_outputs)
        print(f"   Outputs Used: {used_outputs}/{self.total_outputs}")

        # Duration
        final_duration = self._get_total_duration()
        print(f"   Final Duration: {final_duration:.1f}s ({final_duration / 60:.2f} min)")
        print(f"   Target Duration: {self.total_duration:.1f}s ({self.total_duration / 60:.2f} min)")
        print(f"   Difference: {abs(final_duration - self.total_duration):.1f}s")

        # Cue count
        print(f"   Total Cues: {len(self.cues)}")

        # Act breakdown
        print(f"\n   Act Breakdown:")
        for metrics in self.act_metrics:
            print(f"      {metrics.name.upper()}:")
            print(f"         Cues: {metrics.num_cues}")
            print(f"         Outputs: {metrics.actual_outputs}/{metrics.target_outputs}")
            print(f"         Duration: {metrics.actual_duration:.1f}s/{metrics.target_duration:.1f}s")
            print(
                f"         Time Range: {self._format_time(metrics.start_time)} → {self._format_time(metrics.end_time)}")

    def _get_total_duration(self) -> float:
        """Get total show duration in seconds"""
        if not self.cues:
            return 0.0

        last_time = self._parse_time(self.cues[-1].execute_time)
        return last_time

    def _parse_time(self, time_str: str) -> float:
        """Parse MM:SS.SSSSSSSS to seconds"""
        parts = time_str.split(":")
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds

    def _format_time(self, seconds: float) -> str:
        """Format seconds as MM:SS.SSSSSSSS"""
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes:02d}:{secs:011.8f}"