"""
Palm Firework - Thick rising trails like palm fronds
Creates thick, rising trails that curve upward
"""

import random
import math
from firework_visualizer.firework_base import FireworkBase


class FireworkPalm(FireworkBase):
    """
    Palm firework - Thick rising trails.
    
    Characteristics:
    - Thick, rising trails
    - Particles curve upward
    - Dense particle streams
    - Creates palm tree frond effect
    - Continuous dense spawning
    """
    
    def __init__(self, position, velocity, color, particle_manager):
        """Initialize Palm firework."""
        super().__init__(position, velocity, color, particle_manager)
        
        self.firework_type = "Palm"
        self.duration = 3.5
        self.max_particles = 1000  # Dense effect
        
        # Burst parameters
        self.burst_speed_min = 800  # cm/s
        self.burst_speed_max = 1400  # cm/s
        self.particle_lifetime = 3.0
        
        # Trail parameters
        self.trail_spawn_rate = 250  # Dense trails
        self.trail_accumulator = 0.0
        
        # Number of main "fronds"
        self.num_fronds = 8
        self.frond_angles = []
        
        # Create initial burst with frond structure
        self._create_initial_burst()
    
    def _create_initial_burst(self):
        """Create the initial burst with palm frond structure."""
        # Create main fronds at specific angles
        for i in range(self.num_fronds):
            angle = (2 * math.pi * i) / self.num_fronds
            self.frond_angles.append(angle)
            
            # Each frond has multiple particles
            particles_per_frond = 20
            
            for j in range(particles_per_frond):
                color = self._color_variation(self.color, variation=15)
                
                # Frond direction (outward and upward)
                speed = random.uniform(self.burst_speed_min, self.burst_speed_max)
                
                # Horizontal component
                vx = speed * math.cos(angle) * 0.7
                vy = speed * math.sin(angle) * 0.7
                # Strong upward component
                vz = speed * 0.8 + random.uniform(0, 200)
                
                # Add shell velocity
                vx += self.velocity[0] * 0.1
                vy += self.velocity[1] * 0.1
                vz += self.velocity[2] * 0.1
                
                self._spawn_particle(
                    position=list(self.position),
                    velocity=[vx, vy, vz],
                    color=color,
                    lifetime=self.particle_lifetime,
                    size=4.5,
                    brightness=1.8,
                    sparkle=True
                )
        
        # Bright core
        for i in range(40):
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min * 0.3,
                speed_max=self.burst_speed_max * 0.3,
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
        Spawn trail particles continuously along fronds.
        Creates the characteristic thick palm trails.
        """
        if self.age > self.duration * 0.9:
            return  # Stop spawning near end
        
        self.trail_accumulator += dt * self.trail_spawn_rate
        
        while self.trail_accumulator >= 1.0 and self.particles_spawned < self.max_particles:
            self.trail_accumulator -= 1.0
            
            # Spawn trail particle along a random frond
            frond_angle = random.choice(self.frond_angles)
            
            color = self._color_variation(self.color, variation=25)
            
            # Position along frond path
            distance = self.age * 500  # Distance traveled
            spread = 100  # Spread around frond line
            
            pos = [
                self.position[0] + distance * math.cos(frond_angle) * 0.7 + random.uniform(-spread, spread),
                self.position[1] + distance * math.sin(frond_angle) * 0.7 + random.uniform(-spread, spread),
                self.position[2] + distance * 0.8 + random.uniform(-spread, spread)
            ]
            
            # Velocity continues upward and outward
            vel = [
                300 * math.cos(frond_angle) + random.uniform(-100, 100),
                300 * math.sin(frond_angle) + random.uniform(-100, 100),
                400 + random.uniform(-100, 100)  # Strong upward
            ]
            
            self._spawn_particle(
                position=pos,
                velocity=vel,
                color=color,
                lifetime=1.8,
                size=3.0,
                brightness=1.5
            )