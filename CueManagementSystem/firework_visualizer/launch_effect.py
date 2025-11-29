"""
Launch Effects - Flash and smoke effects for firework launches
"""

import math
import random
from firework_visualizer.config import *


class LaunchFlash:
    """
    Bright flash effect at the moment of launch.
    Creates a brief, intense light at the tube exit.
    """
    
    def __init__(self, position, color=(255, 220, 150)):
        """
        Initialize a launch flash.
        
        Args:
            position: (x, y, z) position of the flash
            color: RGB color of the flash
        """
        self.position = list(position)
        self.color = color
        self.age = 0.0
        self.duration = LAUNCH_FLASH_DURATION
        self.max_radius = LAUNCH_FLASH_RADIUS
        self.is_alive = True
        
    def update(self, dt):
        """Update flash animation."""
        self.age += dt
        if self.age >= self.duration:
            self.is_alive = False
    
    def get_intensity(self):
        """
        Get current flash intensity (0-1).
        Flash quickly fades out.
        """
        if not self.is_alive:
            return 0.0
        
        # Quick fade: intensity = 1 - (age/duration)²
        progress = self.age / self.duration
        return 1.0 - (progress * progress)
    
    def get_radius(self):
        """
        Get current flash radius.
        Flash expands quickly then fades.
        """
        if not self.is_alive:
            return 0.0
        
        progress = self.age / self.duration
        # Expand to max radius quickly, then hold
        return self.max_radius * min(1.0, progress * 3.0)
    
    def get_render_data(self):
        """
        Get data for rendering the flash.
        
        Returns:
            Dictionary with position, color, intensity, radius
        """
        intensity = self.get_intensity()
        radius = self.get_radius()
        
        # Scale color by intensity
        render_color = tuple(int(c * intensity) for c in self.color)
        
        return {
            'position': self.position,
            'color': render_color,
            'intensity': intensity,
            'radius': radius,
            'alpha': int(255 * intensity)
        }


class LaunchSmoke:
    """
    Smoke effect rising from the mortar tube.
    Managed through particle system but coordinated here.
    """
    
    def __init__(self, tube_position, tube_exit_position):
        """
        Initialize launch smoke effect.
        
        Args:
            tube_position: Base position of the tube
            tube_exit_position: Exit point of the tube
        """
        self.tube_position = list(tube_position)
        self.tube_exit = list(tube_exit_position)
        self.age = 0.0
        self.duration = LAUNCH_SMOKE_LIFETIME
        self.is_alive = True
        self.spawn_accumulator = 0.0
        
    def update(self, dt):
        """Update smoke effect."""
        self.age += dt
        if self.age >= self.duration:
            self.is_alive = False
    
    def should_spawn_particle(self, dt):
        """
        Check if it's time to spawn a smoke particle.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            True if a particle should be spawned
        """
        if not self.is_alive:
            return False
        
        # Spawn rate decreases over time
        age_factor = 1.0 - (self.age / self.duration)
        spawn_rate = LAUNCH_SMOKE_SPAWN_RATE * age_factor
        
        self.spawn_accumulator += dt * spawn_rate
        if self.spawn_accumulator >= 1.0:
            self.spawn_accumulator -= 1.0
            return True
        return False
    
    def get_smoke_particle_data(self):
        """
        Get data for spawning a smoke particle.
        
        Returns:
            Dictionary with particle spawn parameters
        """
        # Smoke rises from tube exit with random spread
        spread = 15.0 + (self.age * 10.0)  # Spread increases over time
        
        # Position near tube exit
        pos = [
            self.tube_exit[0] + random.uniform(-spread, spread),
            self.tube_exit[1] + random.uniform(-spread, spread),
            self.tube_exit[2] + random.uniform(-5, 5)
        ]
        
        # Velocity: mostly upward with some random drift
        vel = [
            random.uniform(-30, 30),
            random.uniform(-30, 30),
            random.uniform(40, 100)  # Upward
        ]
        
        # Color: gray smoke, darker at start
        age_factor = self.age / self.duration
        gray_value = int(80 + age_factor * 40)  # 80-120 range
        
        return {
            'position': pos,
            'velocity': vel,
            'color': (gray_value, gray_value, gray_value),
            'lifetime': 2.0 + random.uniform(-0.5, 0.5),
            'brightness': 0.4,
            'size': 6.0 + random.uniform(-1.0, 2.0)
        }


class LaunchEffectManager:
    """
    Manages all launch effects (flashes and smoke).
    """
    
    def __init__(self):
        """Initialize the launch effect manager."""
        self.flashes = []
        self.smoke_effects = []
        
    def create_launch_flash(self, position, color=(255, 220, 150)):
        """
        Create a new launch flash effect.
        
        Args:
            position: (x, y, z) position of the flash
            color: RGB color of the flash
        """
        flash = LaunchFlash(position, color)
        self.flashes.append(flash)
        return flash
    
    def create_launch_smoke(self, tube_position, tube_exit_position):
        """
        Create a new launch smoke effect.
        
        Args:
            tube_position: Base position of the tube
            tube_exit_position: Exit point of the tube
        """
        smoke = LaunchSmoke(tube_position, tube_exit_position)
        self.smoke_effects.append(smoke)
        return smoke
    
    def update(self, dt):
        """
        Update all effects and remove dead ones.
        
        Args:
            dt: Time step in seconds
        """
        # Update flashes
        for flash in self.flashes:
            flash.update(dt)
        
        # Update smoke effects
        for smoke in self.smoke_effects:
            smoke.update(dt)
        
        # Remove dead effects
        self.flashes = [f for f in self.flashes if f.is_alive]
        self.smoke_effects = [s for s in self.smoke_effects if s.is_alive]
    
    def get_active_flashes(self):
        """Get list of active flash effects."""
        return [f for f in self.flashes if f.is_alive]
    
    def get_active_smoke(self):
        """Get list of active smoke effects."""
        return [s for s in self.smoke_effects if s.is_alive]
    
    def get_smoke_particles_to_spawn(self, dt):
        """
        Get list of smoke particles that should be spawned this frame.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            List of particle data dictionaries
        """
        particles = []
        for smoke in self.smoke_effects:
            if smoke.should_spawn_particle(dt):
                particles.append(smoke.get_smoke_particle_data())
        return particles
    
    def clear(self):
        """Clear all effects."""
        self.flashes.clear()
        self.smoke_effects.clear()
    
    def get_stats(self):
        """
        Get statistics about active effects.
        
        Returns:
            Dictionary with effect counts
        """
        return {
            'active_flashes': len(self.flashes),
            'active_smoke': len(self.smoke_effects)
        }