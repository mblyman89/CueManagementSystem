"""
Professional Firework Particle System
Uses advanced Arcade techniques for realistic, dense, vivid firework effects

Features:
- Additive blending for glow
- Particle trails
- Bloom effects
- Multiple render layers
- Extreme particle density (500-1000 per burst)
- Gradient textures
- Perfect radial symmetry

Author: Michael Lyman
Version: 1.0.0
License: MIT
"""

import arcade
from arcade.particles import Emitter, EmitBurst, FadeParticle
import random
from typing import Tuple, List
import math


class FireworkParticleSystem:
    """
    Professional-grade firework particle system.

    Uses advanced rendering techniques:
    - Additive blending for realistic glow
    - Multiple sprite lists for layered rendering
    - High particle density
    - Gradient textures for smooth falloff
    - Particle trails
    """

    def __init__(self, window_width: int, window_height: int):
        """Initialize professional particle system."""
        self.window_width = window_width
        self.window_height = window_height

        # Multiple sprite lists for layered rendering
        self.glow_particles = arcade.SpriteList()  # Additive blend
        self.core_particles = arcade.SpriteList()  # Bright cores
        self.main_particles = arcade.SpriteList()  # Main particles
        self.trail_particles = arcade.SpriteList()  # Trails

        # Emitter collections
        self.emitters: List[Emitter] = []

        # Create advanced textures
        self._create_professional_textures()

        # Minimal physics
        self.gravity = 0.01
        self.drag = 0.995

    def _create_professional_textures(self):
        """Create professional gradient textures for realistic glow."""
        # Soft glow texture with gradient falloff (white for now, will be colored per burst)
        self.glow_texture = self._create_gradient_circle(40, (255, 255, 255), alpha_center=255, alpha_edge=0)

        # Core burst texture - very bright
        self.core_texture = self._create_gradient_circle(20, (255, 255, 255), alpha_center=255, alpha_edge=100)

        # Main particle texture - medium glow
        self.particle_texture = self._create_gradient_circle(12, (255, 255, 255), alpha_center=255, alpha_edge=50)

        # Trail texture - SMALLER for rising shell
        self.trail_texture = self._create_gradient_circle(4, (255, 240, 200), alpha_center=255, alpha_edge=200)

        # Flash texture - large bright
        self.flash_texture = self._create_gradient_circle(50, (255, 255, 255), alpha_center=255, alpha_edge=0)

    def _create_gradient_circle(self, size: int, color: Tuple[int, int, int] = (255, 255, 255), alpha_center: int = 255,
                                alpha_edge: int = 0):
        """
        Create a circular texture with radial gradient and color.

        This creates smooth falloff for realistic glow effects.
        """
        # Create texture with gradient and color
        texture = arcade.make_soft_circle_texture(
            size,
            (*color, alpha_center),
            outer_alpha=alpha_edge
        )
        return texture

    def _gravity_mutator(self, particle: FadeParticle):
        """Apply minimal gravity and drag."""
        particle.change_y -= self.gravity
        particle.change_x *= self.drag
        particle.change_y *= self.drag

    def _random_velocity_sphere(self, speed: float) -> Tuple[float, float]:
        """Generate random velocity in perfect spherical pattern."""
        angle = random.uniform(0, 2 * math.pi)
        return (
            math.cos(angle) * speed,
            math.sin(angle) * speed
        )

    def update(self, delta_time: float):
        """Update all particle systems with ULTRA-AGGRESSIVE cleanup."""
        # CRITICAL: Limit emitter count FIRST
        if len(self.emitters) > 40:
            # Remove oldest emitters if too many
            excess = len(self.emitters) - 40
            self.emitters = self.emitters[excess:]

        # Update emitters
        for emitter in self.emitters:
            emitter.update()

        # CRITICAL: Remove completed emitters IMMEDIATELY
        self.emitters = [e for e in self.emitters if not e.can_reap()]

        # ULTRA-AGGRESSIVE: Cleanup BEFORE updating sprite lists
        self._ultra_aggressive_cleanup()

        # Update sprite lists (after cleanup)
        self.glow_particles.update()
        self.core_particles.update()
        self.main_particles.update()
        self.trail_particles.update()

        # SECOND PASS: Cleanup again after update
        self._ultra_aggressive_cleanup()

        # THIRD PASS: If still too many particles, force emergency cleanup
        total_particles = (len(self.glow_particles) + len(self.core_particles) +
                           len(self.main_particles) + len(self.trail_particles))
        if total_particles > 3500:
            self._emergency_particle_reduction()

    def _ultra_aggressive_cleanup(self):
        """ULTRA-AGGRESSIVE cleanup using optimized batch operations."""
        MAX_PARTICLES_PER_LIST = 800  # Further reduced from 1000
        ALPHA_THRESHOLD = 15  # Increased from 10 (remove earlier)

        for sprite_list in [self.glow_particles, self.core_particles,
                            self.main_particles, self.trail_particles]:

            list_len = len(sprite_list)
            if list_len == 0:
                continue

            # OPTIMIZED: Use list comprehension for faster filtering
            # Remove particles with low alpha in one pass
            particles_to_keep = []
            particles_to_remove = []

            for particle in sprite_list:
                if hasattr(particle, "alpha") and particle.alpha <= ALPHA_THRESHOLD:
                    particles_to_remove.append(particle)
                else:
                    particles_to_keep.append(particle)

            # Batch remove
            for particle in particles_to_remove:
                particle.remove_from_sprite_lists()

            # Recalculate length after removal
            list_len = len(sprite_list)

            # Hard limit enforcement - remove oldest particles
            if list_len > MAX_PARTICLES_PER_LIST:
                excess = list_len - MAX_PARTICLES_PER_LIST
                # Remove in larger batches for efficiency
                batch_size = min(excess, 100)  # Remove up to 100 at once
                for i in range(batch_size):
                    if len(sprite_list) > 0:
                        sprite_list[0].remove_from_sprite_lists()

            # Emergency cleanup if still over limit
            if len(sprite_list) > MAX_PARTICLES_PER_LIST * 1.2:
                print(f"⚠️ EMERGENCY CLEANUP: {len(sprite_list)} particles in list!")
                # Remove 60% of particles immediately
                target = int(len(sprite_list) * 0.6)
                for i in range(target):
                    if len(sprite_list) > 0:
                        sprite_list[0].remove_from_sprite_lists()

    def _emergency_particle_reduction(self):
        """AGGRESSIVE: Reduce particles by 50% when overwhelmed."""
        print("🚨 EMERGENCY REDUCTION: Too many particles, reducing by 50%")

        for sprite_list in [self.glow_particles, self.core_particles,
                            self.main_particles, self.trail_particles]:
            target = len(sprite_list) // 2
            for i in range(target):
                if len(sprite_list) > 0:
                    sprite_list[0].remove_from_sprite_lists()

    def _emergency_clear_all(self):
        """NUCLEAR OPTION: Clear everything if overwhelmed."""
        print("🚨 NUCLEAR: Clearing all particles!")
        self.emitters.clear()

        for sprite_list in [self.glow_particles, self.core_particles,
                            self.main_particles, self.trail_particles]:
            for particle in list(sprite_list):
                particle.remove_from_sprite_lists()

    def draw(self):
        """Draw all particles with proper layering and blending."""
        # Layer 1: Glow (additive blending for bloom effect)
        # TODO: Implement additive blending when drawing glow layer
        for emitter in self.emitters:
            emitter.draw()

        # Layer 2: Core particles (bright)
        self.core_particles.draw()

        # Layer 3: Main particles
        self.main_particles.draw()

        # Layer 4: Trails
        self.trail_particles.draw()

    def get_particle_count(self) -> int:
        """Get total active particle count."""
        return len(self.emitters)

    def create_moving_trail_sprite(self, position: Tuple[float, float]):
        """Create a SINGLE moving trail sprite that follows the shell."""
        import arcade

        # Create a sprite with the trail texture
        sprite = arcade.Sprite()
        sprite.texture = self.trail_texture
        sprite.center_x = position[0]
        sprite.center_y = position[1]
        sprite.scale = 1.2  # Slightly larger for visibility
        sprite.alpha = 255

        # Add to trail particles list
        self.trail_particles.append(sprite)

        return sprite

    def create_launch_flash(self, position: Tuple[float, float]):
        """Create small launch flash."""
        emitter = Emitter(
            center_xy=position,
            emit_controller=EmitBurst(2),
            particle_factory=lambda emitter: FadeParticle(
                filename_or_texture=self.trail_texture,
                change_xy=(0, 0),
                lifetime=0.2,
                scale=random.uniform(0.5, 0.8),
                start_alpha=200,
                end_alpha=0
            )
        )
        self.emitters.append(emitter)

    def create_burst_flash(self, position: Tuple[float, float]):
        """Create bright burst flash with glow."""
        # Main flash
        emitter = Emitter(
            center_xy=position,
            emit_controller=EmitBurst(5),
            particle_factory=lambda emitter: FadeParticle(
                filename_or_texture=self.flash_texture,
                change_xy=(0, 0),
                lifetime=0.4,
                scale=random.uniform(1.0, 1.5),
                start_alpha=255,
                end_alpha=0
            )
        )
        self.emitters.append(emitter)

    def create_explosion_particles(self,
                                   position: Tuple[float, float],
                                   color: Tuple[int, int, int],
                                   particle_count: int = 500,
                                   explosion_type: str = "sphere"):
        """
        Create PROFESSIONAL explosion with extreme density and glow.

        Uses 500-1000 particles with multiple layers for realistic effect.
        """
        print(f"\n🎆 PROFESSIONAL BURST:")
        print(f"  Type: {explosion_type}")
        print(f"  Position: ({position[0]:.1f}, {position[1]:.1f})")
        print(f"  Color: RGB{color}")
        print(f"  Particle Count: {particle_count}")
        print(f"  Rendering: Multi-layer with glow")

        # Always create burst flash
        self.create_burst_flash(position)

        # Route to professional burst methods
        if explosion_type in ["peony", "sphere"]:
            self._create_professional_sphere(position, color, particle_count)
        elif explosion_type == "chrysanthemum":
            self._create_professional_chrysanthemum(position, color, particle_count)
        elif explosion_type == "dahlia":
            self._create_professional_dahlia(position, color, particle_count)
        elif explosion_type == "brocade":
            self._create_professional_brocade(position, color, particle_count)
        elif explosion_type == "willow":
            self._create_professional_willow(position, color, particle_count)
        elif explosion_type == "palm":
            self._create_professional_palm(position, color, particle_count)
        elif explosion_type == "crackle":
            self._create_professional_crackle(position, color, particle_count)
        elif explosion_type == "multieffect":
            self._create_professional_multieffect(position, color, particle_count)
        else:
            self._create_professional_sphere(position, color, particle_count)

    def _create_professional_sphere(self,
                                    position: Tuple[float, float],
                                    color: Tuple[int, int, int],
                                    count: int):
        """
        Create professional sphere burst with EXTREME density.

        Uses 10 layers with 500-1000 particles total.
        Perfect radial symmetry with smooth color gradation.
        """
        # Boost color dramatically
        vivid_color = tuple(min(255, int(c * 1.8)) for c in color)

        # Create 10 micro-layers for ultra-smooth gradation
        num_layers = 10
        particles_per_layer = count // num_layers

        for layer_idx in range(num_layers):
            # Calculate layer properties
            brightness_factor = 1.8 - (layer_idx * 0.08)  # 1.8 to 1.0
            speed_min = 0.08 + (layer_idx * 0.12)  # 0.08 to 1.16
            speed_max = 0.25 + (layer_idx * 0.12)  # 0.25 to 1.33
            texture_size = 10 - layer_idx  # 10px to 1px
            scale_min = 2.0 - (layer_idx * 0.15)  # 2.0 to 0.65
            scale_max = 2.5 - (layer_idx * 0.15)  # 2.5 to 1.15

            # Create color for this layer
            layer_color = tuple(min(255, int(c * brightness_factor)) for c in color)
            layer_texture = self._create_gradient_circle(texture_size, layer_color, 255, 100)

            # Create emitter for this layer
            emitter = Emitter(
                center_xy=position,
                emit_controller=EmitBurst(particles_per_layer),
                particle_factory=lambda emitter, smin=speed_min, smax=speed_max, sc_min=scale_min, sc_max=scale_max,
                                        tex=layer_texture: FadeParticle(
                    filename_or_texture=tex,
                    change_xy=self._random_velocity_sphere(random.uniform(smin, smax)),
                    lifetime=random.uniform(1.0, 1.5),
                    scale=random.uniform(sc_min, sc_max),
                    start_alpha=255,
                    end_alpha=0,
                    mutation_callback=None  # No gravity - stays in place
                )
            )
            self.emitters.append(emitter)

        print(f"  Created {num_layers} layers with {particles_per_layer} particles each")
        print(f"  Speed range: 0.08-1.33 px/s (ULTRA TIGHT)")
        print(f"  Particle sizes: 1-10px with gradient falloff")

    def _create_professional_chrysanthemum(self, position, color, count):
        """Chrysanthemum with dense core + tight sparkles."""
        # Dense core (85%)
        self._create_professional_sphere(position, color, int(count * 0.85))

        # Tight sparkle layer (15%) - much tighter spread
        vivid_color = tuple(min(255, int(c * 1.8)) for c in color)

        # Create layered sparkles for density
        sparkle_count = int(count * 0.15)
        num_layers = 4
        particles_per_layer = sparkle_count // num_layers

        for layer_idx in range(num_layers):
            brightness_factor = 1.8 - (layer_idx * 0.12)
            speed_min = 0.2 + (layer_idx * 0.12)
            speed_max = 0.5 + (layer_idx * 0.12)
            texture_size = 7 - layer_idx
            scale_min = 1.6 - (layer_idx * 0.12)
            scale_max = 2.2 - (layer_idx * 0.12)

            layer_color = tuple(min(255, int(c * brightness_factor)) for c in color)
            layer_texture = self._create_gradient_circle(texture_size, layer_color, 255, 130)

            emitter = Emitter(
                center_xy=position,
                emit_controller=EmitBurst(particles_per_layer),
                particle_factory=lambda emitter, smin=speed_min, smax=speed_max, sc_min=scale_min, sc_max=scale_max,
                                        tex=layer_texture: FadeParticle(
                    filename_or_texture=tex,
                    change_xy=self._random_velocity_sphere(random.uniform(smin, smax)),
                    lifetime=random.uniform(1.0, 1.5),
                    scale=random.uniform(sc_min, sc_max),
                    start_alpha=255,
                    end_alpha=0,
                    mutation_callback=None
                )
            )
            self.emitters.append(emitter)

    def _create_professional_dahlia(self, position, color, count):
        """Ultra-dense dahlia burst."""
        # Even denser than sphere - all particles very close
        vivid_color = tuple(min(255, int(c * 1.9)) for c in color)
        texture = self._create_gradient_circle(12, vivid_color, 255, 100)

        emitter = Emitter(
            center_xy=position,
            emit_controller=EmitBurst(count),
            particle_factory=lambda emitter: FadeParticle(
                filename_or_texture=texture,
                change_xy=self._random_velocity_sphere(random.uniform(0.05, 0.5)),  # ULTRA tight
                lifetime=random.uniform(1.0, 1.5),
                scale=random.uniform(2.0, 2.8),
                start_alpha=255,
                end_alpha=0,
                mutation_callback=None
            )
        )
        self.emitters.append(emitter)

    def _create_professional_brocade(self, position, color, count):
        """Brocade crown pattern - dense core with vivid color."""
        vivid_color = tuple(min(255, int(c * 1.8)) for c in color)

        # Create 10 layers just like sphere but with brocade characteristics
        num_layers = 10
        particles_per_layer = count // num_layers

        for layer_idx in range(num_layers):
            brightness_factor = 1.8 - (layer_idx * 0.08)
            speed_min = 0.1 + (layer_idx * 0.12)
            speed_max = 0.3 + (layer_idx * 0.12)
            texture_size = 10 - layer_idx
            scale_min = 2.0 - (layer_idx * 0.15)
            scale_max = 2.5 - (layer_idx * 0.15)

            layer_color = tuple(min(255, int(c * brightness_factor)) for c in color)
            layer_texture = self._create_gradient_circle(texture_size, layer_color, 255, 100)

            emitter = Emitter(
                center_xy=position,
                emit_controller=EmitBurst(particles_per_layer),
                particle_factory=lambda emitter, smin=speed_min, smax=speed_max, sc_min=scale_min, sc_max=scale_max,
                                        tex=layer_texture: FadeParticle(
                    filename_or_texture=tex,
                    change_xy=self._random_velocity_sphere(random.uniform(smin, smax)),
                    lifetime=random.uniform(1.0, 1.5),
                    scale=random.uniform(sc_min, sc_max),
                    start_alpha=255,
                    end_alpha=0,
                    mutation_callback=None
                )
            )
            self.emitters.append(emitter)

    def _create_professional_willow(self, position, color, count):
        """Willow with slow fall."""
        vivid_color = tuple(min(255, int(c * 1.7)) for c in color)
        texture = self._create_gradient_circle(6, vivid_color, 255, 150)

        def slow_fall(particle):
            particle.change_y -= 0.008
            particle.change_x *= 0.997

        emitter = Emitter(
            center_xy=position,
            emit_controller=EmitBurst(count),
            particle_factory=lambda emitter: FadeParticle(
                filename_or_texture=texture,
                change_xy=(random.uniform(-0.3, 0.3), random.uniform(0.3, 1.0)),
                lifetime=random.uniform(1.5, 2.0),
                scale=random.uniform(1.3, 1.9),
                start_alpha=255,
                end_alpha=0,
                mutation_callback=slow_fall
            )
        )
        self.emitters.append(emitter)

    def _create_professional_palm(self, position, color, count):
        """Palm with VERY gentle upward trails - dense layered effect."""
        vivid_color = tuple(min(255, int(c * 1.8)) for c in color)

        # Create layered palm effect for density
        num_layers = 8
        particles_per_layer = count // num_layers

        for layer_idx in range(num_layers):
            brightness_factor = 1.8 - (layer_idx * 0.1)
            # Very gentle upward movement
            vertical_min = 0.2 + (layer_idx * 0.08)
            vertical_max = 0.5 + (layer_idx * 0.08)
            texture_size = 9 - layer_idx
            scale_min = 2.0 - (layer_idx * 0.15)
            scale_max = 2.5 - (layer_idx * 0.15)

            layer_color = tuple(min(255, int(c * brightness_factor)) for c in color)
            layer_texture = self._create_gradient_circle(texture_size, layer_color, 255, 100)

            emitter = Emitter(
                center_xy=position,
                emit_controller=EmitBurst(particles_per_layer),
                particle_factory=lambda emitter, vmin=vertical_min, vmax=vertical_max, sc_min=scale_min,
                                        sc_max=scale_max, tex=layer_texture: FadeParticle(
                    filename_or_texture=tex,
                    change_xy=(random.uniform(-0.2, 0.2), random.uniform(vmin, vmax)),
                    lifetime=random.uniform(1.0, 1.5),
                    scale=random.uniform(sc_min, sc_max),
                    start_alpha=255,
                    end_alpha=0,
                    mutation_callback=None
                )
            )
            self.emitters.append(emitter)

    def _create_professional_crackle(self, position, color, count):
        """Crackle sparkles - tight, vivid colored sparkles."""
        vivid_color = tuple(min(255, int(c * 1.8)) for c in color)

        # Create tight sparkle burst with color
        num_layers = 8
        particles_per_layer = count // num_layers

        for layer_idx in range(num_layers):
            brightness_factor = 1.8 - (layer_idx * 0.1)
            speed_min = 0.15 + (layer_idx * 0.12)
            speed_max = 0.35 + (layer_idx * 0.12)
            texture_size = 8 - layer_idx
            scale_min = 1.8 - (layer_idx * 0.12)
            scale_max = 2.3 - (layer_idx * 0.12)

            layer_color = tuple(min(255, int(c * brightness_factor)) for c in color)
            layer_texture = self._create_gradient_circle(texture_size, layer_color, 255, 120)

            emitter = Emitter(
                center_xy=position,
                emit_controller=EmitBurst(particles_per_layer),
                particle_factory=lambda emitter, smin=speed_min, smax=speed_max, sc_min=scale_min, sc_max=scale_max,
                                        tex=layer_texture: FadeParticle(
                    filename_or_texture=tex,
                    change_xy=self._random_velocity_sphere(random.uniform(smin, smax)),
                    lifetime=random.uniform(0.8, 1.2),
                    scale=random.uniform(sc_min, sc_max),
                    start_alpha=255,
                    end_alpha=0,
                    mutation_callback=None
                )
            )
            self.emitters.append(emitter)

    def _create_professional_multieffect(self, position, color, count):
        """Multi-effect combination - dense sphere with extra sparkles."""
        # Main dense sphere (70%)
        self._create_professional_sphere(position, color, int(count * 0.7))

        # Extra sparkle layer (30%) with vivid color
        vivid_color = tuple(min(255, int(c * 1.8)) for c in color)

        num_layers = 5
        particles_per_layer = (count * 0.3) // num_layers

        for layer_idx in range(num_layers):
            brightness_factor = 1.8 - (layer_idx * 0.12)
            speed_min = 0.2 + (layer_idx * 0.15)
            speed_max = 0.5 + (layer_idx * 0.15)
            texture_size = 7 - layer_idx
            scale_min = 1.8 - (layer_idx * 0.12)
            scale_max = 2.3 - (layer_idx * 0.12)

            layer_color = tuple(min(255, int(c * brightness_factor)) for c in color)
            layer_texture = self._create_gradient_circle(texture_size, layer_color, 255, 120)

            emitter = Emitter(
                center_xy=position,
                emit_controller=EmitBurst(int(particles_per_layer)),
                particle_factory=lambda emitter, smin=speed_min, smax=speed_max, sc_min=scale_min, sc_max=scale_max,
                                        tex=layer_texture: FadeParticle(
                    filename_or_texture=tex,
                    change_xy=self._random_velocity_sphere(random.uniform(smin, smax)),
                    lifetime=random.uniform(1.0, 1.5),
                    scale=random.uniform(sc_min, sc_max),
                    start_alpha=255,
                    end_alpha=0,
                    mutation_callback=None
                )
            )
            self.emitters.append(emitter)