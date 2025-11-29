"""
Background Elements - Distant shore, trees, and atmospheric depth
Adds environmental context and depth to the scene
"""

import math
import random
import arcade
from typing import List, Tuple
import config


class TreeSilhouette:
    """Represents a single tree silhouette in the background"""
    
    def __init__(self, x: float, height: float, width: float):
        """
        Initialize a tree silhouette
        
        Args:
            x: X position (normalized 0-1)
            y: Base Y position (normalized 0-1)
            height: Tree height (normalized)
            width: Tree width (normalized)
        """
        self.x = x
        self.height = height
        self.width = width
        self.tree_type = random.choice(['pine', 'deciduous'])


class BackgroundElements:
    """
    Manages background environmental elements for depth and atmosphere
    """
    
    def __init__(self, camera):
        """
        Initialize background elements
        
        Args:
            camera: Camera3D instance for coordinate transformation
        """
        self.camera = camera
        
        # Distant shore properties
        self.shore_distance = 150000  # 1.5 km away
        self.shore_height = 50        # Height above water
        self.shore_color = (20, 25, 40)  # Dark blue-gray
        
        # Tree line
        self.trees = []
        self._generate_tree_line()
        
        # Atmospheric fog
        self.fog_color = (15, 20, 35)
        self.fog_density = 0.3
    
    def _generate_tree_line(self):
        """Generate a line of trees on the distant shore"""
        num_trees = 40
        
        # Use fixed seed for consistent tree positions
        random.seed(456)
        
        for i in range(num_trees):
            # Distribute trees along the horizon
            x = i / num_trees
            
            # Vary tree heights
            height = random.uniform(0.03, 0.08)  # 3-8% of screen height
            
            # Vary tree widths
            width = random.uniform(0.015, 0.035)  # 1.5-3.5% of screen width
            
            self.trees.append(TreeSilhouette(x, height, width))
    
    def render(self, renderer):
        """
        Render all background elements
        
        Args:
            renderer: SceneRenderer instance
        """
        # Render distant shore
        self._render_shore(renderer)
        
        # Render tree line
        self._render_trees(renderer)
        
        # Render atmospheric fog (optional, subtle)
        self._render_atmosphere(renderer)
    
    def _render_shore(self, renderer):
        """Render the distant shore line"""
        # Shore is a horizontal line at the horizon
        # Calculate shore position in 3D space
        
        shore_y = self.camera.position[1] + self.shore_distance
        shore_z = self.shore_height
        
        # Project shore line to screen
        # Sample multiple points along the shore for proper perspective
        shore_points = []
        
        for i in range(20):
            t = i / 19
            shore_x = -100000 + t * 200000  # -1km to +1km
            
            result = self.camera.world_to_screen(shore_x, shore_y, shore_z)
            if result is not None:
                sx, sy, depth = result
                shore_points.append((sx, sy, depth))
        
        if len(shore_points) < 2:
            return
        
        # Draw shore as a filled polygon (shore to bottom of screen)
        avg_depth = sum(p[2] for p in shore_points) / len(shore_points)
        
        def draw_shore(points=shore_points, color=self.shore_color):
            # Create polygon points (shore line + bottom corners)
            polygon = [(p[0], p[1]) for p in points]
            
            # Add bottom corners
            if polygon:
                polygon.append((config.SCREEN_WIDTH, 0))
                polygon.append((0, 0))
            
            arcade.draw_polygon_filled(polygon, color)
        
        renderer.add_to_layer('background', draw_shore, depth=avg_depth)
    
    def _render_trees(self, renderer):
        """Render tree silhouettes on the distant shore"""
        for tree in self.trees:
            # Calculate tree position
            screen_x = tree.x * config.SCREEN_WIDTH
            
            # Trees sit on the shore line
            shore_y = self.camera.position[1] + self.shore_distance
            shore_z = self.shore_height
            
            # Project base of tree
            result = self.camera.world_to_screen(0, shore_y, shore_z)
            if result is None:
                continue
            
            _, base_y, depth = result
            
            # Calculate tree dimensions in screen space
            tree_height = tree.height * config.SCREEN_HEIGHT
            tree_width = tree.width * config.SCREEN_WIDTH
            
            # Tree color (very dark, silhouette)
            tree_color = (10, 15, 25)
            
            if tree.tree_type == 'pine':
                # Pine tree - triangular shape
                def draw_pine(x=screen_x, y=base_y, h=tree_height, w=tree_width, 
                            col=tree_color, d=depth):
                    # Draw as triangle
                    points = [
                        (x, y + h),           # Top
                        (x - w/2, y),         # Bottom-left
                        (x + w/2, y),         # Bottom-right
                    ]
                    arcade.draw_polygon_filled(points, col)
                
                renderer.add_to_layer('background', draw_pine, depth=depth - 10)
            
            else:
                # Deciduous tree - rounded shape
                def draw_deciduous(x=screen_x, y=base_y, h=tree_height, w=tree_width,
                                 col=tree_color, d=depth):
                    # Draw as circle on top of rectangle (trunk)
                    trunk_height = h * 0.3
                    crown_radius = w / 2
                    
                    # Trunk
                    arcade.draw_lrbt_rectangle_filled(
                        x - w/6, x + w/6,
                        y, y + trunk_height,
                        col
                    )
                    
                    # Crown (foliage)
                    arcade.draw_circle_filled(
                        x, y + trunk_height + crown_radius,
                        crown_radius,
                        col
                    )
                
                renderer.add_to_layer('background', draw_deciduous, depth=depth - 10)
    
    def _render_atmosphere(self, renderer):
        """Render subtle atmospheric fog for depth"""
        # Very subtle fog layer near horizon
        def draw_fog():
            fog_height = int(config.SCREEN_HEIGHT * 0.4)
            
            # Multiple layers for smooth gradient
            layers = 15
            for i in range(layers):
                t = i / layers
                alpha = int(20 * (1 - t) * self.fog_density)
                
                y = fog_height * t
                height = fog_height / layers
                
                r, g, b = self.fog_color
                arcade.draw_lrbt_rectangle_filled(
                    0, config.SCREEN_WIDTH,
                    y, y + height,
                    (r, g, b, alpha)
                )
        
        renderer.add_to_layer('background', draw_fog, depth=float('inf') - 3)