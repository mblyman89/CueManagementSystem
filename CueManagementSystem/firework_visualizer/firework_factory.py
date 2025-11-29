"""
Firework Factory - Creates firework instances based on type
Implements factory pattern for easy firework creation
Supports both base types and Excalibur variants
"""

from firework_visualizer.firework_peony import FireworkPeony
from firework_visualizer.firework_chrysanthemum import FireworkChrysanthemum
from firework_visualizer.firework_brocade import FireworkBrocade
from firework_visualizer.firework_willow import FireworkWillow
from firework_visualizer.firework_palm import FireworkPalm
from firework_visualizer.firework_dahlia import FireworkDahlia
from firework_visualizer.firework_crackle import FireworkCrackle
from firework_visualizer.firework_multieffect import FireworkMultiEffect
from firework_visualizer.excalibur_variants import EXCALIBUR_VARIANTS, get_variant_config


class FireworkFactory:
    """
    Factory for creating firework instances.
    
    Provides a centralized way to create fireworks of different types.
    """
    
    # Available firework types
    TYPES = {
        'Peony': FireworkPeony,
        'Chrysanthemum': FireworkChrysanthemum,
        'Brocade': FireworkBrocade,
        'Willow': FireworkWillow,
        'Palm': FireworkPalm,
        'Dahlia': FireworkDahlia,
        'Crackle': FireworkCrackle,
        'MultiEffect': FireworkMultiEffect
    }
    
    @staticmethod
    def create_firework(firework_type, position, velocity, color, particle_manager):
        """
        Create a firework of the specified type or variant.
        
        Args:
            firework_type: String name of firework type or variant
            position: (x, y, z) burst position
            velocity: (vx, vy, vz) shell velocity at burst
            color: (r, g, b) primary color (may be overridden by variant)
            particle_manager: ParticleManager instance
            
        Returns:
            Firework instance or None if type not found
        """
        # Check if it's an Excalibur variant
        variant_config = get_variant_config(firework_type)
        
        if variant_config:
            # It's a variant - use variant's base type and color
            base_type = variant_config['base_type']
            variant_color = variant_config['color']
            firework_class = FireworkFactory.TYPES.get(base_type)
            
            if firework_class is None:
                print(f"Warning: Unknown base type '{base_type}', using Peony")
                firework_class = FireworkPeony
            
            return firework_class(position, velocity, variant_color, particle_manager)
        
        # Not a variant - check if it's a base type
        firework_class = FireworkFactory.TYPES.get(firework_type)
        
        if firework_class is None:
            print(f"Warning: Unknown firework type '{firework_type}', using Peony")
            firework_class = FireworkPeony
        
        return firework_class(position, velocity, color, particle_manager)
    
    @staticmethod
    def get_available_types():
        """
        Get list of available firework types.
        
        Returns:
            List of type names
        """
        return list(FireworkFactory.TYPES.keys())
    
    @staticmethod
    def get_type_description(firework_type):
        """
        Get description of a firework type.
        
        Args:
            firework_type: String name of firework type
            
        Returns:
            Description string
        """
        descriptions = {
            'Peony': 'Classic spherical burst with single color',
            'Chrysanthemum': 'Trailing particles with long tails',
            'Brocade': 'Crackling gold/silver effect',
            'Willow': 'Drooping trails like a weeping willow',
            'Palm': 'Thick rising trails like palm fronds',
            'Dahlia': 'Large petals with distinct sections',
            'Crackle': 'Dense popping and crackling effect',
            'MultiEffect': 'Multiple stages with different effects'
        }
        return descriptions.get(firework_type, 'Unknown type')
    
    @staticmethod
    def get_available_variants():
        """
        Get list of all Excalibur variants.
        
        Returns:
            List of variant names
        """
        from excalibur_variants import ALL_VARIANTS
        return ALL_VARIANTS
    
    @staticmethod
    def print_available_types():
        """Print all available firework types with descriptions."""
        print("\n=== Available Firework Types ===")
        for i, firework_type in enumerate(FireworkFactory.get_available_types(), 1):
            desc = FireworkFactory.get_type_description(firework_type)
            print(f"{i}. {firework_type:15s} - {desc}")
        print("=" * 60)
    
    @staticmethod
    def print_available_variants():
        """Print all available Excalibur variants."""
        from excalibur_variants import print_all_variants
        print_all_variants()