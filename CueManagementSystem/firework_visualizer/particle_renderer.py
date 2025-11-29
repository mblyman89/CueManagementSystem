"""
Particle Renderer - Efficient rendering of thousands of particles
Handles batch rendering, culling, and visual effects
Enhanced with advanced visual effects support
"""

import arcade
from typing import List
import config
from firework_visualizer.particle import FireworkParticle
import visual_effects_config as vfx


class ParticleRenderer:
    """
    Efficient particle rendering system with batching and culling
    """
    
    def __init__(self, camera):
        """
        Initialize particle renderer
        
        Args:
            camera: Camera3D instance for coordinate transformation
        """
        self.camera = camera
        
        # Rendering statistics
        self.particles_rendered = 0
        self.particles_culled = 0
        
        # Culling distance
        self.culling_distance = config.CULLING_DISTANCE
        
        # Bloom effect settings
        self.bloom_enabled = True
        self.bloom_intensity = config.BLOOM_INTENSITY
    
    def render_particles(self, particles: List[FireworkParticle], renderer):
        """
        Render all particles with efficient batching
        
        Args:
            particles: List of active particles
            renderer: SceneRenderer instance
        """
        self.particles_rendered = 0
        self.particles_culled = 0
        
        # Group particles by depth for proper sorting
        particle_data = []
        
        for particle in particles:
            if not particle.is_alive:
                continue
            
            # Project particle to screen space
            result = self.camera.world_to_screen(particle.x, particle.y, particle.z)
            
            if result is None:
                self.particles_culled += 1
                continue
            
            screen_x, screen_y, depth = result
            
            # Cull particles beyond culling distance
            if depth > self.culling_distance:
                self.particles_culled += 1
                continue
            
            # Calculate size based on distance (perspective)
            scale = self.camera.get_scale_at_distance(depth)
            screen_size = particle.size * scale
            
            # Skip particles that are too small to see
            if screen_size < 0.5:
                self.particles_culled += 1
                continue
            
            # Get render color (with brightness)
            color = particle.get_render_color()
            
            # Store particle data for rendering
            particle_data.append({
                'x': screen_x,
                'y': screen_y,
                'depth': depth,
                'size': screen_size,
                'color': color,
                'alpha': particle.alpha,
                'particle': particle
            })
            
            self.particles_rendered += 1
        
        # Sort particles by depth (far to near for proper alpha blending)
        particle_data.sort(key=lambda p: -p['depth'])
        
        # Render particles in batches
        self._render_particle_batch(particle_data, renderer)
        
        # Render bloom effect if enabled
        if self.bloom_enabled:
            self._render_bloom_effect(particle_data, renderer)
    
    def _render_particle_batch(self, particle_data: List[dict], renderer):
        """
        Render particles in batches for efficiency
        
        Args:
            particle_data: List of particle render data
            renderer: SceneRenderer instance
        """
        for data in particle_data:
            x = data['x']
            y = data['y']
            size = data['size']
            color = data['color']
            alpha = data['alpha']
            depth = data['depth']
            
            # Create RGBA color with alpha
            rgba_color = (color[0], color[1], color[2], alpha)
            
            def draw_particle(px=x, py=y, ps=size, pc=rgba_color, d=depth):
                # Draw particle as a filled circle
                arcade.draw_circle_filled(px, py, ps, pc)
            
            renderer.add_to_layer('particles', draw_particle, depth=depth)
    
    def _render_bloom_effect(self, particle_data: List[dict], renderer):
        """
        Render bloom/glow effect for bright particles
        
        Args:
            particle_data: List of particle render data
            renderer: SceneRenderer instance
        """
        for data in particle_data:
            # Only add bloom to bright particles
            if data['alpha'] < 128:
                continue
            
            x = data['x']
            y = data['y']
            size = data['size']
            color = data['color']
            depth = data['depth']
            
            # Calculate bloom size and alpha
            bloom_size = size * 2.5
            bloom_alpha = int(data['alpha'] * self.bloom_intensity * 0.3)
            
            if bloom_alpha < 10:
                continue
            
            bloom_color = (color[0], color[1], color[2], bloom_alpha)
            
            def draw_bloom(px=x, py=y, bs=bloom_size, bc=bloom_color, d=depth):
                # Draw bloom as a larger, semi-transparent circle
                arcade.draw_circle_filled(px, py, bs, bc)
            
            renderer.add_to_layer('effects', draw_bloom, depth=depth - 1)
    
    def render_particle_trails(self, particles: List[FireworkParticle], renderer):
        """
        Render trails for particles that have them enabled
        
        Args:
            particles: List of active particles
            renderer: SceneRenderer instance
        """
        for particle in particles:
            if not particle.is_alive or not particle.has_trail:
                continue
            
            if len(particle.trail_positions) < 2:
                continue
            
            # Project trail positions to screen
            trail_screen = []
            for pos in particle.trail_positions:
                result = self.camera.world_to_screen(pos[0], pos[1], pos[2])
                if result is not None:
                    trail_screen.append((result[0], result[1], result[2]))
            
            if len(trail_screen) < 2:
                continue
            
            # Calculate average depth for sorting
            avg_depth = sum(p[2] for p in trail_screen) / len(trail_screen)
            
            # Draw trail as connected line segments
            color = particle.get_render_color()
            
            def draw_trail(points=trail_screen, col=color, alpha=particle.alpha):
                # Draw trail with fading alpha
                for i in range(len(points) - 1):
                    # Calculate alpha for this segment (fade toward tail)
                    segment_alpha = int(alpha * (i + 1) / len(points))
                    segment_color = (col[0], col[1], col[2], segment_alpha)
                    
                    arcade.draw_line(
                        points[i][0], points[i][1],
                        points[i+1][0], points[i+1][1],
                        segment_color,
                        2
                    )
            
            renderer.add_to_layer('particles', draw_trail, depth=avg_depth)
    
    def get_statistics(self) -> dict:
        """
        Get rendering statistics
        
        Returns:
            Dictionary with rendering stats
        """
        total = self.particles_rendered + self.particles_culled
        cull_percent = (self.particles_culled / total * 100) if total > 0 else 0
        
        return {
            'rendered': self.particles_rendered,
            'culled': self.particles_culled,
            'total': total,
            'cull_percentage': cull_percent
        }