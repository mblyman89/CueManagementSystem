import random
import math
import traceback
from typing import List, Dict, Any, Tuple, Optional
from datetime import timedelta
from utils.show_enums import ShowSection, EffectSequence

class ShowGenerator:
    """
    Generator for creating random firework shows
    Handles the creation of cues based on specified parameters
    """
    
    # Define cue types and their weights (probability of selection)
    CUE_TYPES = {
        "SINGLE SHOT": 65,   # 65% chance
        "DOUBLE SHOT": 35,   # 35% chance
    }
    
    # These dictionaries are no longer needed since we're only using SHOT types
    # Kept as empty dictionaries for compatibility with existing code
    DELAY_RANGES = {}
    RUN_LENGTH_RANGES = {}
    
    # Time between cues ranges (in seconds)
    TIME_BETWEEN_CUES = {
        "min": 1.0,        # Minimum time between cues
        "max": 5.0,        # Maximum time between cues
        "finale_min": 0.2, # Minimum time during finale (last section)
        "finale_max": 1.5  # Maximum time during finale (last section)
    }
    
    # Time between cues for each section
    TIME_BETWEEN_CUES = {
        ShowSection.OPENING: {"min": 1.5, "max": 5.0},
        ShowSection.BUILDUP: {"min": 1.2, "max": 4.0},
        ShowSection.MAIN_BODY: {"min": 1.0, "max": 3.5},
        ShowSection.PRE_FINALE: {"min": 0.8, "max": 2.5},
        ShowSection.FINALE: {"min": 0.2, "max": 1.5},
    }
    
    # Cue type probabilities for each section
    SECTION_CUE_TYPES = {
        ShowSection.OPENING: {
            "SINGLE SHOT": 70,
            "DOUBLE SHOT": 30
        },
        ShowSection.BUILDUP: {
            "SINGLE SHOT": 65,
            "DOUBLE SHOT": 35
        },
        ShowSection.MAIN_BODY: {
            "SINGLE SHOT": 55,
            "DOUBLE SHOT": 45
        },
        ShowSection.PRE_FINALE: {
            "SINGLE SHOT": 50,
            "DOUBLE SHOT": 50
        },
        ShowSection.FINALE: {
            "SINGLE SHOT": 45,
            "DOUBLE SHOT": 55
        }
    }
    
    # These section-specific dictionaries are no longer needed for RUN types
    # Kept as empty dictionaries for compatibility with existing code
    DELAY_RANGES = {
        ShowSection.OPENING: {},
        ShowSection.BUILDUP: {},
        ShowSection.MAIN_BODY: {},
        ShowSection.PRE_FINALE: {},
        ShowSection.FINALE: {}
    }
    
    # Run length ranges are no longer needed
    RUN_LENGTH_RANGES = {
        ShowSection.OPENING: {},
        ShowSection.BUILDUP: {},
        ShowSection.MAIN_BODY: {},
        ShowSection.PRE_FINALE: {},
        ShowSection.FINALE: {}
    }
    
    # Probability of effect sequences for each section
    SEQUENCE_PROBABILITIES = {
        ShowSection.OPENING: {
            None: 70,  # 70% chance of no special effect
            EffectSequence.FAN: 10,
            EffectSequence.RIPPLE: 10,
            EffectSequence.ALTERNATING: 10,
            EffectSequence.CHASE: 0,
            EffectSequence.SYNCHRONIZED: 0,
            EffectSequence.CRESCENDO: 0
        },
        ShowSection.BUILDUP: {
            None: 60,
            EffectSequence.FAN: 10,
            EffectSequence.RIPPLE: 10,
            EffectSequence.ALTERNATING: 10,
            EffectSequence.CHASE: 5,
            EffectSequence.SYNCHRONIZED: 5,
            EffectSequence.CRESCENDO: 0
        },
        ShowSection.MAIN_BODY: {
            None: 40,
            EffectSequence.FAN: 10,
            EffectSequence.RIPPLE: 10,
            EffectSequence.ALTERNATING: 10,
            EffectSequence.CHASE: 10,
            EffectSequence.SYNCHRONIZED: 10,
            EffectSequence.CRESCENDO: 10
        },
        ShowSection.PRE_FINALE: {
            None: 30,
            EffectSequence.FAN: 10,
            EffectSequence.RIPPLE: 10,
            EffectSequence.ALTERNATING: 10,
            EffectSequence.CHASE: 15,
            EffectSequence.SYNCHRONIZED: 15,
            EffectSequence.CRESCENDO: 10
        },
        ShowSection.FINALE: {
            None: 20,
            EffectSequence.FAN: 10,
            EffectSequence.RIPPLE: 10,
            EffectSequence.ALTERNATING: 15,
            EffectSequence.CHASE: 15,
            EffectSequence.SYNCHRONIZED: 15,
            EffectSequence.CRESCENDO: 15
        }
    }
    
    def __init__(self):
        """Initialize the show generator"""
        # Used to track which outputs have been used
        self.used_outputs = set()
        
        # Used to track the current time position in the show
        self.current_time_seconds = 0.0
        
        # Used to track cue numbers
        self.current_cue_number = 1
    
    def generate_random_show(self, config_data) -> List[List]:
        """
        Generate a show based on configuration data with sequential output assignment
        
        Args:
            config_data: ShowConfigData instance with show parameters
            
        Returns:
            List of formatted cues ready to be added to the cue table
        """
        # Reset state for new generation
        self.used_outputs = set()
        self.current_time_seconds = 0.0
        self.current_cue_number = 1
        
        # Extract configuration parameters
        total_duration = config_data.total_seconds
        total_outputs = config_data.num_outputs
        section_intensities = config_data.section_intensities
        
        # Save show sections and intensities for later use
        self.show_sections = [ShowSection(i) for i in range(len(section_intensities))]
        self.section_intensities = section_intensities
        
        # Calculate the duration of each section
        section_durations = self._calculate_section_durations(total_duration, section_intensities)
        
        # Distribute outputs to sections in sequential order
        self.section_outputs = self._distribute_outputs_to_sections(total_outputs)
        
        # Get the number of outputs per section
        section_outputs = [len(self.section_outputs.get(ShowSection(i), [])) for i in range(len(section_intensities))]
        
        # Ensure we don't exceed the total number of outputs
        actual_outputs = sum(section_outputs)
        if actual_outputs != total_outputs:
            if actual_outputs > total_outputs:
                # Scale down proportionally if we allocated too many
                ratio = total_outputs / actual_outputs
                section_outputs = [int(count * ratio) for count in section_outputs]
            else:
                # Distribute remaining outputs proportionally
                remaining = total_outputs - actual_outputs
                # Give priority to finale section
                if len(section_outputs) > 0:
                    finale_index = len(section_outputs) - 1
                    section_outputs[finale_index] += remaining
            
            # Fix any rounding errors to ensure exact output count
            diff = total_outputs - sum(section_outputs)
            if diff > 0:
                # Add remaining to the finale or first non-zero section
                for i in range(len(section_outputs) - 1, -1, -1):
                    if section_outputs[i] > 0:
                        section_outputs[i] += diff
                        break
            elif diff < 0:
                # Remove excess from sections proportionally
                for i in range(len(section_outputs)):
                    if section_outputs[i] > abs(diff) and section_outputs[i] > 0:
                        section_outputs[i] += diff  # diff is negative
                        break
        
        # Generate cues for each section
        all_cues = []
        start_time = 0.0
        
        for i, (duration, num_outputs) in enumerate(zip(section_durations, section_outputs)):
            # Skip sections with no outputs
            if num_outputs <= 0:
                continue
                
            # Generate cues for this section
            section = ShowSection.FINALE if (i == len(section_durations) - 1) else ShowSection(i)
            section_cues = self._generate_professional_section(
                section=section,
                start_time=start_time,
                duration=duration,
                num_outputs=num_outputs
            )
            
            # Add cues to the list
            all_cues.extend(section_cues)
            
            # Update start time for next section
            start_time += duration
        
        # Check if we've used all outputs and add any remaining as single shots
        used_count = len(self.used_outputs)
        if used_count < total_outputs:
            remaining_outputs = total_outputs - used_count
            # Add remaining outputs as single shots at the end of the show
            finale_time = max([self._time_to_seconds(cue[4]) for cue in all_cues]) if all_cues else start_time
            
            # Space them out evenly in the last 15% of the show duration
            spacing = max(0.5, (total_duration * 0.15) / remaining_outputs)
            
            for i in range(remaining_outputs):
                time_offset = spacing * i
                execute_time = min(finale_time + time_offset, total_duration - 1)
                
                # Get a unique output
                output = self._get_unique_outputs(1)
                if output:
                    # Create a single shot cue
                    cue = [
                        self.current_cue_number,
                        "SINGLE SHOT",
                        str(output[0]),
                        0,  # No delay
                        self._format_time(execute_time)
                    ]
                    all_cues.append(cue)
                    self.current_cue_number += 1
        
        # Sort cues by execution time
        all_cues.sort(key=lambda cue: self._time_to_seconds(cue[4]))
        
        # Reassign cue numbers to ensure they're sequential
        for i, cue in enumerate(all_cues):
            cue[0] = i + 1
        
        return all_cues
    
    def _calculate_crescendo_timing(self, num_outputs: int, start_time: float, duration: float) -> List[float]:
        """
        Calculate timing for crescendo effect with accelerating shots
        
        Args:
            num_outputs: Number of outputs to space out
            start_time: Start time in seconds
            duration: Total duration in seconds
            
        Returns:
            List of shot times in seconds
        """
        if num_outputs <= 0:
            return []
            
        if num_outputs == 1:
            return [start_time]
            
        # For crescendo effect, we use a non-linear timing curve
        # The shots start slower and accelerate toward the end
        shot_times = []
        
        # Use a quadratic function to distribute times with increasing frequency
        for i in range(num_outputs):
            # Normalize position (0 to 1)
            position = i / (num_outputs - 1)
            # Apply quadratic curve (starts slower, ends faster)
            # Position^2 gives accelerating curve
            curved_position = position * position
            # Calculate time
            time = start_time + (curved_position * duration)
            shot_times.append(time)
            
        return shot_times
        
    def _distribute_outputs_to_sections(self, total_outputs: int) -> Dict[ShowSection, List[int]]:
        """
        Distribute outputs across show sections based on section intensity in sequential order
        
        Args:
            total_outputs: Total number of outputs available
            
        Returns:
            Dictionary mapping show sections to lists of output numbers
        """
        # Create a pool of all available outputs in sequential order
        all_outputs = list(range(1, total_outputs + 1))
        # We're not shuffling the outputs to maintain sequential order
        
        # Calculate outputs per section based on section intensities
        section_outputs = {}
        outputs_remaining = total_outputs
        next_output_index = 0
        
        for section in self.show_sections:
            # Determine how many outputs to allocate to this section
            intensity = self.section_intensities[section.value]
            section_output_count = int(round(total_outputs * (intensity / 100)))
            
            # Adjust for rounding errors to ensure we use exactly total_outputs
            if section == self.show_sections[-1]:
                # Last section gets remaining outputs
                section_output_count = outputs_remaining
            else:
                # Ensure we don't allocate more than remaining
                section_output_count = min(section_output_count, outputs_remaining)
                outputs_remaining -= section_output_count
            
            # Assign outputs to this section in sequential order
            section_end_index = next_output_index + section_output_count
            section_outputs[section] = all_outputs[next_output_index:section_end_index]
            next_output_index = section_end_index
        
        return section_outputs
    
    def _calculate_section_durations(self, total_duration: float, 
                                     section_intensities: List[int]) -> List[float]:
        """
        Calculate durations for each section based on total duration and intensities
        
        Args:
            total_duration: Total show duration in seconds
            section_intensities: List of intensity percentages for each section
            
        Returns:
            List of durations in seconds for each section
        """
        # If intensities sum to 0, make them equal
        if sum(section_intensities) == 0:
            section_intensities = [20 for _ in range(len(section_intensities))]
        
        # Calculate proportion of total duration for each section
        total_intensity = sum(section_intensities)
        durations = [
            (intensity / total_intensity) * total_duration
            for intensity in section_intensities
        ]
        
        return durations
    
    def _generate_professional_section(self, section: ShowSection, 
                                     start_time: float, duration: float, 
                                     num_outputs: int) -> List[List]:
        """
        Generate cues for a specific professional show section
        
        Args:
            section: The show section being generated
            start_time: Start time of this section in seconds
            duration: Duration of this section in seconds
            num_outputs: Number of outputs to use in this section
            
        Returns:
            List of cues for this section
        """
        if num_outputs <= 0:
            return []
            
        section_cues = []
        current_time = start_time
        end_time = start_time + duration
        outputs_left = num_outputs
        
        # Track starting output count to ensure we use exactly what was requested
        starting_output_count = len(self.used_outputs)
        target_output_count = starting_output_count + num_outputs
        
        # Reserve some outputs for special effect sequences
        sequence_probability = self._select_weighted_random(self.SEQUENCE_PROBABILITIES[section])
        reserved_for_sequence = 0
        
        if sequence_probability is not None and outputs_left > 8:
            # Reserve 25-40% of outputs for special sequences based on section
            if section == ShowSection.OPENING:
                sequence_percentage = 0.25
            elif section == ShowSection.FINALE:
                sequence_percentage = 0.40
            else:
                sequence_percentage = 0.30
                
            reserved_for_sequence = int(outputs_left * sequence_percentage)
            outputs_left -= reserved_for_sequence
        
        # Get the cue types distribution for this section
        cue_types = self.SECTION_CUE_TYPES[section].copy()
        
        # Keep generating cues until we use all outputs or reach the end time
        while outputs_left > 0 and current_time < end_time:
            # As we approach the end time, prioritize single shots to use up remaining outputs
            time_remaining = end_time - current_time
            if time_remaining < 3.0 and outputs_left > 0:
                # Force single shots when time is running out
                if outputs_left == 1 or random.random() < 0.8:
                    cue_type = "SINGLE SHOT"
                else:
                    cue_type = "DOUBLE SHOT"
            else:
                # Select a cue type based on weighted probabilities for this section
                cue_type = self._select_weighted_random(cue_types)
            
            # For the last few outputs, ensure we use exactly what's needed
            if outputs_left <= 4:
                if outputs_left == 1:
                    cue_type = "SINGLE SHOT"
                elif outputs_left >= 2:
                    cue_type = "DOUBLE SHOT"
            
            # Determine how many outputs this cue will use
            outputs_for_cue = self._get_outputs_for_cue_type(section, cue_type, outputs_left)
            
            if outputs_for_cue <= 0:
                # Can't fit this cue type with remaining outputs, try another
                continue
            
            # Generate the cue
            cue = self._generate_professional_cue(
                section=section,
                cue_type=cue_type,
                num_outputs=outputs_for_cue,
                execute_time=current_time
            )
            
            if cue:
                section_cues.append(cue)
                
                # Update outputs left
                outputs_left -= outputs_for_cue
                
                # Update time for next cue based on section timing
                time_between = random.uniform(
                    self.TIME_BETWEEN_CUES[section]["min"], 
                    self.TIME_BETWEEN_CUES[section]["max"]
                )
                
                # No special handling needed for SHOT types as they have no duration
                
                current_time += time_between
            else:
                # If we couldn't generate a cue, just advance time a bit and try again
                current_time += 0.5
                
                # If we're having trouble finding outputs, allow small time overruns to complete the section
                if current_time >= end_time and outputs_left > 0:
                    # Allow up to 10% time overrun to finish using all outputs
                    allowed_overrun = duration * 0.1
                    end_time = start_time + duration + allowed_overrun
        
        # If we have reserved outputs, generate special effect sequence
        if reserved_for_sequence > 0:
            # Choose a position for the sequence - typically near the end of the section
            sequence_start = start_time + (duration * 0.6)
            
            # Allow sequence to use up to 20% of the section duration
            sequence_duration = duration * 0.2
            
            # Generate the special effect sequence
            sequence_cues = self._generate_effect_sequence(
                section=section,
                effect_type=sequence_probability,
                num_outputs=reserved_for_sequence,
                start_time=sequence_start,
                duration=sequence_duration
            )
            
            section_cues.extend(sequence_cues)
            reserved_for_sequence = 0  # Mark as used
        
        # If we still have outputs left, add them as appropriate shots
        outputs_left = num_outputs - (len(self.used_outputs) - starting_output_count)
        
        if outputs_left > 0:
            # Different handling based on section
            if section == ShowSection.FINALE:
                # For finale, add as rapid-fire shots
                rapid_fire_cues = self._generate_rapid_fire_sequence(
                    section, outputs_left, end_time - 3.0, 2.5
                )
                section_cues.extend(rapid_fire_cues)
            elif section == ShowSection.OPENING:
                # For opening, add as well-spaced individual shots
                for i in range(outputs_left):
                    output = self._get_unique_outputs(1)
                    if output:
                        # Space evenly across the section
                        shot_time = start_time + (duration * (i + 1) / (outputs_left + 1))
                        cue = [
                            self.current_cue_number,
                            "SINGLE SHOT",
                            str(output[0]),
                            0,  # No delay
                            self._format_time(shot_time)
                        ]
                        section_cues.append(cue)
                        self.current_cue_number += 1
            else:
                # For other sections, distribute randomly
                for i in range(outputs_left):
                    output = self._get_unique_outputs(1)
                    if output:
                        # Add at a random time within section
                        random_time = start_time + (random.random() * duration)
                        cue = [
                            self.current_cue_number,
                            "SINGLE SHOT",
                            str(output[0]),
                            0,  # No delay
                            self._format_time(random_time)
                        ]
                        section_cues.append(cue)
                        self.current_cue_number += 1
        
        return section_cues
        
    def _generate_effect_sequence(self, section: ShowSection, effect_type: Optional[EffectSequence],
                                num_outputs: int, start_time: float, 
                                duration: float) -> List[List]:
        """
        Generate a special effect sequence of cues
        
        Args:
            section: The show section
            effect_type: Type of effect sequence to generate
            num_outputs: Number of outputs to use
            start_time: Start time for the sequence
            duration: Duration available for the sequence
            
        Returns:
            List of cues for the effect sequence
        """
        if effect_type is None or num_outputs <= 0:
            return []
            
        sequence_cues = []
        
        # Get unique outputs for this sequence
        outputs = self._get_unique_outputs(num_outputs)
        if not outputs:
            return []
            
        if effect_type == EffectSequence.FAN:
            # Fan/sweep pattern - single shots in rapid sequence
            spacing = duration / num_outputs
            for i, output in enumerate(outputs):
                time = start_time + (i * spacing)
                cue = [
                    self.current_cue_number,
                    "SINGLE SHOT",
                    str(output),
                    0,  # No delay
                    self._format_time(time)
                ]
                sequence_cues.append(cue)
                self.current_cue_number += 1
                
        elif effect_type == EffectSequence.RIPPLE:
            # Ripple/wave effect - alternating speeds
            # Create groups of outputs
            group_size = min(3, num_outputs // 3)
            if group_size < 1:
                group_size = 1
                
            groups = []
            for i in range(0, len(outputs), group_size):
                group = outputs[i:i+group_size]
                if group:
                    groups.append(group)
            
            # Space groups with accelerating pattern
            time = start_time
            speed_up_factor = 0.85  # Each gap is 85% of previous
            gap = duration / (len(groups) * 2)  # Initial gap
            
            for group in groups:
                # Create a single or double shot cue for this group
                if len(group) == 1:
                    cue_type = "SINGLE SHOT"
                    outputs_str = str(group[0])
                    delay = 0
                else:
                    # Always use DOUBLE SHOT for groups of 2 or more
                    cue_type = "DOUBLE SHOT"
                    # Take only the first two outputs for DOUBLE SHOT
                    outputs_str = f"{group[0]}, {group[1]}"
                    delay = 0
                    
                    # If there are more than 2 outputs in the group, create additional cues
                    remaining = group[2:]
                    if remaining:
                        # Create additional SINGLE or DOUBLE SHOTs for remaining outputs
                        additional_time = time + 0.25  # Add a small delay
                        
                        # Process remaining outputs in pairs if possible
                        for i in range(0, len(remaining), 2):
                            if i + 1 < len(remaining):
                                # Create DOUBLE SHOT
                                additional_cue = [
                                    self.current_cue_number,
                                    "DOUBLE SHOT",
                                    f"{remaining[i]}, {remaining[i+1]}",
                                    0,
                                    self._format_time(additional_time)
                                ]
                            else:
                                # Create SINGLE SHOT
                                additional_cue = [
                                    self.current_cue_number,
                                    "SINGLE SHOT",
                                    str(remaining[i]),
                                    0,
                                    self._format_time(additional_time)
                                ]
                            
                            sequence_cues.append(additional_cue)
                            self.current_cue_number += 1
                            additional_time += 0.25  # Space out additional cues
                        
                cue = [
                    self.current_cue_number,
                    cue_type,
                    outputs_str,
                    delay,
                    self._format_time(time)
                ]
                sequence_cues.append(cue)
                self.current_cue_number += 1
                
                # Update time and gap for next group
                time += gap
                gap *= speed_up_factor
                
        elif effect_type == EffectSequence.ALTERNATING:
            # Alternating left-right effect
            # Split outputs into two groups
            mid = len(outputs) // 2
            left_outputs = outputs[:mid]
            right_outputs = outputs[mid:]
            
            # Space shots evenly, alternating sides
            shots = []
            for i in range(max(len(left_outputs), len(right_outputs))):
                if i < len(left_outputs):
                    shots.append(("left", left_outputs[i]))
                if i < len(right_outputs):
                    shots.append(("right", right_outputs[i]))
            
            # Timing between shots
            shot_spacing = duration / len(shots)
            
            # Create cues
            time = start_time
            for side, output in shots:
                cue = [
                    self.current_cue_number,
                    "SINGLE SHOT",
                    str(output),
                    0,  # No delay
                    self._format_time(time)
                ]
                sequence_cues.append(cue)
                self.current_cue_number += 1
                time += shot_spacing
                
        elif effect_type == EffectSequence.CHASE:
            # Chase sequence - series of shots with tight timing
            # Space shots evenly, with a chase effect
            # Outputs are already in sequential order
            shot_spacing = duration / (num_outputs + 2)  # +2 for some padding
            time = start_time
            
            # Process outputs in pairs if possible, or as singles
            for i in range(0, len(outputs), 2):
                if i + 1 < len(outputs):
                    # Create DOUBLE SHOT with sequential outputs
                    cue = [
                        self.current_cue_number,
                        "DOUBLE SHOT",
                        f"{outputs[i]}, {outputs[i+1]}",
                        0,
                        self._format_time(time)
                    ]
                else:
                    # Create SINGLE SHOT for odd output
                    cue = [
                        self.current_cue_number,
                        "SINGLE SHOT",
                        str(outputs[i]),
                        0,
                        self._format_time(time)
                    ]
                
                sequence_cues.append(cue)
                self.current_cue_number += 1
                
                # Update time for next shot
                time += shot_spacing
                
        elif effect_type == EffectSequence.SYNCHRONIZED:
            # Synchronized effect - groups firing together
            # Create 2-4 synchronized groups
            num_groups = min(4, num_outputs // 2)
            if num_groups < 2:
                num_groups = 1
                
            # Divide outputs into groups
            outputs_per_group = num_outputs // num_groups
            groups = []
            
            for i in range(num_groups):
                start_idx = i * outputs_per_group
                end_idx = start_idx + outputs_per_group if i < num_groups - 1 else len(outputs)
                group = outputs[start_idx:end_idx]
                if group:
                    groups.append(group)
            
            # Space groups evenly
            group_spacing = duration / (len(groups) + 1)
            time = start_time
            
            for group in groups:
                # For all groups, process in pairs to create DOUBLE SHOT or SINGLE SHOT cues
                # All cues will fire at the same time to create synchronized effect
                for i in range(0, len(group), 2):
                    if i + 1 < len(group):
                        # Create DOUBLE SHOT
                        cue = [
                            self.current_cue_number,
                            "DOUBLE SHOT",
                            f"{group[i]}, {group[i+1]}",
                            0,
                            self._format_time(time)
                        ]
                    else:
                        # Create SINGLE SHOT for odd output
                        cue = [
                            self.current_cue_number,
                            "SINGLE SHOT",
                            str(group[i]),
                            0,
                            self._format_time(time)
                        ]
                    
                    sequence_cues.append(cue)
                    self.current_cue_number += 1
                
                # Update time for next group
                time += group_spacing
                
        elif effect_type == EffectSequence.CRESCENDO:
            # Crescendo - building intensity
            # Calculate accelerating timing
            shot_times = self._calculate_crescendo_timing(len(outputs), start_time, duration)
            
            # First half - single shots with increasing frequency
            half = len(outputs) // 2
            for i in range(half):
                cue = [
                    self.current_cue_number,
                    "SINGLE SHOT",
                    str(outputs[i]),
                    0,
                    self._format_time(shot_times[i])
                ]
                sequence_cues.append(cue)
                self.current_cue_number += 1
            
            # Second half - mix of double shots and runs with increasing intensity
            remaining = outputs[half:]
            
            # Group remaining outputs
            i = 0
            while i < len(remaining):
                # Determine group size based on position (larger toward end)
                position = i / len(remaining)
                remaining_count = len(remaining) - i
                
                if position > 0.7:  # Last 30%
                    # Ensure min value doesn't exceed max value
                    min_size = min(3, remaining_count)
                    max_size = min(5, remaining_count)
                    if min_size <= max_size:
                        group_size = random.randint(min_size, max_size)
                    else:
                        group_size = min_size
                elif position > 0.4:  # Middle 30%
                    min_size = min(2, remaining_count)
                    max_size = min(3, remaining_count)
                    if min_size <= max_size:
                        group_size = random.randint(min_size, max_size)
                    else:
                        group_size = min_size
                else:  # First 40%
                    min_size = min(1, remaining_count)
                    max_size = min(2, remaining_count)
                    if min_size <= max_size:
                        group_size = random.randint(min_size, max_size)
                    else:
                        group_size = min_size
                
                # Get group of outputs
                group = remaining[i:i+group_size]
                i += len(group)
                
                # Calculate time index
                time_index = half + i - len(group)
                if time_index >= len(shot_times):
                    time_index = len(shot_times) - 1
                
                # Determine cue type based on group size - only SINGLE SHOT and DOUBLE SHOT allowed
                if len(group) == 1:
                    cue_type = "SINGLE SHOT"
                    outputs_str = str(group[0])
                    delay = 0
                else:
                    # Use at most 2 outputs for DOUBLE SHOT
                    cue_type = "DOUBLE SHOT"
                    outputs_str = f"{group[0]}, {group[1]}"
                    delay = 0
                    
                    # If there are more outputs in the group, create additional cues
                    # with slightly staggered timing to maintain crescendo effect
                    if len(group) > 2:
                        remaining = group[2:]
                        time_offset = 0.1  # Small time offset
                        
                        for i in range(0, len(remaining), 2):
                            if i + 1 < len(remaining):
                                # Create DOUBLE SHOT
                                additional_cue = [
                                    self.current_cue_number,
                                    "DOUBLE SHOT",
                                    f"{remaining[i]}, {remaining[i+1]}",
                                    0,
                                    self._format_time(shot_times[time_index] + time_offset)
                                ]
                            else:
                                # Create SINGLE SHOT
                                additional_cue = [
                                    self.current_cue_number,
                                    "SINGLE SHOT",
                                    str(remaining[i]),
                                    0,
                                    self._format_time(shot_times[time_index] + time_offset)
                                ]
                            
                            sequence_cues.append(additional_cue)
                            self.current_cue_number += 1
                            time_offset += 0.1  # Increase offset for each additional cue
                
                cue = [
                    self.current_cue_number,
                    cue_type,
                    ", ".join(map(str, group)),
                    delay,
                    self._format_time(shot_times[time_index])
                ]
                sequence_cues.append(cue)
                self.current_cue_number += 1
        
        return sequence_cues
        
    def _generate_rapid_fire_sequence(self, section: ShowSection, num_outputs: int, 
                                    start_time: float, duration: float) -> List[List]:
        """
        Generate a rapid-fire sequence of shots with sequential outputs
        
        Args:
            section: Show section
            num_outputs: Number of outputs to use
            start_time: Start time for the sequence
            duration: Duration available for the sequence
            
        Returns:
            List of cues for the rapid-fire sequence
        """
        sequence_cues = []
        
        # Get unique outputs in sequential order
        outputs = self._get_unique_outputs(num_outputs)
        if not outputs:
            return []
        
        # Ensure outputs are sorted in ascending order
        outputs.sort()
            
        # For small numbers, use single shots
        if num_outputs <= 4:
            spacing = duration / num_outputs
            for i, output in enumerate(outputs):
                time = start_time + (i * spacing)
                cue = [
                    self.current_cue_number,
                    "SINGLE SHOT",
                    str(output),
                    0,
                    self._format_time(time)
                ]
                sequence_cues.append(cue)
                self.current_cue_number += 1
        else:
            # For larger numbers, use rapid sequence of SHOT types
            # Space shots more tightly to create rapid-fire effect
            shot_spacing = duration / (num_outputs * 1.2)  # Slightly tighter spacing
            time = start_time
            
            # Process outputs in pairs where possible
            for i in range(0, len(outputs), 2):
                if i + 1 < len(outputs):
                    # Create DOUBLE SHOT
                    cue = [
                        self.current_cue_number,
                        "DOUBLE SHOT",
                        f"{outputs[i]}, {outputs[i+1]}",
                        0,
                        self._format_time(time)
                    ]
                else:
                    # Create SINGLE SHOT for odd output
                    cue = [
                        self.current_cue_number,
                        "SINGLE SHOT",
                        str(outputs[i]),
                        0,
                        self._format_time(time)
                    ]
                
                sequence_cues.append(cue)
                self.current_cue_number += 1
                time += shot_spacing
                
        return sequence_cues
    
    def _generate_professional_cue(self, section: ShowSection, cue_type: str, 
                                 num_outputs: int, execute_time: float) -> List:
        """
        Generate a single cue of the specified type for a professional show
        
        Args:
            section: Show section this cue belongs to
            cue_type: Type of cue (SINGLE SHOT, DOUBLE SHOT, etc.)
            num_outputs: Number of outputs to use
            execute_time: Execution time in seconds
            
        Returns:
            A formatted cue ready for the cue table, or None if can't be created
        """
        # Generate required number of unique outputs
        outputs = self._get_unique_outputs(num_outputs)
        if not outputs:
            return None  # Couldn't get enough unique outputs
        
        # Format time as minutes:seconds.milliseconds
        formatted_time = self._format_time(execute_time)
        
        # Format outputs string based on cue type
        outputs_str = self._format_outputs_string(cue_type, outputs)
        
        # Set delay for run types
        delay = 0
        if "RUN" in cue_type:
            # Use only specific delay values: 0.25, 0.5, 0.75, or 1 second
            # Select delay based on section (faster for finale, slower for opening)
            if section == ShowSection.OPENING:
                # Opening - slower, more deliberate
                delay_options = [0.5, 0.75, 1.0]
            elif section == ShowSection.BUILDUP:
                # Buildup - medium
                delay_options = [0.5, 0.75]
            elif section == ShowSection.MAIN_BODY:
                # Main body - medium
                delay_options = [0.25, 0.5, 0.75]
            elif section == ShowSection.PRE_FINALE:
                # Pre-finale - faster
                delay_options = [0.25, 0.5]
            else:  # Finale
                # Finale - fastest
                delay_options = [0.25, 0.5]
                
            # Select a delay from the appropriate options
            delay = random.choice(delay_options)
        
        # Create the formatted cue for the table
        cue = [
            self.current_cue_number,  # Cue number
            cue_type,                 # Cue type
            outputs_str,              # Outputs string
            delay,                    # Delay (0 for SHOT types)
            formatted_time            # Execute time
        ]
        
        # Increment cue number for next cue
        self.current_cue_number += 1
        
        return cue
    
    def _get_outputs_for_cue_type(self, section: ShowSection, cue_type: str, 
                                available_outputs: int) -> int:
        """
        Determine how many outputs to use for a specific cue type in a section
        
        Args:
            section: Show section
            cue_type: Type of cue
            available_outputs: Number of outputs available
            
        Returns:
            Number of outputs to use for this cue
        """
        if "SINGLE SHOT" == cue_type:
            return 1
        elif "DOUBLE SHOT" == cue_type:
            return 2 if available_outputs >= 2 else 0
        
        # No other cue types are supported
        return 0
    
    def _get_unique_outputs(self, num_outputs: int) -> List[int]:
        """
        Get a list of unique output numbers that haven't been used yet, in sequential order
        
        Args:
            num_outputs: Number of unique outputs needed
            
        Returns:
            List of unique output numbers in sequential order, or empty list if not enough are available
        """
        # Find available outputs (1-1000 that are not already used)
        available_outputs = [i for i in range(1, 1001) if i not in self.used_outputs]
        
        # Sort the available outputs to ensure sequential selection
        available_outputs.sort()
        
        # If not enough outputs available, return empty list
        if len(available_outputs) < num_outputs:
            return []
        
        # Select the first num_outputs in sequential order
        selected_outputs = available_outputs[:num_outputs]
        
        # Mark these outputs as used
        self.used_outputs.update(selected_outputs)
        
        return selected_outputs
    
    def _format_outputs_string(self, cue_type: str, outputs: List[int]) -> str:
        """
        Format outputs into the appropriate string format for the cue table
        
        Args:
            cue_type: Type of cue
            outputs: List of output numbers
            
        Returns:
            Formatted string representation of outputs
        """
        if "DOUBLE SHOT" == cue_type:
            # Format as two outputs separated by comma
            return f"{outputs[0]}, {outputs[1]}"
        else:  # SINGLE SHOT
            # Single output
            return str(outputs[0])
    
    def _format_time(self, seconds: float) -> str:
        """
        Format time in seconds as minutes:seconds.milliseconds
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:05.2f}"
    
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
    
    def _select_weighted_random(self, weighted_dict: Dict[str, int]) -> str:
        """
        Select a random item from a dictionary based on weights
        
        Args:
            weighted_dict: Dictionary with items as keys and weights as values
            
        Returns:
            Randomly selected key
        """
        total_weight = sum(weighted_dict.values())
        rand_val = random.uniform(0, total_weight)
        
        cumulative_weight = 0
        for item, weight in weighted_dict.items():
            cumulative_weight += weight
            if rand_val <= cumulative_weight:
                return item
        
        # Fallback to first item
        return list(weighted_dict.keys())[0]
