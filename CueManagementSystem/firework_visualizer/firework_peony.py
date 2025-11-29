"""
Peony Firework - Classic spherical burst
The most common firework type, creates a perfect sphere of particles
"""

import random
from firework_visualizer.firework_base import FireworkBase


class FireworkPeony(FireworkBase):
    """
    Peony firework - Classic spherical burst.
    
    Characteristics:
    - Perfect sphere of particles
    - Single color or color variations
    - Quick burst, all particles at once
    - Medium speed particles
    - Clean, symmetrical appearance
    """
    
    def __init__(self, position, velocity, color, particle_manager):
        """Initialize Peony firework."""
        super().__init__(position, velocity, color, particle_manager)
        
        self.firework_type = "Peony"
        self.duration = 2.5
        self.max_particles = 300
        
        # Burst parameters
        self.burst_speed_min = 800  # cm/s
        self.burst_speed_max = 1500  # cm/s
        self.particle_lifetime = 2.0
        
        # Spawn all particles immediately
        self._create_burst()
    
    def _create_burst(self):
        """Create the initial burst of particles."""
        # Main burst - spherical pattern
        num_particles = 250
        
        # Use color variations for more natural look
        for i in range(num_particles):
            color = self._color_variation(self.color, variation=20)
            
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min,
                speed_max=self.burst_speed_max,
                color=color,
                lifetime=self.particle_lifetime,
                size=3.5,
                brightness=1.5
            )
        
        # Add some brighter core particles
        core_particles = 50
        for i in range(core_particles):
            # Brighter, faster particles in the center
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min * 0.7,
                speed_max=self.burst_speed_max * 0.7,
                color=(255, 255, 200),  # Bright yellow-white
                lifetime=self.particle_lifetime * 0.8,
                size=4.0,
                brightness=2.5
            )
    
    def update(self, dt):
        """Update firework state."""
        super().update(dt)
        # Peony spawns all particles at once, so no ongoing spawning
    
    def spawn_particles(self, dt):
        """Peony spawns all particles at creation."""
        pass  # All particles spawned in __init__