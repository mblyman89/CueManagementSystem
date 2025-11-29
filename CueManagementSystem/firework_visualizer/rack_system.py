"""
Rack System - Manages all 20 mortar racks in 4×5 grid layout
Handles rack positioning, organization, and access
"""

import math
from typing import List, Tuple, Optional
import config
from firework_visualizer.mortar_rack import MortarRack
from firework_visualizer.mortar_tube import MortarTube


class RackSystem:
    """
    Manages the complete system of 20 mortar racks arranged in a 4×5 grid
    """
    
    def __init__(self):
        """Initialize the rack system with all 20 racks"""
        self.racks: List[MortarRack] = []
        
        # Grid configuration
        self.rows = config.RACK_ROWS  # 4 rows
        self.cols = config.RACK_COLS  # 5 columns
        self.spacing = config.RACK_SPACING  # 50 cm between racks
        
        # Calculate grid center position (behind dock)
        # Racks are positioned behind the camera, in front of the dock
        self.grid_center_x = 0  # Centered on X axis
        self.grid_center_y = -200  # 2 meters behind camera
        self.grid_center_z = 0  # On ground level
        
        # Create all racks
        self._create_rack_grid()
        
        print(f"Rack System initialized:")
        print(f"  - {len(self.racks)} racks created")
        print(f"  - {self.get_total_tubes()} total tubes")
        print(f"  - Grid: {self.rows} rows × {self.cols} columns")
        print(f"  - Spacing: {self.spacing} cm")
    
    def _create_rack_grid(self):
        """Create all 20 racks in a 4×5 grid layout"""
        # Calculate total grid dimensions
        total_width = (self.cols - 1) * (config.RACK_WIDTH + self.spacing)
        total_depth = (self.rows - 1) * (config.RACK_DEPTH + self.spacing)
        
        # Starting position (front-left corner of grid)
        start_x = self.grid_center_x - total_width / 2
        start_y = self.grid_center_y - total_depth / 2
        
        rack_id = 0
        
        for row in range(self.rows):
            for col in range(self.cols):
                # Calculate rack position
                rack_x = start_x + col * (config.RACK_WIDTH + self.spacing)
                rack_y = start_y + row * (config.RACK_DEPTH + self.spacing)
                rack_z = self.grid_center_z
                
                # Create rack
                rack = MortarRack(
                    world_position=(rack_x, rack_y, rack_z),
                    rack_id=rack_id
                )
                
                self.racks.append(rack)
                rack_id += 1
    
    def get_rack(self, row: int, col: int) -> Optional[MortarRack]:
        """
        Get a specific rack by grid position
        
        Args:
            row: Row index (0-3)
            col: Column index (0-4)
        
        Returns:
            MortarRack instance or None
        """
        if 0 <= row < self.rows and 0 <= col < self.cols:
            index = row * self.cols + col
            return self.racks[index]
        return None
    
    def get_rack_by_id(self, rack_id: int) -> Optional[MortarRack]:
        """
        Get a rack by its ID
        
        Args:
            rack_id: Rack ID (0-19)
        
        Returns:
            MortarRack instance or None
        """
        if 0 <= rack_id < len(self.racks):
            return self.racks[rack_id]
        return None
    
    def get_tube(self, rack_id: int, tube_row: int, tube_col: int) -> Optional[MortarTube]:
        """
        Get a specific tube by rack ID and tube position
        
        Args:
            rack_id: Rack ID (0-19)
            tube_row: Tube row in rack (0-4)
            tube_col: Tube column in rack (0-9)
        
        Returns:
            MortarTube instance or None
        """
        rack = self.get_rack_by_id(rack_id)
        if rack:
            return rack.get_tube(tube_row, tube_col)
        return None
    
    def get_tube_by_global_id(self, tube_id: int) -> Optional[MortarTube]:
        """
        Get a tube by its global ID (0-999)
        
        Args:
            tube_id: Global tube ID (0-999)
        
        Returns:
            MortarTube instance or None
        """
        if 0 <= tube_id < config.TOTAL_TUBES:
            rack_id = tube_id // config.TUBES_PER_RACK
            tube_index = tube_id % config.TUBES_PER_RACK
            
            rack = self.get_rack_by_id(rack_id)
            if rack and tube_index < len(rack.tubes):
                return rack.tubes[tube_index]
        
        return None
    
    def get_total_tubes(self) -> int:
        """Get total number of tubes in the system"""
        return len(self.racks) * config.TUBES_PER_RACK
    
    def get_available_tubes(self) -> List[MortarTube]:
        """
        Get all tubes that have shells and haven't been fired
        
        Returns:
            List of available MortarTube instances
        """
        available = []
        for rack in self.racks:
            for tube in rack.tubes:
                if tube.has_shell and not tube.is_fired:
                    available.append(tube)
        return available
    
    def get_grid_bounds(self) -> dict:
        """
        Get the bounding box of the entire rack grid
        
        Returns:
            Dictionary with min/max X, Y, Z coordinates
        """
        if not self.racks:
            return None
        
        # Calculate bounds from all rack positions
        min_x = min(rack.position[0] - config.RACK_WIDTH/2 for rack in self.racks)
        max_x = max(rack.position[0] + config.RACK_WIDTH/2 for rack in self.racks)
        min_y = min(rack.position[1] - config.RACK_DEPTH/2 for rack in self.racks)
        max_y = max(rack.position[1] + config.RACK_DEPTH/2 for rack in self.racks)
        min_z = min(rack.position[2] for rack in self.racks)
        max_z = max(rack.position[2] + config.RACK_HEIGHT for rack in self.racks)
        
        return {
            'min_x': min_x,
            'max_x': max_x,
            'min_y': min_y,
            'max_y': max_y,
            'min_z': min_z,
            'max_z': max_z,
        }
    
    def render(self, camera, renderer):
        """
        Render all racks and tubes
        
        Args:
            camera: Camera3D instance
            renderer: SceneRenderer instance
        """
        # Render racks from back to front for proper depth sorting
        # Sort by Y position (further away = higher Y value)
        sorted_racks = sorted(self.racks, key=lambda r: -r.position[1])
        
        for rack in sorted_racks:
            rack.render(camera, renderer)
    
    def get_rack_info(self) -> str:
        """
        Get formatted information about the rack system
        
        Returns:
            Multi-line string with rack system info
        """
        info = []
        info.append(f"Rack System Information:")
        info.append(f"  Total Racks: {len(self.racks)}")
        info.append(f"  Grid Layout: {self.rows} rows × {self.cols} columns")
        info.append(f"  Total Tubes: {self.get_total_tubes()}")
        info.append(f"  Tubes per Rack: {config.TUBES_PER_RACK}")
        info.append(f"  Rack Spacing: {self.spacing} cm")
        
        available = len(self.get_available_tubes())
        info.append(f"  Available Tubes: {available}")
        
        bounds = self.get_grid_bounds()
        if bounds:
            width = bounds['max_x'] - bounds['min_x']
            depth = bounds['max_y'] - bounds['min_y']
            info.append(f"  Grid Dimensions: {width:.1f} × {depth:.1f} cm")
        
        return "\n".join(info)