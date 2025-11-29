"""
Configuration file for Firework Visualizer
All constants and settings in one place for easy customization
"""

# ============================================================================
# WINDOW SETTINGS
# ============================================================================
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
SCREEN_TITLE = "Firework Visualizer - Lake Scene"
TARGET_FPS = 60

# ============================================================================
# COORDINATE SYSTEM
# ============================================================================
# Matching UE5 coordinate system:
# X = Right (positive to the right)
# Y = Forward (positive away from camera)
# Z = Up (positive upward)
# Units: Centimeters

# Camera settings
CAMERA_POSITION = (0, -800, 300)  # X, Y, Z in cm
CAMERA_ROTATION = (-10, 0, 0)     # Pitch, Yaw, Roll in degrees
CAMERA_FOV = 90                    # Field of view in degrees

# ============================================================================
# SCENE DIMENSIONS (in centimeters)
# ============================================================================
# Dock dimensions
DOCK_WIDTH = 1219    # 12.19 meters
DOCK_DEPTH = 244     # 2.44 meters
DOCK_HEIGHT = 61     # 0.61 meters
DOCK_POSITION = (0, 400, 0)  # Centered, 4 meters in front of racks

# Mortar rack dimensions
RACK_WIDTH = 96.52   # Width of each rack
RACK_DEPTH = 63.5    # Depth of each rack
RACK_HEIGHT = 38.1   # Height of each rack
RACK_SPACING = 50    # Space between racks

# Rack grid layout (20 racks total)
RACK_ROWS = 4        # 4 rows
RACK_COLS = 5        # 5 columns

# Tubes per rack
TUBES_PER_RACK = 50  # 5 rows × 10 columns
TUBE_ROWS = 5
TUBE_COLS = 10
TUBE_DIAMETER = 7.62  # 3 inches = 7.62 cm
TUBE_LENGTH = 30      # Approximate tube length

# Total tubes
TOTAL_RACKS = RACK_ROWS * RACK_COLS  # 20 racks
TOTAL_TUBES = TOTAL_RACKS * TUBES_PER_RACK  # 1000 tubes

# ============================================================================
# PHYSICS CONSTANTS
# ============================================================================
GRAVITY = -980       # cm/s² (Earth gravity)
AIR_DRAG = 0.98      # Drag coefficient (0-1, 1 = no drag)
WIND_SPEED = 0       # cm/s (can be adjusted)
WIND_DIRECTION = 0   # degrees (0 = north, 90 = east)

# Firework physics
LAUNCH_VELOCITY = 30000      # cm/s (300 m/s = ~670 mph)
LAUNCH_ACCELERATION = 50000  # cm/s² (initial thrust)
LAUNCH_DURATION = 0.3        # seconds of powered flight
BURST_HEIGHT = 76200         # 250 feet = 76,200 cm
BURST_DIAMETER = 45720       # 150 feet = 45,720 cm
PARTICLE_LIFETIME_MIN = 1.0  # seconds
PARTICLE_LIFETIME_MAX = 3.0  # seconds

# Shell properties
SHELL_MASS = 60.0            # grams (Excalibur 60g shell)
SHELL_DRAG_COEFFICIENT = 0.47  # Sphere drag coefficient
SHELL_CROSS_SECTION = 28.27  # cm² (3" diameter = 7.62cm radius)
BURST_TIME_VARIANCE = 0.2    # ±20% variance in burst timing

# Launch effects
LAUNCH_TRAIL_SPAWN_RATE = 200   # particles per second
LAUNCH_TRAIL_LIFETIME = 1.5     # seconds
LAUNCH_SMOKE_SPAWN_RATE = 50    # particles per second
LAUNCH_SMOKE_LIFETIME = 3.0     # seconds
LAUNCH_FLASH_DURATION = 0.1     # seconds
LAUNCH_FLASH_RADIUS = 50.0      # cm

# ============================================================================
# VISUAL SETTINGS
# ============================================================================
# Colors (RGB)
SKY_COLOR_TOP = (10, 15, 35)        # Dark blue night sky
SKY_COLOR_BOTTOM = (25, 35, 60)     # Lighter at horizon
WATER_COLOR = (15, 25, 45)          # Dark blue water
DOCK_COLOR = (101, 67, 33)          # Brown wood
RACK_COLOR = (139, 90, 43)          # Lighter brown wood

# Lighting
AMBIENT_LIGHT = 0.3      # 0-1, overall scene brightness
EXPLOSION_LIGHT = 1.0    # 0-1, brightness of firework explosions
BLOOM_INTENSITY = 0.8    # 0-1, glow effect strength

# Particle settings
PARTICLE_SIZE_MIN = 2    # pixels
PARTICLE_SIZE_MAX = 8    # pixels
PARTICLE_ALPHA_START = 255  # 0-255
PARTICLE_ALPHA_END = 0      # 0-255

# ============================================================================
# AUDIO SETTINGS
# ============================================================================
MASTER_VOLUME = 0.7      # 0-1
LAUNCH_VOLUME = 0.5      # 0-1
EXPLOSION_VOLUME = 0.8   # 0-1
CRACKLE_VOLUME = 0.4     # 0-1
AMBIENT_VOLUME = 0.2     # 0-1

# Speed of sound (for distance delay)
SPEED_OF_SOUND = 34300   # cm/s (343 m/s)

# ============================================================================
# PERFORMANCE SETTINGS
# ============================================================================
MAX_PARTICLES = 50000    # Maximum particles on screen
PARTICLE_POOL_SIZE = 100000  # Pre-allocated particle pool
CULLING_DISTANCE = 100000    # cm, particles beyond this are culled
LOD_DISTANCE_NEAR = 50000    # cm, full detail
LOD_DISTANCE_FAR = 80000     # cm, reduced detail

# ============================================================================
# EXCALIBUR SHELL SPECIFICATIONS
# ============================================================================
# Shell types and their base effects
SHELL_TYPES = {
    1: {"name": "Red Peony", "type": "Peony", "color": (255, 50, 50)},
    2: {"name": "Blue Peony", "type": "Peony", "color": (50, 100, 255)},
    3: {"name": "Green Peony", "type": "Peony", "color": (50, 255, 100)},
    4: {"name": "Purple Peony", "type": "Peony", "color": (200, 50, 255)},
    5: {"name": "Gold Chrysanthemum", "type": "Chrysanthemum", "color": (255, 215, 0)},
    6: {"name": "Silver Chrysanthemum", "type": "Chrysanthemum", "color": (192, 192, 192)},
    7: {"name": "Red Chrysanthemum", "type": "Chrysanthemum", "color": (255, 50, 50)},
    8: {"name": "Blue Chrysanthemum", "type": "Chrysanthemum", "color": (50, 100, 255)},
    9: {"name": "Gold Brocade", "type": "Brocade", "color": (255, 215, 0)},
    10: {"name": "Silver Brocade", "type": "Brocade", "color": (192, 192, 192)},
    11: {"name": "Red Brocade", "type": "Brocade", "color": (255, 50, 50)},
    12: {"name": "Green Brocade", "type": "Brocade", "color": (50, 255, 100)},
    13: {"name": "Gold Willow", "type": "Willow", "color": (255, 215, 0)},
    14: {"name": "Silver Willow", "type": "Willow", "color": (192, 192, 192)},
    15: {"name": "Purple Willow", "type": "Willow", "color": (200, 50, 255)},
    16: {"name": "Red Palm", "type": "Palm", "color": (255, 50, 50)},
    17: {"name": "Green Palm", "type": "Palm", "color": (50, 255, 100)},
    18: {"name": "Gold Palm", "type": "Palm", "color": (255, 215, 0)},
    19: {"name": "Red Dahlia", "type": "Dahlia", "color": (255, 50, 50)},
    20: {"name": "Blue Dahlia", "type": "Dahlia", "color": (50, 100, 255)},
    21: {"name": "Purple Dahlia", "type": "Dahlia", "color": (200, 50, 255)},
    22: {"name": "Gold Crackle", "type": "Crackle", "color": (255, 215, 0)},
    23: {"name": "Silver Crackle", "type": "Crackle", "color": (192, 192, 192)},
    24: {"name": "Rainbow Multi-Effect", "type": "MultiEffect", "color": (255, 255, 255)},
}

# ============================================================================
# DEBUG SETTINGS
# ============================================================================
DEBUG_MODE = False       # Show debug info
SHOW_FPS = True         # Display FPS counter
SHOW_PARTICLE_COUNT = True  # Display particle count
SHOW_WIREFRAME = False  # Show wireframe rendering