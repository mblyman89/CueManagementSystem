"""
Willow Firework - Drooping trails like a weeping willow tree
Creates long, drooping trails that fall gracefully
"""

import random
import math
from firework_visualizer.firework_base import FireworkBase


class FireworkWillow(FireworkBase):
    """
    Willow firework - Drooping trails.
    
    Characteristics:
    - Long, drooping trails
    - Particles fall gracefully
    - Slower initial speed
    - Creates weeping willow effect
    - Continuous trail spawning
    """
    
    def __init__(self, position, velocity, color, particle_manager):
        """Initialize Willow firework."""
        super().__init__(position, velocity, color, particle_manager)
        
        self.firework_type = "Willow"
        self.duration = 4.0  # Longer duration for drooping effect
        self.max_particles = 800
        
        # Burst parameters
        self.burst_speed_min = 700  # cm/s
        self.burst_speed_max = 1300  # cm/s
        self.particle_lifetime = 3.5  # Long lifetime for trails
        
        # Trail parameters
        self.trail_spawn_rate = 200  # trails per second
        self.trail_accumulator = 0.0
        
        # Create initial burst
        self._create_initial_burst()
    
    def _create_initial_burst(self):
        """Create the initial burst of main particles."""
        # Main particles that will create drooping trails
        num_particles = 120
        
        for i in range(num_particles):
            color = self._color_variation(self.color, variation=20)
            
            # Willow particles start with upward bias
            theta = random.uniform(0, 2 * math.pi)
            phi = random.uniform(0, math.pi * 0.6)  # Bias toward upward
            
            speed = random.uniform(self.burst_speed_min, self.burst_speed_max)
            
            vx = speed * math.sin(phi) * math.cos(theta)
            vy = speed * math.sin(phi) * math.sin(theta)
            vz = speed * math.cos(phi) + 300  # Extra upward velocity
            
            # Add shell velocity
            vx += self.velocity[0] * 0.1
            vy += self.velocity[1] * 0.1
            vz += self.velocity[2] * 0.1
            
            self._spawn_particle(
                position=list(self.position),
                velocity=[vx, vy, vz],
                color=color,
                lifetime=self.particle_lifetime,
                size=4.0,
                brightness=1.5,
                sparkle=True
            )
        
        # Bright core
        for i in range(30):
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min * 0.4,
                speed_max=self.burst_speed_max * 0.4,
                color=(255, 240, 200),
                lifetime=self.particle_lifetime * 0.6,
                size=5.0,
                brightness=2.5
            )
    
    def update(self, dt):
        """Update firework state."""
        super().update(dt)
    
    def spawn_particles(self, dt):
        """
        Spawn trail particles continuously.
        Creates the characteristic drooping willow effect.
        """
        if self.age > self.duration * 0.85:
            return  # Stop spawning near end
        
        self.trail_accumulator += dt * self.trail_spawn_rate
        
        while self.trail_accumulator >= 1.0 and self.particles_spawned < self.max_particles:
            self.trail_accumulator -= 1.0
            
            # Spawn a trail particle
            # These fall behind the main particles, creating drooping effect
            color = self._color_variation(self.color, variation=30)
            
            # Position spreads out over time
            spread = self.age * 300
            pos = [
                self.position[0] + random.uniform(-spread, spread),
                self.position[1] + random.uniform(-spread, spread),
                self.position[2] + random.uniform(-spread * 0.5, spread * 0.3)  # Less vertical spread
            ]
            
            # Downward velocity bias (drooping)
            vel = [
                random.uniform(-200, 200),
                random.uniform(-200, 200),
                random.uniform(-400, -100)  # Downward bias
            ]
            
            self._spawn_particle(
                position=pos,
                velocity=vel,
                color=color,
                lifetime=2.0,
                size=2.5,
                brightness=1.2
            )