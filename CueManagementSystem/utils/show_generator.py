import random
import math
import traceback
import time
from typing import List, Dict, Any, Tuple, Optional, Set
from datetime import timedelta
from PySide6.QtWidgets import QTableWidgetItem
from CueManagementSystem.utils.show_enums import ShowSection, EffectSequence, ShowStyle, RhythmPattern, ComplexityLevel


class ShowGenerator:
    """
    Generator for creating firework shows based on user parameters
    Handles the creation of cues based on specified parameters from the dialog
    """

    # HARDCODED CORE REQUIREMENTS FROM CSV FILES
    # ==========================================

    # DELAY BETWEEN CUES (increments of 0.25 seconds) - FROM CSV
    DELAY_BETWEEN_CUES = {
        "opening": {"min": 1.0, "max": 4.0, "increment": 0.25},
        "buildup": {"min": 1.0, "max": 3.0, "increment": 0.25},
        "false_finale": {"min": 1.0, "max": 2.0, "increment": 0.25},
        "finale": {"min": 0.5, "max": 1.0, "increment": 0.25}
    }

    # DELAY BETWEEN OUTPUTS FOR RUN TYPES (increments of 0.125 seconds) - FROM CSV
    RUN_DELAY_RANGES = {
        "opening": {"min": 0.5, "max": 1.0, "increment": 0.125},
        "buildup": {"min": 0.375, "max": 0.875, "increment": 0.125},
        "false_finale": {"min": 0.25, "max": 0.75, "increment": 0.125},
        "finale": {"min": 0.125, "max": 0.5, "increment": 0.125}
    }

    # SINGLE RUN TYPES (# of outputs per chain per cue) - FROM CSV
    SINGLE_RUN_OUTPUTS = {
        "opening": {"min": 1, "max": 4},
        "buildup": {"min": 1, "max": 6},
        "false_finale": {"min": 1, "max": 8},
        "finale": {"min": 1, "max": 10}
    }

    # DOUBLE RUN TYPES (# of pairs of outputs per chain per cue) - FROM CSV
    DOUBLE_RUN_OUTPUTS = {
        "opening": {"min": 1, "max": 1},  # N/A - using 1 as placeholder
        "buildup": {"min": 1, "max": 4},
        "false_finale": {"min": 1, "max": 5},
        "finale": {"min": 1, "max": 6}
    }

    # SPECIAL EFFECTS PATTERNS - FROM CSV
    SPECIAL_EFFECTS_PATTERNS = {
        "rock_ballad": {
            "description": "Mimic the drum pattern of a rock and roll ballad",
            "rhythm_pattern": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0],
            "delay_pattern": [1.0, 0.5, 0.75, 0.5]
        },
        "metal_ballad": {
            "description": "Mimic the drum pattern of a melodic metal ballad",
            "rhythm_pattern": [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0],
            "delay_pattern": [0.5, 0.25, 0.5, 0.25]
        },
        "trot": {
            "description": "Mimic the pattern of a horse trotting",
            "rhythm_pattern": [1, 0, 1, 0, 1, 0, 1, 0],
            "delay_pattern": [0.75, 0.75, 0.75, 0.75]
        },
        "gallop": {
            "description": "Mimic the pattern of a horse galloping",
            "rhythm_pattern": [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0],
            "delay_pattern": [0.25, 0.25, 0.5, 0.25, 0.25, 0.5]
        },
        "step": {
            "description": "Mimic the pattern of someone taking one step at a time",
            "rhythm_pattern": [1, 0, 0, 0, 1, 0, 0, 0],
            "delay_pattern": [1.0, 0.5, 1.0, 0.5]
        },
        "chase": {
            "description": "Simple chase pattern with consistent delays",
            "rhythm_pattern": [1, 0, 1, 0, 1, 0, 1, 0],
            "delay_pattern": [0.5, 0.5, 0.5, 0.5]
        },
        "random": {
            "description": "Random pattern with varied delays",
            "rhythm_pattern": None,
            "delay_pattern": None
        },
        "false_finale": {
            "description": "Short and intense burst leading audience to believe it's the true finale",
            "rhythm_pattern": [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0],
            "delay_pattern": [0.125, 0.125, 0.125, 0.125, 0.125, 0.5, 0.125, 0.125, 0.125, 0.125, 0.125, 0.5]
        }
    }

    # Define delay ranges for run types (in seconds)
    RUN_DELAY_RANGES = {
        "opening": {"min": 0.5, "max": 1.0, "increment": 0.125},
        "buildup": {"min": 0.375, "max": 0.875, "increment": 0.125},
        "false_finale": {"min": 0.25, "max": 0.75, "increment": 0.125},
        "finale": {"min": 0.125, "max": 0.5, "increment": 0.125}
    }

    # Define output counts for run types
    SINGLE_RUN_OUTPUTS = {
        "opening": {"min": 1, "max": 4},
        "buildup": {"min": 1, "max": 6},
        "false_finale": {"min": 1, "max": 8},
        "finale": {"min": 1, "max": 10}
    }

    # Define output pair counts for double run types
    DOUBLE_RUN_OUTPUTS = {
        "opening": {"min": 1, "max": 1},  # N/A in spreadsheet, using 1 as default
        "buildup": {"min": 1, "max": 4},
        "false_finale": {"min": 1, "max": 5},
        "finale": {"min": 1, "max": 6}
    }

    # Define rhythm patterns for special effects
    RHYTHM_PATTERNS = {
        "rock_ballad": {
            "description": "Mimic the drum pattern of a rock and roll ballad",
            "pattern": [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 1, 0, 1, 0, 0, 0],  # Basic rock beat
            "delay_multipliers": [1.0, 0.5, 0.75, 0.5]  # Varied delays for rock feel
        },
        "metal_ballad": {
            "description": "Mimic the drum pattern of a melodic metal ballad",
            "pattern": [1, 0, 1, 0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1, 0],  # More intense pattern
            "delay_multipliers": [0.5, 0.25, 0.5, 0.25]  # Faster delays for metal feel
        },
        "trot": {
            "description": "Mimic the pattern of a horse trotting",
            "pattern": [1, 0, 1, 0, 1, 0, 1, 0],  # Even pattern
            "delay_multipliers": [0.75, 0.75, 0.75, 0.75]  # Consistent delays
        },
        "gallop": {
            "description": "Mimic the pattern of a horse galloping",
            "pattern": [1, 0, 1, 1, 0, 0, 1, 0, 1, 1, 0, 0],  # Gallop rhythm
            "delay_multipliers": [0.25, 0.25, 0.5, 0.25, 0.25, 0.5]  # Quick triplet feel
        },
        "step": {
            "description": "Mimic the pattern of someone taking one step at a time",
            "pattern": [1, 0, 0, 0, 1, 0, 0, 0],  # Step pattern
            "delay_multipliers": [1.0, 0.5, 1.0, 0.5]  # Alternating delays
        },
        "chase": {
            "description": "Simple chase pattern with consistent delays",
            "pattern": [1, 0, 1, 0, 1, 0, 1, 0],  # Even pattern
            "delay_multipliers": [0.5, 0.5, 0.5, 0.5]  # Consistent delays
        },
        "random": {
            "description": "Random pattern with varied delays",
            "pattern": None,  # Will be generated dynamically
            "delay_multipliers": None  # Will be generated dynamically
        }
    }

    # Maximum number of generation attempts
    MAX_GENERATION_ATTEMPTS = 5

    # Maximum time to spend generating (in seconds)
    MAX_GENERATION_TIME = 10

    def __init__(self):
        """Initialize the show generator"""
        # Used to track which outputs have been used
        self.used_outputs = set()

        # Used to track the current time position in the show
        self.current_time_seconds = 0.0

        # Used to track cue numbers
        self.current_cue_number = 1

        # Store generated cues
        self.cues = []

        # Store act configuration from dialog
        self.act_config = None

        # Store whether cues should be sequential or random
        self.sequential_cues = True

        # Store all available outputs (1 to total_outputs)
        self.all_outputs = []

        # Store output allocation for each act
        self.act_outputs = {}

        # Store output allocation for each shot type within each act
        self.shot_type_outputs = {}

        # Store total outputs
        self.total_outputs = 0

        # Store total duration
        self.total_duration = 0

        # Store generation statistics
        self.generation_attempts = 0
        self.generation_start_time = 0

        # Debug mode
        self.debug = True

        # Initialize constants as instance attributes
        self.DELAY_BETWEEN_CUES = {
            1: {"min": 3, "max": 5, "increment": 0.25},  # Act 1: 3-5 seconds between cues
            2: {"min": 4, "max": 7, "increment": 0.25},  # Act 2: 4-7 seconds between cues
            3: {"min": 2, "max": 4, "increment": 0.25},  # Act 3: 2-4 seconds between cues
            4: {"min": 3, "max": 6, "increment": 0.25},  # Act 4: 3-6 seconds between cues
            5: {"min": 4, "max": 8, "increment": 0.25},  # Act 5: 4-8 seconds between cues
            "opening": {"min": 3, "max": 5, "increment": 0.25},
            "buildup": {"min": 4, "max": 7, "increment": 0.25},
            "false_finale": {"min": 3, "max": 5, "increment": 0.25},
            "finale": {"min": 2, "max": 4, "increment": 0.25}
        }

        # Define delay ranges for run types (in seconds)
        self.RUN_DELAY_RANGES = {
            "opening": {"min": 0.5, "max": 1.0, "increment": 0.125},
            "buildup": {"min": 0.375, "max": 0.875, "increment": 0.125},
            "false_finale": {"min": 0.25, "max": 0.75, "increment": 0.125},
            "finale": {"min": 0.125, "max": 0.5, "increment": 0.125}
        }

        # Define output counts for run types
        self.SINGLE_RUN_OUTPUTS = {
            "opening": {"min": 1, "max": 4},
            "buildup": {"min": 1, "max": 6},
            "false_finale": {"min": 2, "max": 8},
            "finale": {"min": 3, "max": 10}
        }

        self.DOUBLE_RUN_OUTPUTS = {
            "opening": {"min": 2, "max": 8},
            "buildup": {"min": 4, "max": 12},
            "false_finale": {"min": 6, "max": 16},
            "finale": {"min": 8, "max": 20}
        }

        # Define rhythm patterns for special effects
        self.RHYTHM_PATTERNS = {
            "opening_buildup": {
                "description": "Gradual increase in intensity to build excitement",
                "rhythm_pattern": [1, 0, 0, 1, 0, 1, 0, 1, 1, 0, 1, 1, 1, 0, 1, 1],
                "delay_pattern": [0.5, 0.5, 0.5, 0.5, 0.5, 0.375, 0.375, 0.375, 0.375, 0.375, 0.25, 0.25, 0.25, 0.25,
                                  0.125, 0.125]
            },
            "finale_climax": {
                "description": "Rapid-fire sequence for maximum impact at show finale",
                "rhythm_pattern": [1, 1, 1, 0, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 1, 1],
                "delay_pattern": [0.125, 0.125, 0.125, 0.25, 0.125, 0.125, 0.125, 0.25, 0.125, 0.125, 0.125, 0.125,
                                  0.125, 0.125, 0.125, 0.125]
            },
            "false_finale": {
                "description": "Short and intense burst leading audience to believe it's the true finale",
                "rhythm_pattern": [1, 1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 0],
                "delay_pattern": [0.125, 0.125, 0.125, 0.125, 0.125, 0.5, 0.125, 0.125, 0.125, 0.125, 0.125, 0.5]
            }
        }

        # Maximum attempts and time for generation
        self.MAX_GENERATION_ATTEMPTS = 5
        self.MAX_GENERATION_TIME = 10

    def generate_random_show(self, config_data) -> List[List]:
        """
        Generate a show based on configuration data from the dialog

        Args:
            config_data: ShowConfigData instance with show parameters

        Returns:
            List of formatted cues ready to be added to the cue table
        """
        # Start generation timer
        self.generation_start_time = time.time()

        # Reset state for new generation
        self.used_outputs = set()
        self.current_time_seconds = 0.0
        self.current_cue_number = 1
        self.cues = []
        self.generation_attempts = 0

        # Extract configuration parameters
        self.total_duration = config_data.total_seconds
        self.total_outputs = config_data.num_outputs

        # Get act configuration
        self.act_config = config_data.act_config

        # Get cue order preference
        self.sequential_cues = config_data.sequential_cues

        # Initialize all outputs
        self.all_outputs = list(range(1, self.total_outputs + 1))

        # Log configuration for debugging
        if self.debug:
            print(f"Generating show with {self.total_outputs} outputs over {self.total_duration} seconds")
            print(f"Sequential cues: {self.sequential_cues}")

        # Validate act configuration
        if not self._validate_act_configuration():
            print("Error: Invalid act configuration")
            return []

        # Allocate outputs to acts
        self._allocate_outputs_to_acts()

        # Allocate outputs to shot types within each act
        self._allocate_outputs_to_shot_types()

        # Generate cues with multiple attempts if needed
        best_cues = []
        best_score = -1

        while self.generation_attempts < self.MAX_GENERATION_ATTEMPTS:
            self.generation_attempts += 1

            # Check if we've exceeded the maximum generation time
            if time.time() - self.generation_start_time > self.MAX_GENERATION_TIME:
                if self.debug:
                    print(f"Exceeded maximum generation time ({self.MAX_GENERATION_TIME} seconds)")
                break

            # Reset state for this attempt
            self.used_outputs = set()  # Clear the used outputs tracking set for each attempt
            self.current_time_seconds = 0.0
            self.current_cue_number = 1
            self.cues = []

            # Generate cues for each act with interleaved shot types
            # Reset used_outputs before each act to prevent duplicates
            self.used_outputs = set()
            self._generate_interleaved_act_cues("opening")

            # Reset used_outputs before each act to prevent duplicates
            self.used_outputs = set()
            self._generate_interleaved_act_cues("buildup")

            # Reset used_outputs before each act to prevent duplicates
            self.used_outputs = set()
            self._generate_interleaved_act_cues("finale")

            # Sort cues by execution time
            self.cues.sort(key=lambda cue: self._time_to_seconds(cue[4]))

            # Reassign cue numbers to ensure they're sequential
            for i, cue in enumerate(self.cues):
                cue[0] = i + 1

            # Evaluate the quality of this generation
            score = self._evaluate_generation()

            if self.debug:
                print(f"Generation attempt {self.generation_attempts}: Score = {score}")

            # Keep the best generation
            if score > best_score:
                best_cues = self.cues.copy()
                best_score = score

                # If we have a perfect score, stop generating
                if score == 100:
                    if self.debug:
                        print("Perfect score achieved, stopping generation")
                    break

        # Use the best generation
        self.cues = best_cues

        # Verify the final generation
        self._verify_generation()

        return self.cues

    def _validate_act_configuration(self) -> bool:
        """
        Validate the act configuration to ensure it's valid

        Returns:
            True if the configuration is valid, False otherwise
        """
        if not self.act_config:
            print("Error: No act configuration provided")
            return False

        # Check if all required acts are present
        required_acts = ["opening", "buildup", "finale"]
        for act in required_acts:
            if act not in self.act_config:
                print(f"Error: Missing act configuration for {act}")
                return False

        # Check if percentages add up to 100%
        total_percentage = 0
        for act in required_acts:
            percentage = self.act_config[act].get("percentage", 0)
            total_percentage += percentage

        if abs(total_percentage - 100) > 0.01:  # Allow small floating point errors
            print(f"Warning: Act percentages add up to {total_percentage}%, not 100%")
            # We'll continue anyway, as the dialog should normalize this

        # Check if shot types are valid for each act
        for act in required_acts:
            shot_types = self.act_config[act].get("shot_types", {})

            # Check if any shot types are enabled
            enabled_types = [st for st, config in shot_types.items() if config.get("checkbox", False)]
            if not enabled_types:
                print(f"Warning: No shot types enabled for {act} act")
                # We'll continue anyway, as we'll handle this case in the generation

            # Check if percentages add up to 100% for enabled shot types
            total_percentage = 0
            for shot_type, config in shot_types.items():
                if config.get("checkbox", False):
                    percentage = config.get("percentage", 0)
                    total_percentage += percentage

            if enabled_types and abs(total_percentage - 100) > 0.01:  # Allow small floating point errors
                print(f"Warning: Shot type percentages for {act} act add up to {total_percentage}%, not 100%")
                # We'll continue anyway, as we'll normalize this in the generation

        return True

    def _allocate_outputs_to_acts(self):
        """Allocate outputs to acts based on act percentages ensuring no duplicates"""
        self.act_outputs = {}

        # Calculate exact output counts based on normalized percentages
        total_percentage = sum(self.act_config[act].get("percentage", 0) for act in ["opening", "buildup", "finale"])

        # Normalize to exactly 100%
        normalized_percentages = {}
        for act in ["opening", "buildup", "finale"]:
            percentage = self.act_config[act].get("percentage", 0)
            normalized_percentages[act] = (percentage / total_percentage) * 100

        # Calculate exact output counts
        act_outputs = {}
        total_allocated = 0

        for act in ["opening", "buildup", "finale"]:
            percentage = normalized_percentages[act]
            count = int(round((percentage / 100.0) * self.total_outputs))

            # Ensure we don't exceed total
            if act == "finale":
                # Finale gets remaining outputs to ensure exact total
                count = self.total_outputs - total_allocated

            act_outputs[act] = count
            total_allocated += count

        # Allocate specific output numbers ensuring no duplicates
        all_outputs = list(range(1, self.total_outputs + 1))

        if self.sequential_cues:
            # Sequential allocation: opening -> buildup -> finale
            current_idx = 0
            for act in ["opening", "buildup", "finale"]:
                count = act_outputs[act]
                self.act_outputs[act] = all_outputs[current_idx:current_idx + count]
                current_idx += count
        else:
            # Random allocation ensuring no duplicates
            remaining_outputs = all_outputs.copy()
            for act in ["opening", "buildup", "finale"]:
                count = act_outputs[act]
                selected = random.sample(remaining_outputs, count)
                self.act_outputs[act] = selected
                for output in selected:
                    remaining_outputs.remove(output)

        # Ensure exact allocation
        total_allocated = sum(len(outputs) for outputs in self.act_outputs.values())
        if total_allocated != self.total_outputs:
            print(f"ERROR: Allocated {total_allocated} outputs instead of {self.total_outputs}")
            # Fix by adjusting finale
            finale_outputs = self.act_outputs.get("finale", [])
            adjustment = self.total_outputs - total_allocated
            if adjustment != 0:
                print(f"Adjusting finale by {adjustment} outputs")
                # This should never happen with proper rounding

        if self.debug:
            for act, outputs in self.act_outputs.items():
                print(f"{act} act: {len(outputs)} outputs ({sorted(outputs)})")

    def _allocate_outputs_to_shot_types(self):
        """Allocate outputs to shot types within each act"""
        self.shot_type_outputs = {}

        for act, outputs in self.act_outputs.items():
            self.shot_type_outputs[act] = {}

            # Get shot types for this act
            shot_types = self.act_config[act].get("shot_types", {})

            # Get enabled shot types
            enabled_types = [st for st, config in shot_types.items() if config.get("checkbox", False)]

            # If no shot types are enabled, use SINGLE SHOT as default
            if not enabled_types:
                self.shot_type_outputs[act]["SINGLE SHOT"] = outputs.copy()
                continue

            # Calculate total percentage of enabled shot types
            total_percentage = 0
            for shot_type in enabled_types:
                percentage = shot_types[shot_type].get("percentage", 0)
                total_percentage += percentage

            # Normalize percentages if needed
            if abs(total_percentage - 100) > 0.01:  # Allow small floating point errors
                for shot_type in enabled_types:
                    shot_types[shot_type]["percentage"] = (shot_types[shot_type].get("percentage",
                                                                                     0) / total_percentage) * 100

            # Allocate outputs to shot types
            remaining_outputs = outputs.copy()

            for i, shot_type in enumerate(enabled_types):
                percentage = shot_types[shot_type].get("percentage", 0)

                # Calculate outputs for this shot type
                if i < len(enabled_types) - 1:
                    # For all shot types except the last one, calculate based on percentage
                    shot_type_output_count = int(round((percentage / 100.0) * len(outputs)))
                else:
                    # For the last shot type, use all remaining outputs
                    shot_type_output_count = len(remaining_outputs)

                # Ensure we don't exceed remaining outputs
                shot_type_output_count = min(shot_type_output_count, len(remaining_outputs))

                # Allocate outputs to this shot type
                if self.sequential_cues:
                    # Sequential allocation
                    self.shot_type_outputs[act][shot_type] = remaining_outputs[:shot_type_output_count]
                    remaining_outputs = remaining_outputs[shot_type_output_count:]
                else:
                    # Random allocation
                    self.shot_type_outputs[act][shot_type] = random.sample(remaining_outputs, shot_type_output_count)
                    # Remove allocated outputs from remaining_outputs
                    for output in self.shot_type_outputs[act][shot_type]:
                        remaining_outputs.remove(output)

            # Verify that all outputs for this act have been allocated
            total_allocated = sum(len(outputs) for outputs in self.shot_type_outputs[act].values())
            if total_allocated != len(self.act_outputs[act]):
                print(
                    f"Warning: Allocated {total_allocated} outputs for {act} act instead of {len(self.act_outputs[act])}")

            if self.debug:
                for shot_type, outputs in self.shot_type_outputs[act].items():
                    print(f"{act} act - {shot_type}: {len(outputs)} outputs ({sorted(outputs)})")

    def _generate_interleaved_act_cues(self, act_key: str):
        """
        Generate cues for a specific act with interleaved shot types

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')
        """
        if act_key not in self.act_config:
            print(f"Warning: No configuration found for {act_key} act")
            return

        if act_key not in self.shot_type_outputs:
            print(f"Warning: No outputs allocated for {act_key} act")
            return

        # Calculate start time and duration for this act
        act_percentage = self.act_config[act_key].get("percentage", 0)
        act_duration = (act_percentage / 100.0) * self.total_duration

        if act_key == "opening":
            act_start_time = 0.0
        elif act_key == "buildup":
            opening_percentage = self.act_config["opening"].get("percentage", 0)
            act_start_time = (opening_percentage / 100.0) * self.total_duration
        else:  # finale
            opening_percentage = self.act_config["opening"].get("percentage", 0)
            buildup_percentage = self.act_config["buildup"].get("percentage", 0)
            act_start_time = ((opening_percentage + buildup_percentage) / 100.0) * self.total_duration

        if self.debug:
            print(
                f"Generating {act_key} act: {len(self.act_outputs[act_key])} outputs over {act_duration:.2f} seconds (starting at {act_start_time:.2f}s)")

        # Get special effects configuration
        special_effects = self.act_config[act_key].get("special_effects", {})

        # Create a list of shot types with their outputs
        shot_type_list = []
        for shot_type, outputs in self.shot_type_outputs[act_key].items():
            if outputs:
                shot_config = self.act_config[act_key].get("shot_types", {}).get(shot_type, {})
                shot_type_list.append((shot_type, outputs, shot_config))

        # If no shot types, return
        if not shot_type_list:
            return

        # Calculate time segments for interleaving
        num_segments = 10  # Divide the act into 10 segments for interleaving
        segment_duration = act_duration / num_segments

        # Generate cues for each segment with interleaved shot types
        for segment in range(num_segments):
            segment_start_time = act_start_time + segment * segment_duration
            segment_end_time = segment_start_time + segment_duration

            # Shuffle shot types for this segment to randomize the order
            random.shuffle(shot_type_list)

            # Calculate outputs per shot type for this segment
            total_remaining_outputs = sum(len(outputs) for _, outputs, _ in shot_type_list)
            if total_remaining_outputs == 0:
                continue

            # Calculate segment outputs proportionally
            segment_outputs = {}
            for shot_type, outputs, _ in shot_type_list:
                # Calculate proportion of outputs for this shot type
                proportion = len(outputs) / total_remaining_outputs
                # Calculate outputs for this segment
                segment_output_count = max(1, int(round(proportion * total_remaining_outputs / num_segments)))
                # Ensure we don't exceed available outputs
                segment_output_count = min(segment_output_count, len(outputs))
                # Store segment outputs
                segment_outputs[shot_type] = segment_output_count

            # Generate cues for each shot type in this segment
            current_time = segment_start_time

            for shot_type, outputs, shot_config in shot_type_list:
                if shot_type not in segment_outputs or segment_outputs[shot_type] <= 0:
                    continue

                # Get outputs for this shot type in this segment
                output_count = segment_outputs[shot_type]
                segment_shot_outputs = outputs[:output_count]

                # Remove used outputs from the shot type's outputs
                self.shot_type_outputs[act_key][shot_type] = outputs[output_count:]

                # Update shot_type_list for the next segment
                shot_type_list = [(st, remaining_outputs, sc) for st, remaining_outputs, sc in shot_type_list if
                                  remaining_outputs]

                # Calculate duration for this shot type in this segment
                shot_duration = segment_duration * (output_count / sum(segment_outputs.values()))

                # Generate cues for this shot type
                shot_cues = self._generate_shot_type_cues(
                    act_key=act_key,
                    shot_type=shot_type,
                    outputs=segment_shot_outputs,
                    start_time=current_time,
                    duration=shot_duration,
                    shot_config=shot_config,
                    special_effects=special_effects
                )

                # Add cues to the list
                self.cues.extend(shot_cues)

                # Update current time
                if shot_cues:
                    # Find the latest cue time
                    latest_time = max([self._time_to_seconds(cue[4]) for cue in shot_cues])
                    current_time = latest_time + random.uniform(
                        self.DELAY_BETWEEN_CUES[act_key]["min"],
                        self.DELAY_BETWEEN_CUES[act_key]["max"]
                    )
                else:
                    # If no cues were generated, advance time by a small amount
                    current_time += self.DELAY_BETWEEN_CUES[act_key]["min"]

    def _generate_shot_type_cues(self, act_key: str, shot_type: str, outputs: List[int],
                                 start_time: float, duration: float, shot_config: Dict,
                                 special_effects: Dict) -> List[List]:
        """
        Generate cues for a specific shot type using all user parameters explicitly

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')
            shot_type: Type of shot ('SINGLE SHOT', 'DOUBLE SHOT', 'SINGLE RUN', 'DOUBLE RUN')
            outputs: List of outputs to use
            start_time: Start time in seconds
            duration: Duration in seconds
            shot_config: Configuration for this shot type
            special_effects: Special effects configuration

        Returns:
            List of cues
        """
        if not outputs:
            return []

        # IMPORTANT: We're NOT filtering outputs here anymore to ensure ALL outputs are used
        # This was causing the issue where many outputs were being skipped

        if not outputs:
            return []

        # Get user-configured delay ranges from shot_config
        min_delay = shot_config.get("min_delay", self.RUN_DELAY_RANGES[act_key]["min"])
        max_delay = shot_config.get("max_delay", self.RUN_DELAY_RANGES[act_key]["max"])

        # Check for special effects based on user selection
        effect_type = self._get_special_effect_type(special_effects)

        # Enhanced special effects handling
        if effect_type and len(outputs) >= 4:
            # Use exact percentages based on user configuration
            effect_percentage = 0.7  # 70% for effects as per requirements
            effect_output_count = int(len(outputs) * effect_percentage)
            regular_output_count = len(outputs) - effect_output_count

            effect_outputs = outputs[:effect_output_count]
            regular_outputs = outputs[effect_output_count:]

            # Generate effect sequence using hard-coded patterns
            effect_cues = self._generate_enhanced_effect_sequence(
                act_key=act_key,
                shot_type=shot_type,
                effect_type=effect_type,
                outputs=effect_outputs,
                start_time=start_time,
                duration=duration * effect_percentage,
                shot_config=shot_config,
                min_delay=min_delay,
                max_delay=max_delay
            )

            # Generate regular cues for remaining outputs
            regular_cues = self._generate_enhanced_regular_cues(
                act_key=act_key,
                shot_type=shot_type,
                outputs=regular_outputs,
                start_time=start_time + duration * effect_percentage,
                duration=duration * (1 - effect_percentage),
                shot_config=shot_config,
                min_delay=min_delay,
                max_delay=max_delay
            )

            return effect_cues + regular_cues
        else:
            # Generate regular cues using exact user parameters
            return self._generate_enhanced_regular_cues(
                act_key=act_key,
                shot_type=shot_type,
                outputs=outputs,
                start_time=start_time,
                duration=duration,
                shot_config=shot_config,
                min_delay=min_delay,
                max_delay=max_delay
            )

    def _get_special_effect_type(self, special_effects: Dict) -> Optional[str]:
        """
        Determine which special effect to use based on configuration

        Args:
            special_effects: Special effects configuration

        Returns:
            Effect type or None if no effect should be used
        """
        # Check if any special effects are enabled
        enabled_effects = []
        for effect, enabled in special_effects.items():
            if enabled:
                enabled_effects.append(effect)

        # If no effects are enabled, return None
        if not enabled_effects:
            return None

        # Select a random effect from enabled effects
        return random.choice(enabled_effects)

    def _generate_enhanced_effect_sequence(self, act_key: str, shot_type: str, effect_type: str,
                                           outputs: List[int], start_time: float, duration: float,
                                           shot_config: Dict = None, min_delay: float = None,
                                           max_delay: float = None) -> List[List]:
        """
        Generate an enhanced special effect sequence with user parameters

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')
            shot_type: Type of shot ('SINGLE SHOT', 'DOUBLE SHOT', 'SINGLE RUN', 'DOUBLE RUN')
            effect_type: Type of effect to generate
            outputs: List of outputs to use
            start_time: Start time in seconds
            duration: Duration in seconds
            shot_config: Configuration for the shot (optional)
            min_delay: Minimum delay between cues (optional)
            max_delay: Maximum delay between cues (optional)

        Returns:
            List of cues
        """
        # Use empty dict if shot_config is None
        if shot_config is None:
            shot_config = {}

        # If min_delay and max_delay are provided, update shot_config
        if min_delay is not None:
            shot_config = shot_config.copy()  # Create a copy to avoid modifying the original
            shot_config["min_delay"] = min_delay

        if max_delay is not None:
            shot_config = shot_config.copy() if "min_delay" not in shot_config else shot_config
            shot_config["max_delay"] = max_delay

        # Call the underlying implementation
        return self._generate_effect_sequence(act_key, shot_type, effect_type, outputs, start_time, duration,
                                              shot_config)

    def _generate_effect_sequence(self, act_key: str, shot_type: str, effect_type: str,
                                  outputs: List[int], start_time: float, duration: float,
                                  shot_config: Dict) -> List[List]:
        """
        Generate a special effect sequence

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')
            shot_type: Type of shot ('SINGLE SHOT', 'DOUBLE SHOT', 'SINGLE RUN', 'DOUBLE RUN')
            effect_type: Type of effect to generate
            outputs: List of outputs to use
            start_time: Start time in seconds
            duration: Duration in seconds
            shot_config: Configuration for this shot type

        Returns:
            List of cues
        """
        # IMPORTANT: We're NOT filtering outputs here anymore to ensure ALL outputs are used
        # This was causing the issue where many outputs were being skipped

        if not outputs:
            return []

        # Map effect type to rhythm pattern
        rhythm_key = None
        if effect_type == "Rock Ballad":
            rhythm_key = "rock_ballad"
        elif effect_type == "Metal Ballad":
            rhythm_key = "metal_ballad"
        elif effect_type == "Trot":
            rhythm_key = "trot"
        elif effect_type == "Gallop":
            rhythm_key = "gallop"
        elif effect_type == "Step":
            rhythm_key = "step"
        elif effect_type == "Chase":
            rhythm_key = "chase"
        elif effect_type == "Random":
            rhythm_key = "random"
        elif effect_type == "False Finale" and act_key == "finale":
            return self._generate_false_finale(
                act_key=act_key,
                shot_type=shot_type,
                outputs=outputs,
                start_time=start_time,
                duration=duration,
                shot_config=shot_config
            )

        # If no valid rhythm pattern, generate regular cues
        if not rhythm_key or rhythm_key not in self.RHYTHM_PATTERNS:
            return self._generate_regular_cues(
                act_key=act_key,
                shot_type=shot_type,
                outputs=outputs,
                start_time=start_time,
                duration=duration,
                shot_config=shot_config
            )

        # Get rhythm pattern
        rhythm_pattern = self.RHYTHM_PATTERNS[rhythm_key]

        # For random pattern, generate a random pattern
        if rhythm_key == "random":
            pattern = [random.choice([0, 1, 1, 1]) for _ in range(16)]  # 75% chance of 1, 25% chance of 0
            delay_multipliers = [random.uniform(0.25, 1.0) for _ in range(8)]
        else:
            pattern = rhythm_pattern["pattern"]
            delay_multipliers = rhythm_pattern["delay_multipliers"]

        # Generate cues based on rhythm pattern
        cues = []
        current_time = start_time

        # Calculate base delay between outputs
        if shot_type in ["SINGLE RUN", "DOUBLE RUN"]:
            # For run types, use the min/max delay from shot config
            min_delay = shot_config.get("min_delay", self.RUN_DELAY_RANGES[act_key]["min"])
            max_delay = shot_config.get("max_delay", self.RUN_DELAY_RANGES[act_key]["max"])
            base_delay = (min_delay + max_delay) / 2
        else:
            # For shot types, use the act's delay between cues
            base_delay = (self.DELAY_BETWEEN_CUES[act_key]["min"] + self.DELAY_BETWEEN_CUES[act_key]["max"]) / 2

        # Adjust base delay to fit all outputs within duration
        pattern_length = len(pattern)
        pattern_repeats = math.ceil(len(outputs) / sum(1 for p in pattern if p > 0))
        total_pattern_steps = pattern_length * pattern_repeats

        # Ensure we don't divide by zero
        if total_pattern_steps > 0:
            base_delay = min(base_delay, duration / total_pattern_steps)

        # Generate cues based on pattern
        pattern_index = 0
        outputs_index = 0

        while outputs_index < len(outputs) and current_time < start_time + duration:
            # Get pattern value for this step
            pattern_value = pattern[pattern_index % pattern_length]

            # Apply delay multiplier
            delay_multiplier = delay_multipliers[pattern_index % len(delay_multipliers)]
            step_delay = base_delay * delay_multiplier

            # If pattern value is 0, just advance time
            if pattern_value == 0:
                current_time += step_delay
                pattern_index += 1
                continue

            # Generate cue based on shot type
            if shot_type == "SINGLE SHOT":
                # Create cue
                cue = [
                    self.current_cue_number,
                    "SINGLE SHOT",
                    str(outputs[outputs_index]),
                    0,  # No delay for SINGLE SHOT
                    self._format_time(current_time)
                ]
                cues.append(cue)
                self.current_cue_number += 1
                self.used_outputs.add(outputs[outputs_index])  # Mark output as used
                outputs_index += 1

            elif shot_type == "DOUBLE SHOT" and outputs_index + 1 < len(outputs):
                # Create cue
                cue = [
                    self.current_cue_number,
                    "DOUBLE SHOT",
                    f"{outputs[outputs_index]}, {outputs[outputs_index + 1]}",
                    0,  # No delay for DOUBLE SHOT
                    self._format_time(current_time)
                ]
                cues.append(cue)
                self.current_cue_number += 1
                self.used_outputs.add(outputs[outputs_index])  # Mark first output as used
                self.used_outputs.add(outputs[outputs_index + 1])  # Mark second output as used
                outputs_index += 2

            elif shot_type == "SINGLE RUN":
                # Determine number of outputs for this run
                run_outputs = min(
                    random.randint(
                        self.SINGLE_RUN_OUTPUTS[act_key]["min"],
                        self.SINGLE_RUN_OUTPUTS[act_key]["max"]
                    ),
                    len(outputs) - outputs_index
                )

                # Ensure we have at least 2 outputs for a run
                run_outputs = max(2, run_outputs)

                if outputs_index + run_outputs <= len(outputs):
                    # Get outputs for this run
                    run_output_list = outputs[outputs_index:outputs_index + run_outputs]

                    # Create cue with all outputs in the chain
                    outputs_str = ", ".join(map(str, run_output_list))

                    # Get delay from shot config or use default
                    delay = random.uniform(
                        shot_config.get("min_delay", self.RUN_DELAY_RANGES[act_key]["min"]),
                        shot_config.get("max_delay", self.RUN_DELAY_RANGES[act_key]["max"])
                    )

                    # Round delay to nearest increment
                    increment = self.RUN_DELAY_RANGES[act_key]["increment"]
                    delay = round(delay / increment) * increment

                    cue = [
                        self.current_cue_number,
                        "SINGLE RUN",
                        outputs_str,
                        delay,
                        self._format_time(current_time)
                    ]
                    cues.append(cue)
                    self.current_cue_number += 1

                    # Mark outputs as used
                    for output in run_output_list:
                        self.used_outputs.add(output)

                    outputs_index += run_outputs
                else:
                    # Not enough outputs left for a run, create a single shot
                    cue = [
                        self.current_cue_number,
                        "SINGLE SHOT",
                        str(outputs[outputs_index]),
                        0,  # No delay for SINGLE SHOT
                        self._format_time(current_time)
                    ]
                    cues.append(cue)
                    self.current_cue_number += 1
                    self.used_outputs.add(outputs[outputs_index])  # Mark output as used
                    outputs_index += 1

            elif shot_type == "DOUBLE RUN" and outputs_index + 1 < len(outputs):
                # Determine number of output pairs for this run
                run_pairs = min(
                    random.randint(
                        self.DOUBLE_RUN_OUTPUTS[act_key]["min"],
                        self.DOUBLE_RUN_OUTPUTS[act_key]["max"]
                    ),
                    (len(outputs) - outputs_index) // 2
                )

                # Ensure we have at least 1 pair for a run
                run_pairs = max(1, run_pairs)

                if outputs_index + run_pairs * 2 <= len(outputs):
                    # Get all outputs for this run
                    run_outputs = outputs[outputs_index:outputs_index + run_pairs * 2]

                    # Format all outputs as a comma-separated list
                    outputs_str = ", ".join(map(str, run_outputs))

                    # Get delay from shot config or use default
                    delay = random.uniform(
                        shot_config.get("min_delay", self.RUN_DELAY_RANGES[act_key]["min"]),
                        shot_config.get("max_delay", self.RUN_DELAY_RANGES[act_key]["max"])
                    )

                    # Round delay to nearest increment
                    increment = self.RUN_DELAY_RANGES[act_key]["increment"]
                    delay = round(delay / increment) * increment

                    cue = [
                        self.current_cue_number,
                        "DOUBLE RUN",
                        outputs_str,
                        delay,
                        self._format_time(current_time)
                    ]
                    cues.append(cue)
                    self.current_cue_number += 1

                    # Mark outputs as used
                    for output in run_outputs:
                        self.used_outputs.add(output)

                    outputs_index += run_pairs * 2
                else:
                    # Not enough outputs left for a double run, create a double shot
                    cue = [
                        self.current_cue_number,
                        "DOUBLE SHOT",
                        f"{outputs[outputs_index]}, {outputs[outputs_index + 1]}",
                        0,  # No delay for DOUBLE SHOT
                        self._format_time(current_time)
                    ]
                    cues.append(cue)
                    self.current_cue_number += 1
                    self.used_outputs.add(outputs[outputs_index])  # Mark first output as used
                    self.used_outputs.add(outputs[outputs_index + 1])  # Mark second output as used
                    outputs_index += 2

            # Advance time and pattern index
            current_time += step_delay
            pattern_index += 1

        # If we have remaining outputs, add them as regular cues
        if outputs_index < len(outputs):
            remaining_outputs = outputs[outputs_index:]
            remaining_duration = max(0, start_time + duration - current_time)

            remaining_cues = self._generate_regular_cues(
                act_key=act_key,
                shot_type=shot_type,
                outputs=remaining_outputs,
                start_time=current_time,
                duration=remaining_duration,
                shot_config=shot_config
            )

            cues.extend(remaining_cues)

        return cues

    def _generate_false_finale(self, act_key: str, shot_type: str, outputs: List[int],
                               start_time: float, duration: float,
                               shot_config: Dict) -> List[List]:
        """
        Generate a false finale sequence

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')
            shot_type: Type of shot ('SINGLE SHOT', 'DOUBLE SHOT', 'SINGLE RUN', 'DOUBLE RUN')
            outputs: List of outputs to use
            start_time: Start time in seconds
            duration: Duration in seconds
            shot_config: Configuration for this shot type

        Returns:
            List of cues
        """
        # IMPORTANT: We're NOT filtering outputs here anymore to ensure ALL outputs are used
        # This was causing the issue where many outputs were being skipped

        if not outputs:
            return []

        # For false finale, we'll create a sequence with:
        # 1. Initial build-up (40% of outputs)
        # 2. Brief pause
        # 3. Intense finale (60% of outputs)

        cues = []

        # Calculate outputs for each part
        buildup_output_count = int(len(outputs) * 0.4)
        finale_output_count = len(outputs) - buildup_output_count

        buildup_outputs = outputs[:buildup_output_count]
        finale_outputs = outputs[buildup_output_count:]

        # Calculate durations
        buildup_duration = duration * 0.3
        pause_duration = 2.0  # 2 second pause
        finale_duration = duration - buildup_duration - pause_duration

        # Generate build-up cues
        buildup_cues = self._generate_regular_cues(
            act_key="false_finale",
            shot_type=shot_type,
            outputs=buildup_outputs,
            start_time=start_time,
            duration=buildup_duration,
            shot_config=shot_config
        )

        cues.extend(buildup_cues)

        # Generate finale cues with gallop pattern
        finale_cues = self._generate_effect_sequence(
            act_key="finale",
            shot_type=shot_type,
            effect_type="Gallop",
            outputs=finale_outputs,
            start_time=start_time + buildup_duration + pause_duration,
            duration=finale_duration,
            shot_config=shot_config
        )

        cues.extend(finale_cues)

        return cues

    def _generate_enhanced_regular_cues(self, act_key: str, shot_type: str, outputs: List[int],
                                        start_time: float, duration: float,
                                        shot_config: Dict, min_delay: float = None, max_delay: float = None) -> List[
        List]:
        """
        Generate enhanced regular cues with user parameters

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')
            shot_type: Type of shot ('single', 'double', etc.)
            outputs: List of outputs to use
            start_time: Start time for the cues
            duration: Duration for the cues
            shot_config: Configuration for the shot
            min_delay: Minimum delay between cues (optional)
            max_delay: Maximum delay between cues (optional)

        Returns:
            List of cues
        """
        # If min_delay and max_delay are provided, update shot_config
        if min_delay is not None:
            shot_config = shot_config.copy()  # Create a copy to avoid modifying the original
            shot_config["min_delay"] = min_delay

        if max_delay is not None:
            shot_config = shot_config.copy() if "min_delay" not in shot_config else shot_config
            shot_config["max_delay"] = max_delay

        # Pass updated shot_config to the underlying method
        return self._generate_regular_cues(act_key, shot_type, outputs, start_time, duration, shot_config)

    def _generate_regular_cues(self, act_key: str, shot_type: str, outputs: List[int],
                               start_time: float, duration: float,
                               shot_config: Dict) -> List[List]:
        """
        Generate regular cues without special effects

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')
            shot_type: Type of shot ('SINGLE SHOT', 'DOUBLE SHOT', 'SINGLE RUN', 'DOUBLE RUN')
            outputs: List of outputs to use
            start_time: Start time in seconds
            duration: Duration in seconds
            shot_config: Configuration for this shot type

        Returns:
            List of cues
        """
        if not outputs:
            return []

        # Filter out outputs that have already been used to prevent duplicates
        unused_outputs = [output for output in outputs if output not in self.used_outputs]

        # If all outputs have been used, return empty list
        if not unused_outputs:
            return []

        cues = []
        current_time = start_time

        # Calculate delay between cues
        min_delay = self.DELAY_BETWEEN_CUES[act_key]["min"]
        max_delay = self.DELAY_BETWEEN_CUES[act_key]["max"]

        # For run types, get delay range from shot config
        if shot_type in ["SINGLE RUN", "DOUBLE RUN"]:
            run_min_delay = shot_config.get("min_delay", self.RUN_DELAY_RANGES[act_key]["min"])
            run_max_delay = shot_config.get("max_delay", self.RUN_DELAY_RANGES[act_key]["max"])

        # Adjust delay to fit all cues within duration
        if shot_type == "SINGLE SHOT":
            # Each cue uses 1 output
            cues_needed = len(unused_outputs)
        elif shot_type == "DOUBLE SHOT":
            # Each cue uses 2 outputs
            cues_needed = math.ceil(len(unused_outputs) / 2)
        elif shot_type == "SINGLE RUN":
            # Estimate average outputs per run
            avg_outputs = (self.SINGLE_RUN_OUTPUTS[act_key]["min"] + self.SINGLE_RUN_OUTPUTS[act_key]["max"]) / 2
            cues_needed = math.ceil(len(unused_outputs) / avg_outputs)
        else:  # DOUBLE RUN
            # Estimate average output pairs per run
            avg_pairs = (self.DOUBLE_RUN_OUTPUTS[act_key]["min"] + self.DOUBLE_RUN_OUTPUTS[act_key]["max"]) / 2
            cues_needed = math.ceil(len(unused_outputs) / (avg_pairs * 2))

        # Ensure we don't divide by zero
        if cues_needed > 0:
            # Calculate time per cue to ensure we fit all cues within the duration
            time_per_cue = duration / cues_needed
            # Adjust delays to ensure all cues fit
            avg_delay = min(time_per_cue * 0.5, (min_delay + max_delay) / 2)
            min_delay = min(min_delay, avg_delay * 0.8)
            max_delay = min(max_delay, avg_delay * 1.2)

        # Generate cues
        outputs_index = 0
        max_iterations = len(unused_outputs) * 2  # Safety limit to prevent infinite loops
        iteration_count = 0

        while outputs_index < len(outputs) and iteration_count < max_iterations:
            if shot_type == "SINGLE SHOT":
                # Create cue
                cue = [
                    self.current_cue_number,
                    "SINGLE SHOT",
                    str(outputs[outputs_index]),
                    0,  # No delay for SINGLE SHOT
                    self._format_time(current_time)
                ]
                cues.append(cue)
                self.current_cue_number += 1
                self.used_outputs.add(outputs[outputs_index])  # Mark output as used
                outputs_index += 1

            elif shot_type == "DOUBLE SHOT" and outputs_index + 1 < len(outputs):
                # Create cue
                cue = [
                    self.current_cue_number,
                    "DOUBLE SHOT",
                    f"{outputs[outputs_index]}, {outputs[outputs_index + 1]}",
                    0,  # No delay for DOUBLE SHOT
                    self._format_time(current_time)
                ]
                cues.append(cue)
                self.current_cue_number += 1
                self.used_outputs.add(outputs[outputs_index])  # Mark first output as used
                self.used_outputs.add(outputs[outputs_index + 1])  # Mark second output as used
                outputs_index += 2

            elif shot_type == "SINGLE RUN":
                # Determine number of outputs for this run
                run_outputs = min(
                    random.randint(
                        self.SINGLE_RUN_OUTPUTS[act_key]["min"],
                        self.SINGLE_RUN_OUTPUTS[act_key]["max"]
                    ),
                    len(outputs) - outputs_index
                )

                # Ensure we have at least 2 outputs for a run
                run_outputs = max(2, run_outputs)

                if outputs_index + run_outputs <= len(outputs):
                    # Get outputs for this run
                    run_output_list = outputs[outputs_index:outputs_index + run_outputs]

                    # Create cue with all outputs in the chain
                    outputs_str = ", ".join(map(str, run_output_list))

                    # Get delay from shot config or use default
                    delay = random.uniform(
                        shot_config.get("min_delay", self.RUN_DELAY_RANGES[act_key]["min"]),
                        shot_config.get("max_delay", self.RUN_DELAY_RANGES[act_key]["max"])
                    )

                    # Round delay to nearest increment
                    increment = self.RUN_DELAY_RANGES[act_key]["increment"]
                    delay = round(delay / increment) * increment

                    cue = [
                        self.current_cue_number,
                        "SINGLE RUN",
                        outputs_str,
                        delay,
                        self._format_time(current_time)
                    ]
                    cues.append(cue)
                    self.current_cue_number += 1

                    # Mark outputs as used
                    for output in run_output_list:
                        self.used_outputs.add(output)

                    outputs_index += run_outputs
                else:
                    # Not enough outputs left for a run, create a single shot
                    cue = [
                        self.current_cue_number,
                        "SINGLE SHOT",
                        str(outputs[outputs_index]),
                        0,  # No delay for SINGLE SHOT
                        self._format_time(current_time)
                    ]
                    cues.append(cue)
                    self.current_cue_number += 1
                    self.used_outputs.add(outputs[outputs_index])  # Mark output as used
                    outputs_index += 1

            elif shot_type == "DOUBLE RUN" and outputs_index + 1 < len(outputs):
                # Determine number of output pairs for this run
                run_pairs = min(
                    random.randint(
                        self.DOUBLE_RUN_OUTPUTS[act_key]["min"],
                        self.DOUBLE_RUN_OUTPUTS[act_key]["max"]
                    ),
                    (len(outputs) - outputs_index) // 2
                )

                # Ensure we have at least 1 pair for a run
                run_pairs = max(1, run_pairs)

                if outputs_index + run_pairs * 2 <= len(outputs):
                    # Get all outputs for this run
                    run_outputs = outputs[outputs_index:outputs_index + run_pairs * 2]

                    # Format all outputs as a comma-separated list
                    outputs_str = ", ".join(map(str, run_outputs))

                    # Get delay from shot config or use default
                    delay = random.uniform(
                        shot_config.get("min_delay", self.RUN_DELAY_RANGES[act_key]["min"]),
                        shot_config.get("max_delay", self.RUN_DELAY_RANGES[act_key]["max"])
                    )

                    # Round delay to nearest increment
                    increment = self.RUN_DELAY_RANGES[act_key]["increment"]
                    delay = round(delay / increment) * increment

                    cue = [
                        self.current_cue_number,
                        "DOUBLE RUN",
                        outputs_str,
                        delay,
                        self._format_time(current_time)
                    ]
                    cues.append(cue)
                    self.current_cue_number += 1

                    # Mark outputs as used
                    for output in run_outputs:
                        self.used_outputs.add(output)

                    outputs_index += run_pairs * 2
                else:
                    # Not enough outputs left for a double run, create a double shot
                    cue = [
                        self.current_cue_number,
                        "DOUBLE SHOT",
                        f"{outputs[outputs_index]}, {outputs[outputs_index + 1]}",
                        0,  # No delay for DOUBLE SHOT
                        self._format_time(current_time)
                    ]
                    cues.append(cue)
                    self.current_cue_number += 1
                    self.used_outputs.add(outputs[outputs_index])  # Mark first output as used
                    self.used_outputs.add(outputs[outputs_index + 1])  # Mark second output as used
                    outputs_index += 2

            # Calculate delay to next cue
            delay = random.uniform(min_delay, max_delay)

            # Round delay to nearest increment
            increment = self.DELAY_BETWEEN_CUES[act_key]["increment"]
            # Safety check to prevent division by zero or very small values
            if increment > 0.001:  # Ensure increment is not too small
                delay = round(delay / increment) * increment
            else:
                delay = min_delay  # Fallback to minimum delay

            current_time += delay

            # Increment iteration counter to prevent infinite loops
            iteration_count += 1

        # If we have remaining outputs and we're out of time, add them at the end
        if outputs_index < len(outputs):
            remaining_outputs = outputs[outputs_index:]

            # If we hit the iteration limit, log a warning
            if iteration_count >= max_iterations:
                print(f"WARNING: Reached maximum iterations ({max_iterations}) in _generate_regular_cues. " +
                      f"Adding {len(remaining_outputs)} remaining outputs at the end.")

            if shot_type == "SINGLE SHOT":
                # Add remaining outputs as single shots at the end
                for output in remaining_outputs:
                    if output not in self.used_outputs:  # Only use outputs that haven't been used
                        cue = [
                            self.current_cue_number,
                            "SINGLE SHOT",
                            str(output),
                            0,  # No delay for SINGLE SHOT
                            self._format_time(current_time)
                        ]
                        cues.append(cue)
                        self.current_cue_number += 1
                        self.used_outputs.add(output)  # Mark output as used
                        current_time += min_delay

            elif shot_type == "DOUBLE SHOT":
                # Add remaining outputs as double shots at the end
                for i in range(0, len(remaining_outputs), 2):
                    if i + 1 < len(remaining_outputs):
                        # Check if both outputs are unused
                        if remaining_outputs[i] not in self.used_outputs and remaining_outputs[
                            i + 1] not in self.used_outputs:
                            cue = [
                                self.current_cue_number,
                                "DOUBLE SHOT",
                                f"{remaining_outputs[i]}, {remaining_outputs[i + 1]}",
                                0,  # No delay for DOUBLE SHOT
                                self._format_time(current_time)
                            ]
                            cues.append(cue)
                            self.current_cue_number += 1
                            self.used_outputs.add(remaining_outputs[i])  # Mark first output as used
                            self.used_outputs.add(remaining_outputs[i + 1])  # Mark second output as used
                            current_time += min_delay
                    else:
                        # Odd number of outputs, add the last one as a single shot if unused
                        if remaining_outputs[i] not in self.used_outputs:
                            cue = [
                                self.current_cue_number,
                                "SINGLE SHOT",
                                str(remaining_outputs[i]),
                                0,  # No delay for SINGLE SHOT
                                self._format_time(current_time)
                            ]
                            cues.append(cue)
                            self.current_cue_number += 1
                            self.used_outputs.add(remaining_outputs[i])  # Mark output as used
                            current_time += min_delay

            elif shot_type == "SINGLE RUN":
                # Filter out used outputs
                unused_remaining_outputs = [output for output in remaining_outputs if output not in self.used_outputs]

                # Ensure we have at least 2 outputs for a run
                if len(unused_remaining_outputs) < 2:
                    return cues

                # Add remaining outputs as a single run at the end
                outputs_str = ", ".join(map(str, unused_remaining_outputs))

                # Get delay from shot config or use default
                delay = random.uniform(
                    shot_config.get("min_delay", self.RUN_DELAY_RANGES[act_key]["min"]),
                    shot_config.get("max_delay", self.RUN_DELAY_RANGES[act_key]["max"])
                )

                # Round delay to nearest increment
                increment = self.RUN_DELAY_RANGES[act_key]["increment"]
                delay = round(delay / increment) * increment

                cue = [
                    self.current_cue_number,
                    "SINGLE RUN",
                    outputs_str,
                    delay,
                    self._format_time(current_time)
                ]
                cues.append(cue)
                self.current_cue_number += 1

                # Mark outputs as used
                for output in unused_remaining_outputs:
                    self.used_outputs.add(output)

            elif shot_type == "DOUBLE RUN":
                # Filter out used outputs
                unused_remaining_outputs = [output for output in remaining_outputs if output not in self.used_outputs]

                # Ensure we have an even number of outputs for DOUBLE RUN (must be pairs)
                if len(unused_remaining_outputs) % 2 != 0:
                    unused_remaining_outputs = unused_remaining_outputs[:-1]

                # Ensure we have at least 2 outputs (1 pair) for a double run
                if len(unused_remaining_outputs) < 2:
                    return cues

                # Format all outputs as a comma-separated list
                outputs_str = ", ".join(map(str, unused_remaining_outputs))

                # Get delay from shot config or use default
                delay = random.uniform(
                    shot_config.get("min_delay", self.RUN_DELAY_RANGES[act_key]["min"]),
                    shot_config.get("max_delay", self.RUN_DELAY_RANGES[act_key]["max"])
                )

                # Round delay to nearest increment
                increment = self.RUN_DELAY_RANGES[act_key]["increment"]
                delay = round(delay / increment) * increment

                cue = [
                    self.current_cue_number,
                    "DOUBLE RUN",
                    outputs_str,
                    delay,
                    self._format_time(current_time)
                ]
                cues.append(cue)
                self.current_cue_number += 1

                # Mark outputs as used
                for output in unused_remaining_outputs:
                    self.used_outputs.add(output)

        return cues

    def _evaluate_generation(self) -> float:
        """
        Evaluate the quality of the current generation

        Returns:
            Score from 0 to 100, where 100 is perfect
        """
        score = 100.0

        # Check if all outputs are used
        used_outputs = self._get_used_outputs()
        if len(used_outputs) != self.total_outputs:
            # Penalize for missing outputs
            missing_outputs = self.total_outputs - len(used_outputs)
            score -= (missing_outputs / self.total_outputs) * 50

        # Check if outputs are used in the correct acts
        for act, outputs in self.act_outputs.items():
            act_used_outputs = self._get_act_used_outputs(act)

            # Check if all outputs for this act are used
            if len(act_used_outputs) != len(outputs):
                # Penalize for missing outputs in this act
                missing_outputs = len(outputs) - len(act_used_outputs)
                score -= (missing_outputs / len(outputs)) * 10

            # Check if outputs are used in the correct shot types
            for shot_type, shot_outputs in self.shot_type_outputs[act].items():
                shot_type_used_outputs = self._get_shot_type_used_outputs(act, shot_type)

                # Check if all outputs for this shot type are used
                if len(shot_type_used_outputs) != len(shot_outputs):
                    # Penalize for missing outputs in this shot type
                    missing_outputs = len(shot_outputs) - len(shot_type_used_outputs)
                    score -= (missing_outputs / len(shot_outputs)) * 5

        # Check if run types have the correct number of outputs
        for cue in self.cues:
            cue_type = cue[1]
            outputs_str = cue[2]

            if cue_type == "SINGLE RUN":
                # Count outputs in this run
                outputs = outputs_str.split(",")

                # Find which act this cue belongs to
                act_key = None
                for act in ["opening", "buildup", "finale"]:
                    if self._is_cue_in_act(act, cue):
                        act_key = act
                        break

                if act_key:
                    # Check if the number of outputs is within the allowed range
                    min_outputs = self.SINGLE_RUN_OUTPUTS[act_key]["min"]
                    max_outputs = self.SINGLE_RUN_OUTPUTS[act_key]["max"]

                    if len(outputs) < min_outputs:
                        # Penalize for too few outputs in this run
                        score -= 2
                    elif len(outputs) > max_outputs:
                        # Penalize for too many outputs in this run
                        score -= 2

            elif cue_type == "DOUBLE RUN":
                # Count outputs in this run
                outputs = outputs_str.split(",")

                # Find which act this cue belongs to
                act_key = None
                for act in ["opening", "buildup", "finale"]:
                    if self._is_cue_in_act(act, cue):
                        act_key = act
                        break

                if act_key:
                    # Check if the number of outputs is even (should be pairs)
                    if len(outputs) % 2 != 0:
                        # Penalize for odd number of outputs in DOUBLE RUN
                        score -= 5

                    # Check if the number of pairs is within the allowed range
                    pairs = len(outputs) // 2
                    min_pairs = self.DOUBLE_RUN_OUTPUTS[act_key]["min"]
                    max_pairs = self.DOUBLE_RUN_OUTPUTS[act_key]["max"]

                    if pairs < min_pairs:
                        # Penalize for too few pairs in this run
                        score -= 2
                    elif pairs > max_pairs:
                        # Penalize for too many pairs in this run
                        score -= 2

        # Check if the show duration is correct
        if self.cues:
            last_cue_time = self._time_to_seconds(self.cues[-1][4])
            if abs(last_cue_time - self.total_duration) > 30:  # Allow 30 seconds margin
                # Penalize for incorrect duration
                score -= min(10, abs(last_cue_time - self.total_duration) / 10)

        # Ensure score is between 0 and 100
        return max(0, min(100, score))

    def _get_used_outputs(self) -> Set[int]:
        """
        Get all outputs used in the current generation by analyzing the cues
        This is the definitive source of truth for which outputs are used

        Returns:
            Set of used output numbers
        """
        used_outputs = set()

        for cue in self.cues:
            outputs_str = cue[2]

            # Handle multiple outputs (comma-separated)
            if "," in outputs_str:
                outputs = [int(output.strip()) for output in outputs_str.split(",")]
                used_outputs.update(outputs)
            else:
                # Single output
                output = int(outputs_str.strip())
                used_outputs.add(output)

        return used_outputs

    def _get_act_used_outputs(self, act_key: str) -> Set[int]:
        """
        Get outputs used in a specific act

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')

        Returns:
            Set of used output numbers for this act
        """
        used_outputs = set()

        for cue in self.cues:
            if self._is_cue_in_act(act_key, cue):
                outputs_str = cue[2]

                # Handle multiple outputs (comma-separated)
                if "," in outputs_str:
                    outputs = [int(output.strip()) for output in outputs_str.split(",")]
                    used_outputs.update(outputs)
                else:
                    # Single output
                    output = int(outputs_str.strip())
                    used_outputs.add(output)

        return used_outputs

    def _get_shot_type_used_outputs(self, act_key: str, shot_type: str) -> Set[int]:
        """
        Get outputs used in a specific shot type within an act

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')
            shot_type: Type of shot ('SINGLE SHOT', 'DOUBLE SHOT', 'SINGLE RUN', 'DOUBLE RUN')

        Returns:
            Set of used output numbers for this shot type
        """
        used_outputs = set()

        for cue in self.cues:
            if self._is_cue_in_act(act_key, cue) and cue[1] == shot_type:
                outputs_str = cue[2]

                # Handle multiple outputs (comma-separated)
                if "," in outputs_str:
                    outputs = [int(output.strip()) for output in outputs_str.split(",")]
                    used_outputs.update(outputs)
                else:
                    # Single output
                    output = int(outputs_str.strip())
                    used_outputs.add(output)

        return used_outputs

    def _verify_generation(self):
        """Enhanced verification ensuring all outputs are used exactly once and parameters are respected"""
        if self.debug:
            print("\n=== ENHANCED GENERATION VERIFICATION ===")

            # Reset the used_outputs set before verification
            # This ensures we're only counting outputs from the cues, not from the generation process
            self.used_outputs = set()

            # Get all outputs that should be used
            all_expected_outputs = set(range(1, self.total_outputs + 1))
            used_outputs = self._get_used_outputs()

            # CRITICAL CHECK: Ensure all outputs are used exactly once
            if len(used_outputs) != self.total_outputs:
                missing = all_expected_outputs - used_outputs
                extra = used_outputs - all_expected_outputs

                if missing:
                    print(f"CRITICAL ERROR: Missing {len(missing)} outputs: {sorted(list(missing))}")
                if extra:
                    print(f"CRITICAL ERROR: Extra outputs used: {sorted(list(extra))}")

                print(f"FAILED: Expected {self.total_outputs} outputs, got {len(used_outputs)}")
                return False

            # Verify no duplicate cue numbers
            cue_numbers = [cue[0] for cue in self.cues]
            if len(set(cue_numbers)) != len(cue_numbers):
                duplicates = [num for num in cue_numbers if cue_numbers.count(num) > 1]
                print(f"CRITICAL ERROR: Duplicate cue numbers: {duplicates}")
                return False

            print(f"✓ SUCCESS: All {self.total_outputs} outputs used exactly once")
            print(f"✓ SUCCESS: All cue numbers are unique ({len(cue_numbers)} total)")

            # Verify act-specific output allocation
            for act, expected_outputs in self.act_outputs.items():
                act_used_outputs = self._get_act_used_outputs(act)
                if set(act_used_outputs) == set(expected_outputs):
                    print(f"✓ {act} act: {len(expected_outputs)} outputs correctly allocated")
                else:
                    print(f"ERROR: {act} act output mismatch")

            # Count and display final statistics
            cue_counts = {"SINGLE SHOT": 0, "DOUBLE SHOT": 0, "SINGLE RUN": 0, "DOUBLE RUN": 0}
            for cue in self.cues:
                cue_type = cue[1]
                if cue_type in cue_counts:
                    cue_counts[cue_type] += 1

            print("\nFinal Cue Distribution:")
            total_cues = len(self.cues)
            for cue_type, count in cue_counts.items():
                if count > 0:
                    percentage = (count / total_cues) * 100
                    print(f"  {cue_type}: {count} ({percentage:.1f}%)")

            # Verify timing
            if self.cues:
                last_cue_time = self._time_to_seconds(self.cues[-1][4])
                timing_error = abs(last_cue_time - self.total_duration)

                print(f"\nTiming Verification:")
                print(f"  Actual duration: {last_cue_time:.2f}s")
                print(f"  Target duration: {self.total_duration}s")
                print(f"  Error: {timing_error:.2f}s")

                if timing_error <= 5.0:  # Allow 5 seconds margin
                    print("✓ Timing within acceptable range")
                else:
                    print("⚠ Timing outside target range")

            print(f"\nGeneration Summary:")
            print(f"  Total cues: {len(self.cues)}")
            print(f"  Outputs used: {len(used_outputs)}/{self.total_outputs}")
            print(f"  Generation attempts: {self.generation_attempts}")
            print(f"  Generation time: {time.time() - self.generation_start_time:.2f} seconds")

            # Final success indicator
            success = (len(used_outputs) == self.total_outputs and
                       len(set(cue_numbers)) == len(cue_numbers))
            PASSED = "PASSED"
            FAILED = "FAILED"
            print(f"✓ VERIFICATION COMPLETE: {PASSED if success else FAILED}")

            return True

    def _format_time(self, seconds: float) -> str:
        """
        Convert seconds to a formatted time string (MM:SS.SS)

        Args:
            seconds: Time in seconds as a float

        Returns:
            Time string in format MM:SS.SS
        """
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes:02d}:{remaining_seconds:06.3f}"

    def _time_to_seconds(self, time_str: str) -> float:
        """
        Convert a time string (MM:SS.SS) to seconds

        Args:
            time_str: Time string in format MM:SS.SS

        Returns:
            Time in seconds as a float
        """
        try:
            minutes, seconds = time_str.split(':')
            return int(minutes) * 60 + float(seconds)
        except (ValueError, TypeError):
            return 0.0

    def _is_cue_in_act(self, act_key: str, cue: List) -> bool:
        """
        Check if a cue belongs to a specific act based on output number

        Args:
            act_key: Key for the act ('opening', 'buildup', or 'finale')
            cue: Cue to check

        Returns:
            True if the cue belongs to the act, False otherwise
        """
        if act_key not in self.act_outputs:
            return False

        # Get outputs for this act
        act_outputs = set(self.act_outputs[act_key])

        # Get output numbers from cue
        outputs_str = cue[2]
        try:
            # Handle multiple outputs (comma-separated)
            outputs = [int(output.strip()) for output in outputs_str.split(",")]
        except ValueError:
            return False

        # Check if any output is in this act
        for output in outputs:
            if output in act_outputs:
                return True

        return False

    def delete_cues_from_table(self, cue_table):
        """
        Delete all cues from the cue table

        Args:
            cue_table: Cue table widget to clear
        """
        # Clear the cue table
        cue_table.setRowCount(0)

    def add_cues_to_table(self, cue_table, cues):
        """
        Add cues to the cue table

        Args:
            cue_table: Cue table widget to add cues to
            cues: List of cues to add
        """
        # Add each cue to the table
        for cue in cues:
            row_position = cue_table.rowCount()
            cue_table.insertRow(row_position)

            # Add cue data to the row
            for col, value in enumerate(cue):
                item = QTableWidgetItem(str(value))
                cue_table.setItem(row_position, col, item)

    def verify_cues(self, cues):
        """
        Verify that cues are valid

        Args:
            cues: List of cues to verify

        Returns:
            True if all cues are valid, False otherwise
        """
        if not cues:
            print("Warning: No cues generated")
            return False

        # Check for duplicate outputs
        used_outputs = set()
        for cue in cues:
            outputs_str = cue[2]
            try:
                # Handle multiple outputs (comma-separated)
                outputs = [int(output.strip()) for output in outputs_str.split(",")]
                for output in outputs:
                    if output in used_outputs:
                        print(f"Warning: Output {output} used multiple times")
                        return False
                    used_outputs.add(output)
            except ValueError:
                print(f"Warning: Invalid output format: {outputs_str}")
                return False

        # Check for valid cue types
        valid_cue_types = ["SINGLE SHOT", "DOUBLE SHOT", "SINGLE RUN", "DOUBLE RUN"]
        for cue in cues:
            cue_type = cue[1]
            if cue_type not in valid_cue_types:
                print(f"Warning: Invalid cue type: {cue_type}")
                return False

        # Check for valid delays
        for cue in cues:
            try:
                delay = float(cue[3])
                if delay < 0:
                    print(f"Warning: Negative delay: {delay}")
                    return False
            except ValueError:
                print(f"Warning: Invalid delay format: {cue[3]}")
                return False

        # Check for valid execution times
        for cue in cues:
            try:
                self._time_to_seconds(cue[4])
            except ValueError:
                print(f"Warning: Invalid execution time format: {cue[4]}")
                return False

        # Check for run types with correct number of outputs
        for cue in cues:
            cue_type = cue[1]
            outputs_str = cue[2]

            if cue_type == "SINGLE RUN":
                # Count outputs in this run
                outputs = outputs_str.split(",")

                # Find which act this cue belongs to
                act_key = None
                for act in ["opening", "buildup", "finale"]:
                    if self._is_cue_in_act(act, cue):
                        act_key = act
                        break

                if act_key:
                    # Check if the number of outputs is within the allowed range
                    min_outputs = self.SINGLE_RUN_OUTPUTS[act_key]["min"]
                    max_outputs = self.SINGLE_RUN_OUTPUTS[act_key]["max"]

                    if len(outputs) < min_outputs:
                        print(f"Warning: SINGLE RUN cue has {len(outputs)} outputs, but minimum is {min_outputs}")
                        return False
                    elif len(outputs) > max_outputs:
                        print(f"Warning: SINGLE RUN cue has {len(outputs)} outputs, but maximum is {max_outputs}")
                        return False

            elif cue_type == "DOUBLE RUN":
                # Count outputs in this run
                outputs = outputs_str.split(",")

                # Find which act this cue belongs to
                act_key = None
                for act in ["opening", "buildup", "finale"]:
                    if self._is_cue_in_act(act, cue):
                        act_key = act
                        break

                if act_key:
                    # Check if the number of outputs is even (should be pairs)
                    if len(outputs) % 2 != 0:
                        print(f"Warning: DOUBLE RUN cue has odd number of outputs: {len(outputs)}")
                        return False

                    # Check if the number of pairs is within the allowed range
                    pairs = len(outputs) // 2
                    min_pairs = self.DOUBLE_RUN_OUTPUTS[act_key]["min"]
                    max_pairs = self.DOUBLE_RUN_OUTPUTS[act_key]["max"]

                    if pairs < min_pairs:
                        print(f"Warning: DOUBLE RUN cue has {pairs} pairs, but minimum is {min_pairs}")
                        return False
                    elif pairs > max_pairs:
                        print(f"Warning: DOUBLE RUN cue has {pairs} pairs, but maximum is {max_pairs}")
                        return False

        return True
