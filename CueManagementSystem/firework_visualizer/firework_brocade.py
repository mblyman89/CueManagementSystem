"""
Brocade Firework - Crackling gold effect
Creates a shimmering gold effect with crackling particles
"""

import random
import math
from firework_visualizer.firework_base import FireworkBase


class FireworkBrocade(FireworkBase):
    """
    Brocade firework - Crackling gold effect.
    
    Characteristics:
    - Gold/silver color
    - Particles that sparkle and crackle
    - Slower expansion
    - Dense particle cloud
    - Shimmering appearance
    """
    
    def __init__(self, position, velocity, color, particle_manager):
        """Initialize Brocade firework."""
        super().__init__(position, velocity, color, particle_manager)
        
        self.firework_type = "Brocade"
        self.duration = 3.0
        self.max_particles = 600
        
        # Brocade uses gold/silver colors regardless of input
        self.gold_color = (255, 215, 0)
        self.silver_color = (192, 192, 192)
        
        # Burst parameters
        self.burst_speed_min = 500  # cm/s (slow expansion)
        self.burst_speed_max = 1000  # cm/s
        self.particle_lifetime = 2.5
        
        # Crackle parameters
        self.crackle_spawn_rate = 150  # crackles per second
        self.crackle_accumulator = 0.0
        
        # Create initial burst
        self._create_initial_burst()
    
    def _create_initial_burst(self):
        """Create the initial burst of crackling particles."""
        # Main gold particles
        num_particles = 200
        
        for i in range(num_particles):
            # Mix of gold and silver
            if random.random() < 0.7:
                color = self._color_variation(self.gold_color, variation=20)
            else:
                color = self._color_variation(self.silver_color, variation=20)
            
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min,
                speed_max=self.burst_speed_max,
                color=color,
                lifetime=self.particle_lifetime,
                size=3.0,
                brightness=2.0,
                sparkle=True  # All brocade particles sparkle
            )
        
        # Dense core of bright particles
        for i in range(50):
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min * 0.3,
                speed_max=self.burst_speed_max * 0.3,
                color=(255, 255, 200),  # Bright yellow-white
                lifetime=self.particle_lifetime * 0.8,
                size=4.0,
                brightness=3.0,
                sparkle=True
            )
    
    def update(self, dt):
        """Update firework state."""
        super().update(dt)
    
    def spawn_particles(self, dt):
        """
        Spawn crackling particles continuously.
        Creates the characteristic brocade shimmer.
        """
        if self.age > self.duration * 0.9:
            return  # Stop spawning near end
        
        self.crackle_accumulator += dt * self.crackle_spawn_rate
        
        while self.crackle_accumulator >= 1.0 and self.particles_spawned < self.max_particles:
            self.crackle_accumulator -= 1.0
            
            # Spawn a crackle particle
            # Small, bright, short-lived particles
            if random.random() < 0.6:
                color = self._color_variation(self.gold_color, variation=30)
            else:
                color = self._color_variation(self.silver_color, variation=30)
            
            # Random position in expanding cloud
            radius = self.age * 400  # Expanding radius
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
            
            # Very slow velocity (crackles don't move much)
            vel = [
                random.uniform(-100, 100),
                random.uniform(-100, 100),
                random.uniform(-100, 100)
            ]
            
            self._spawn_particle(
                position=pos,
                velocity=vel,
                color=color,
                lifetime=0.5,  # Short-lived crackles
                size=2.0,
                brightness=2.5,
                sparkle=True
            )