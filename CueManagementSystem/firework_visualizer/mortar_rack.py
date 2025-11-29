"""
Mortar Rack - Wooden rack containing 50 mortar tubes
Handles rack geometry, tube positioning, and rendering
"""

import math
import random
import arcade
from typing import List, Tuple
import config
from firework_visualizer.mortar_tube import MortarTube


class MortarRack:
    """
    Represents a wooden mortar rack with 50 tubes (5 rows × 10 columns)
    """
    
    def __init__(self, world_position: Tuple[float, float, float], rack_id: int):
        """
        Initialize a mortar rack
        
        Args:
            world_position: (x, y, z) position in world space (cm)
            rack_id: Unique identifier for this rack (0-19)
        """
        self.position = list(world_position)
        self.rack_id = rack_id
        
        # Rack dimensions (from config)
        self.width = config.RACK_WIDTH    # 96.52 cm (X dimension)
        self.depth = config.RACK_DEPTH    # 63.5 cm (Y dimension)
        self.height = config.RACK_HEIGHT  # 38.1 cm (Z dimension)
        
        # Tube configuration
        self.tube_rows = config.TUBE_ROWS  # 5 rows
        self.tube_cols = config.TUBE_COLS  # 10 columns
        self.tubes_per_rack = config.TUBES_PER_RACK  # 50 tubes
        
        # Wood appearance (similar to dock)
        self.base_color = config.RACK_COLOR  # Lighter brown than dock
        self.frame_color = (max(0, self.base_color[0] - 20),
                           max(0, self.base_color[1] - 20),
                           max(0, self.base_color[2] - 20))
        
        # Calculate rack vertices (8 corners)
        self._calculate_vertices()
        
        # Generate wood grain (unique per rack)
        random.seed(100 + rack_id)
        self.wood_grain = self._generate_wood_grain()
        
        # Create tubes
        self.tubes: List[MortarTube] = []
        self._create_tubes()
    
    def _calculate_vertices(self):
        """Calculate the 8 corner vertices of the rack in world space"""
        half_width = self.width / 2
        half_depth = self.depth / 2
        
        x, y, z = self.position
        
        # 8 vertices of the rectangular box
        self.vertices = {
            'bottom_front_left':  (x - half_width, y - half_depth, z),
            'bottom_front_right': (x + half_width, y - half_depth, z),
            'bottom_back_left':   (x - half_width, y + half_depth, z),
            'bottom_back_right':  (x + half_width, y + half_depth, z),
            'top_front_left':     (x - half_width, y - half_depth, z + self.height),
            'top_front_right':    (x + half_width, y - half_depth, z + self.height),
            'top_back_left':      (x - half_width, y + half_depth, z + self.height),
            'top_back_right':     (x + half_width, y + half_depth, z + self.height),
        }
    
    def _generate_wood_grain(self) -> List[Tuple[float, float, int]]:
        """Generate wood grain pattern for this rack"""
        grain = []
        num_knots = 4  # Fewer knots than dock (smaller surface)
        
        for _ in range(num_knots):
            x_offset = random.uniform(-self.width/2, self.width/2)
            y_offset = random.uniform(-self.depth/2, self.depth/2)
            darkness = random.randint(-15, -5)
            grain.append((x_offset, y_offset, darkness))
        
        return grain
    
    def _create_tubes(self):
        """Create all 50 tubes in their proper positions"""
        # Calculate spacing between tubes
        tube_spacing_x = self.width / (self.tube_cols + 1)
        tube_spacing_y = self.depth / (self.tube_rows + 1)
        
        # Starting position (bottom-left of rack, on top surface)
        start_x = self.position[0] - self.width/2 + tube_spacing_x
        start_y = self.position[1] - self.depth/2 + tube_spacing_y
        tube_z = self.position[2] + self.height  # Tubes sit on top of rack
        
        tube_index = 0
        
        for row in range(self.tube_rows):
            for col in range(self.tube_cols):
                # Calculate tube position
                tube_x = start_x + col * tube_spacing_x
                tube_y = start_y + row * tube_spacing_y
                
                # Calculate tube angle (slight variation for realism)
                # Most tubes point straight up (90°) with slight variations
                base_pitch = 85  # Slightly angled back for safety
                pitch_variation = random.uniform(-2, 2)
                angle_pitch = base_pitch + pitch_variation
                
                # Yaw angle (horizontal direction) - mostly forward
                angle_yaw = random.uniform(-3, 3)
                
                # Create unique tube ID
                tube_id = self.rack_id * self.tubes_per_rack + tube_index
                
                # Create tube
                tube = MortarTube(
                    world_position=(tube_x, tube_y, tube_z),
                    angle_pitch=angle_pitch,
                    angle_yaw=angle_yaw,
                    tube_id=tube_id
                )
                
                self.tubes.append(tube)
                tube_index += 1
    
    def get_tube(self, row: int, col: int) -> MortarTube:
        """
        Get a specific tube by row and column
        
        Args:
            row: Row index (0-4)
            col: Column index (0-9)
        
        Returns:
            MortarTube instance
        """
        if 0 <= row < self.tube_rows and 0 <= col < self.tube_cols:
            index = row * self.tube_cols + col
            return self.tubes[index]
        return None
    
    def render(self, camera, renderer):
        """
        Render the mortar rack with all tubes
        
        Args:
            camera: Camera3D instance
            renderer: SceneRenderer instance
        """
        # Project all vertices to screen space
        screen_vertices = {}
        depths = {}
        
        for name, (wx, wy, wz) in self.vertices.items():
            result = camera.world_to_screen(wx, wy, wz)
            if result is not None:
                sx, sy, depth = result
                screen_vertices[name] = (sx, sy)
                depths[name] = depth
            else:
                return  # Rack not visible
        
        if len(screen_vertices) != 8:
            return
        
        avg_depth = sum(depths.values()) / len(depths)
        
        # Render rack structure (simplified - just frame)
        self._render_frame(screen_vertices, renderer, avg_depth)
        
        # Render all tubes
        for tube in self.tubes:
            tube.render(camera, renderer, depth_offset=avg_depth)
    
    def _render_frame(self, vertices, renderer, depth):
        """Render the wooden frame of the rack"""
        # Render as a simple box frame
        # Top face (where tubes sit)
        top_corners = [
            vertices['top_front_left'],
            vertices['top_front_right'],
            vertices['top_back_right'],
            vertices['top_back_left'],
        ]
        
        def draw_top(corners=top_corners, col=self.base_color):
            arcade.draw_polygon_filled(corners, col)
            # Draw frame outline
            arcade.draw_polygon_outline(corners, self.frame_color, 2)
        
        renderer.add_to_layer('environment', draw_top, depth=depth)
        
        # Front face
        if vertices['top_front_left'][1] > vertices['bottom_front_left'][1]:
            front_corners = [
                vertices['bottom_front_left'],
                vertices['bottom_front_right'],
                vertices['top_front_right'],
                vertices['top_front_left'],
            ]
            
            def draw_front(corners=front_corners, col=self.frame_color):
                arcade.draw_polygon_filled(corners, col)
            
            renderer.add_to_layer('environment', draw_front, depth=depth + 5)
        
        # Left face
        if vertices['top_front_left'][0] < vertices['top_back_left'][0]:
            left_corners = [
                vertices['bottom_front_left'],
                vertices['top_front_left'],
                vertices['top_back_left'],
                vertices['bottom_back_left'],
            ]
            
            def draw_left(corners=left_corners, col=self.frame_color):
                arcade.draw_polygon_filled(corners, col)
            
            renderer.add_to_layer('environment', draw_left, depth=depth + 5)
        
        # Right face
        if vertices['top_front_right'][0] > vertices['top_back_right'][0]:
            right_corners = [
                vertices['bottom_front_right'],
                vertices['bottom_back_right'],
                vertices['top_back_right'],
                vertices['top_front_right'],
            ]
            
            def draw_right(corners=right_corners, col=self.frame_color):
                arcade.draw_polygon_filled(corners, col)
            
            renderer.add_to_layer('environment', draw_right, depth=depth + 5)