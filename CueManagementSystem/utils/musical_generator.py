import random
import traceback
from typing import List, Dict, Any

class MusicalShowGenerator:
    """
    Generator for creating firework shows synchronized to music.
    """

    def __init__(self):
        """Initialize the show generator"""
        self.used_outputs = set()
        self.current_cue_number = 1

    def generate_musical_show(self, analysis_data: Dict[str, Any], num_outputs: int,
                              output_mode: str = "random", time_offset_ms: int = 0,
                              selected_peaks: set = None) -> List[List]:
        """
        Generate a musical show based on analyzed peak data, respecting selected peaks.

        Args:
            analysis_data: Dictionary containing music analysis data (peaks).
            num_outputs: Number of outputs to use in the show.
            output_mode: "random" or "sequential" for output assignment.
            time_offset_ms: Time offset in milliseconds.
            selected_peaks: A set of peak indices to include in the show. If None, all peaks are used.

        Returns:
            List of formatted cues, or None on error.
        """
        self.used_outputs = set()
        self.current_cue_number = 1
        cues = []

        try:
            peak_data = analysis_data.get('beat_markers', [])
            if not peak_data:
                raise ValueError("No peak data found.")

            # Filter peaks based on selected_peaks
            if selected_peaks is not None:
                peak_data = [peak for i, peak in enumerate(peak_data) if i in selected_peaks]

            if not peak_data:  # Check again after filtering
                raise ValueError("No peaks selected or available after filtering.")

            num_outputs = min(num_outputs, 1000)  # Limit outputs
            num_peaks = len(peak_data)

            if output_mode == "random":
                outputs = self._get_unique_outputs(num_outputs)
            elif output_mode == "sequential":
                outputs = list(range(1, num_outputs + 1))
            else:
                raise ValueError("Invalid output_mode.")

            if not outputs:
                raise ValueError("Not enough outputs available.")

            # Calculate indices for even distribution across the entire song
            cue_indices = [i * num_peaks // num_outputs for i in range(num_outputs)]

            for i, cue_index in enumerate(cue_indices):
                if cue_index < num_peaks:  # Check if cue_index is within bounds
                    peak = peak_data[cue_index]

                    peak_time_seconds = self._time_to_seconds(peak.time_str)
                    offset_time_seconds = peak_time_seconds - (time_offset_ms / 1000)
                    offset_time_str = self._format_time(offset_time_seconds)

                    cue = [
                        self.current_cue_number,
                        "SINGLE SHOT",
                        str(outputs[i]),
                        0,
                        offset_time_str
                    ]
                    cues.append(cue)
                    self.current_cue_number += 1

            return cues

        except (ValueError, TypeError, Exception) as e:
            traceback.print_exc()
            return None

    def _get_unique_outputs(self, num_outputs: int) -> List[int]:
        """Get a list of unique output numbers."""
        available_outputs = list(range(1, 1001))
        if num_outputs > len(available_outputs):
            raise ValueError("Not enough unique outputs available.")

        if num_outputs == len(available_outputs):
            return available_outputs

        random.shuffle(available_outputs)
        return available_outputs[:num_outputs]

    def _time_to_seconds(self, time_str: str) -> float:
        """Convert time string (MM:SS.SS) to seconds."""
        try:
            minutes, seconds = time_str.split(':')
            return int(minutes) * 60 + float(seconds)
        except (ValueError, TypeError):
            return 0.0

    def _format_time(self, seconds: float) -> str:
        """Format time in seconds to string (MM:SS.SS)."""
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:05.2f}"