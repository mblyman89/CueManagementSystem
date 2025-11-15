# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller Spec File for CuePi
Firework Cue Management System - macOS App Bundle

This spec file configures PyInstaller to bundle the CuePi application
with all necessary dependencies, resources, and configurations.
"""

import os
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Define paths
block_cipher = None
project_root = 'CueManagementSystem/CueManagementSystem'

# Collect all data files
datas = [
    (os.path.join(project_root, 'images'), 'images'),
    (os.path.join(project_root, 'resources'), 'resources'),
    (os.path.join(project_root, 'config'), 'config'),
    (os.path.join(project_root, 'raspberry_pi'), 'raspberry_pi'),
    # New files for dynamic Spleeter path support
    (os.path.join(project_root, 'config_manager.py'), '.'),
    (os.path.join(project_root, 'views/dialogs/spleeter_setup_dialog.py'), 'views/dialogs'),
]

# Add librosa data files (audio processing models)
try:
    datas += collect_data_files('librosa')
except:
    pass

# Add madmom data files (beat detection models)
try:
    datas += collect_data_files('madmom')
except:
    pass

# Collect hidden imports
hiddenimports = [
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
    'librosa.onset',
    'librosa.beat',
    'soundfile',
    'audioread',
    'audioread.ffdec',
    'audioread.rawread',
    
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
    'madmom.audio.filters',
    'madmom.processors',
    'madmom.ml',
    'madmom.ml.nn',
    
    # Scientific computing
    'numpy',
    'numpy.core',
    'numpy.fft',
    'scipy',
    'scipy.signal',
    'scipy.fft',
    'scipy.ndimage',
    'scipy.interpolate',
    'matplotlib',
    'matplotlib.pyplot',
    'matplotlib.backends',
    'matplotlib.backends.backend_qt5agg',
    'matplotlib.figure',
    
    # Networking
    'asyncssh',
    'asyncio',
    'cryptography',
    
    # Image processing
    'PIL',
    'PIL.Image',
    'PIL.ImageQt',
    
    # Utilities
    'psutil',
    'tqdm',
    'jsonschema',
    'dataclasses',
    'configparser',
    'orjson',
    'dataclasses_json',
    
    # Platform specific
    'pyobjc',
    'Foundation',
    'AppKit',
]

# Collect all submodules for critical packages
try:
    hiddenimports += collect_submodules('madmom')
except:
    pass

try:
    hiddenimports += collect_submodules('librosa')
except:
    pass

# Analysis
a = Analysis(
    [os.path.join(project_root, 'main.py')],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'test',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ Archive
pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

# EXE
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CuePi',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # No console window for GUI app
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='CuePi'
)

# macOS App Bundle
app = BUNDLE(
    coll,
    name='CuePi.app',
    icon='CuePi_1024.png',  # Will be converted to .icns on macOS
    bundle_identifier='com.cuepi.fireworks',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSAppleScriptEnabled': False,
        'CFBundleName': 'CuePi',
        'CFBundleDisplayName': 'CuePi',
        'CFBundleGetInfoString': 'Firework Cue Management System',
        'CFBundleIdentifier': 'com.cuepi.fireworks',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2024 CuePi. All rights reserved.',
        'NSHighResolutionCapable': 'True',
        'LSMinimumSystemVersion': '10.15.0',
        'NSRequiresAquaSystemAppearance': 'False',
        'LSApplicationCategoryType': 'public.app-category.utilities',
    },
)