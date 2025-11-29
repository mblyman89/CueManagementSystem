"""
Chrysanthemum Firework - Trailing particles with long tails
Creates a flower-like effect with particles that leave trails
"""

import random
import math
from firework_visualizer.firework_base import FireworkBase


class FireworkChrysanthemum(FireworkBase):
    """
    Chrysanthemum firework - Trailing particles.
    
    Characteristics:
    - Particles leave long trails
    - Slower moving particles
    - Graceful, flowing appearance
    - Multiple stages of particle spawning
    - Creates "flower petal" effect
    """
    
    def __init__(self, position, velocity, color, particle_manager):
        """Initialize Chrysanthemum firework."""
        super().__init__(position, velocity, color, particle_manager)
        
        self.firework_type = "Chrysanthemum"
        self.duration = 3.5
        self.max_particles = 500
        
        # Burst parameters
        self.burst_speed_min = 600  # cm/s (slower than Peony)
        self.burst_speed_max = 1200  # cm/s
        self.particle_lifetime = 3.0  # Longer lifetime
        
        # Trail parameters
        self.trail_spawn_rate = 100  # trails per second
        self.trail_accumulator = 0.0
        
        # Create initial burst
        self._create_initial_burst()
    
    def _create_initial_burst(self):
        """Create the initial burst of main particles."""
        # Main particles that will leave trails
        num_main_particles = 150
        
        for i in range(num_main_particles):
            color = self._color_variation(self.color, variation=15)
            
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min,
                speed_max=self.burst_speed_max,
                color=color,
                lifetime=self.particle_lifetime,
                size=4.0,
                brightness=1.8,
                sparkle=True  # Main particles sparkle
            )
        
        # Bright core
        for i in range(30):
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min * 0.5,
                speed_max=self.burst_speed_max * 0.5,
                color=(255, 240, 200),
                lifetime=self.particle_lifetime * 0.7,
                size=5.0,
                brightness=2.5
            )
    
    def update(self, dt):
        """Update firework state."""
        super().update(dt)
    
    def spawn_particles(self, dt):
        """
        Spawn trail particles continuously.
        Chrysanthemum creates trailing effects.
        """
        if self.age > self.duration * 0.8:
            return  # Stop spawning near end
        
        self.trail_accumulator += dt * self.trail_spawn_rate
        
        while self.trail_accumulator >= 1.0 and self.particles_spawned < self.max_particles:
            self.trail_accumulator -= 1.0
            
            # Spawn a trail particle
            # These are smaller, dimmer particles that create the trail effect
            color = self._color_variation(self.color, variation=25)
            
            # Random position near burst center (simulating trail behind main particles)
            offset = 100  # cm
            pos = [
                self.position[0] + random.uniform(-offset, offset),
                self.position[1] + random.uniform(-offset, offset),
                self.position[2] + random.uniform(-offset, offset)
            ]
            
            # Slower, more random velocity
            vel = [
                random.uniform(-300, 300),
                random.uniform(-300, 300),
                random.uniform(-300, 300)
            ]
            
            self._spawn_particle(
                position=pos,
                velocity=vel,
                color=color,
                lifetime=1.5,
                size=2.5,
                brightness=1.0
            )