"""
Enhanced Launch System - Integrates physics-based shells with particle effects
Manages the complete firework lifecycle from launch to burst
"""

import random
from typing import List, Tuple, Optional, Dict
from enhanced_shell import EnhancedFireworkShell
from firework_physics import FireworkPhysics
from firework_particles import FireworkParticleSystem


class EnhancedLaunchSystem:
    """
    Complete launch system for realistic fireworks.

    Features:
    - Physics-based shell trajectories
    - Particle effects (trails, bursts, explosions)
    - Excalibur shell mapping support
    - Multiple simultaneous fireworks
    """

    def __init__(self, window_width: int, window_height: int):
        """
        Initialize enhanced launch system.

        Args:
            window_width: Window width in pixels
            window_height: Window height in pixels
        """
        self.window_width = window_width
        self.window_height = window_height

        # Initialize physics and particle systems
        self.physics = FireworkPhysics(window_width, window_height)
        self.particles = FireworkParticleSystem(window_width, window_height)

        # Active shells
        self.active_shells: List[EnhancedFireworkShell] = []

        # Statistics
        self.total_launches = 0
        self.total_bursts = 0

        # Excalibur shell type mapping - each type gets its own effect
        self.shell_type_map = {
            "peony": "peony",  # Classic dense sphere
            "chrysanthemum": "chrysanthemum",  # Sphere with trailing sparkles
            "willow": "willow",  # Slow falling particles
            "palm": "palm",  # Upward trails
            "dahlia": "dahlia",  # Very dense tight burst
            "brocade": "brocade",  # Crown pattern
            "crackle": "crackle",  # Small sparkles
            "multieffect": "multieffect"  # Combination effect
        }

        # Color palettes for different effects
        self.color_palettes = {
            "red": [(255, 50, 50), (255, 100, 100), (255, 150, 150)],
            "orange": [(255, 150, 50), (255, 180, 80), (255, 200, 100)],
            "yellow": [(255, 255, 100), (255, 255, 150), (255, 255, 200)],
            "green": [(50, 255, 50), (100, 255, 100), (150, 255, 150)],
            "blue": [(50, 150, 255), (100, 180, 255), (150, 200, 255)],
            "purple": [(200, 50, 255), (220, 100, 255), (240, 150, 255)],
            "white": [(255, 255, 255), (240, 240, 240), (220, 220, 220)],
            "gold": [(255, 215, 0), (255, 230, 50), (255, 240, 100)]
        }

    def launch_shell(self,
                     tube_index: int,
                     launch_angle: float,
                     azimuth_angle: float = 0.0,
                     shell_type: str = "peony",
                     color_name: str = "random") -> EnhancedFireworkShell:
        """
        Launch a firework shell.

        Args:
            tube_index: Tube index (0-49 for 4x5 grid)
            launch_angle: Vertical launch angle (degrees, 0-90)
            azimuth_angle: Horizontal angle (degrees, -45 to 45)
            shell_type: Type of firework effect
            color_name: Color palette name or "random"

        Returns:
            EnhancedFireworkShell instance
        """
        # Select color
        if color_name == "random":
            color_name = random.choice(list(self.color_palettes.keys()))

        colors = self.color_palettes.get(color_name, self.color_palettes["white"])
        color = random.choice(colors)

        # Create shell
        shell = EnhancedFireworkShell(
            physics=self.physics,
            tube_index=tube_index,
            launch_angle=launch_angle,
            azimuth_angle=azimuth_angle,
            shell_type=shell_type,
            color=color
        )

        self.active_shells.append(shell)
        self.total_launches += 1

        # NO launch smoke - too far away to see from distance
        # Just a small flash at launch
        launch_pos = shell.get_position_2d()

        # Get explosion type for debug
        explosion_type = self.shell_type_map.get(shell.shell_type.lower(), "sphere")

        print(f"\n🚀 LAUNCH:")
        print(f"  Shell Type: {shell.shell_type}")
        print(f"  Effect Type: {explosion_type}")
        print(f"  Position: {launch_pos}")
        print(f"  Color: RGB{shell.color}")
        print(f"  Burst Time: {shell.time_to_burst:.2f}s")
        print(f"  3D Position: {shell.position}")
        print(f"  Velocity: {shell.velocity}")

        self.particles.create_launch_flash(launch_pos)

        return shell

    def launch_excalibur_shell(self,
                               output_number: int,
                               shell_data: Dict) -> Optional[EnhancedFireworkShell]:
        """
        Launch a shell using Excalibur output mapping.

        Args:
            output_number: Output number (1-1000)
            shell_data: Dictionary with shell parameters from config

        Returns:
            EnhancedFireworkShell instance or None if invalid
        """
        if output_number < 1 or output_number > 1000:
            return None

        # Convert output number to tube index (0-49)
        tube_index = (output_number - 1) % 50

        # Get shell parameters
        launch_angle = shell_data.get("angle", 75.0)
        azimuth = shell_data.get("azimuth", 0.0)
        shell_type = shell_data.get("type", "peony").lower()
        color_name = shell_data.get("color", "random").lower()

        return self.launch_shell(
            tube_index=tube_index,
            launch_angle=launch_angle,
            azimuth_angle=azimuth,
            shell_type=shell_type,
            color_name=color_name
        )

    def launch_random_shell(self) -> EnhancedFireworkShell:
        """
        Launch a random firework shell.

        Returns:
            EnhancedFireworkShell instance
        """
        tube_index = random.randint(0, 49)
        launch_angle = random.uniform(70, 85)
        azimuth = random.uniform(-15, 15)
        shell_type = random.choice(list(self.shell_type_map.keys()))

        return self.launch_shell(
            tube_index=tube_index,
            launch_angle=launch_angle,
            azimuth_angle=azimuth,
            shell_type=shell_type,
            color_name="random"
        )

    def update(self, delta_time: float):
        """
        Update all active shells and particle effects.

        Args:
            delta_time: Time step in seconds
        """
        # Update all shells
        for shell in self.active_shells[:]:
            # Update shell physics
            should_spawn_trail = shell.update(delta_time)

            # Spawn trail particles
            if should_spawn_trail and not shell.has_burst:
                pos = shell.get_position_2d()
                vel = shell.get_velocity_2d()
                self.particles.create_trail_particle(pos, vel)

            # NO SMOKE - disabled for distant fireworks
            # (should_spawn_smoke always returns False now)

            # Handle burst
            if shell.has_burst and shell.is_alive:
                pos = shell.get_position_2d()
                print(f"BURST at position: {pos}, age: {shell.age:.2f}s")
                print(f"  3D position: {shell.position}")
                print(f"  Expected burst height: 800-1000px")
                self._create_burst_effects(shell)
                shell.is_alive = False
                self.total_bursts += 1

            # Remove dead shells
            if not shell.is_alive:
                self.active_shells.remove(shell)

        # Update particle system
        self.particles.update(delta_time)

    def _create_burst_effects(self, shell: EnhancedFireworkShell):
        """
        Create all burst effects for a shell.

        Args:
            shell: Shell that is bursting
        """
        burst_pos = shell.get_burst_position()

        # Flash
        self.particles.create_burst_flash(burst_pos)

        # Explosion particles
        explosion_type = self.shell_type_map.get(
            shell.shell_type.lower(),
            "sphere"
        )

        # Particle count based on shell type - PROFESSIONAL DENSITY (500-1000)
        particle_counts = {
            "peony": 600,  # Professional dense sphere
            "chrysanthemum": 700,  # Sphere + sparkles
            "willow": 100,  # Falling particles (keep lower)
            "palm": 200,  # Upward trails
            "dahlia": 800,  # ULTRA dense
            "brocade": 600,  # Crown pattern
            "crackle": 500,  # Dense sparkles
            "multieffect": 750,  # Combination
            "sphere": 600,  # Fallback
            "ring": 500  # Fallback
        }

        particle_count = particle_counts.get(explosion_type, 120)

        self.particles.create_explosion_particles(
            position=burst_pos,
            color=shell.color,
            particle_count=particle_count,
            explosion_type=explosion_type
        )

    def draw(self):
        """Draw all particle effects."""
        self.particles.draw()

    def get_statistics(self) -> Dict:
        """
        Get system statistics.

        Returns:
            Dictionary with statistics
        """
        return {
            "active_shells": len(self.active_shells),
            "total_launches": self.total_launches,
            "total_bursts": self.total_bursts,
            "active_particles": self.particles.get_particle_count(),
            "active_emitters": len(self.particles.emitters)
        }

    def clear(self):
        """Clear all active shells and particles."""
        self.active_shells.clear()
        self.particles.emitters.clear()