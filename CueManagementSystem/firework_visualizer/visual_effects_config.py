"""
Visual Effects Configuration
Settings for advanced visual effects and rendering enhancements
"""

# ============================================================================
# BLOOM & GLOW SETTINGS
# ============================================================================
BLOOM_ENABLED = True
BLOOM_INTENSITY = 0.8        # 0-1, strength of bloom effect
BLOOM_THRESHOLD = 0.7        # 0-1, brightness threshold for bloom
BLOOM_RADIUS = 15.0          # pixels, bloom spread radius

# Particle glow settings
PARTICLE_GLOW_ENABLED = True
PARTICLE_GLOW_MULTIPLIER = 1.5  # Brightness multiplier for glowing particles
PARTICLE_GLOW_SIZE = 1.3        # Size multiplier for glow halo

# ============================================================================
# WATER REFLECTION SETTINGS
# ============================================================================
WATER_REFLECTIONS_ENABLED = True
REFLECTION_INTENSITY = 0.6    # 0-1, strength of reflections
REFLECTION_BLUR = 2.0         # Amount of blur on reflections
REFLECTION_DISTORTION = 0.3   # Wave distortion on reflections

# ============================================================================
# ATMOSPHERIC EFFECTS
# ============================================================================
ATMOSPHERIC_GLOW_ENABLED = True
ATMOSPHERIC_INTENSITY = 0.4   # 0-1, ambient glow from fireworks
ATMOSPHERIC_FALLOFF = 0.95    # How quickly glow fades (0-1)
ATMOSPHERIC_COLOR_BLEND = 0.3 # How much firework color affects sky

# Light pollution effect
LIGHT_POLLUTION_ENABLED = True
LIGHT_POLLUTION_RADIUS = 500  # cm, radius of light effect
LIGHT_POLLUTION_INTENSITY = 0.5  # 0-1, strength of effect

# ============================================================================
# PARTICLE TRAIL ENHANCEMENTS
# ============================================================================
ENHANCED_TRAILS_ENABLED = True
TRAIL_FADE_SMOOTHNESS = 0.9   # 0-1, how smoothly trails fade
TRAIL_MOTION_BLUR = True      # Enable motion blur on fast particles
TRAIL_GLOW_INTENSITY = 1.2    # Brightness of trail glow

# ============================================================================
# COLOR GRADING
# ============================================================================
COLOR_GRADING_ENABLED = True
CONTRAST = 1.1                # >1 increases contrast
SATURATION = 1.15             # >1 increases color saturation
BRIGHTNESS = 1.0              # Overall brightness adjustment
GAMMA = 1.0                   # Gamma correction

# Color temperature
COLOR_TEMPERATURE = 6500      # Kelvin, 6500 = neutral, <6500 = warm, >6500 = cool

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================
# Quality presets
QUALITY_PRESET = 'HIGH'  # 'LOW', 'MEDIUM', 'HIGH', 'ULTRA'

QUALITY_PRESETS = {
    'LOW': {
        'bloom_enabled': False,
        'water_reflections': False,
        'atmospheric_glow': False,
        'enhanced_trails': False,
        'particle_glow_multiplier': 1.0,
    },
    'MEDIUM': {
        'bloom_enabled': True,
        'bloom_intensity': 0.5,
        'water_reflections': False,
        'atmospheric_glow': True,
        'atmospheric_intensity': 0.3,
        'enhanced_trails': True,
        'particle_glow_multiplier': 1.2,
    },
    'HIGH': {
        'bloom_enabled': True,
        'bloom_intensity': 0.8,
        'water_reflections': True,
        'reflection_intensity': 0.6,
        'atmospheric_glow': True,
        'atmospheric_intensity': 0.4,
        'enhanced_trails': True,
        'particle_glow_multiplier': 1.5,
    },
    'ULTRA': {
        'bloom_enabled': True,
        'bloom_intensity': 1.0,
        'water_reflections': True,
        'reflection_intensity': 0.8,
        'atmospheric_glow': True,
        'atmospheric_intensity': 0.5,
        'enhanced_trails': True,
        'particle_glow_multiplier': 2.0,
        'trail_motion_blur': True,
    }
}

def apply_quality_preset(preset_name):
    """
    Apply a quality preset to visual effects settings.
    
    Args:
        preset_name: Name of preset ('LOW', 'MEDIUM', 'HIGH', 'ULTRA')
    """
    global BLOOM_ENABLED, BLOOM_INTENSITY, WATER_REFLECTIONS_ENABLED
    global REFLECTION_INTENSITY, ATMOSPHERIC_GLOW_ENABLED, ATMOSPHERIC_INTENSITY
    global ENHANCED_TRAILS_ENABLED, PARTICLE_GLOW_MULTIPLIER, TRAIL_MOTION_BLUR
    
    preset = QUALITY_PRESETS.get(preset_name.upper())
    if not preset:
        print(f"Warning: Unknown preset '{preset_name}', using HIGH")
        preset = QUALITY_PRESETS['HIGH']
    
    # Apply preset settings
    BLOOM_ENABLED = preset.get('bloom_enabled', BLOOM_ENABLED)
    BLOOM_INTENSITY = preset.get('bloom_intensity', BLOOM_INTENSITY)
    WATER_REFLECTIONS_ENABLED = preset.get('water_reflections', WATER_REFLECTIONS_ENABLED)
    REFLECTION_INTENSITY = preset.get('reflection_intensity', REFLECTION_INTENSITY)
    ATMOSPHERIC_GLOW_ENABLED = preset.get('atmospheric_glow', ATMOSPHERIC_GLOW_ENABLED)
    ATMOSPHERIC_INTENSITY = preset.get('atmospheric_intensity', ATMOSPHERIC_INTENSITY)
    ENHANCED_TRAILS_ENABLED = preset.get('enhanced_trails', ENHANCED_TRAILS_ENABLED)
    PARTICLE_GLOW_MULTIPLIER = preset.get('particle_glow_multiplier', PARTICLE_GLOW_MULTIPLIER)
    TRAIL_MOTION_BLUR = preset.get('trail_motion_blur', TRAIL_MOTION_BLUR)
    
    print(f"Applied visual effects preset: {preset_name.upper()}")

def get_current_settings():
    """Get current visual effects settings as dictionary."""
    return {
        'bloom_enabled': BLOOM_ENABLED,
        'bloom_intensity': BLOOM_INTENSITY,
        'water_reflections': WATER_REFLECTIONS_ENABLED,
        'reflection_intensity': REFLECTION_INTENSITY,
        'atmospheric_glow': ATMOSPHERIC_GLOW_ENABLED,
        'atmospheric_intensity': ATMOSPHERIC_INTENSITY,
        'enhanced_trails': ENHANCED_TRAILS_ENABLED,
        'particle_glow_multiplier': PARTICLE_GLOW_MULTIPLIER,
        'color_grading': COLOR_GRADING_ENABLED,
        'contrast': CONTRAST,
        'saturation': SATURATION,
    }

def print_current_settings():
    """Print current visual effects settings."""
    print("\n" + "=" * 60)
    print("VISUAL EFFECTS SETTINGS")
    print("=" * 60)
    print(f"Quality Preset: {QUALITY_PRESET}")
    print(f"\nBloom & Glow:")
    print(f"  Enabled: {BLOOM_ENABLED}")
    print(f"  Intensity: {BLOOM_INTENSITY}")
    print(f"  Particle Glow: {PARTICLE_GLOW_MULTIPLIER}x")
    print(f"\nWater Reflections:")
    print(f"  Enabled: {WATER_REFLECTIONS_ENABLED}")
    print(f"  Intensity: {REFLECTION_INTENSITY}")
    print(f"\nAtmospheric Effects:")
    print(f"  Enabled: {ATMOSPHERIC_GLOW_ENABLED}")
    print(f"  Intensity: {ATMOSPHERIC_INTENSITY}")
    print(f"\nParticle Trails:")
    print(f"  Enhanced: {ENHANCED_TRAILS_ENABLED}")
    print(f"  Motion Blur: {TRAIL_MOTION_BLUR}")
    print(f"\nColor Grading:")
    print(f"  Enabled: {COLOR_GRADING_ENABLED}")
    print(f"  Contrast: {CONTRAST}")
    print(f"  Saturation: {SATURATION}")
    print("=" * 60)