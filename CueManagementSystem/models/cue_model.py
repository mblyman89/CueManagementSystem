"""
Cue Data Model
==============

Data model for managing firework cues with observer pattern for change notifications.

Features:
- Cue dataclass definition
- CueModel class for cue list management
- Add, update, delete, retrieve operations
- Observer pattern implementation
- Change notification system
- Data validation
- List management

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from typing import List, Dict, Callable, Any, Optional
from dataclasses import dataclass


@dataclass
class Cue:
    cue_number: int
    cue_type: str
    outputs: str
    delay: float
    execute_time: str
    output_values: List[int] = None

    @property
    def is_run_type(self) -> bool:
        return "RUN" in self.cue_type

    @property
    def is_double_type(self) -> bool:
        return "DOUBLE" in self.cue_type


class CueModel:
    def __init__(self):
        self._cues: List[Cue] = []
        self._observers: List[Callable] = []

    def add_cue(self, cue: Cue) -> bool:
        """Add a new cue to the model"""
        # Validate cue data
        if not self._is_valid_cue(cue):
            return False

        self._cues.append(cue)
        self._notify_observers()
        return True

    def update_cue(self, cue_number: int, updated_cue: Cue) -> bool:
        """Update an existing cue"""
        index = self._find_cue_index(cue_number)
        if index < 0:
            return False

        self._cues[index] = updated_cue
        self._notify_observers()
        return True

    def delete_cue(self, cue_number: int) -> bool:
        """Delete a cue by number"""
        index = self._find_cue_index(cue_number)
        if index < 0:
            return False

        del self._cues[index]
        self._notify_observers()
        return True

    def get_cues(self) -> List[Cue]:
        """Get all cues"""
        return self._cues.copy()

    def get_cue(self, cue_number: int) -> Optional[Cue]:
        """Get a specific cue by number"""
        index = self._find_cue_index(cue_number)
        if index < 0:
            return None
        return self._cues[index]

    def register_observer(self, callback: Callable) -> None:
        """Register observer to be notified of changes"""
        if callback not in self._observers:
            self._observers.append(callback)

    def unregister_observer(self, callback: Callable) -> None:
        """Remove observer"""
        if callback in self._observers:
            self._observers.remove(callback)

    def _notify_observers(self) -> None:
        """Notify all observers of changes"""
        for callback in self._observers:
            callback(self._cues)

    def _find_cue_index(self, cue_number: int) -> int:
        """Find index of cue with given number"""
        for i, cue in enumerate(self._cues):
            if cue.cue_number == cue_number:
                return i
        return -1

    def _is_valid_cue(self, cue: Cue) -> bool:
        """Validate cue data"""
        # Check for duplicate cue numbers
        if self._find_cue_index(cue.cue_number) >= 0:
            return False

        # Check that output values are valid
        # Add other validation as needed
        return True