"""
MultiEffect Firework - Combined effects
Creates multiple effects in sequence or simultaneously
"""

import random
from firework_visualizer.firework_base import FireworkBase


class FireworkMultiEffect(FireworkBase):
    """
    MultiEffect firework - Combined effects.
    
    Characteristics:
    - Multiple stages
    - Different colors per stage
    - Combines different patterns
    - Longer duration
    - Complex visual appearance
    """
    
    def __init__(self, position, velocity, color, particle_manager):
        """Initialize MultiEffect firework."""
        super().__init__(position, velocity, color, particle_manager)
        
        self.firework_type = "MultiEffect"
        self.duration = 4.5  # Longer for multiple stages
        self.max_particles = 1000
        
        # Stage tracking
        self.current_stage = 0
        self.stage_times = [0.0, 0.8, 1.8, 3.0]  # When each stage starts
        self.stages_triggered = [False, False, False, False]
        
        # Colors for different stages
        self.stage_colors = [
            color,  # Stage 0: Main color
            (255, 215, 0),  # Stage 1: Gold
            (192, 192, 192),  # Stage 2: Silver
            (255, 100, 100)  # Stage 3: Red
        ]
        
        # Burst parameters
        self.burst_speed_min = 700  # cm/s
        self.burst_speed_max = 1300  # cm/s
        
        # Trail parameters
        self.trail_spawn_rate = 150
        self.trail_accumulator = 0.0
    
    def update(self, dt):
        """Update firework state and trigger stages."""
        super().update(dt)
        
        # Check for stage triggers
        for i, stage_time in enumerate(self.stage_times):
            if not self.stages_triggered[i] and self.age >= stage_time:
                self.stages_triggered[i] = True
                self.current_stage = i
                self._trigger_stage(i)
    
    def _trigger_stage(self, stage: int):
        """
        Trigger a specific stage effect.
        
        Args:
            stage: Stage number (0-3)
        """
        stage_color = self.stage_colors[stage]
        
        if stage == 0:
            # Stage 0: Initial burst - spherical
            self._create_sphere_stage(stage_color, 150, 2.5)
        
        elif stage == 1:
            # Stage 1: Gold ring
            self._create_ring_stage(stage_color, 100, 2.0)
        
        elif stage == 2:
            # Stage 2: Silver crackling
            self._create_crackle_stage(stage_color, 120, 1.5)
        
        elif stage == 3:
            # Stage 3: Final burst
            self._create_sphere_stage(stage_color, 80, 1.8)
    
    def _create_sphere_stage(self, color, num_particles, lifetime):
        """Create a spherical burst stage."""
        for i in range(num_particles):
            particle_color = self._color_variation(color, variation=20)
            
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min,
                speed_max=self.burst_speed_max,
                color=particle_color,
                lifetime=lifetime,
                size=4.0,
                brightness=1.8,
                sparkle=True
            )
    
    def _create_ring_stage(self, color, num_particles, lifetime):
        """Create a ring-shaped burst stage."""
        import math
        
        for i in range(num_particles):
            particle_color = self._color_variation(color, variation=15)
            
            # Ring pattern (horizontal circle)
            angle = (2 * math.pi * i) / num_particles
            speed = random.uniform(self.burst_speed_min, self.burst_speed_max)
            
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            vz = random.uniform(-100, 100)  # Small vertical variation
            
            self._spawn_particle(
                position=list(self.position),
                velocity=[vx, vy, vz],
                color=particle_color,
                lifetime=lifetime,
                size=4.5,
                brightness=2.0,
                sparkle=True
            )
    
    def _create_crackle_stage(self, color, num_particles, lifetime):
        """Create a crackling stage."""
        for i in range(num_particles):
            particle_color = self._color_variation(color, variation=25)
            
            self._spawn_sphere_burst(
                num_particles=1,
                speed_min=self.burst_speed_min * 0.6,
                speed_max=self.burst_speed_max * 0.6,
                color=particle_color,
                lifetime=lifetime,
                size=2.5,
                brightness=2.5,
                sparkle=True
            )
    
    def spawn_particles(self, dt):
        """
        Spawn trail particles continuously.
        Creates connecting trails between stages.
        """
        if self.age > self.duration * 0.95:
            return
        
        self.trail_accumulator += dt * self.trail_spawn_rate
        
        while self.trail_accumulator >= 1.0 and self.particles_spawned < self.max_particles:
            self.trail_accumulator -= 1.0
            
            # Use current stage color
            color = self._color_variation(
                self.stage_colors[self.current_stage],
                variation=30
            )
            
            # Random position
            spread = 200
            pos = [
                self.position[0] + random.uniform(-spread, spread),
                self.position[1] + random.uniform(-spread, spread),
                self.position[2] + random.uniform(-spread, spread)
            ]
            
            # Random velocity
            vel = [
                random.uniform(-300, 300),
                random.uniform(-300, 300),
                random.uniform(-300, 300)
            ]
            
            self._spawn_particle(
                position=pos,
                velocity=vel,
                color=color,
                lifetime=1.2,
                size=3.0,
                brightness=1.5
            )