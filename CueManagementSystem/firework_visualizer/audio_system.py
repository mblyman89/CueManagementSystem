"""
Audio System - Sound effects for firework launches and explosions
Handles launch sounds, explosion sounds, crackle effects, and distance-based audio
"""

import arcade
import random
import math
from typing import Tuple, Optional


class AudioSystem:
    """
    Manages all audio for the firework visualizer.
    
    Features:
    - Launch sounds
    - Explosion sounds
    - Crackle sounds
    - Distance-based volume
    - 3D positional audio
    """
    
    def __init__(self, camera_position: Tuple[float, float, float]):
        """
        Initialize the audio system.
        
        Args:
            camera_position: (x, y, z) camera position for distance calculations
        """
        self.camera_position = list(camera_position)
        
        # Audio enabled flag
        self.audio_enabled = True
        self.master_volume = 0.7
        
        # Volume settings
        self.launch_volume = 0.5
        self.explosion_volume = 0.8
        self.crackle_volume = 0.4
        
        # Distance settings (in cm)
        self.max_audio_distance = 500000  # 5km
        self.reference_distance = 10000   # 100m
        
        # Sound pools (would contain actual sound objects)
        self.launch_sounds = []
        self.explosion_sounds = []
        self.crackle_sounds = []
        
        # Active sounds tracking
        self.active_sounds = []
        
        print("Audio System initialized")
        print(f"  - Master volume: {self.master_volume}")
        print(f"  - Max audio distance: {self.max_audio_distance/100}m")
    
    def update_camera_position(self, position: Tuple[float, float, float]):
        """
        Update camera position for distance calculations.
        
        Args:
            position: (x, y, z) new camera position
        """
        self.camera_position = list(position)
    
    def calculate_distance(self, sound_position: Tuple[float, float, float]) -> float:
        """
        Calculate distance from camera to sound source.
        
        Args:
            sound_position: (x, y, z) position of sound source
            
        Returns:
            Distance in cm
        """
        dx = sound_position[0] - self.camera_position[0]
        dy = sound_position[1] - self.camera_position[1]
        dz = sound_position[2] - self.camera_position[2]
        
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def calculate_volume(self, distance: float, base_volume: float) -> float:
        """
        Calculate volume based on distance using inverse square law.
        
        Args:
            distance: Distance to sound source in cm
            base_volume: Base volume (0-1)
            
        Returns:
            Adjusted volume (0-1)
        """
        if not self.audio_enabled:
            return 0.0
        
        if distance > self.max_audio_distance:
            return 0.0
        
        # Inverse square law with reference distance
        # volume = base_volume * (reference_distance / distance)²
        if distance < self.reference_distance:
            distance = self.reference_distance
        
        volume_factor = (self.reference_distance / distance) ** 2
        volume = base_volume * volume_factor * self.master_volume
        
        return max(0.0, min(1.0, volume))
    
    def calculate_delay(self, distance: float) -> float:
        """
        Calculate audio delay based on distance (speed of sound).
        
        Args:
            distance: Distance to sound source in cm
            
        Returns:
            Delay in seconds
        """
        # Speed of sound: ~34,300 cm/s at sea level
        speed_of_sound = 34300  # cm/s
        return distance / speed_of_sound
    
    def play_launch_sound(self, position: Tuple[float, float, float]):
        """
        Play launch sound with distance-based volume.
        
        Args:
            position: (x, y, z) position of launch
        """
        if not self.audio_enabled:
            return
        
        distance = self.calculate_distance(position)
        volume = self.calculate_volume(distance, self.launch_volume)
        delay = self.calculate_delay(distance)
        
        if volume > 0.01:  # Only play if audible
            # In a real implementation, would play actual sound here
            # arcade.play_sound(launch_sound, volume, delay=delay)
            print(f"Launch sound: volume={volume:.2f}, delay={delay:.2f}s, distance={distance/100:.1f}m")
    
    def play_explosion_sound(self, position: Tuple[float, float, float], 
                            shell_type: str = "Peony"):
        """
        Play explosion sound with distance-based volume.
        
        Args:
            position: (x, y, z) position of explosion
            shell_type: Type of firework for sound variation
        """
        if not self.audio_enabled:
            return
        
        distance = self.calculate_distance(position)
        volume = self.calculate_volume(distance, self.explosion_volume)
        delay = self.calculate_delay(distance)
        
        if volume > 0.01:  # Only play if audible
            # In a real implementation, would play actual sound here
            # Different sounds for different types
            print(f"Explosion sound ({shell_type}): volume={volume:.2f}, delay={delay:.2f}s")
    
    def play_crackle_sound(self, position: Tuple[float, float, float], 
                          intensity: float = 1.0):
        """
        Play crackle sound with distance-based volume.
        
        Args:
            position: (x, y, z) position of crackle
            intensity: Crackle intensity (0-1)
        """
        if not self.audio_enabled:
            return
        
        distance = self.calculate_distance(position)
        base_volume = self.crackle_volume * intensity
        volume = self.calculate_volume(distance, base_volume)
        delay = self.calculate_delay(distance)
        
        if volume > 0.01:  # Only play if audible
            # In a real implementation, would play actual sound here
            print(f"Crackle sound: volume={volume:.2f}, delay={delay:.2f}s")
    
    def set_master_volume(self, volume: float):
        """
        Set master volume.
        
        Args:
            volume: Volume level (0-1)
        """
        self.master_volume = max(0.0, min(1.0, volume))
        print(f"Master volume set to {self.master_volume:.2f}")
    
    def toggle_audio(self):
        """Toggle audio on/off."""
        self.audio_enabled = not self.audio_enabled
        status = "enabled" if self.audio_enabled else "disabled"
        print(f"Audio {status}")
        return self.audio_enabled
    
    def get_stats(self) -> dict:
        """
        Get audio system statistics.
        
        Returns:
            Dictionary with stats
        """
        return {
            'enabled': self.audio_enabled,
            'master_volume': self.master_volume,
            'launch_volume': self.launch_volume,
            'explosion_volume': self.explosion_volume,
            'crackle_volume': self.crackle_volume,
            'max_distance': self.max_audio_distance / 100,  # in meters
            'active_sounds': len(self.active_sounds)
        }
    
    def print_stats(self):
        """Print audio system statistics."""
        stats = self.get_stats()
        print("\n=== Audio System Statistics ===")
        print(f"Status: {'Enabled' if stats['enabled'] else 'Disabled'}")
        print(f"Master Volume: {stats['master_volume']:.2f}")
        print(f"Launch Volume: {stats['launch_volume']:.2f}")
        print(f"Explosion Volume: {stats['explosion_volume']:.2f}")
        print(f"Crackle Volume: {stats['crackle_volume']:.2f}")
        print(f"Max Audio Distance: {stats['max_distance']:.0f}m")
        print(f"Active Sounds: {stats['active_sounds']}")
        print("=" * 60)


# Audio configuration presets
AUDIO_PRESETS = {
    'QUIET': {
        'master_volume': 0.3,
        'launch_volume': 0.3,
        'explosion_volume': 0.4,
        'crackle_volume': 0.2
    },
    'NORMAL': {
        'master_volume': 0.7,
        'launch_volume': 0.5,
        'explosion_volume': 0.8,
        'crackle_volume': 0.4
    },
    'LOUD': {
        'master_volume': 1.0,
        'launch_volume': 0.8,
        'explosion_volume': 1.0,
        'crackle_volume': 0.6
    }
}


def apply_audio_preset(audio_system: AudioSystem, preset_name: str):
    """
    Apply an audio preset to the audio system.
    
    Args:
        audio_system: AudioSystem instance
        preset_name: Name of preset ('QUIET', 'NORMAL', 'LOUD')
    """
    preset = AUDIO_PRESETS.get(preset_name.upper())
    if not preset:
        print(f"Warning: Unknown preset '{preset_name}', using NORMAL")
        preset = AUDIO_PRESETS['NORMAL']
    
    audio_system.master_volume = preset['master_volume']
    audio_system.launch_volume = preset['launch_volume']
    audio_system.explosion_volume = preset['explosion_volume']
    audio_system.crackle_volume = preset['crackle_volume']
    
    print(f"Applied audio preset: {preset_name.upper()}")