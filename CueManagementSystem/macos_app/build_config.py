"""
PyInstaller Build Configuration Helper
Analyzes the project and generates the spec file
"""
import os
from pathlib import Path

def get_all_data_files(base_path):
    """
    Recursively collect all data files from the project
    """
    data_files = []
    
    # Define directories to include
    data_dirs = [
        'images',
        'resources',
        'config',
        'raspberry_pi',
    ]
    
    for data_dir in data_dirs:
        dir_path = os.path.join(base_path, data_dir)
        if os.path.exists(dir_path):
            # Add the entire directory
            data_files.append((data_dir, data_dir))
            print(f"  ✓ Including directory: {data_dir}")
    
    return data_files

def get_hidden_imports():
    """
    Get list of hidden imports that PyInstaller might miss
    """
    hidden_imports = [
        # PySide6 modules
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'PySide6.QtMultimedia',
        'PySide6.QtMultimediaWidgets',
        'PySide6.QtAsyncio',
        'PySide6.QtAsyncio.events',
        
        # Audio processing
        'librosa',
        'librosa.core',
        'librosa.feature',
        'librosa.display',
        'soundfile',
        'audioread',
        
        # Madmom (critical for beat detection)
        'madmom',
        'madmom.features',
        'madmom.features.beats',
        'madmom.features.onsets',
        'madmom.features.tempo',
        'madmom.audio',
        'madmom.audio.signal',
        'madmom.audio.spectrogram',
        'madmom.audio.stft',
        'madmom.processors',
        
        # Scientific computing
        'numpy',
        'scipy',
        'scipy.signal',
        'scipy.fft',
        'matplotlib',
        'matplotlib.pyplot',
        'matplotlib.backends.backend_qt5agg',
        
        # Networking
        'asyncssh',
        'asyncio',
        
        # Utilities
        'PIL',
        'PIL.Image',
        'psutil',
        'tqdm',
        'jsonschema',
        'dataclasses',
        'configparser',
        
        # Project modules
        'controllers',
        'models',
        'views',
        'utils',
    ]
    
    return hidden_imports

def analyze_project(project_path):
    """
    Analyze the project structure and report findings
    """
    print("\n" + "="*60)
    print("PROJECT ANALYSIS")
    print("="*60)
    
    main_file = os.path.join(project_path, 'main.py')
    print(f"\n📍 Main entry point: {main_file}")
    print(f"   Exists: {os.path.exists(main_file)}")
    
    print("\n📦 Data directories:")
    data_files = get_all_data_files(project_path)
    
    print("\n🔍 Hidden imports to include:")
    hidden_imports = get_hidden_imports()
    for imp in hidden_imports[:10]:
        print(f"   • {imp}")
    print(f"   ... and {len(hidden_imports) - 10} more")
    
    print("\n" + "="*60)
    
    return data_files, hidden_imports

if __name__ == "__main__":
    project_path = "CueManagementSystem/CueManagementSystem"
    analyze_project(project_path)