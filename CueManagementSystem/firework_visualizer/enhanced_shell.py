"""
Enhanced Firework Shell - Uses realistic physics for trajectory
Integrates with the new FireworkPhysics system
"""

import random
from typing import Tuple, List, Optional
from firework_physics import FireworkPhysics


class EnhancedFireworkShell:
    """
    Firework shell with realistic physics-based trajectory.
    
    Features:
    - Launches from far shore of lake
    - Realistic projectile motion with gravity and drag
    - Configurable launch angles (Excalibur mapping)
    - Burst at appropriate height in sky
    - Trail particle spawning during ascent
    """
    
    def __init__(self,
                 physics: FireworkPhysics,
                 tube_index: int,
                 launch_angle: float,
                 azimuth_angle: float = 0.0,
                 shell_type: str = "Peony",
                 color: Tuple[int, int, int] = (255, 100, 0)):
        """
        Initialize enhanced firework shell.
        
        Args:
            physics: FireworkPhysics instance
            tube_index: Tube index (0-49 for 4x5 grid)
            launch_angle: Vertical launch angle (degrees, 0-90)
            azimuth_angle: Horizontal angle (degrees, -45 to 45)
            shell_type: Type of firework effect
            color: RGB color tuple
        """
        self.physics = physics
        self.tube_index = tube_index
        self.launch_angle = launch_angle
        self.azimuth_angle = azimuth_angle
        self.shell_type = shell_type
        self.color = color
        
        # Calculate tube position offset
        # 4x5 grid: 4 rows, 5 columns
        row = tube_index // 5
        col = tube_index % 5
        
        # Spread tubes across far shore
        # Map to -1.0 to 1.0 range
        tube_x_offset = (col - 2) * 0.15  # -0.3 to 0.3
        
        # Calculate launch position
        launch_x, launch_y = physics.calculate_launch_position(tube_x_offset)
        # Position is [x, y, z] where y is depth (0) and z is vertical
        self.launch_position = [launch_x, 0.0, launch_y]  # x, depth, vertical
        
        # Current position (start at launch)
        self.position = self.launch_position.copy()
        
        # Calculate initial velocity
        vx, vy, vz = physics.calculate_launch_velocity(launch_angle, azimuth_angle)
        self.velocity = [vx, vy, vz]
        
        # Calculate burst time
        self.time_to_burst = physics.calculate_burst_time(
            vz, 
            self.launch_position[1]
        )
        
        # State tracking
        self.age = 0.0
        self.has_burst = False
        self.is_alive = True
        
        # Trail spawning - LESS FREQUENT for shorter trail
        self.trail_spawn_timer = 0.0
        self.trail_spawn_interval = 0.01  # Spawn trail ultra-frequently for ultra-smooth single solid light
        
        # COMPLETELY DISABLE smoke spawning
        self.smoke_spawn_timer = 999999.0  # Never trigger
        self.smoke_spawn_interval = 999999.0  # Never trigger
        self.launch_phase_duration = 0.0  # No launch phase
        
    def update(self, dt: float) -> bool:
        """
        Update shell physics and state.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            True if shell should spawn trail particles
        """
        if not self.is_alive:
            return False
        
        self.age += dt
        
        # Check for burst
        if not self.has_burst and self.age >= self.time_to_burst:
            self.has_burst = True
            return False
        
        # Update physics
        self.position, self.velocity = self.physics.update_position(
            self.position,
            self.velocity,
            dt
        )
        
        # Check bounds
        if not self.physics.is_in_bounds(self.position):
            self.is_alive = False
            return False
        
        # Update trail spawn timer
        self.trail_spawn_timer += dt
        should_spawn_trail = False
        if self.trail_spawn_timer >= self.trail_spawn_interval:
            should_spawn_trail = True
            self.trail_spawn_timer = 0.0
        
        return should_spawn_trail
    
    def should_spawn_smoke(self, dt: float) -> bool:
        """
        DISABLED - No smoke spawning for distant fireworks.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            Always False
        """
        return False  # NEVER spawn smoke
    
    def get_position_2d(self) -> Tuple[float, float]:
        """
        Get 2D position for rendering.
        
        Returns:
            (x, y) position in pixels where y is the vertical (z) component
        """
        return (self.position[0], self.position[2])  # x and z (vertical)
    
    def get_velocity_2d(self) -> Tuple[float, float]:
        """
        Get 2D velocity for particle effects.
        
        Returns:
            (vx, vy) velocity
        """
        # Convert from cm/s to pixels/s
        vx_pixels = self.velocity[0] * self.physics.cm_to_pixels
        vy_pixels = self.velocity[2] * self.physics.cm_to_pixels  # Use vz for vertical
        return (vx_pixels, vy_pixels)
    
    def get_burst_position(self) -> Tuple[float, float]:
        """
        Get position where shell burst.
        
        Returns:
            (x, y) position in pixels
        """
        return self.get_position_2d()
    
    def get_trail_color(self) -> Tuple[int, int, int]:
        """
        Get color for trail particles.
        
        Returns:
            RGB color tuple
        """
        # Trail is typically orange/yellow
        return (255, 200, 100)
    
    def get_smoke_color(self) -> Tuple[int, int, int]:
        """
        Get color for smoke particles.
        
        Returns:
            RGB color tuple
        """
        return (150, 150, 150)