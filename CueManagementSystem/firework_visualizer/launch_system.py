"""
Launch System - Coordinates firework shell launches
Manages shells, trails, smoke, and flash effects
"""

import random
from firework_visualizer.shell import FireworkShell
from firework_visualizer.launch_effect import LaunchEffectManager
from firework_visualizer.firework_factory import FireworkFactory
from firework_visualizer.config import *


class LaunchSystem:
    """
    Main launch system that coordinates all aspects of firework launches.
    
    Responsibilities:
    - Launch shells from mortar tubes
    - Track active shells in flight
    - Coordinate trail particle spawning
    - Manage launch effects (flash, smoke)
    - Detect burst conditions
    - Interface with particle system for visual effects
    """
    
    def __init__(self, rack_system, particle_manager, audio_system=None):
        """
        Initialize the launch system.
        
        Args:
            rack_system: RackSystem instance for accessing tubes
            particle_manager: ParticleManager instance for spawning particles
            audio_system: AudioSystem instance for sound effects (optional)
        """
        self.rack_system = rack_system
        self.particle_manager = particle_manager
        self.effect_manager = LaunchEffectManager()
        self.audio_system = audio_system
        
        # Active shells in flight
        self.active_shells = []
        
        # Statistics
        self.total_launches = 0
        self.total_bursts = 0
        
        # Burst callback (will be set by game to trigger firework effects)
        self.burst_callback = None
        
    def launch_shell(self, tube_id, shell_type="Peony", color=(255, 100, 0)):
        """
        Launch a firework shell from a specific tube.
        
        Args:
            tube_id: Global tube ID (0-999)
            shell_type: Type of firework effect
            color: RGB color tuple
            
        Returns:
            FireworkShell instance or None if tube not found
        """
        # Get the tube
        tube = self.rack_system.get_tube_by_global_id(tube_id)
        if not tube:
            print(f"Warning: Tube {tube_id} not found")
            return None
        
        # Create the shell
        shell = FireworkShell(tube, shell_type, color)
        self.active_shells.append(shell)
        
        # Create launch effects
        tube_pos = tube.position
        exit_pos = tube.get_exit_position()
        
        # Flash at tube exit
        self.effect_manager.create_launch_flash(exit_pos, (255, 220, 150))
        
        # Smoke from tube
        self.effect_manager.create_launch_smoke(tube_pos, exit_pos)
        
        # Play launch sound
        if self.audio_system:
            self.audio_system.play_launch_sound(exit_pos)
        
        # Statistics
        self.total_launches += 1
        
        return shell
    
    def launch_random_shell(self, shell_type="Peony", color=None):
        """
        Launch a shell from a random tube.
        
        Args:
            shell_type: Type of firework effect
            color: RGB color tuple (random if None)
            
        Returns:
            FireworkShell instance
        """
        # Random tube
        tube_id = random.randint(0, TOTAL_TUBES - 1)
        
        # Random color if not specified
        if color is None:
            color = (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255)
            )
        
        return self.launch_shell(tube_id, shell_type, color)
    
    def launch_sequence(self, tube_ids, shell_type="Peony", color=(255, 100, 0), delay=0.1):
        """
        Launch a sequence of shells with delays.
        Note: This is a simple version. For complex sequences, use the
        CueManagementSystem integration.
        
        Args:
            tube_ids: List of tube IDs to launch
            shell_type: Type of firework effect
            color: RGB color tuple
            delay: Delay between launches (seconds)
        """
        # This would need a timer system for proper implementation
        # For now, just launch them all at once
        for tube_id in tube_ids:
            self.launch_shell(tube_id, shell_type, color)
    
    def update(self, dt):
        """
        Update all active shells and effects.
        
        Args:
            dt: Time step in seconds
        """
        # Update all shells
        for shell in self.active_shells:
            shell.update(dt)
            
            # Spawn trail particles
            if shell.should_spawn_trail_particle(dt):
                trail_data = shell.get_trail_particle_data()
                self._spawn_trail_particle(trail_data)
            
            # Spawn smoke particles (during powered flight)
            if shell.should_spawn_smoke_particle(dt):
                smoke_data = shell.get_smoke_particle_data()
                self._spawn_smoke_particle(smoke_data)
            
            # Check for burst
            if shell.has_burst and not hasattr(shell, '_burst_triggered'):
                shell._burst_triggered = True
                self._trigger_burst(shell)
        
        # Update launch effects
        self.effect_manager.update(dt)
        
        # Spawn smoke particles from launch effects
        smoke_particles = self.effect_manager.get_smoke_particles_to_spawn(dt)
        for particle_data in smoke_particles:
            self._spawn_smoke_particle(particle_data)
        
        # Remove dead shells
        self.active_shells = [s for s in self.active_shells if s.is_alive]
    
    def _spawn_trail_particle(self, data):
        """
        Spawn a trail particle behind the shell.
        
        Args:
            data: Dictionary with particle parameters
        """
        self.particle_manager.spawn_particle(
            position=data['position'],
            velocity=data['velocity'],
            color=data['color'],
            lifetime=data['lifetime'],
            brightness=data['brightness'],
            size=data['size']
        )
    
    def _spawn_smoke_particle(self, data):
        """
        Spawn a smoke particle.
        
        Args:
            data: Dictionary with particle parameters
        """
        self.particle_manager.spawn_particle(
            position=data['position'],
            velocity=data['velocity'],
            color=data['color'],
            lifetime=data['lifetime'],
            brightness=data['brightness'],
            size=data['size']
        )
    
    def _trigger_burst(self, shell):
        """
        Trigger the burst effect for a shell.
        
        Args:
            shell: FireworkShell that has burst
        """
        self.total_bursts += 1
        
        # Get burst data
        burst_data = shell.get_burst_data()
        
        # Play explosion sound
        if self.audio_system:
            self.audio_system.play_explosion_sound(
                burst_data['position'],
                burst_data['shell_type']
            )
        
        # Call burst callback if set (this will trigger the actual firework effect)
        if self.burst_callback:
            self.burst_callback(burst_data)
        else:
            # Default: create firework using factory
            self._create_firework_burst(burst_data)
    
    def _create_firework_burst(self, burst_data):
        """
        Create a firework burst using the factory.
        
        Args:
            burst_data: Dictionary with burst parameters
        """
        position = burst_data['position']
        velocity = burst_data['velocity']
        shell_type = burst_data['shell_type']
        color = burst_data['color']
        
        # Create firework using factory
        firework = FireworkFactory.create_firework(
            shell_type,
            position,
            velocity,
            color,
            self.particle_manager
        )
        
        # Store firework for updates (will be managed by game_view)
        # For now, firework spawns its particles immediately
        return firework
    
    def set_burst_callback(self, callback):
        """
        Set the callback function for burst events.
        
        Args:
            callback: Function that takes burst_data dictionary
        """
        self.burst_callback = callback
    
    def get_active_shells(self):
        """Get list of active shells."""
        return self.active_shells
    
    def get_active_flashes(self):
        """Get list of active flash effects."""
        return self.effect_manager.get_active_flashes()
    
    def clear_all(self):
        """Clear all active shells and effects."""
        self.active_shells.clear()
        self.effect_manager.clear()
    
    def get_stats(self):
        """
        Get launch system statistics.
        
        Returns:
            Dictionary with statistics
        """
        effect_stats = self.effect_manager.get_stats()
        
        return {
            'active_shells': len(self.active_shells),
            'total_launches': self.total_launches,
            'total_bursts': self.total_bursts,
            'active_flashes': effect_stats['active_flashes'],
            'active_smoke': effect_stats['active_smoke']
        }
    
    def print_stats(self):
        """Print launch system statistics."""
        stats = self.get_stats()
        print("\n=== Launch System Statistics ===")
        print(f"Active Shells: {stats['active_shells']}")
        print(f"Total Launches: {stats['total_launches']}")
        print(f"Total Bursts: {stats['total_bursts']}")
        print(f"Active Flashes: {stats['active_flashes']}")
        print(f"Active Smoke Effects: {stats['active_smoke']}")
        print("================================\n")