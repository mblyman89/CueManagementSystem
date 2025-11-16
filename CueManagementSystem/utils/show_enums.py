"""
Show Generation Enumerations
============================

Defines enumerations for firework show generation including sections, effects, styles, rhythms, and complexity levels.

Features:
- Show section definitions (intro, buildup, climax, finale)
- Effect sequence patterns
- Show style categories
- Rhythm pattern definitions
- Complexity level settings
- Type-safe show configuration
- Enhanced show generation support

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from enum import Enum

class ShowSection(Enum):
    """
    Defines sections of a firework show
    Used to control pacing, timing, and cue type selection
    """
    OPENING = 0
    BUILDUP = 1
    MAIN_BODY = 2
    PRE_FINALE = 3
    FINALE = 4

class EffectSequence(Enum):
    """
    Defines special effect sequences for a firework show
    Used to create visually interesting patterns
    """
    FAN = 0
    RIPPLE = 1
    ALTERNATING = 2
    CHASE = 3
    SYNCHRONIZED = 4
    CRESCENDO = 5

# Professional Show Enums (for enhanced show generator)
class ShowStyle(Enum):
    """Professional show styles"""
    CLASSICAL = "classical"
    ROCK_CONCERT = "rock_concert"
    PATRIOTIC = "patriotic"
    WEDDING = "wedding"
    CORPORATE = "corporate"
    COMPETITION = "competition"
    FINALE_HEAVY = "finale_heavy"
    TECHNICAL_SHOWCASE = "technical_showcase"
    EMOTIONAL_JOURNEY = "emotional_journey"

class RhythmPattern(Enum):
    """Professional rhythm patterns"""
    DRUMMING_ROCK = "drumming_rock"
    DRUMMING_JAZZ = "drumming_jazz"
    GALLOPING = "galloping"
    TROTTING = "trotting"
    MARCHING = "marching"
    WALTZ = "waltz"
    SWING = "swing"
    LATIN = "latin"

class ComplexityLevel(Enum):
    """Complexity levels for show generation"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"
