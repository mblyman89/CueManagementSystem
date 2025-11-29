"""
Enhanced Cue Data Model with Visual Properties
===============================================

Extended data model for managing firework cues with visual properties
for ultra-realistic 3D visualization in Unreal Engine 5.

Features:
- Extended Cue dataclass with visual properties
- Firework effect type definitions
- Color and size specifications
- 3D position data
- Effect parameters
- Backward compatibility with existing cue system

Author: Michael Lyman
Version: 2.0.0
License: MIT
"""

from typing import List, Dict, Callable, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class FireworkEffectType(Enum):
    """Predefined firework effect types matching UE5 Niagara systems"""
    # Classic Effects
    GOLD_PEONY = "gold_peony"
    RED_CHRYSANTHEMUM = "red_chrysanthemum"
    SILVER_WILLOW = "silver_willow"
    BLUE_CROSSETTE = "blue_crossette"
    GREEN_PALM = "green_palm"

    # Multi-Color Effects
    MULTI_COLOR_BURST = "multi_color_burst"
    RAINBOW_PEONY = "rainbow_peony"

    # Special Effects
    CRACKLE = "crackle"
    STROBE = "strobe"
    COMET = "comet"
    FOUNTAIN = "fountain"

    # Advanced Effects
    DOUBLE_BREAK = "double_break"
    TRIPLE_BREAK = "triple_break"
    CASCADING = "cascading"
    RING_SHELL = "ring_shell"

    # Custom
    CUSTOM = "custom"


class FireworkSize(Enum):
    """Firework size presets"""
    SMALL = "small"  # 2-3 inch shells
    MEDIUM = "medium"  # 4-6 inch shells
    LARGE = "large"  # 8-10 inch shells
    EXTRA_LARGE = "xl"  # 12+ inch shells
    CUSTOM = "custom"  # Custom size multiplier


class FireworkColor(Enum):
    """Predefined firework colors"""
    # Primary Colors
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)

    # Secondary Colors
    YELLOW = (255, 255, 0)
    ORANGE = (255, 165, 0)
    PURPLE = (128, 0, 128)
    PINK = (255, 192, 203)

    # Metallic Colors
    GOLD = (255, 215, 0)
    SILVER = (192, 192, 192)
    WHITE = (255, 255, 255)

    # Special Colors
    MULTI_COLOR = (0, 0, 0)  # Placeholder for multi-color effects
    CUSTOM = (0, 0, 0)  # Custom RGB


@dataclass
class VisualProperties:
    """Visual properties for firework effects"""
    # Effect Type
    effect_type: str = FireworkEffectType.GOLD_PEONY.value

    # Color Properties
    color: Tuple[int, int, int] = FireworkColor.GOLD.value
    secondary_color: Optional[Tuple[int, int, int]] = None  # For multi-color effects
    color_gradient: bool = False  # Fade from primary to secondary

    # Size Properties
    size: str = FireworkSize.MEDIUM.value
    size_multiplier: float = 1.0  # Custom size scaling

    # Intensity & Brightness
    intensity: float = 1.0  # 0.0 to 2.0, affects brightness and particle count
    brightness: float = 1.0  # HDR brightness multiplier

    # 3D Position (relative to launch site)
    position_x: float = 0.0  # Horizontal position (meters)
    position_y: float = 0.0  # Depth position (meters)
    position_z: float = 0.0  # Height offset (meters, added to calculated height)

    # Physics Properties
    launch_velocity: float = 1.0  # Velocity multiplier
    gravity_scale: float = 1.0  # Gravity effect multiplier
    wind_influence: float = 0.3  # How much wind affects the effect

    # Timing Properties
    ascent_duration: float = 0.0  # 0 = auto-calculate based on height
    explosion_duration: float = 0.0  # 0 = use effect default
    fade_duration: float = 2.0  # How long particles fade out

    # Effect-Specific Parameters
    effect_parameters: Dict[str, Any] = field(default_factory=dict)
    # Examples:
    # - "star_count": 100 (number of particles)
    # - "spread_angle": 360 (degrees)
    # - "trail_length": 1.5 (seconds)
    # - "crackle_intensity": 0.8
    # - "strobe_frequency": 10 (Hz)

    # Audio Properties
    audio_enabled: bool = True
    audio_volume: float = 1.0
    audio_variation: int = 0  # Which sound variation to use

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "effect_type": self.effect_type,
            "color": self.color,
            "secondary_color": self.secondary_color,
            "color_gradient": self.color_gradient,
            "size": self.size,
            "size_multiplier": self.size_multiplier,
            "intensity": self.intensity,
            "brightness": self.brightness,
            "position_x": self.position_x,
            "position_y": self.position_y,
            "position_z": self.position_z,
            "launch_velocity": self.launch_velocity,
            "gravity_scale": self.gravity_scale,
            "wind_influence": self.wind_influence,
            "ascent_duration": self.ascent_duration,
            "explosion_duration": self.explosion_duration,
            "fade_duration": self.fade_duration,
            "effect_parameters": self.effect_parameters,
            "audio_enabled": self.audio_enabled,
            "audio_volume": self.audio_volume,
            "audio_variation": self.audio_variation
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VisualProperties':
        """Create from dictionary"""
        return cls(
            effect_type=data.get("effect_type", FireworkEffectType.GOLD_PEONY.value),
            color=tuple(data.get("color", FireworkColor.GOLD.value)),
            secondary_color=tuple(data["secondary_color"]) if data.get("secondary_color") else None,
            color_gradient=data.get("color_gradient", False),
            size=data.get("size", FireworkSize.MEDIUM.value),
            size_multiplier=data.get("size_multiplier", 1.0),
            intensity=data.get("intensity", 1.0),
            brightness=data.get("brightness", 1.0),
            position_x=data.get("position_x", 0.0),
            position_y=data.get("position_y", 0.0),
            position_z=data.get("position_z", 0.0),
            launch_velocity=data.get("launch_velocity", 1.0),
            gravity_scale=data.get("gravity_scale", 1.0),
            wind_influence=data.get("wind_influence", 0.3),
            ascent_duration=data.get("ascent_duration", 0.0),
            explosion_duration=data.get("explosion_duration", 0.0),
            fade_duration=data.get("fade_duration", 2.0),
            effect_parameters=data.get("effect_parameters", {}),
            audio_enabled=data.get("audio_enabled", True),
            audio_volume=data.get("audio_volume", 1.0),
            audio_variation=data.get("audio_variation", 0)
        )


@dataclass
class EnhancedCue:
    """Enhanced Cue with visual properties for 3D visualization"""
    # Original Cue Properties (backward compatible)
    cue_number: int
    cue_type: str
    outputs: str
    delay: float
    execute_time: str
    output_values: List[int] = None

    # New Visual Properties
    visual_properties: VisualProperties = field(default_factory=VisualProperties)

    # Metadata
    notes: str = ""
    tags: List[str] = field(default_factory=list)

    @property
    def is_run_type(self) -> bool:
        return "RUN" in self.cue_type

    @property
    def is_double_type(self) -> bool:
        return "DOUBLE" in self.cue_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "cue_number": self.cue_number,
            "cue_type": self.cue_type,
            "outputs": self.outputs,
            "delay": self.delay,
            "execute_time": self.execute_time,
            "output_values": self.output_values,
            "visual_properties": self.visual_properties.to_dict(),
            "notes": self.notes,
            "tags": self.tags
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedCue':
        """Create from dictionary"""
        visual_props = VisualProperties.from_dict(data.get("visual_properties", {}))
        return cls(
            cue_number=data["cue_number"],
            cue_type=data["cue_type"],
            outputs=data["outputs"],
            delay=data["delay"],
            execute_time=data["execute_time"],
            output_values=data.get("output_values"),
            visual_properties=visual_props,
            notes=data.get("notes", ""),
            tags=data.get("tags", [])
        )

    def to_visualization_command(self) -> Dict[str, Any]:
        """
        Convert cue to visualization command for UE5
        This is the message format sent over WebSocket
        """
        return {
            "command": "launch_firework",
            "cue_number": self.cue_number,
            "timestamp": self.execute_time,
            "effect": {
                "type": self.visual_properties.effect_type,
                "color": {
                    "r": self.visual_properties.color[0],
                    "g": self.visual_properties.color[1],
                    "b": self.visual_properties.color[2]
                },
                "secondary_color": {
                    "r": self.visual_properties.secondary_color[0] if self.visual_properties.secondary_color else 0,
                    "g": self.visual_properties.secondary_color[1] if self.visual_properties.secondary_color else 0,
                    "b": self.visual_properties.secondary_color[2] if self.visual_properties.secondary_color else 0
                } if self.visual_properties.secondary_color else None,
                "size": self.visual_properties.size,
                "size_multiplier": self.visual_properties.size_multiplier,
                "intensity": self.visual_properties.intensity,
                "brightness": self.visual_properties.brightness
            },
            "position": {
                "x": self.visual_properties.position_x,
                "y": self.visual_properties.position_y,
                "z": self.visual_properties.position_z
            },
            "physics": {
                "launch_velocity": self.visual_properties.launch_velocity,
                "gravity_scale": self.visual_properties.gravity_scale,
                "wind_influence": self.visual_properties.wind_influence
            },
            "timing": {
                "ascent_duration": self.visual_properties.ascent_duration,
                "explosion_duration": self.visual_properties.explosion_duration,
                "fade_duration": self.visual_properties.fade_duration
            },
            "audio": {
                "enabled": self.visual_properties.audio_enabled,
                "volume": self.visual_properties.audio_volume,
                "variation": self.visual_properties.audio_variation
            },
            "parameters": self.visual_properties.effect_parameters
        }


class EnhancedCueModel:
    """Enhanced CueModel with visual properties support"""

    def __init__(self):
        self._cues: List[EnhancedCue] = []
        self._observers: List[Callable] = []

    def add_cue(self, cue: EnhancedCue) -> bool:
        """Add a new cue to the model"""
        if not self._is_valid_cue(cue):
            return False

        self._cues.append(cue)
        self._notify_observers()
        return True

    def update_cue(self, cue_number: int, updated_cue: EnhancedCue) -> bool:
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

    def get_cues(self) -> List[EnhancedCue]:
        """Get all cues"""
        return self._cues.copy()

    def get_cue(self, cue_number: int) -> Optional[EnhancedCue]:
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

    def _is_valid_cue(self, cue: EnhancedCue) -> bool:
        """Validate cue data"""
        # Check for duplicate cue numbers
        if self._find_cue_index(cue.cue_number) >= 0:
            return False

        # Validate visual properties
        if cue.visual_properties.intensity < 0 or cue.visual_properties.intensity > 2.0:
            return False

        if cue.visual_properties.size_multiplier <= 0:
            return False

        return True

    def get_visualization_commands(self) -> List[Dict[str, Any]]:
        """Get all cues as visualization commands for UE5"""
        return [cue.to_visualization_command() for cue in self._cues]


# Preset Effect Configurations
EFFECT_PRESETS = {
    "gold_peony": VisualProperties(
        effect_type=FireworkEffectType.GOLD_PEONY.value,
        color=FireworkColor.GOLD.value,
        size=FireworkSize.MEDIUM.value,
        intensity=1.0,
        effect_parameters={"star_count": 100, "spread_angle": 360}
    ),
    "red_chrysanthemum": VisualProperties(
        effect_type=FireworkEffectType.RED_CHRYSANTHEMUM.value,
        color=FireworkColor.RED.value,
        size=FireworkSize.LARGE.value,
        intensity=1.2,
        effect_parameters={"star_count": 150, "spread_angle": 360, "trail_length": 2.0}
    ),
    "silver_willow": VisualProperties(
        effect_type=FireworkEffectType.SILVER_WILLOW.value,
        color=FireworkColor.SILVER.value,
        size=FireworkSize.LARGE.value,
        intensity=0.9,
        gravity_scale=1.5,
        effect_parameters={"star_count": 200, "spread_angle": 360, "trail_length": 3.0}
    ),
    "multi_color_burst": VisualProperties(
        effect_type=FireworkEffectType.MULTI_COLOR_BURST.value,
        color=FireworkColor.RED.value,
        secondary_color=FireworkColor.BLUE.value,
        color_gradient=True,
        size=FireworkSize.LARGE.value,
        intensity=1.3,
        effect_parameters={"star_count": 120, "color_sections": 4}
    ),
    "crackle": VisualProperties(
        effect_type=FireworkEffectType.CRACKLE.value,
        color=FireworkColor.WHITE.value,
        size=FireworkSize.MEDIUM.value,
        intensity=1.1,
        effect_parameters={"crackle_intensity": 0.8, "crackle_frequency": 50}
    )
}