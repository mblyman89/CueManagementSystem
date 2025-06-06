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

from enum import Enum

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
