"""
Crackle Firework - Popping, crackling effect
Creates a dense cloud of small, popping particles
"""

import random
import math
from firework_visualizer.firework_base import FireworkBase


class FireworkCrackle(FireworkBase):
    """
    Crackle firework - Popping sounds and effects.
    
    Characteristics:
    - Dense cloud of small particles
    - Continuous popping/crackling
    - White/silver color
    - Short-lived particles
    - High spawn rate
    """
    
    def __init__(self, position, velocity, color, particle_manager):
        """Initialize Crackle firework."""
        super().__init__(position, velocity, color, particle_manager)
        
        self.firework_type = "Crackle"
        self.duration = 2.5
        self.max_particles = 1200  # Very dense
        
        # Crackle uses white/silver regardless of input color
        self.crackle_color = (255, 255, 255)
        
        # Burst parameters
        self.burst_speed_min = 400  # cm/s (slow expansion)
        self.burst_speed_max = 900  # cm/s
        self.particle_lifetime = 0.8  # Short-lived
        
        # Crackle parameters
        self.crackle_spawn_rate = 300  # Very high spawn rate
        self.crackle_accumulator = 0.0
        
        # Create initial burst
        self._create_initial_burst()
    
    def _create_initial_burst(self):
        """Create the initial burst of crackling particles."""
        # Initial cloud of particles
        num_particles = 150
        
        for i in range(num_particles):
            color = self._color_variation(self.crackle_color, variation=20)
            
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min,
                speed_max=self.burst_speed_max,
                color=color,
                lifetime=self.particle_lifetime,
                size=2.0,  # Small particles
                brightness=2.5,
                sparkle=True
            )
        
        # Dense bright core
        for i in range(50):
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min * 0.2,
                speed_max=self.burst_speed_max * 0.2,
                color=(255, 255, 255),
                lifetime=self.particle_lifetime * 1.2,
                size=3.0,
                brightness=3.0,
                sparkle=True
            )
    
    def update(self, dt):
        """Update firework state."""
        super().update(dt)
    
    def spawn_particles(self, dt):
        """
        Spawn crackling particles continuously.
        Creates the characteristic dense popping effect.
        """
        if self.age > self.duration * 0.95:
            return  # Stop spawning near end
        
        self.crackle_accumulator += dt * self.crackle_spawn_rate
        
        while self.crackle_accumulator >= 1.0 and self.particles_spawned < self.max_particles:
            self.crackle_accumulator -= 1.0
            
            # Spawn a crackle particle
            color = self._color_variation(self.crackle_color, variation=25)
            
            # Random position in expanding cloud
            radius = self.age * 350  # Expanding radius
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi)
            
            offset_x = radius * math.sin(phi) * math.cos(theta)
            offset_y = radius * math.sin(phi) * math.sin(theta)
            offset_z = radius * math.cos(phi)
            
            pos = [
                self.position[0] + offset_x,
                self.position[1] + offset_y,
                self.position[2] + offset_z
            ]
            
            # Random velocity (crackles pop in all directions)
            vel = [
                random.uniform(-200, 200),
                random.uniform(-200, 200),
                random.uniform(-200, 200)
            ]
            
            self._spawn_particle(
                position=pos,
                velocity=vel,
                color=color,
                lifetime=random.uniform(0.3, 0.6),  # Very short-lived
                size=1.5,  # Very small
                brightness=2.0,
                sparkle=True
            )