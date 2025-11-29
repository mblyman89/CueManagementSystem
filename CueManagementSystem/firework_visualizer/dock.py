"""
Wooden Dock - 3D perspective rendering of weathered wooden dock
Handles dock geometry, wood texture, and realistic appearance
"""

import math
import random
import arcade
from typing import List, Tuple
import config


class WoodenDock:
    """
    Represents a wooden dock with realistic 3D rendering and wood texture
    """
    
    def __init__(self, camera):
        """
        Initialize wooden dock
        
        Args:
            camera: Camera3D instance for coordinate transformation
        """
        self.camera = camera
        
        # Dock dimensions (from config, in cm)
        self.width = config.DOCK_WIDTH    # 1219 cm (X dimension)
        self.depth = config.DOCK_DEPTH    # 244 cm (Y dimension)
        self.height = config.DOCK_HEIGHT  # 61 cm (Z dimension)
        
        # Dock position in world space
        self.position = list(config.DOCK_POSITION)  # [x, y, z]
        
        # Wood appearance
        self.base_color = config.DOCK_COLOR  # Brown wood color
        self.plank_width = 15  # cm, width of each plank
        self.plank_gap = 1     # cm, gap between planks
        
        # Calculate dock vertices (8 corners of the box)
        self._calculate_vertices()
        
        # Generate wood grain pattern (deterministic based on position)
        random.seed(42)  # Fixed seed for consistent appearance
        self.wood_grain = self._generate_wood_grain()
    
    def _calculate_vertices(self):
        """Calculate the 8 corner vertices of the dock in world space"""
        # Center the dock at its position
        half_width = self.width / 2
        half_depth = self.depth / 2
        
        x, y, z = self.position
        
        # 8 vertices of the rectangular box
        # Bottom face (z = z)
        self.vertices = {
            'bottom_front_left':  (x - half_width, y - half_depth, z),
            'bottom_front_right': (x + half_width, y - half_depth, z),
            'bottom_back_left':   (x - half_width, y + half_depth, z),
            'bottom_back_right':  (x + half_width, y + half_depth, z),
            # Top face (z = z + height)
            'top_front_left':     (x - half_width, y - half_depth, z + self.height),
            'top_front_right':    (x + half_width, y - half_depth, z + self.height),
            'top_back_left':      (x - half_width, y + half_depth, z + self.height),
            'top_back_right':     (x + half_width, y + half_depth, z + self.height),
        }
    
    def _generate_wood_grain(self) -> List[Tuple[float, float, int]]:
        """
        Generate wood grain pattern (knots and variations)
        
        Returns:
            List of (x_offset, y_offset, darkness) tuples
        """
        grain = []
        num_knots = 8  # Number of wood knots
        
        for _ in range(num_knots):
            x_offset = random.uniform(-self.width/2, self.width/2)
            y_offset = random.uniform(-self.depth/2, self.depth/2)
            darkness = random.randint(-20, -5)  # Darker spots
            grain.append((x_offset, y_offset, darkness))
        
        return grain
    
    def _get_wood_color_at(self, local_x: float, local_y: float) -> Tuple[int, int, int]:
        """
        Get wood color at a local position (with grain variation)
        
        Args:
            local_x: X position relative to dock center
            local_y: Y position relative to dock center
        
        Returns:
            RGB color tuple
        """
        r, g, b = self.base_color
        
        # Add wood grain variation
        for grain_x, grain_y, darkness in self.wood_grain:
            distance = math.sqrt((local_x - grain_x)**2 + (local_y - grain_y)**2)
            if distance < 30:  # Knot radius
                influence = 1 - (distance / 30)
                r += int(darkness * influence)
                g += int(darkness * influence)
                b += int(darkness * influence)
        
        # Add subtle random variation for weathered look
        variation = random.randint(-5, 5)
        r = max(0, min(255, r + variation))
        g = max(0, min(255, g + variation))
        b = max(0, min(255, b + variation))
        
        return (r, g, b)
    
    def render(self, renderer):
        """
        Render the wooden dock with 3D perspective
        
        Args:
            renderer: SceneRenderer instance
        """
        # Project all vertices to screen space
        screen_vertices = {}
        depths = {}
        
        for name, (wx, wy, wz) in self.vertices.items():
            result = self.camera.world_to_screen(wx, wy, wz)
            if result is not None:
                sx, sy, depth = result
                screen_vertices[name] = (sx, sy)
                depths[name] = depth
            else:
                # Vertex is not visible
                return
        
        # Check if we have all vertices
        if len(screen_vertices) != 8:
            return
        
        # Calculate average depth for sorting
        avg_depth = sum(depths.values()) / len(depths)
        
        # Render dock faces (visible faces only, back-to-front)
        # We'll render: top, front, left, right (back is usually not visible)
        
        # === TOP FACE === (most important, always visible)
        self._render_top_face(screen_vertices, renderer, avg_depth)
        
        # === FRONT FACE === (facing camera)
        if screen_vertices['top_front_left'][1] > screen_vertices['bottom_front_left'][1]:
            self._render_front_face(screen_vertices, renderer, avg_depth + 10)
        
        # === LEFT FACE ===
        if screen_vertices['top_front_left'][0] < screen_vertices['top_back_left'][0]:
            self._render_left_face(screen_vertices, renderer, avg_depth + 20)
        
        # === RIGHT FACE ===
        if screen_vertices['top_front_right'][0] > screen_vertices['top_back_right'][0]:
            self._render_right_face(screen_vertices, renderer, avg_depth + 20)
    
    def _render_top_face(self, vertices, renderer, depth):
        """Render the top face of the dock with wood planks"""
        # Top face is the most visible and important
        # Render as individual planks for realism
        
        num_planks = int(self.depth / (self.plank_width + self.plank_gap))
        
        for i in range(num_planks):
            # Calculate plank position
            plank_start = -self.depth/2 + i * (self.plank_width + self.plank_gap)
            plank_end = plank_start + self.plank_width
            
            # Get color for this plank (with variation)
            plank_center_y = (plank_start + plank_end) / 2
            color = self._get_wood_color_at(0, plank_center_y)
            
            # Calculate plank corners in world space
            x, y, z = self.position
            half_width = self.width / 2
            
            corners_world = [
                (x - half_width, y + plank_start, z + self.height),
                (x + half_width, y + plank_start, z + self.height),
                (x + half_width, y + plank_end, z + self.height),
                (x - half_width, y + plank_end, z + self.height),
            ]
            
            # Project to screen space
            corners_screen = []
            for wx, wy, wz in corners_world:
                result = self.camera.world_to_screen(wx, wy, wz)
                if result is not None:
                    sx, sy, _ = result
                    corners_screen.append((sx, sy))
            
            if len(corners_screen) == 4:
                # Calculate depth for this plank
                plank_depth = depth
                
                def draw_plank(corners=corners_screen, col=color):
                    arcade.draw_polygon_filled(corners, col)
                    # Add plank outline for definition
                    arcade.draw_polygon_outline(corners, (col[0]-20, col[1]-20, col[2]-20), 1)
                
                renderer.add_to_layer('environment', draw_plank, depth=plank_depth)
    
    def _render_front_face(self, vertices, renderer, depth):
        """Render the front face of the dock"""
        # Front face (facing camera)
        corners = [
            vertices['bottom_front_left'],
            vertices['bottom_front_right'],
            vertices['top_front_right'],
            vertices['top_front_left'],
        ]
        
        # Darker color for side face
        r, g, b = self.base_color
        color = (max(0, r-30), max(0, g-30), max(0, b-30))
        
        def draw_face(c=corners, col=color):
            arcade.draw_polygon_filled(c, col)
        
        renderer.add_to_layer('environment', draw_face, depth=depth)
    
    def _render_left_face(self, vertices, renderer, depth):
        """Render the left face of the dock"""
        corners = [
            vertices['bottom_front_left'],
            vertices['top_front_left'],
            vertices['top_back_left'],
            vertices['bottom_back_left'],
        ]
        
        # Darker color for side face
        r, g, b = self.base_color
        color = (max(0, r-40), max(0, g-40), max(0, b-40))
        
        def draw_face(c=corners, col=color):
            arcade.draw_polygon_filled(c, col)
        
        renderer.add_to_layer('environment', draw_face, depth=depth)
    
    def _render_right_face(self, vertices, renderer, depth):
        """Render the right face of the dock"""
        corners = [
            vertices['bottom_front_right'],
            vertices['bottom_back_right'],
            vertices['top_back_right'],
            vertices['top_front_right'],
        ]
        
        # Darker color for side face
        r, g, b = self.base_color
        color = (max(0, r-40), max(0, g-40), max(0, b-40))
        
        def draw_face(c=corners, col=color):
            arcade.draw_polygon_filled(c, col)
        
        renderer.add_to_layer('environment', draw_face, depth=depth)