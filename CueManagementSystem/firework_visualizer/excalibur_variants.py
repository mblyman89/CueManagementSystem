"""
Excalibur Shell Variants - 24 Production Configurations
Based on real Excalibur 60g artillery shell specifications
"""

# Excalibur Shell Variants
# 24 variants total: 3 variants per base type (8 types × 3 = 24)

EXCALIBUR_VARIANTS = {
    # ========== PEONY VARIANTS (Classic Spherical) ==========
    'Red Peony': {
        'base_type': 'Peony',
        'color': (255, 50, 50),
        'description': 'Classic red spherical burst',
        'effects': ['sphere', 'bright_core']
    },
    'Blue Peony': {
        'base_type': 'Peony',
        'color': (50, 100, 255),
        'description': 'Deep blue spherical burst',
        'effects': ['sphere', 'bright_core']
    },
    'Purple Peony': {
        'base_type': 'Peony',
        'color': (200, 50, 255),
        'description': 'Vibrant purple spherical burst',
        'effects': ['sphere', 'bright_core']
    },
    
    # ========== CHRYSANTHEMUM VARIANTS (Trailing) ==========
    'Gold Chrysanthemum': {
        'base_type': 'Chrysanthemum',
        'color': (255, 215, 0),
        'description': 'Golden trailing particles',
        'effects': ['trails', 'sparkle']
    },
    'Silver Chrysanthemum': {
        'base_type': 'Chrysanthemum',
        'color': (192, 192, 192),
        'description': 'Silver trailing particles',
        'effects': ['trails', 'sparkle']
    },
    'Green Chrysanthemum': {
        'base_type': 'Chrysanthemum',
        'color': (50, 255, 100),
        'description': 'Bright green trailing particles',
        'effects': ['trails', 'sparkle']
    },
    
    # ========== BROCADE VARIANTS (Crackling) ==========
    'Gold Brocade': {
        'base_type': 'Brocade',
        'color': (255, 215, 0),  # Color ignored, uses gold/silver
        'description': 'Traditional gold crackling effect',
        'effects': ['crackle', 'sparkle', 'gold']
    },
    'Silver Brocade': {
        'base_type': 'Brocade',
        'color': (192, 192, 192),  # Color ignored, uses gold/silver
        'description': 'Silver crackling effect',
        'effects': ['crackle', 'sparkle', 'silver']
    },
    'Titanium Brocade': {
        'base_type': 'Brocade',
        'color': (220, 220, 255),  # Color ignored, uses gold/silver
        'description': 'Bright titanium crackling',
        'effects': ['crackle', 'sparkle', 'titanium']
    },
    
    # ========== WILLOW VARIANTS (Drooping) ==========
    'Red Willow': {
        'base_type': 'Willow',
        'color': (255, 80, 80),
        'description': 'Red drooping willow trails',
        'effects': ['droop', 'trails']
    },
    'Green Willow': {
        'base_type': 'Willow',
        'color': (100, 255, 100),
        'description': 'Green drooping willow trails',
        'effects': ['droop', 'trails']
    },
    'Gold Willow': {
        'base_type': 'Willow',
        'color': (255, 200, 50),
        'description': 'Golden drooping willow trails',
        'effects': ['droop', 'trails', 'sparkle']
    },
    
    # ========== PALM VARIANTS (Rising) ==========
    'Red Palm': {
        'base_type': 'Palm',
        'color': (255, 60, 60),
        'description': 'Red rising palm fronds',
        'effects': ['rising', 'fronds']
    },
    'Green Palm': {
        'base_type': 'Palm',
        'color': (80, 255, 80),
        'description': 'Green rising palm fronds',
        'effects': ['rising', 'fronds']
    },
    'Gold Palm': {
        'base_type': 'Palm',
        'color': (255, 215, 0),
        'description': 'Golden rising palm fronds',
        'effects': ['rising', 'fronds', 'sparkle']
    },
    
    # ========== DAHLIA VARIANTS (Petals) ==========
    'Red Dahlia': {
        'base_type': 'Dahlia',
        'color': (255, 40, 40),
        'description': 'Red flower with distinct petals',
        'effects': ['petals', 'flower']
    },
    'Blue Dahlia': {
        'base_type': 'Dahlia',
        'color': (60, 120, 255),
        'description': 'Blue flower with distinct petals',
        'effects': ['petals', 'flower']
    },
    'Purple Dahlia': {
        'base_type': 'Dahlia',
        'color': (180, 60, 255),
        'description': 'Purple flower with distinct petals',
        'effects': ['petals', 'flower']
    },
    
    # ========== CRACKLE VARIANTS (Popping) ==========
    'White Crackle': {
        'base_type': 'Crackle',
        'color': (255, 255, 255),  # Color ignored, uses white
        'description': 'Dense white crackling',
        'effects': ['crackle', 'pop', 'dense']
    },
    'Silver Crackle': {
        'base_type': 'Crackle',
        'color': (192, 192, 192),  # Color ignored, uses white/silver
        'description': 'Silver crackling effect',
        'effects': ['crackle', 'pop', 'dense']
    },
    'Titanium Crackle': {
        'base_type': 'Crackle',
        'color': (220, 220, 255),  # Color ignored, uses white
        'description': 'Bright titanium crackling',
        'effects': ['crackle', 'pop', 'dense', 'bright']
    },
    
    # ========== MULTIEFFECT VARIANTS (Stages) ==========
    'Red to Gold': {
        'base_type': 'MultiEffect',
        'color': (255, 50, 50),
        'description': 'Red burst transitioning to gold',
        'effects': ['stages', 'color_change', 'complex']
    },
    'Blue to Silver': {
        'base_type': 'MultiEffect',
        'color': (50, 100, 255),
        'description': 'Blue burst transitioning to silver',
        'effects': ['stages', 'color_change', 'complex']
    },
    'Purple to Green': {
        'base_type': 'MultiEffect',
        'color': (200, 50, 255),
        'description': 'Purple burst transitioning to green',
        'effects': ['stages', 'color_change', 'complex']
    }
}

# Variant categories for easy access
VARIANT_CATEGORIES = {
    'Peony': ['Red Peony', 'Blue Peony', 'Purple Peony'],
    'Chrysanthemum': ['Gold Chrysanthemum', 'Silver Chrysanthemum', 'Green Chrysanthemum'],
    'Brocade': ['Gold Brocade', 'Silver Brocade', 'Titanium Brocade'],
    'Willow': ['Red Willow', 'Green Willow', 'Gold Willow'],
    'Palm': ['Red Palm', 'Green Palm', 'Gold Palm'],
    'Dahlia': ['Red Dahlia', 'Blue Dahlia', 'Purple Dahlia'],
    'Crackle': ['White Crackle', 'Silver Crackle', 'Titanium Crackle'],
    'MultiEffect': ['Red to Gold', 'Blue to Silver', 'Purple to Green']
}

# All variant names in order
ALL_VARIANTS = [
    # Peony
    'Red Peony', 'Blue Peony', 'Purple Peony',
    # Chrysanthemum
    'Gold Chrysanthemum', 'Silver Chrysanthemum', 'Green Chrysanthemum',
    # Brocade
    'Gold Brocade', 'Silver Brocade', 'Titanium Brocade',
    # Willow
    'Red Willow', 'Green Willow', 'Gold Willow',
    # Palm
    'Red Palm', 'Green Palm', 'Gold Palm',
    # Dahlia
    'Red Dahlia', 'Blue Dahlia', 'Purple Dahlia',
    # Crackle
    'White Crackle', 'Silver Crackle', 'Titanium Crackle',
    # MultiEffect
    'Red to Gold', 'Blue to Silver', 'Purple to Green'
]


def get_variant_config(variant_name):
    """
    Get configuration for a specific variant.
    
    Args:
        variant_name: Name of the variant
        
    Returns:
        Dictionary with variant configuration or None
    """
    return EXCALIBUR_VARIANTS.get(variant_name)


def get_variants_by_type(base_type):
    """
    Get all variants for a specific base type.
    
    Args:
        base_type: Base firework type (e.g., 'Peony')
        
    Returns:
        List of variant names
    """
    return VARIANT_CATEGORIES.get(base_type, [])


def get_random_variant():
    """
    Get a random variant name.
    
    Returns:
        Random variant name
    """
    import random
    return random.choice(ALL_VARIANTS)


def print_all_variants():
    """Print all available variants organized by type."""
    print("\n" + "=" * 70)
    print("EXCALIBUR SHELL VARIANTS - 24 Configurations")
    print("=" * 70)
    
    for base_type, variants in VARIANT_CATEGORIES.items():
        print(f"\n{base_type} Variants:")
        for i, variant in enumerate(variants, 1):
            config = EXCALIBUR_VARIANTS[variant]
            print(f"  {i}. {variant:25s} - {config['description']}")
    
    print("\n" + "=" * 70)
    print(f"Total: {len(ALL_VARIANTS)} variants")
    print("=" * 70)


def get_variant_stats():
    """
    Get statistics about variants.
    
    Returns:
        Dictionary with stats
    """
    return {
        'total_variants': len(ALL_VARIANTS),
        'base_types': len(VARIANT_CATEGORIES),
        'variants_per_type': 3,
        'categories': list(VARIANT_CATEGORIES.keys())
    }