"""
Firework Physics System - Realistic projectile motion for firework shells
Handles trajectory calculations, burst timing, and particle spawning
"""

import math
import random
from typing import Tuple, List


class FireworkPhysics:
    """
    Physics engine for firework shells using realistic projectile motion.

    Based on research from fireworks simulation papers:
    - Gravity: -9.8 m/s²
    - Air drag: F_d = 0.5 * ρ * v² * C_d * A
    - Launch velocity: 50-80 m/s typical for aerial shells
    """

    # Physical constants - REDUCED for distant gentle effect
    GRAVITY = -200.0  # cm/s² (much reduced for distant gentle rise)
    AIR_DENSITY = 0.0012  # g/cm³ at sea level

    # Shell properties (typical 3-inch aerial shell)
    SHELL_MASS = 200.0  # grams
    SHELL_DIAMETER = 7.6  # cm (3 inches)
    SHELL_CROSS_SECTION = math.pi * (SHELL_DIAMETER / 2) ** 2  # cm²
    DRAG_COEFFICIENT = 0.47  # Sphere drag coefficient

    # Launch parameters - Balanced for gentle rise that reaches top
    MIN_LAUNCH_VELOCITY = 1000.0  # cm/s (10 m/s) - enough to reach top
    MAX_LAUNCH_VELOCITY = 1500.0  # cm/s (15 m/s) - enough to reach top

    # Burst parameters (adjusted for distant perspective)
    # Bursts should happen in upper portion of window (top 20-30%)
    MIN_BURST_HEIGHT = 850  # pixels from bottom (upper sky)
    MAX_BURST_HEIGHT = 950  # pixels from bottom (near top)
    BURST_HEIGHT_VARIANCE = 0.05  # ±5% variance - tighter control

    # Distance scaling factor (fireworks are far away)
    DISTANCE_SCALE = 0.35  # Scale everything to 35% for distant view

    def __init__(self, window_width: int, window_height: int):
        """
        Initialize physics system.

        Args:
            window_width: Window width in pixels
            window_height: Window height in pixels
        """
        self.window_width = window_width
        self.window_height = window_height

        # Scale factor: pixels to cm (approximate)
        # Assume window height represents ~100 meters = 10000 cm
        self.pixels_to_cm = 10000.0 / window_height
        self.cm_to_pixels = window_height / 10000.0

    def calculate_launch_position(self, tube_x_offset: float = 0.0) -> Tuple[float, float]:
        """
        Calculate launch position on far shore of lake.

        Based on the reference image:
        - Far shore is approximately 45-50% up from bottom (middle of lake)
        - Horizontal position can vary across the shore

        Args:
            tube_x_offset: Horizontal offset from center (-1.0 to 1.0)

        Returns:
            (x, y) position in pixels
        """
        # Far shore is at approximately 65% from bottom (middle of window, far shore line)
        # In Arcade, Y=0 is at BOTTOM, so 65% means 65% UP from bottom
        far_shore_y = self.window_height * 0.485  # Launch from far distant shore (halfway between 32% and 65%)

        # Horizontal position: center ± offset
        # Narrower spread due to distance perspective
        center_x = self.window_width / 2
        max_offset = self.window_width * 0.2  # ±20% of width (narrower due to distance)
        launch_x = center_x + (tube_x_offset * max_offset)

        # Clamp to safe bounds
        launch_x = max(self.window_width * 0.3, min(self.window_width * 0.7, launch_x))

        return (launch_x, far_shore_y)

    def calculate_launch_velocity(self,
                                  launch_angle: float,
                                  azimuth_angle: float = 0.0) -> Tuple[float, float, float]:
        """
        Calculate initial velocity vector from launch angles.

        Args:
            launch_angle: Vertical angle from horizontal (degrees, 0-90)
            azimuth_angle: Horizontal angle from forward (degrees, -45 to 45)

        Returns:
            (vx, vy, vz) velocity in cm/s
        """
        # Random launch velocity within realistic range
        v0 = random.uniform(self.MIN_LAUNCH_VELOCITY, self.MAX_LAUNCH_VELOCITY)

        # Convert angles to radians
        theta = math.radians(launch_angle)  # Vertical angle
        phi = math.radians(azimuth_angle)  # Horizontal angle

        # Calculate velocity components
        # vx: horizontal (left/right)
        # vy: horizontal (forward/back) - not used in 2D
        # vz: vertical (up/down)
        vx = v0 * math.cos(theta) * math.sin(phi)
        vy = 0.0  # 2D simulation
        vz = v0 * math.sin(theta)

        return (vx, vy, vz)

    def calculate_burst_time(self,
                             vz: float,
                             launch_y: float,
                             target_burst_height: float = None) -> float:
        """
        Calculate time until shell should burst.

        Uses kinematic equation accounting for reduced gravity.

        Args:
            vz: Initial vertical velocity (cm/s)
            launch_y: Launch position y (pixels)
            target_burst_height: Desired burst height (pixels), random if None

        Returns:
            Time to burst in seconds
        """
        if target_burst_height is None:
            target_burst_height = random.uniform(self.MIN_BURST_HEIGHT,
                                                 self.MAX_BURST_HEIGHT)

        # Calculate height to travel
        h_pixels = target_burst_height - launch_y
        h_cm = h_pixels * self.pixels_to_cm

        # Use kinematic equation: h = v0*t + 0.5*g*t²
        # Solve for t using quadratic formula
        a = 0.5 * self.GRAVITY
        b = vz
        c = -h_cm

        discriminant = b * b - 4 * a * c

        if discriminant < 0:
            # Can't reach height, use time to apex
            t = -vz / self.GRAVITY
        else:
            # Take the smaller positive root (ascending phase)
            t1 = (-b + math.sqrt(discriminant)) / (2 * a)
            t2 = (-b - math.sqrt(discriminant)) / (2 * a)

            # Choose the positive root that represents ascending
            if t1 > 0 and t2 > 0:
                t = min(t1, t2)
            elif t1 > 0:
                t = t1
            elif t2 > 0:
                t = t2
            else:
                t = 2.5

        # Clamp to reasonable range
        t = max(1.5, min(4.0, t))

        return t

    def update_position(self,
                        position: List[float],
                        velocity: List[float],
                        dt: float) -> Tuple[List[float], List[float]]:
        """
        Update shell position and velocity using physics.

        Applies:
        - Gravity
        - Air drag

        Args:
            position: [x, y, z] in pixels
            velocity: [vx, vy, vz] in cm/s
            dt: Time step in seconds

        Returns:
            (new_position, new_velocity) both as lists
        """
        # Convert position to cm for physics calculations
        pos_cm = [p * self.pixels_to_cm for p in position]

        # Calculate speed
        speed = math.sqrt(sum(v * v for v in velocity))

        # Calculate drag force
        if speed > 0:
            drag_force = (0.5 * self.AIR_DENSITY * speed * speed *
                          self.DRAG_COEFFICIENT * self.SHELL_CROSS_SECTION)

            # Drag acceleration (opposite to velocity)
            drag_accel = [-(v / speed) * (drag_force / self.SHELL_MASS)
                          for v in velocity]
        else:
            drag_accel = [0.0, 0.0, 0.0]

        # Total acceleration
        accel = [
            drag_accel[0],
            drag_accel[1],
            self.GRAVITY + drag_accel[2]  # Gravity + drag in z
        ]

        # Update velocity: v = v0 + a*dt
        new_velocity = [
            velocity[0] + accel[0] * dt,
            velocity[1] + accel[1] * dt,
            velocity[2] + accel[2] * dt
        ]

        # Update position: p = p0 + v*dt + 0.5*a*dt²
        new_pos_cm = [
            pos_cm[0] + velocity[0] * dt + 0.5 * accel[0] * dt * dt,
            pos_cm[1] + velocity[1] * dt + 0.5 * accel[1] * dt * dt,
            pos_cm[2] + velocity[2] * dt + 0.5 * accel[2] * dt * dt
        ]

        # Convert back to pixels
        new_position = [p * self.cm_to_pixels for p in new_pos_cm]

        return new_position, new_velocity

    def is_in_bounds(self, position: List[float]) -> bool:
        """
        Check if position is within window bounds.

        Args:
            position: [x, y, z] in pixels

        Returns:
            True if in bounds, False otherwise
        """
        x, y, _ = position

        # Add margin for particles
        margin = 50

        return (-margin <= x <= self.window_width + margin and
                -margin <= y <= self.window_height + margin)