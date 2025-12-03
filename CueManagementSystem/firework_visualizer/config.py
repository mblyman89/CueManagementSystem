"""
Configuration Module - REALISTIC LAKE SCENE VERSION
All settings and constants for the Firework Visualizer
Updated to match the beautiful reference photo with dock and realistic mortar placement

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

# ============================================
# WINDOW SETTINGS
# ============================================
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
SCREEN_WIDTH = 1920  # Alias for compatibility
SCREEN_HEIGHT = 1080  # Alias for compatibility
WINDOW_TITLE = "Firework Visualizer - Realistic Lake Scene"
SCREEN_TITLE = "Firework Visualizer - Realistic Lake Scene"  # Alias for compatibility
TARGET_FPS = 60

# ============================================
# CAMERA SETTINGS (Optimized for full firework view)
# ============================================
# Camera positioned to show full scene: dock in foreground, fireworks in sky
CAMERA_POSITION = (0, -2500, 120)  # Further back, lower to ground
CAMERA_ROTATION = (-3, 0, 0)  # Slight upward tilt to see more sky
CAMERA_FOV = 85  # Wider FOV to capture full firework trajectory
CAMERA_NEAR = 10
CAMERA_FAR = 500000

# ============================================
# COORDINATE SYSTEM (UE5 Compatible)
# ============================================
# X = Right/Left
# Y = Forward/Backward
# Z = Up/Down
# Units: Centimeters

# ============================================
# SCENE SETTINGS - REALISTIC LAKE
# ============================================

# Water (Calm lake surface with reflections)
WATER_COLOR = (15, 25, 45)  # Dark blue water
WATER_REFLECTION_ALPHA = 0.5  # More visible reflections
WATER_REFLECTION_COLOR = (20, 30, 55)  # Slightly lighter for reflections
WATER_WAVE_HEIGHT = 0.3  # Very calm water
WATER_WAVE_SPEED = 0.05  # Slow, gentle movement
WATER_SEGMENTS = 50  # Smoother water surface
WATER_LEVEL_Z = -60  # Z position of water surface

# Sky (Night sky with stars - enhanced for realism)
SKY_TOP_COLOR = (10, 15, 35)  # Deep night blue at zenith
SKY_MID_COLOR = (25, 40, 70)  # Mid-sky transition
SKY_HORIZON_COLOR = (40, 60, 100)  # Lighter blue at horizon
SKY_COLOR_BOTTOM = (40, 60, 100)  # Alias for SKY_HORIZON_COLOR
SKY_STAR_COUNT = 500  # More stars for realism
SKY_MILKY_WAY = True  # Enable Milky Way effect
MILKY_WAY_COLOR = (60, 70, 120)  # Brighter, more visible
MILKY_WAY_ALPHA = 0.35  # More prominent
MILKY_WAY_WIDTH = 800  # Width of Milky Way band in pixels
MILKY_WAY_PARTICLE_COUNT = 1000  # Particles for Milky Way effect

# Dock (Realistic perspective from camera position)
DOCK_LENGTH = 3000  # 30 meters - extends far into water
DOCK_WIDTH = 250  # 2.5 meters wide
DOCK_HEIGHT = 20  # Visible plank thickness
DOCK_POSITION = (0, -800, -55)  # Starts in foreground, extends to distance
DOCK_PLANK_COUNT = 35  # More planks for length
DOCK_PLANK_WIDTH = 85  # Width of each plank (with gaps)
DOCK_PLANK_GAP = 5  # Gap between planks
DOCK_COLOR = (70, 50, 30)  # Weathered wood color
DOCK_COLOR_VARIATION = 15  # Color variation between planks
DOCK_SHOW_GRAIN = True
DOCK_WEATHERED = True

# Distant Shore (Horizon line with silhouetted trees)
SHORE_DISTANCE = 150000  # 1.5km away
SHORE_TREE_COUNT = 80  # More trees for fuller horizon
SHORE_HEIGHT_VARIATION = 40  # Varied treeline
SHORE_BASE_HEIGHT = 50  # Base height of shore
SHORE_COLOR = (10, 15, 25)  # Very dark silhouette
SHORE_TREE_COLOR = (5, 10, 20)  # Even darker for trees
HORIZON_LINE_Y = 400  # Y position of horizon line on screen (pixels from bottom)

# ============================================
# MORTAR RACK SETTINGS - REALISTIC BOXES
# ============================================

# Rack Dimensions (Smaller, more realistic boxes)
RACK_WIDTH = 50  # 50cm wide (smaller boxes)
RACK_DEPTH = 35  # 35cm deep
RACK_HEIGHT = 25  # 25cm tall (low profile)

# Rack Positioning (On the end of the dock)
RACK_GRID_ROWS = 4  # 4 rows
RACK_GRID_COLS = 5  # 5 columns = 20 racks total
RACK_ROWS = 4  # Alias for RACK_GRID_ROWS
RACK_COLS = 5  # Alias for RACK_GRID_COLS
RACK_SPACING_X = 60  # 60cm between racks (side to side)
RACK_SPACING_Y = 45  # 45cm between rows (front to back)
RACK_START_POSITION = (-150, 800, -35)  # On the far end of dock

# Rack Appearance (Simple wooden boxes)
RACK_COLOR = (70, 50, 30)  # Dark wood
RACK_SHOW_TUBES = False  # Don't render individual tubes
RACK_SHOW_WOOD_GRAIN = True
RACK_WEATHERED = True

# Tube Configuration (Invisible but tracked)
TUBES_PER_RACK = 50  # 5 rows × 10 columns
TUBE_ROWS = 5
TUBE_COLS = 10
TUBE_DIAMETER = 7.62  # 3 inches
TUBE_LENGTH = 30  # 30cm
TUBE_BASE_ANGLE = 85  # Degrees from horizontal
TUBE_ANGLE_VARIATION = 2  # ±2 degrees

# ============================================
# PHYSICS SETTINGS
# ============================================
GRAVITY = -980  # cm/s² (Earth gravity)
AIR_DRAG = 0.98  # Exponential drag coefficient
WIND_FORCE = (5, 0, 0)  # Slight breeze (cm/s²)
WIND_SPEED = 5  # Wind speed in cm/s
WIND_DIRECTION = 90  # Wind direction in degrees (0=North, 90=East, 180=South, 270=West)

# ============================================
# PARTICLE SYSTEM
# ============================================
MAX_PARTICLES = 100000  # Maximum particle count
PARTICLE_POOL_SIZE = 100000  # Pre-allocated pool
PARTICLE_RENDER_DISTANCE = 100000  # Render distance in cm
PARTICLE_CULL_FRUSTUM = True  # Enable frustum culling
PARTICLE_DEPTH_SORT = True  # Sort for proper transparency

# Particle Rendering
PARTICLE_BASE_SIZE = 3  # Base particle size
PARTICLE_GLOW_ENABLED = True
PARTICLE_GLOW_RADIUS = 8
PARTICLE_TRAIL_LENGTH = 5
PARTICLE_TRAIL_FADE = 0.85

# ============================================
# LAUNCH SYSTEM
# ============================================
SHELL_MASS = 60  # grams (Excalibur 60g)
SHELL_LAUNCH_VELOCITY = 30000  # cm/s (670 mph)
LAUNCH_VELOCITY = 30000  # Alias for SHELL_LAUNCH_VELOCITY
SHELL_TARGET_ALTITUDE = 76200  # cm (250 feet)
SHELL_THRUST_DURATION = 0.8  # seconds
SHELL_TRAIL_PARTICLES = 20  # particles per frame

# Launch Effects
LAUNCH_FLASH_DURATION = 0.1  # seconds
LAUNCH_FLASH_RADIUS = 30  # cm
LAUNCH_SMOKE_PARTICLES = 50
LAUNCH_SMOKE_DURATION = 2.0  # seconds
LAUNCH_SMOKE_LIFETIME = 2.0  # Alias for LAUNCH_SMOKE_DURATION
LAUNCH_SMOKE_SPAWN_RATE = 25  # particles per second

# Shell physics constants
SHELL_DRAG_COEFFICIENT = 0.47  # Drag coefficient for sphere
SHELL_CROSS_SECTION = 45.6  # Cross-sectional area in cm² (3 inch diameter)

# Launch phase constants
LAUNCH_DURATION = 0.5  # seconds of powered flight
LAUNCH_ACCELERATION = 15000  # cm/s² during powered phase
LAUNCH_TRAIL_SPAWN_RATE = 50  # trail particles per second during launch
LAUNCH_TRAIL_LIFETIME = 1.0  # seconds for trail particles
BURST_TIME_VARIANCE = 0.2  # seconds of random variance in burst timing

# ============================================
# FIREWORK EFFECTS
# ============================================

# Burst Parameters (Adjusted to stay in camera view)
BURST_ALTITUDE = 50000  # cm (164 feet) - Lower to stay in view
BURST_HEIGHT = 50000  # Alias for BURST_ALTITUDE
BURST_DIAMETER = 30000  # cm (98 feet) - Proportionally smaller
BURST_PARTICLE_COUNT = {
    'peony': 200,
    'chrysanthemum': 300,
    'brocade': 250,
    'willow': 200,
    'palm': 180,
    'dahlia': 220,
    'crackle': 150,
    'multieffect': 280
}

# Effect Durations (seconds)
EFFECT_DURATION = {
    'peony': 2.5,
    'chrysanthemum': 3.5,
    'brocade': 3.0,
    'willow': 4.5,
    'palm': 4.0,
    'dahlia': 3.0,
    'crackle': 2.0,
    'multieffect': 4.0
}

# ============================================
# AUDIO SETTINGS
# ============================================
AUDIO_ENABLED = True
AUDIO_MASTER_VOLUME = 0.7
AUDIO_DISTANCE_FALLOFF = True
AUDIO_SPEED_OF_SOUND = 34300  # cm/s
AUDIO_MAX_DISTANCE = 300000  # cm

# Audio Presets
AUDIO_PRESET = "NORMAL"  # QUIET, NORMAL, LOUD
AUDIO_VOLUMES = {
    'QUIET': {'launch': 0.3, 'explosion': 0.4, 'crackle': 0.2},
    'NORMAL': {'launch': 0.6, 'explosion': 0.8, 'crackle': 0.5},
    'LOUD': {'launch': 0.9, 'explosion': 1.0, 'crackle': 0.8}
}

# ============================================
# VISUAL EFFECTS
# ============================================
BLOOM_ENABLED = True
BLOOM_THRESHOLD = 0.7
BLOOM_INTENSITY = 0.3
BLOOM_RADIUS = 15

WATER_REFLECTIONS = True
REFLECTION_QUALITY = "MEDIUM"  # LOW, MEDIUM, HIGH

ATMOSPHERIC_FOG = True
FOG_DENSITY = 0.00001
FOG_COLOR = (15, 20, 35)

# Rendering optimization
CULLING_DISTANCE = 50000  # Distance beyond which particles are not rendered (in cm)

# ============================================
# RENDERING LAYERS
# ============================================
LAYER_BACKGROUND = 0  # Sky
LAYER_WATER = 1  # Water surface
LAYER_ENVIRONMENT = 2  # Dock, shore, trees
LAYER_RACKS = 3  # Mortar racks (boxes only)
LAYER_PARTICLES = 4  # Firework particles
LAYER_EFFECTS = 5  # Flash, smoke, glow
LAYER_UI = 6  # Debug info, FPS

# ============================================
# DEBUG SETTINGS
# ============================================
DEBUG_MODE = False
SHOW_FPS = True
SHOW_PARTICLE_COUNT = True
SHOW_RACK_INFO = False
SHOW_TUBE_INFO = False
SHOW_CAMERA_INFO = False

# ============================================
# EXCALIBUR SHELL SPECIFICATIONS
# ============================================
EXCALIBUR_SHELLS = {
    # Peony Variants (4)
    'red_peony': {
        'type': 'peony',
        'color': (255, 50, 50),
        'brightness': 2.5,
        'duration': 2.5
    },
    'blue_peony': {
        'type': 'peony',
        'color': (50, 100, 255),
        'brightness': 2.3,
        'duration': 2.5
    },
    'white_peony': {
        'type': 'peony',
        'color': (255, 255, 255),
        'brightness': 3.0,
        'duration': 2.5
    },
    'purple_peony': {
        'type': 'peony',
        'color': (200, 50, 255),
        'brightness': 2.4,
        'duration': 2.5
    },

    # Chrysanthemum Variants (4)
    'gold_chrysanthemum': {
        'type': 'chrysanthemum',
        'color': (255, 200, 50),
        'brightness': 2.8,
        'duration': 3.5
    },
    'silver_chrysanthemum': {
        'type': 'chrysanthemum',
        'color': (220, 220, 255),
        'brightness': 2.6,
        'duration': 3.5
    },
    'red_chrysanthemum': {
        'type': 'chrysanthemum',
        'color': (255, 60, 60),
        'brightness': 2.7,
        'duration': 3.5
    },
    'green_chrysanthemum': {
        'type': 'chrysanthemum',
        'color': (50, 255, 100),
        'brightness': 2.5,
        'duration': 3.5
    },

    # Brocade Variants (4)
    'gold_brocade': {
        'type': 'brocade',
        'color': (255, 180, 50),
        'brightness': 2.6,
        'duration': 3.0
    },
    'silver_brocade': {
        'type': 'brocade',
        'color': (200, 200, 240),
        'brightness': 2.4,
        'duration': 3.0
    },
    'red_brocade': {
        'type': 'brocade',
        'color': (255, 70, 70),
        'brightness': 2.5,
        'duration': 3.0
    },
    'blue_brocade': {
        'type': 'brocade',
        'color': (70, 120, 255),
        'brightness': 2.3,
        'duration': 3.0
    },

    # Willow Variants (3)
    'gold_willow': {
        'type': 'willow',
        'color': (255, 200, 80),
        'brightness': 2.4,
        'duration': 4.5
    },
    'silver_willow': {
        'type': 'willow',
        'color': (220, 220, 255),
        'brightness': 2.2,
        'duration': 4.5
    },
    'purple_willow': {
        'type': 'willow',
        'color': (180, 80, 255),
        'brightness': 2.3,
        'duration': 4.5
    },

    # Palm Variants (3)
    'gold_palm': {
        'type': 'palm',
        'color': (255, 190, 70),
        'brightness': 2.5,
        'duration': 4.0
    },
    'silver_palm': {
        'type': 'palm',
        'color': (210, 210, 250),
        'brightness': 2.3,
        'duration': 4.0
    },
    'red_palm': {
        'type': 'palm',
        'color': (255, 80, 80),
        'brightness': 2.4,
        'duration': 4.0
    },

    # Dahlia Variants (3)
    'red_dahlia': {
        'type': 'dahlia',
        'color': (255, 60, 60),
        'brightness': 2.6,
        'duration': 3.0
    },
    'blue_dahlia': {
        'type': 'dahlia',
        'color': (60, 110, 255),
        'brightness': 2.4,
        'duration': 3.0
    },
    'purple_dahlia': {
        'type': 'dahlia',
        'color': (190, 60, 255),
        'brightness': 2.5,
        'duration': 3.0
    },

    # Crackle Variants (2)
    'gold_crackle': {
        'type': 'crackle',
        'color': (255, 200, 100),
        'brightness': 2.2,
        'duration': 2.0
    },
    'silver_crackle': {
        'type': 'crackle',
        'color': (230, 230, 255),
        'brightness': 2.0,
        'duration': 2.0
    },

    # Multi-Effect (1)
    'patriot': {
        'type': 'multieffect',
        'color': (255, 255, 255),
        'brightness': 2.8,
        'duration': 4.0
    }
}

# ============================================
# ENHANCED SCENE RENDERING SETTINGS
# ============================================

# Layer System Configuration
ENABLE_PARALLAX_SCROLLING = True
PARALLAX_CAMERA_SPEED = 0.5  # How fast camera moves for parallax effect

# Background Layer Settings
BACKGROUND_STAR_COUNT = 600
BACKGROUND_ENABLE_MILKY_WAY = True
BACKGROUND_ENABLE_NEBULA = True
BACKGROUND_MOUNTAIN_COUNT = 2  # Number of mountain ranges
BACKGROUND_SHORE_TREE_COUNT = 40

# Water Rendering Settings
WATER_ENABLE_REFLECTIONS = True
WATER_REFLECTION_INTENSITY = 0.6  # 0.0 to 1.0
WATER_ENABLE_SHADOWS = True
WATER_SHADOW_INTENSITY = 0.5
WATER_COLOR_ZONES = 4  # Number of depth-based color zones
WATER_GRADIENT_SMOOTHNESS = 20  # Higher = smoother gradients

# Dock Rendering Settings
DOCK_PLANK_DETAIL_LEVEL = 0.4  # 0.0 to 1.0, percentage of planks with details
DOCK_ENABLE_WOOD_GRAIN = True
DOCK_ENABLE_KNOTS = True
DOCK_ENABLE_SHADOWS = True
DOCK_PERSPECTIVE_ENABLED = True

# Atmospheric Effects Settings
ATMOSPHERE_ENABLE_DEPTH_FOG = True
ATMOSPHERE_FOG_DENSITY = 0.3  # 0.0 to 1.0
ATMOSPHERE_ENABLE_HAZE = True
ATMOSPHERE_HAZE_INTENSITY = 0.5
ATMOSPHERE_ENABLE_VIGNETTE = True
ATMOSPHERE_VIGNETTE_INTENSITY = 0.6
ATMOSPHERE_ENABLE_COLOR_GRADING = True
ATMOSPHERE_ENABLE_AMBIENT_PARTICLES = False  # Optional performance impact

# Color Palette for Night Scene (Darker to match reference)
NIGHT_SKY_DEEP = (5, 8, 18)
NIGHT_SKY_MID = (10, 15, 30)
NIGHT_SKY_HORIZON = (15, 25, 45)
NIGHT_WATER_DEEP = (8, 15, 30)
NIGHT_WATER_MID = (12, 22, 40)
NIGHT_WATER_NEAR = (18, 32, 55)
NIGHT_FOG_COLOR = (10, 15, 28)
NIGHT_HAZE_COLOR = (12, 18, 32)

# Wood Color Palette (Darker, more weathered)
WOOD_COLORS = [
    (80, 55, 35),
    (90, 60, 40),
    (70, 50, 30),
    (85, 58, 38),
    (75, 52, 32),
]

# Mortar Rack Visual Settings
MORTAR_RACK_COLOR = (40, 35, 30)
MORTAR_RACK_TUBE_COLOR = (50, 45, 40)
MORTAR_RACK_TUBES_PER_RACK = 5

