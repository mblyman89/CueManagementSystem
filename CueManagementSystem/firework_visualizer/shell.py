"""
Firework Shell - Represents a physical firework shell in flight
Handles trajectory physics, wind effects, and burst timing
"""

import math
import random
from firework_visualizer.config import *


class FireworkShell:
    """
    Represents a firework shell in flight with realistic physics.
    
    The shell experiences:
    - Initial launch velocity from mortar tube
    - Gravity pulling it down
    - Air drag slowing it down
    - Wind pushing it sideways
    - Powered flight during launch phase
    """
    
    def __init__(self, tube, shell_type="Peony", color=(255, 100, 0)):
        """
        Initialize a firework shell.
        
        Args:
            tube: MortarTube object that launched this shell
            shell_type: Type of firework effect (Peony, Chrysanthemum, etc.)
            color: RGB color tuple for the burst
        """
        self.tube = tube
        self.shell_type = shell_type
        self.color = color
        
        # Position (start at tube exit)
        self.position = list(tube.get_exit_position())
        
        # Velocity (launch direction * launch velocity)
        launch_dir = tube.get_launch_direction()
        self.velocity = [
            launch_dir[0] * LAUNCH_VELOCITY,
            launch_dir[1] * LAUNCH_VELOCITY,
            launch_dir[2] * LAUNCH_VELOCITY
        ]
        
        # Physics properties
        self.mass = SHELL_MASS  # grams
        self.drag_coefficient = SHELL_DRAG_COEFFICIENT
        self.cross_section = SHELL_CROSS_SECTION  # cm²
        
        # Launch phase tracking
        self.launch_time = 0.0
        self.is_powered = True  # True during powered flight
        
        # Burst timing
        self.time_to_burst = self._calculate_burst_time()
        self.has_burst = False
        
        # Lifetime tracking
        self.age = 0.0
        self.is_alive = True
        
        # Trail tracking for particle spawning
        self.trail_spawn_accumulator = 0.0
        self.smoke_spawn_accumulator = 0.0
        
    def _calculate_burst_time(self):
        """
        Calculate when the shell should burst based on target altitude.
        Includes random variance for realism.
        """
        # Estimate time to reach burst height using kinematic equations
        # This is approximate since we have drag, but good enough
        v0 = self.velocity[2]  # Initial vertical velocity
        g = GRAVITY
        h = BURST_HEIGHT
        
        # Using: h = v0*t + 0.5*g*t²
        # Solving quadratic: 0.5*g*t² + v0*t - h = 0
        a = 0.5 * g
        b = v0
        c = -h
        
        discriminant = b*b - 4*a*c
        if discriminant < 0:
            # Can't reach target height, burst at apex
            return -v0 / g
        
        t = (-b - math.sqrt(discriminant)) / (2*a)
        
        # Add variance
        variance = random.uniform(-BURST_TIME_VARIANCE, BURST_TIME_VARIANCE)
        t *= (1.0 + variance)
        
        return max(0.5, t)  # At least 0.5 seconds
    
    def update(self, dt):
        """
        Update shell physics and check for burst condition.
        
        Args:
            dt: Time step in seconds
        """
        if not self.is_alive:
            return
        
        self.age += dt
        self.launch_time += dt
        
        # Check if powered flight has ended
        if self.is_powered and self.launch_time >= LAUNCH_DURATION:
            self.is_powered = False
        
        # Apply forces
        forces = [0.0, 0.0, 0.0]
        
        # 1. Gravity (always present)
        forces[2] += GRAVITY * self.mass
        
        # 2. Powered thrust (only during launch phase)
        if self.is_powered:
            # Apply thrust in launch direction
            launch_dir = self.tube.get_launch_direction()
            thrust = LAUNCH_ACCELERATION * self.mass
            forces[0] += launch_dir[0] * thrust
            forces[1] += launch_dir[1] * thrust
            forces[2] += launch_dir[2] * thrust
        
        # 3. Air drag (F = 0.5 * ρ * v² * Cd * A)
        # Simplified: F = k * v² where k includes all constants
        speed = math.sqrt(sum(v*v for v in self.velocity))
        if speed > 0:
            # Air density at sea level: ~0.0012 g/cm³
            air_density = 0.0012
            drag_force = 0.5 * air_density * speed * speed * self.drag_coefficient * self.cross_section
            
            # Apply drag opposite to velocity direction
            drag_dir = [-v/speed for v in self.velocity]
            forces[0] += drag_dir[0] * drag_force
            forces[1] += drag_dir[1] * drag_force
            forces[2] += drag_dir[2] * drag_force
        
        # 4. Wind force (simplified)
        if WIND_SPEED > 0:
            wind_force = WIND_SPEED * 0.1 * self.mass  # Simplified wind effect
            wind_rad = math.radians(WIND_DIRECTION)
            forces[0] += math.sin(wind_rad) * wind_force
            forces[1] += math.cos(wind_rad) * wind_force
        
        # Apply forces to velocity (F = ma, so a = F/m)
        acceleration = [f / self.mass for f in forces]
        self.velocity[0] += acceleration[0] * dt
        self.velocity[1] += acceleration[1] * dt
        self.velocity[2] += acceleration[2] * dt
        
        # Update position
        self.position[0] += self.velocity[0] * dt
        self.position[1] += self.velocity[1] * dt
        self.position[2] += self.velocity[2] * dt
        
        # Check for burst condition
        if not self.has_burst and self.age >= self.time_to_burst:
            self.has_burst = True
            # Burst will be handled by launch_system
        
        # Check if shell has fallen below ground or gone too far
        if self.position[2] < -100 or self.age > 10.0:
            self.is_alive = False
    
    def should_spawn_trail_particle(self, dt):
        """
        Check if it's time to spawn a trail particle.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            True if a trail particle should be spawned
        """
        self.trail_spawn_accumulator += dt * LAUNCH_TRAIL_SPAWN_RATE
        if self.trail_spawn_accumulator >= 1.0:
            self.trail_spawn_accumulator -= 1.0
            return True
        return False
    
    def should_spawn_smoke_particle(self, dt):
        """
        Check if it's time to spawn a smoke particle.
        Only spawn smoke during powered flight.
        
        Args:
            dt: Time step in seconds
            
        Returns:
            True if a smoke particle should be spawned
        """
        if not self.is_powered:
            return False
            
        self.smoke_spawn_accumulator += dt * LAUNCH_SMOKE_SPAWN_RATE
        if self.smoke_spawn_accumulator >= 1.0:
            self.smoke_spawn_accumulator -= 1.0
            return True
        return False
    
    def get_trail_particle_data(self):
        """
        Get data for spawning a trail particle.
        
        Returns:
            Dictionary with particle spawn parameters
        """
        # Trail particles spawn slightly behind the shell
        offset = [-v * 0.01 for v in self.velocity]  # 1cm behind
        
        return {
            'position': [
                self.position[0] + offset[0],
                self.position[1] + offset[1],
                self.position[2] + offset[2]
            ],
            'velocity': [v * 0.3 for v in self.velocity],  # 30% of shell velocity
            'color': (255, 200, 100),  # Bright yellow-orange
            'lifetime': LAUNCH_TRAIL_LIFETIME,
            'brightness': 2.0,
            'size': 4.0
        }
    
    def get_smoke_particle_data(self):
        """
        Get data for spawning a smoke particle.
        
        Returns:
            Dictionary with particle spawn parameters
        """
        # Smoke spawns at tube exit with random spread
        spread = 20.0  # cm
        
        return {
            'position': [
                self.tube.position[0] + random.uniform(-spread, spread),
                self.tube.position[1] + random.uniform(-spread, spread),
                self.tube.position[2] + self.tube.length + random.uniform(0, spread)
            ],
            'velocity': [
                random.uniform(-50, 50),
                random.uniform(-50, 50),
                random.uniform(50, 150)  # Upward bias
            ],
            'color': (100, 100, 100),  # Gray smoke
            'lifetime': LAUNCH_SMOKE_LIFETIME,
            'brightness': 0.5,
            'size': 8.0
        }
    
    def get_burst_data(self):
        """
        Get data for the burst effect.
        
        Returns:
            Dictionary with burst parameters
        """
        return {
            'position': list(self.position),
            'velocity': list(self.velocity),
            'shell_type': self.shell_type,
            'color': self.color,
            'burst_diameter': BURST_DIAMETER
        }