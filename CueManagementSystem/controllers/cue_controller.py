"""
Cue Controller
==============

Manages creation, updating, deletion, and selection of Cue objects with validation and data conversion.

Features:
- Cue creation management
- Cue update operations
- Cue deletion handling
- Cue selection tracking
- Data conversion utilities
- Output formatting
- Duplicate prevention
- Conflict detection

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from typing import List, Dict, Any, Optional
from models.cue_model import CueModel, Cue


class CueController:
    def __init__(self, model: CueModel):
        self.model = model

    def create_cue(self, cue_data: Dict[str, Any]) -> bool:
        """Process and validate cue creation"""
        # Convert dictionary to Cue object
        cue = self._dict_to_cue(cue_data)

        # Validate outputs
        if not self._validate_outputs(cue):
            return False

        # Add to model
        return self.model.add_cue(cue)

    def update_cue(self, cue_number: int, cue_data: Dict[str, Any]) -> bool:
        """Process and validate cue update"""
        # Convert dictionary to Cue object
        cue = self._dict_to_cue(cue_data)

        # Validate outputs
        if not self._validate_outputs(cue):
            return False

        # Update in model
        return self.model.update_cue(cue_number, cue)

    def delete_cue(self, cue_number: int) -> bool:
        """Delete a cue"""
        return self.model.delete_cue(cue_number)

    def select_cue(self, cue_number: int) -> Optional[Cue]:
        """Get a cue for selection"""
        return self.model.get_cue(cue_number)

    def _dict_to_cue(self, data: Dict[str, Any]) -> Cue:
        """Convert dictionary to Cue object"""
        # Handle different formats of input data
        # Format outputs string based on cue type
        return Cue(
            cue_number=data.get("cue_number", 0),
            cue_type=data.get("cue_type", ""),
            outputs=self._format_outputs(data),
            delay=data.get("delay", 0.0),
            execute_time=data.get("execute_time", "00:00.0000"),
            output_values=data.get("output_values", [])
        )

    def _format_outputs(self, data: Dict[str, Any]) -> str:
        """Format outputs string based on cue type and values"""
        cue_type = data.get("cue_type", "")
        output_values = data.get("output_values", [])

        if not output_values:
            return ""

        if "DOUBLE RUN" in cue_type:
            # Format as pairs: "1,2; 3,4; 5,6"
            pairs = []
            for i in range(0, len(output_values), 2):
                if i + 1 < len(output_values):
                    pairs.append(f"{output_values[i]},{output_values[i + 1]}")
            return "; ".join(pairs)
        elif "RUN" in cue_type:
            # Format as comma list: "1, 2, 3, 4"
            return ", ".join(map(str, output_values))
        elif "DOUBLE" in cue_type:
            # Format as two values: "1, 2"
            if len(output_values) >= 2:
                return f"{output_values[0]}, {output_values[1]}"
            return ", ".join(map(str, output_values))
        else:
            # Format as single value: "1"
            if output_values:
                return str(output_values[0])
            return "1"

    def _validate_outputs(self, cue: Cue) -> bool:
        """Validate output values"""
        # Check for duplicate outputs
        if cue.output_values and len(cue.output_values) != len(set(cue.output_values)):
            return False

        # Check for conflicts with other cues' outputs
        all_cues = self.model.get_cues()
        used_outputs = set()

        for existing_cue in all_cues:
            # Skip the cue being validated
            if existing_cue.cue_number == cue.cue_number:
                continue

            # Collect outputs from existing cue
            if existing_cue.output_values:
                used_outputs.update(existing_cue.output_values)

        # Check for conflicts
        if cue.output_values:
            for output in cue.output_values:
                if output in used_outputs:
                    return False

        return True