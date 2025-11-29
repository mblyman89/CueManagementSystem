"""
Excalibur Firework Shell Effects Library
=========================================

Detailed effect definitions for World Class Excalibur artillery shells,
the #1 selling canister shell kit in the industry.

Excalibur shells are known for:
- Maximum 60-gram powder load (legal limit)
- Hard-breaking, loud reports
- High altitude bursts (200-300 feet)
- Consistent performance
- Vibrant colors and effects
- HDPE tubes for safe launching

This module provides accurate visual properties for all Excalibur effects
to ensure realistic simulation in Unreal Engine 5.

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

from typing import Dict, Any
from dataclasses import dataclass
from models.cue_visual_model import VisualProperties, FireworkColor, FireworkSize


# Excalibur-specific effect types
class ExcaliburEffectType:
    """Excalibur shell effect type identifiers"""

    # Classic Breaks
    EXCALIBUR_RED_PEONY = "excalibur_red_peony"
    EXCALIBUR_BLUE_PEONY = "excalibur_blue_peony"
    EXCALIBUR_GREEN_PEONY = "excalibur_green_peony"
    EXCALIBUR_PURPLE_PEONY = "excalibur_purple_peony"
    EXCALIBUR_YELLOW_PEONY = "excalibur_yellow_peony"
    EXCALIBUR_ORANGE_PEONY = "excalibur_orange_peony"
    EXCALIBUR_WHITE_PEONY = "excalibur_white_peony"

    # Chrysanthemum Effects
    EXCALIBUR_RED_CHRYSANTHEMUM = "excalibur_red_chrysanthemum"
    EXCALIBUR_BLUE_CHRYSANTHEMUM = "excalibur_blue_chrysanthemum"
    EXCALIBUR_GREEN_CHRYSANTHEMUM = "excalibur_green_chrysanthemum"
    EXCALIBUR_PURPLE_CHRYSANTHEMUM = "excalibur_purple_chrysanthemum"

    # Brocade/Willow Effects
    EXCALIBUR_SILVER_BROCADE = "excalibur_silver_brocade"
    EXCALIBUR_GOLD_BROCADE = "excalibur_gold_brocade"
    EXCALIBUR_SILVER_WILLOW = "excalibur_silver_willow"
    EXCALIBUR_GOLD_WILLOW = "excalibur_gold_willow"

    # Palm Tree Effects
    EXCALIBUR_RED_PALM = "excalibur_red_palm"
    EXCALIBUR_GREEN_PALM = "excalibur_green_palm"
    EXCALIBUR_PURPLE_PALM = "excalibur_purple_palm"

    # Crackle Effects
    EXCALIBUR_SILVER_CRACKLE = "excalibur_silver_crackle"
    EXCALIBUR_GOLD_CRACKLE = "excalibur_gold_crackle"
    EXCALIBUR_TITANIUM_CRACKLE = "excalibur_titanium_crackle"

    # Strobe Effects
    EXCALIBUR_WHITE_STROBE = "excalibur_white_strobe"
    EXCALIBUR_COLOR_STROBE = "excalibur_color_strobe"

    # Dahlia Effects
    EXCALIBUR_RED_DAHLIA = "excalibur_red_dahlia"
    EXCALIBUR_PURPLE_DAHLIA = "excalibur_purple_dahlia"

    # Multi-Effect Combinations
    EXCALIBUR_BROCADE_CROWN = "excalibur_brocade_crown"
    EXCALIBUR_CRACKLE_CROWN = "excalibur_crackle_crown"
    EXCALIBUR_PALM_CRACKLE = "excalibur_palm_crackle"
    EXCALIBUR_PEONY_CRACKLE = "excalibur_peony_crackle"

    # Whistling Effects
    EXCALIBUR_WHISTLING_REPORT = "excalibur_whistling_report"


# Excalibur Shell Specifications
EXCALIBUR_SPECS = {
    "shell_diameter": 1.75,  # inches
    "tube_diameter": 4.0,  # inches (HDPE tubes)
    "powder_load": 60,  # grams (maximum legal)
    "burst_height": 250,  # feet average
    "burst_diameter": 150,  # feet average
    "report_level": "loud",  # Very loud reports
    "lift_charge": "strong",  # High velocity launch
}

# Excalibur Effect Presets
EXCALIBUR_EFFECTS: Dict[str, VisualProperties] = {

    # ========== RED EFFECTS ==========
    "excalibur_red_peony": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_RED_PEONY,
        color=(255, 0, 0),  # Bright red
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,  # Excalibur shells are large
        intensity=1.4,  # High intensity
        brightness=1.3,  # Bright burst
        launch_velocity=1.2,  # Strong lift
        gravity_scale=1.0,
        wind_influence=0.2,
        ascent_duration=0.0,  # Auto-calculate
        explosion_duration=2.5,  # Long-lasting
        fade_duration=2.0,
        effect_parameters={
            "star_count": 120,
            "spread_angle": 360,
            "symmetry": "spherical",
            "tail_length": 1.5,
            "report_intensity": 0.9,  # Loud report
            "shell_type": "excalibur_60g"
        },
        audio_enabled=True,
        audio_volume=1.2,  # Louder than standard
    ),

    "excalibur_red_chrysanthemum": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_RED_CHRYSANTHEMUM,
        color=(220, 0, 0),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.4,
        intensity=1.5,
        brightness=1.2,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 150,
            "spread_angle": 360,
            "symmetry": "chrysanthemum",
            "tail_length": 2.5,  # Long tails
            "secondary_break": True,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_red_palm": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_RED_PALM,
        color=(200, 0, 0),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.3,
        brightness=1.1,
        launch_velocity=1.2,
        gravity_scale=1.4,  # Drooping palm effect
        effect_parameters={
            "star_count": 100,
            "spread_angle": 360,
            "symmetry": "palm",
            "tail_length": 3.0,  # Very long tails
            "droop_factor": 1.5,
            "report_intensity": 0.8,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.1,
    ),

    "excalibur_red_dahlia": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_RED_DAHLIA,
        color=(240, 0, 0),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.5,
        intensity=1.6,
        brightness=1.4,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 80,
            "spread_angle": 360,
            "symmetry": "dahlia",
            "petal_count": 12,
            "tail_length": 1.0,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    # ========== BLUE EFFECTS ==========
    "excalibur_blue_peony": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_BLUE_PEONY,
        color=(0, 100, 255),  # Bright blue
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.4,
        brightness=1.3,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 120,
            "spread_angle": 360,
            "symmetry": "spherical",
            "tail_length": 1.5,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_blue_chrysanthemum": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_BLUE_CHRYSANTHEMUM,
        color=(0, 120, 255),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.4,
        intensity=1.5,
        brightness=1.2,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 150,
            "spread_angle": 360,
            "symmetry": "chrysanthemum",
            "tail_length": 2.5,
            "secondary_break": True,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    # ========== GREEN EFFECTS ==========
    "excalibur_green_peony": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_GREEN_PEONY,
        color=(0, 255, 50),  # Bright green
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.4,
        brightness=1.3,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 120,
            "spread_angle": 360,
            "symmetry": "spherical",
            "tail_length": 1.5,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_green_chrysanthemum": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_GREEN_CHRYSANTHEMUM,
        color=(0, 240, 60),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.4,
        intensity=1.5,
        brightness=1.2,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 150,
            "spread_angle": 360,
            "symmetry": "chrysanthemum",
            "tail_length": 2.5,
            "secondary_break": True,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_green_palm": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_GREEN_PALM,
        color=(0, 220, 40),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.3,
        brightness=1.1,
        launch_velocity=1.2,
        gravity_scale=1.4,
        effect_parameters={
            "star_count": 100,
            "spread_angle": 360,
            "symmetry": "palm",
            "tail_length": 3.0,
            "droop_factor": 1.5,
            "report_intensity": 0.8,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.1,
    ),

    # ========== PURPLE EFFECTS ==========
    "excalibur_purple_peony": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_PURPLE_PEONY,
        color=(150, 0, 255),  # Bright purple
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.4,
        brightness=1.3,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 120,
            "spread_angle": 360,
            "symmetry": "spherical",
            "tail_length": 1.5,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_purple_chrysanthemum": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_PURPLE_CHRYSANTHEMUM,
        color=(160, 0, 240),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.4,
        intensity=1.5,
        brightness=1.2,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 150,
            "spread_angle": 360,
            "symmetry": "chrysanthemum",
            "tail_length": 2.5,
            "secondary_break": True,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_purple_palm": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_PURPLE_PALM,
        color=(140, 0, 220),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.3,
        brightness=1.1,
        launch_velocity=1.2,
        gravity_scale=1.4,
        effect_parameters={
            "star_count": 100,
            "spread_angle": 360,
            "symmetry": "palm",
            "tail_length": 3.0,
            "droop_factor": 1.5,
            "report_intensity": 0.8,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.1,
    ),

    "excalibur_purple_dahlia": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_PURPLE_DAHLIA,
        color=(170, 0, 255),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.5,
        intensity=1.6,
        brightness=1.4,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 80,
            "spread_angle": 360,
            "symmetry": "dahlia",
            "petal_count": 12,
            "tail_length": 1.0,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    # ========== YELLOW/ORANGE EFFECTS ==========
    "excalibur_yellow_peony": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_YELLOW_PEONY,
        color=(255, 255, 0),  # Bright yellow
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.4,
        brightness=1.4,  # Yellow is very bright
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 120,
            "spread_angle": 360,
            "symmetry": "spherical",
            "tail_length": 1.5,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_orange_peony": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_ORANGE_PEONY,
        color=(255, 140, 0),  # Bright orange
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.4,
        brightness=1.3,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 120,
            "spread_angle": 360,
            "symmetry": "spherical",
            "tail_length": 1.5,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    # ========== WHITE/SILVER EFFECTS ==========
    "excalibur_white_peony": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_WHITE_PEONY,
        color=(255, 255, 255),  # Pure white
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.5,
        brightness=1.5,  # Very bright
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 120,
            "spread_angle": 360,
            "symmetry": "spherical",
            "tail_length": 1.5,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_silver_brocade": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_SILVER_BROCADE,
        color=(200, 200, 200),  # Silver
        size=FireworkSize.LARGE.value,
        size_multiplier=1.4,
        intensity=1.4,
        brightness=1.2,
        launch_velocity=1.2,
        gravity_scale=1.2,
        effect_parameters={
            "star_count": 200,  # Many small stars
            "spread_angle": 360,
            "symmetry": "brocade",
            "tail_length": 2.0,
            "shimmer": True,
            "report_intensity": 0.8,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.1,
    ),

    "excalibur_gold_brocade": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_GOLD_BROCADE,
        color=(255, 215, 0),  # Gold
        size=FireworkSize.LARGE.value,
        size_multiplier=1.4,
        intensity=1.4,
        brightness=1.3,
        launch_velocity=1.2,
        gravity_scale=1.2,
        effect_parameters={
            "star_count": 200,
            "spread_angle": 360,
            "symmetry": "brocade",
            "tail_length": 2.0,
            "shimmer": True,
            "report_intensity": 0.8,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.1,
    ),

    "excalibur_silver_willow": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_SILVER_WILLOW,
        color=(220, 220, 220),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.5,
        intensity=1.3,
        brightness=1.1,
        launch_velocity=1.2,
        gravity_scale=1.6,  # Heavy droop
        effect_parameters={
            "star_count": 250,
            "spread_angle": 360,
            "symmetry": "willow",
            "tail_length": 4.0,  # Very long tails
            "droop_factor": 2.0,
            "report_intensity": 0.7,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.0,
    ),

    "excalibur_gold_willow": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_GOLD_WILLOW,
        color=(255, 200, 0),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.5,
        intensity=1.3,
        brightness=1.2,
        launch_velocity=1.2,
        gravity_scale=1.6,
        effect_parameters={
            "star_count": 250,
            "spread_angle": 360,
            "symmetry": "willow",
            "tail_length": 4.0,
            "droop_factor": 2.0,
            "report_intensity": 0.7,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.0,
    ),

    # ========== CRACKLE EFFECTS ==========
    "excalibur_silver_crackle": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_SILVER_CRACKLE,
        color=(240, 240, 240),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.4,
        brightness=1.2,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 150,
            "spread_angle": 360,
            "symmetry": "spherical",
            "crackle_intensity": 0.95,  # Very loud crackle
            "crackle_frequency": 80,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.3,  # Crackle is loud
    ),

    "excalibur_gold_crackle": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_GOLD_CRACKLE,
        color=(255, 215, 0),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.4,
        brightness=1.3,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 150,
            "spread_angle": 360,
            "symmetry": "spherical",
            "crackle_intensity": 0.95,
            "crackle_frequency": 80,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.3,
    ),

    "excalibur_titanium_crackle": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_TITANIUM_CRACKLE,
        color=(255, 255, 255),  # Bright white
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.5,
        brightness=1.4,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 150,
            "spread_angle": 360,
            "symmetry": "spherical",
            "crackle_intensity": 1.0,  # Maximum crackle
            "crackle_frequency": 100,
            "report_intensity": 1.0,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.4,  # Very loud
    ),

    # ========== STROBE EFFECTS ==========
    "excalibur_white_strobe": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_WHITE_STROBE,
        color=(255, 255, 255),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.5,
        brightness=1.6,  # Very bright flashes
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 100,
            "spread_angle": 360,
            "symmetry": "spherical",
            "strobe_frequency": 15,  # Hz
            "strobe_duration": 3.0,
            "report_intensity": 0.8,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.1,
    ),

    "excalibur_color_strobe": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_COLOR_STROBE,
        color=(255, 100, 200),  # Multi-color
        secondary_color=(100, 200, 255),
        color_gradient=True,
        size=FireworkSize.LARGE.value,
        size_multiplier=1.3,
        intensity=1.5,
        brightness=1.5,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 100,
            "spread_angle": 360,
            "symmetry": "spherical",
            "strobe_frequency": 15,
            "strobe_duration": 3.0,
            "color_change": True,
            "report_intensity": 0.8,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.1,
    ),

    # ========== MULTI-EFFECT COMBINATIONS ==========
    "excalibur_brocade_crown": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_BROCADE_CROWN,
        color=(200, 200, 200),
        secondary_color=(255, 215, 0),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.5,
        intensity=1.6,
        brightness=1.3,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 180,
            "spread_angle": 360,
            "symmetry": "crown",
            "tail_length": 2.5,
            "multi_break": True,
            "secondary_effect": "brocade",
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_crackle_crown": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_CRACKLE_CROWN,
        color=(255, 255, 255),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.5,
        intensity=1.6,
        brightness=1.4,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 150,
            "spread_angle": 360,
            "symmetry": "crown",
            "crackle_intensity": 0.9,
            "crackle_frequency": 70,
            "multi_break": True,
            "report_intensity": 1.0,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.3,
    ),

    "excalibur_palm_crackle": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_PALM_CRACKLE,
        color=(0, 255, 100),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.4,
        intensity=1.5,
        brightness=1.2,
        launch_velocity=1.2,
        gravity_scale=1.4,
        effect_parameters={
            "star_count": 120,
            "spread_angle": 360,
            "symmetry": "palm",
            "tail_length": 3.0,
            "crackle_intensity": 0.8,
            "crackle_frequency": 60,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    "excalibur_peony_crackle": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_PEONY_CRACKLE,
        color=(255, 0, 100),
        size=FireworkSize.LARGE.value,
        size_multiplier=1.4,
        intensity=1.5,
        brightness=1.3,
        launch_velocity=1.2,
        effect_parameters={
            "star_count": 130,
            "spread_angle": 360,
            "symmetry": "spherical",
            "tail_length": 1.5,
            "crackle_intensity": 0.8,
            "crackle_frequency": 60,
            "report_intensity": 0.9,
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.2,
    ),

    # ========== WHISTLING EFFECTS ==========
    "excalibur_whistling_report": VisualProperties(
        effect_type=ExcaliburEffectType.EXCALIBUR_WHISTLING_REPORT,
        color=(255, 255, 200),  # Slight yellow tint
        size=FireworkSize.LARGE.value,
        size_multiplier=1.2,
        intensity=1.3,
        brightness=1.1,
        launch_velocity=1.3,  # Fast ascent
        effect_parameters={
            "star_count": 50,  # Fewer stars, focus on report
            "spread_angle": 360,
            "symmetry": "spherical",
            "whistle_duration": 1.5,  # Whistle on ascent
            "report_intensity": 1.0,  # Maximum report
            "shell_type": "excalibur_60g"
        },
        audio_volume=1.4,  # Very loud
    ),
}

# Excalibur Effect Categories for UI Organization
EXCALIBUR_CATEGORIES = {
    "Peony Effects": [
        "excalibur_red_peony",
        "excalibur_blue_peony",
        "excalibur_green_peony",
        "excalibur_purple_peony",
        "excalibur_yellow_peony",
        "excalibur_orange_peony",
        "excalibur_white_peony",
    ],
    "Chrysanthemum Effects": [
        "excalibur_red_chrysanthemum",
        "excalibur_blue_chrysanthemum",
        "excalibur_green_chrysanthemum",
        "excalibur_purple_chrysanthemum",
    ],
    "Brocade & Willow Effects": [
        "excalibur_silver_brocade",
        "excalibur_gold_brocade",
        "excalibur_silver_willow",
        "excalibur_gold_willow",
    ],
    "Palm Tree Effects": [
        "excalibur_red_palm",
        "excalibur_green_palm",
        "excalibur_purple_palm",
    ],
    "Crackle Effects": [
        "excalibur_silver_crackle",
        "excalibur_gold_crackle",
        "excalibur_titanium_crackle",
    ],
    "Strobe Effects": [
        "excalibur_white_strobe",
        "excalibur_color_strobe",
    ],
    "Dahlia Effects": [
        "excalibur_red_dahlia",
        "excalibur_purple_dahlia",
    ],
    "Multi-Effect Combinations": [
        "excalibur_brocade_crown",
        "excalibur_crackle_crown",
        "excalibur_palm_crackle",
        "excalibur_peony_crackle",
    ],
    "Whistling Effects": [
        "excalibur_whistling_report",
    ],
}


# Helper function to get all Excalibur effect names
def get_excalibur_effect_names():
    """Get list of all Excalibur effect names"""
    return list(EXCALIBUR_EFFECTS.keys())


# Helper function to get Excalibur effects by category
def get_excalibur_effects_by_category(category: str):
    """Get Excalibur effects for a specific category"""
    return EXCALIBUR_CATEGORIES.get(category, [])


# Helper function to get all categories
def get_excalibur_categories():
    """Get list of all Excalibur effect categories"""
    return list(EXCALIBUR_CATEGORIES.keys())


# Wrapper class for compatibility with test scripts and other code
class ExcaliburEffects:
    """
    Wrapper class for Excalibur effects library

    Provides a class-based interface to the Excalibur effects data
    for compatibility with existing code and test scripts.
    """

    # Reference to the effects dictionary
    EFFECTS = {}

    @classmethod
    def _initialize(cls):
        """Initialize the EFFECTS dictionary by category"""
        if not cls.EFFECTS:
            for category, effect_names in EXCALIBUR_CATEGORIES.items():
                cls.EFFECTS[category] = {}
                for effect_name in effect_names:
                    if effect_name in EXCALIBUR_EFFECTS:
                        # Convert VisualProperties to dictionary
                        visual_props = EXCALIBUR_EFFECTS[effect_name]
                        cls.EFFECTS[category][effect_name] = visual_props.to_dict()

    @classmethod
    def get_effect(cls, effect_name: str) -> Dict[str, Any]:
        """
        Get effect configuration by name

        Args:
            effect_name: Name of the effect (e.g., "Red Peony")

        Returns:
            Dictionary with effect configuration or None if not found
        """
        cls._initialize()

        # Search through all categories
        for category_effects in cls.EFFECTS.values():
            for name, config in category_effects.items():
                # Match by display name or effect type
                if name == effect_name or config.get('shell_name') == effect_name:
                    return config

        return None

    @classmethod
    def get_all_effects(cls) -> list:
        """
        Get all effect names

        Returns:
            List of all effect names
        """
        cls._initialize()

        all_effects = []
        for category_effects in cls.EFFECTS.values():
            all_effects.extend(category_effects.keys())

        return all_effects

    @classmethod
    def get_effects_by_category(cls, category: str) -> Dict[str, Dict[str, Any]]:
        """
        Get all effects in a category

        Args:
            category: Category name

        Returns:
            Dictionary of effects in the category
        """
        cls._initialize()
        return cls.EFFECTS.get(category, {})

    @classmethod
    def get_categories(cls) -> list:
        """
        Get all category names

        Returns:
            List of category names
        """
        cls._initialize()
        return list(cls.EFFECTS.keys())


# Initialize the class on module load
ExcaliburEffects._initialize()