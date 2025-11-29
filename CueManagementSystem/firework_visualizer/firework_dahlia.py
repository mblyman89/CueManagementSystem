"""
Dahlia Firework - Large petals with distinct sections
Creates a flower-like effect with distinct petal sections
"""

import random
import math
from firework_visualizer.firework_base import FireworkBase


class FireworkDahlia(FireworkBase):
    """
    Dahlia firework - Large petals.
    
    Characteristics:
    - Distinct petal sections
    - Larger, slower particles
    - Flower-like appearance
    - Color variations per petal
    - Symmetrical structure
    """
    
    def __init__(self, position, velocity, color, particle_manager):
        """Initialize Dahlia firework."""
        super().__init__(position, velocity, color, particle_manager)
        
        self.firework_type = "Dahlia"
        self.duration = 3.0
        self.max_particles = 500
        
        # Burst parameters
        self.burst_speed_min = 600  # cm/s (slower, larger particles)
        self.burst_speed_max = 1100  # cm/s
        self.particle_lifetime = 2.8
        
        # Petal structure
        self.num_petals = 12
        self.petal_angles = []
        self.petal_colors = []
        
        # Generate petal colors
        for i in range(self.num_petals):
            angle = (2 * math.pi * i) / self.num_petals
            self.petal_angles.append(angle)
            
            # Alternate between main color and lighter variation
            if i % 2 == 0:
                self.petal_colors.append(self.color)
            else:
                # Lighter variation
                lighter = tuple(min(255, c + 40) for c in self.color)
                self.petal_colors.append(lighter)
        
        # Create initial burst
        self._create_initial_burst()
    
    def _create_initial_burst(self):
        """Create the initial burst with petal structure."""
        # Create distinct petals
        for petal_idx in range(self.num_petals):
            angle = self.petal_angles[petal_idx]
            petal_color = self.petal_colors[petal_idx]
            
            # Each petal has multiple particles
            particles_per_petal = 25
            
            for j in range(particles_per_petal):
                color = self._color_variation(petal_color, variation=15)
                
                # Petal direction with some spread
                angle_spread = math.radians(15)  # 15 degree spread per petal
                particle_angle = angle + random.uniform(-angle_spread, angle_spread)
                
                speed = random.uniform(self.burst_speed_min, self.burst_speed_max)
                
                # Mostly horizontal spread (creates flat flower)
                vx = speed * math.cos(particle_angle)
                vy = speed * math.sin(particle_angle)
                vz = random.uniform(-200, 200)  # Small vertical variation
                
                # Add shell velocity
                vx += self.velocity[0] * 0.1
                vy += self.velocity[1] * 0.1
                vz += self.velocity[2] * 0.1
                
                self._spawn_particle(
                    position=list(self.position),
                    velocity=[vx, vy, vz],
                    color=color,
                    lifetime=self.particle_lifetime,
                    size=5.0,  # Larger particles
                    brightness=1.6
                )
        
        # Bright center
        for i in range(50):
            # Yellow-white center
            center_color = (255, 240, 180)
            
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min * 0.3,
                speed_max=self.burst_speed_max * 0.3,
                color=center_color,
                lifetime=self.particle_lifetime * 0.8,
                size=6.0,
                brightness=2.5
            )
    
    def update(self, dt):
        """Update firework state."""
        super().update(dt)
    
    def spawn_particles(self, dt):
        """
        Dahlia spawns all particles at creation.
        No continuous spawning needed.
        """
        pass  # All particles spawned in __init__