# 🎆 Firework Cue Management System (CuePi)

**A Professional Desktop Application for Designing, Synchronizing, and Executing Firework Shows with Musical Integration**

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/) [![PySide6](https://img.shields.io/badge/GUI-PySide6-green.svg)](https://www.qt.io/qt-for-python) ![License](https://img.shields.io/badge/license-Proprietary-red.svg)

* * *

## 📑 Table of Contents

-   [Overview](#-overview)
-   [Key Features](#-key-features)
-   [System Architecture](#-system-architecture)
-   [System Requirements](#-system-requirements)
-   [Installation Guide](#-installation-guide)
    -   [Quick Start](#quick-start)
    -   [Detailed Setup](#detailed-setup)
    -   [Spleeter Configuration](#spleeter-configuration)
    -   [Raspberry Pi Setup](#raspberry-pi-setup)
-   [Building macOS Application](#-building-macos-application)
-   [Usage Guide](#-usage-guide)
-   [Advanced Features](#-advanced-features)
-   [Troubleshooting](#-troubleshooting)
-   [Tips & Tricks](#-tips--tricks)
-   [Project Structure](#-project-structure)
-   [API Documentation](#-api-documentation)
-   [Contributing](#-contributing)
-   [License](#-license)
-   [Acknowledgments](#-acknowledgments)

* * *

## 🎯 Overview

The **Firework Cue Management System** (also known as **CuePi**) is a comprehensive, professional-grade desktop application designed for pyrotechnicians, show designers, and firework enthusiasts. It enables users to create, design, and execute sophisticated firework displays synchronized with music, featuring state-of-the-art audio analysis, beat detection, and hardware control capabilities.

### What Makes CuePi Special?

-   **🎵 Advanced Music Synchronization**: Automatically detect beats, drum hits, and musical elements to create perfectly timed firework sequences
-   **🤖 AI-Powered Beat Detection**: Utilizes machine learning (madmom RNN) for professional-grade beat tracking
-   **🎼 Audio Stem Separation**: Integrates Spleeter to isolate drums for superior beat detection accuracy
-   **🎮 Hardware Control**: Direct integration with Raspberry Pi GPIO for real-world firework control
-   **📊 Real-Time Visualization**: Professional waveform rendering with multiple visualization modes
-   **🔒 Safety First**: Comprehensive safety features including arm/disarm controls, emergency stops, and pre-show checklists
-   **🖥️ Cross-Platform**: Runs on Windows, macOS, and Linux with native look and feel

* * *

## ✨ Key Features

### 🎨 Show Design and Management

#### Cue Creation & Editing

-   **Manual Cue Creation**: Create individual cues with precise timing control (millisecond accuracy)
-   **Automatic Show Generation**: Generate entire shows based on music analysis
-   **Cue Types Supported**:
    -   `SHOT`: Single firework ignition
    -   `DOUBLE_SHOT`: Two simultaneous firework ignitions
    -   `RUN`: Sequential firing of multiple outputs
    -   `DOUBLE_RUN`: Sequential firing with paired outputs
-   **Drag-and-Drop Reordering**: Intuitive cue sequence management
-   **Bulk Operations**: Edit, delete, or modify multiple cues simultaneously
-   **Cue Validation**: Automatic conflict detection and resolution

#### Show Management

-   **Save/Load Shows**: JSON-based show file format for easy sharing
-   **Import/Export**: CSV import/export for external editing
-   **Show Templates**: Pre-configured show templates for common scenarios
-   **Version Control**: Track changes and maintain show history
-   **Backup System**: Automatic backup of show configurations

### 🎵 Music Integration and Analysis

#### Audio Processing

-   **Multi-Format Support**: WAV, MP3, FLAC, OGG, M4A, and more
-   **Waveform Visualization**:
    -   Traditional amplitude view
    -   RMS envelope rendering
    -   Spectral color mapping
    -   Frequency band visualization
    -   Dual-layer rendering
-   **Zoom & Navigation**: Precise waveform navigation with multiple zoom levels
-   **Real-Time Playback**: Synchronized audio playback with visual feedback

#### Beat Detection & Analysis

-   **Multiple Detection Methods**:
    -   **Librosa Beat Tracking**: Fast, reliable beat detection
    -   **Madmom RNN**: State-of-the-art neural network-based detection
    -   **Onset Detection**: Spectral flux, high-frequency content, complex domain
    -   **Peak Detection**: Amplitude-based peak finding with customizable thresholds
-   **Drum Classification**: Automatic identification of kick, snare, hi-hat, and other drum sounds
-   **Tempo Estimation**: Automatic BPM detection and tempo tracking
-   **Beat Confidence Scoring**: Quality metrics for detected beats

#### Spleeter Integration

-   **Audio Stem Separation**: Isolate drums, vocals, bass, and other instruments
-   **Enhanced Beat Detection**: Analyze isolated drum tracks for superior accuracy
-   **Stem Models**:
    -   2stems: vocals/accompaniment
    -   4stems: vocals/drums/bass/other
    -   5stems: vocals/drums/bass/piano/other
-   **Caching System**: Intelligent caching of separated stems for performance
-   **Background Processing**: Non-blocking audio separation with progress tracking

### 🎆 Firework Control

#### Output Management

-   **Multiple Output Channels**: Support for 128+ individual firework outputs
-   **Output Mapping**: Flexible mapping of cues to physical outputs
-   **Output Grouping**: Organize outputs into logical groups
-   **Output Testing**: Safe testing mode for individual output verification
-   **Output Status Monitoring**: Real-time status display for all outputs

#### Timing & Synchronization

-   **Millisecond Precision**: Accurate timing control for professional shows
-   **Music Synchronization**: Lock cues to specific musical timestamps
-   **Offset Adjustment**: Fine-tune timing with global or per-cue offsets
-   **Tempo Sync**: Automatic adjustment for tempo changes
-   **Preview Mode**: Simulate shows before execution

#### Safety Features

-   **Arm/Disarm System**: Physical arming switch requirement
-   **Emergency Stop**: Instant shutdown of all outputs
-   **Pre-Show Checklist**: Comprehensive safety verification before execution
-   **Watchdog Timer**: Automatic safety shutdown on connection loss
-   **Output Enable Control**: Master enable/disable for all outputs
-   **Connection Monitoring**: Real-time hardware connection status

### 🔌 Hardware Integration

#### Raspberry Pi Support

-   **GPIO Control**: Direct control via 74HC595 shift registers
-   **Remote Execution**: SSH-based remote control from desktop application
-   **Network Modes**:
    -   WiFi Client Mode: Connect to existing network
    -   Ad-Hoc Mode: Create dedicated hotspot for direct connection
-   **Hardware Monitoring**: Real-time GPIO status and diagnostics
-   **Automatic Reconnection**: Robust connection handling with auto-retry

#### Shift Register Control

-   **74HC595 Support**: Industry-standard shift register control
-   **Daisy-Chaining**: Support for multiple cascaded shift registers
-   **Pin Configuration**:
    -   Data Pin: Serial data input
    -   Clock Pin: Shift clock
    -   Latch Pin: Output latch
    -   Enable Pin: Output enable (active low)
    -   Clear Pin: Master clear (active low)
-   **State Management**: Persistent state tracking and recovery

### 🖥️ User Interface

#### Main Window

-   **Cue Table**: Sortable, filterable table with inline editing
-   **LED Panel**: Visual representation of output states
    -   Traditional view: Individual LED indicators
    -   Grouped view: Organized by output groups
-   **Timeline**: Visual timeline for show preview and scrubbing
-   **Status Bar**: Real-time system status and connection info
-   **Button Bar**: Quick access to common operations

#### Dialogs & Tools

-   **Cue Creator**: Intuitive dialog for creating new cues
-   **Cue Editor**: Advanced editing with validation
-   **Music Manager**: Audio file management and playback
-   **Waveform Analyzer**: Professional audio analysis interface
-   **Musical Generator**: Automatic cue generation from beats
-   **Show Generator**: Random show generation with customizable parameters
-   **Mode Selector**: System mode configuration (Simulation/Hardware)
-   **Terminal Emulator**: Built-in SSH terminal for Raspberry Pi
-   **Pre-Show Checklist**: Safety verification dialog

#### Customization

-   **Theme Support**: Dark and light themes
-   **Color Schemes**: Multiple waveform color schemes
-   **Layout Options**: Customizable window layouts
-   **Keyboard Shortcuts**: Extensive keyboard shortcut support
-   **Preferences**: Comprehensive settings management

* * *

## 🏗️ System Architecture

### Application Structure

```
CueManagementSystem/
├── CueManagementSystem/          # Main application package
│   ├── main.py                   # Application entry point
│   ├── controllers/              # Business logic controllers
│   │   ├── cue_controller.py     # Cue management logic
│   │   ├── system_mode_controller.py  # System mode management
│   │   ├── hardware_controller.py     # Hardware communication
│   │   ├── show_execution_manager.py  # Show execution logic
│   │   └── ...
│   ├── models/                   # Data models
│   │   ├── cue_model.py         # Cue data structure
│   │   ├── database_model.py    # Database interface
│   │   └── ...
│   ├── views/                    # UI components
│   │   ├── main_window.py       # Main application window
│   │   ├── welcome_page.py      # Welcome screen
│   │   ├── cue_table.py         # Cue table widget
│   │   ├── led_grid.py          # LED visualization
│   │   ├── waveform_widget.py   # Waveform display
│   │   └── ...
│   ├── utils/                    # Utility modules
│   │   ├── json_utils.py        # JSON serialization
│   │   ├── spleeter_service.py  # Spleeter integration
│   │   ├── waveform_analyzer.py # Audio analysis
│   │   ├── music_manager.py     # Music file management
│   │   └── ...
│   ├── raspberry_pi/             # Raspberry Pi scripts
│   │   ├── execute_cue.py       # Cue execution script
│   │   ├── execute_show.py      # Show execution script
│   │   ├── toggle_outputs.py    # Output control
│   │   ├── emergency_stop.py    # Emergency stop
│   │   ├── get_gpio_status.py   # GPIO status query
│   │   └── ...
│   ├── macos_app/                # macOS app building
│   │   ├── build_macos_app.sh   # Build script
│   │   ├── fix_spleeter_hardcode.sh  # Spleeter path fix
│   │   ├── create_dmg.sh        # DMG installer creation
│   │   └── CuePi.spec           # PyInstaller spec file
│   ├── config/                   # Configuration files
│   ├── resources/                # Application resources
│   ├── images/                   # Image assets
│   └── logs/                     # Application logs
├── requirements.txt              # Python dependencies
└── README.md                     # This file
```

### Technology Stack

#### Frontend (GUI)

-   **PySide6**: Qt 6 bindings for Python - provides entire GUI framework
-   **Custom Widgets**: Specialized widgets for LED visualization, waveform display, etc.

#### Audio Processing

-   **Librosa**: Core audio analysis and feature extraction
-   **Madmom**: Advanced beat detection with RNN models
-   **SciPy**: Signal processing and filtering
-   **NumPy**: Numerical computing and array operations
-   **Soundfile**: Audio file I/O
-   **Spleeter**: Audio source separation (separate environment)

#### Machine Learning

-   **Scikit-learn**: Clustering, classification, and preprocessing
-   **TensorFlow**: Backend for Spleeter (in separate environment)

#### Networking

-   **Paramiko**: SSH client for Raspberry Pi communication
-   **AsyncSSH**: Asynchronous SSH operations

#### Hardware Control

-   **RPi.GPIO**: Raspberry Pi GPIO control
-   **lgpio**: Modern GPIO library alternative

#### Data Management

-   **SQLite**: Local database for show storage
-   **JSON**: Configuration and show file format
-   **CSV**: Import/export format

* * *

## 💻 System Requirements

### Minimum Requirements

| Component | Requirement |
| --- | --- |
| **Operating System** | Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+) |
| **Python Version** | 3.8 or higher (3.10+ recommended) |
| **CPU** | Dual-core 2.0 GHz or faster |
| **RAM** | 8 GB |
| **Storage** | 2 GB free space |
| **Display** | 1280x720 minimum resolution |
| **Audio** | Sound card for audio playback |

### Recommended Requirements

| Component | Requirement |
| --- | --- |
| **Operating System** | macOS 12+, Windows 11, Ubuntu 22.04+ |
| **Python Version** | 3.10 or 3.11 |
| **CPU** | Quad-core 2.5 GHz or faster |
| **RAM** | 16 GB (for large audio files and Spleeter) |
| **Storage** | 5 GB free space (includes Spleeter models) |
| **Display** | 1920x1080 or higher |
| **GPU** | Dedicated GPU recommended for Spleeter (Apple Silicon or NVIDIA) |

### Hardware Requirements (Optional)

For physical firework control:

| Component | Specification |
| --- | --- |
| **Raspberry Pi** | Raspberry Pi 3B+, 4, or Zero W2 |
| **Power Supply** | 5V 3A USB-C (Pi 4) or 5V 2.5A micro-USB (Pi 3) |
| **SD Card** | 16 GB Class 10 or better |
| **Shift Registers** | 74HC595 (one or more, daisy-chained) |
| **Network** | WiFi or Ethernet connection |
| **Relay Board** | Solid-state relays for firework ignition |

### System Dependencies

#### macOS

```bash
# Install via Homebrew
brew install ffmpeg libsndfile portaudio
```

#### Ubuntu/Debian

```bash
sudo apt-get update
sudo apt-get install ffmpeg libsndfile1 portaudio19-dev python3-dev
```

#### Raspberry Pi (Raspbian/Raspberry Pi OS)

```bash
sudo apt-get update
sudo apt-get install ffmpeg libsndfile1 portaudio19-dev python3-rpi.gpio python3-dev
```

#### Windows

-   **FFmpeg**: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH
-   **Visual C++ Redistributable**: Required for some audio libraries

* * *

## 📦 Installation Guide

### Quick Start

For users who want to get started quickly:

```bash
# 1. Clone the repository
git clone https://github.com/mblyman89/CueManagementSystem.git
cd CueManagementSystem

# 2. Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
cd CueManagementSystem
python main.py
```

### Detailed Setup

#### Step 1: Install Python

**Option A: Using System Python**

1.  Download Python from [python.org](https://www.python.org/downloads/)
2.  Install Python 3.10 or 3.11 (recommended)
3.  Verify installation:
    
    ```bash
    python3 --version
    ```
    

**Option B: Using Anaconda/Miniconda (Recommended)**

1.  Download Miniconda from [Anaconda's website](https://docs.conda.io/en/latest/miniconda.html)
2.  Install Miniconda following the installer instructions
3.  Verify installation:
    
    ```bash
    conda --version
    ```
    

#### Step 2: Clone the Repository

```bash
# Using HTTPS
git clone https://github.com/mblyman89/CueManagementSystem.git

# Or using SSH
git clone git@github.com:mblyman89/CueManagementSystem.git

# Navigate to the project directory
cd CueManagementSystem
```

#### Step 3: Set Up Virtual Environment

**Option A: Using Conda (Recommended)**

```bash
# Create a new conda environment
conda create -n firework_env python=3.11

# Activate the environment
conda activate firework_env

# Verify Python version
python --version  # Should show Python 3.11.x
```

**Option B: Using venv**

```bash
# Create virtual environment
python3 -m venv .venv

# Activate the environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Verify activation (should show .venv in prompt)
which python  # Should point to .venv/bin/python
```

#### Step 4: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt

# Verify installation
pip list
```

**Common Installation Issues:**

1.  **NumPy/SciPy Installation Fails**:
    
    ```bash
    # Install build tools first
    # macOS:
    xcode-select --install
    
    # Ubuntu/Debian:
    sudo apt-get install build-essential python3-dev
    
    # Then retry pip install
    ```
    
2.  **PyAudio Installation Fails (Windows)**:
    
    ```bash
    # Download pre-built wheel from:
    # https://www.lfd.uci.edu/~gohlke/pythonlibs/#pyaudio
    pip install PyAudio‑0.2.11‑cp311‑cp311‑win_amd64.whl
    ```
    
3.  **Madmom Installation Issues**:
    
    ```bash
    # Ensure NumPy < 2.0
    pip install "numpy<2.0"
    pip install madmom
    ```
    

#### Step 5: Verify Installation

```bash
# Test import of key modules
python -c "import PySide6; print('PySide6:', PySide6.__version__)"
python -c "import librosa; print('Librosa:', librosa.__version__)"
python -c "import numpy; print('NumPy:', numpy.__version__)"
python -c "import scipy; print('SciPy:', scipy.__version__)"
python -c "import madmom; print('Madmom: OK')"
```

### Spleeter Configuration

Spleeter requires a **separate Python 3.8 environment** due to TensorFlow compatibility issues.

#### Step 1: Create Spleeter Environment

```bash
# Create Python 3.8 environment
conda create -n spleeter_env python=3.8

# Activate the environment
conda activate spleeter_env
```

#### Step 2: Install Spleeter

**For Intel/AMD (x86\_64) Systems:**

```bash
pip install spleeter
```

**For Apple Silicon (M1/M2/M3) Macs:**

```bash
# Install Apple's optimized TensorFlow
pip install tensorflow-macos tensorflow-metal

# Install Spleeter
pip install spleeter
```

#### Step 3: Download Pre-trained Models

```bash
# Create a dummy audio file
python -c "import numpy as np; import soundfile as sf; sf.write('dummy.wav', np.zeros(44100), 44100)"

# Download models (this will take a few minutes)
spleeter separate -p spleeter:4stems -o output_folder dummy.wav

# You can cancel (Ctrl+C) after models are downloaded
# Models are stored in: ~/.cache/spleeter/ (Linux/macOS) or %USERPROFILE%\.cache\spleeter\ (Windows)

# Clean up
rm dummy.wav
rm -rf output_folder
```

#### Step 4: Configure Spleeter Path in Application

**Method 1: Environment Variable**

```bash
# Find spleeter binary path
conda activate spleeter_env
which spleeter  # macOS/Linux
where spleeter  # Windows

# Set environment variable
# macOS/Linux (add to ~/.bashrc or ~/.zshrc):
export CUE_SPLEETER_PATH="/path/to/spleeter_env/bin/spleeter"

# Windows (System Environment Variables):
# Add CUE_SPLEETER_PATH = C:\path\to\spleeter_env\Scripts\spleeter.exe
```

**Method 2: Application Settings**

1.  Launch the application
2.  Go to Settings/Preferences
3.  Navigate to "Audio Analysis" section
4.  Set "Spleeter Command Path" to the full path of spleeter binary
5.  Click "Test Connection" to verify
6.  Save settings

**Method 3: Hardcode Path (for macOS App Build)**

```bash
# Use the provided script
cd CueManagementSystem/macos_app
chmod +x fix_spleeter_hardcode.sh
./fix_spleeter_hardcode.sh /path/to/spleeter_env/bin/spleeter
```

#### Step 5: Verify Spleeter Installation

```bash
# Activate spleeter environment
conda activate spleeter_env

# Test spleeter
spleeter --help

# Test separation (optional)
spleeter separate -p spleeter:2stems -o test_output your_audio_file.wav
```

### Raspberry Pi Setup

For physical firework control, you'll need to set up a Raspberry Pi.

#### Hardware Setup

1.  **Prepare Raspberry Pi**:
    -   Flash Raspberry Pi OS (32-bit or 64-bit) to SD card
    -   Use Raspberry Pi Imager: [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)
    -   Enable SSH during setup
2.  **Connect Hardware**:
    -   Connect 74HC595 shift register(s) to GPIO pins
    -   Default pin configuration:
        -   Data Pin: GPIO 17
        -   Clock Pin: GPIO 27
        -   Latch Pin: GPIO 22
        -   Enable Pin: GPIO 23
        -   Clear Pin: GPIO 24
        -   Arm Pin: GPIO 25
3.  **Power Supply**:
    -   Use adequate power supply (5V 3A for Pi 4)
    -   Consider separate power for relay board

#### Software Setup

```bash
# 1. SSH into Raspberry Pi
ssh pi@raspberrypi.local
# Default password: raspberry (change this!)

# 2. Update system
sudo apt-get update
sudo apt-get upgrade -y

# 3. Install dependencies
sudo apt-get install -y python3-pip python3-rpi.gpio python3-dev git

# 4. Clone repository (or copy scripts)
git clone https://github.com/mblyman89/CueManagementSystem.git
cd CueManagementSystem/CueManagementSystem/raspberry_pi

# 5. Make scripts executable
chmod +x *.py

# 6. Test GPIO
python3 test_gpio_pins.py

# 7. Configure network (optional)
# For ad-hoc mode setup:
cd ../..
chmod +x setup-network-switching.sh
sudo ./setup-network-switching.sh
```

#### Network Configuration

**Option 1: WiFi Client Mode (Connect to existing network)**

```bash
# On Raspberry Pi
sudo raspi-config
# Navigate to: System Options > Wireless LAN
# Enter SSID and password

# Or use command line:
sudo nmcli device wifi connect "YourSSID" password "YourPassword"
```

**Option 2: Ad-Hoc Mode (Create hotspot)**

```bash
# Use provided scripts
cd CueManagementSystem
sudo ./adhoc-mode.sh

# Default settings:
# SSID: CuePi-Hotspot
# Password: fireworks123
# IP: 10.0.0.1
```

**Switch Between Modes:**

```bash
# Switch to WiFi
sudo ./wifi-mode.sh "YourSSID" "YourPassword"

# Switch to Ad-Hoc
sudo ./adhoc-mode.sh
```

#### Testing Raspberry Pi Connection

From your desktop application:

1.  Launch CueManagementSystem
2.  Click "Mode Selector" button
3.  Select "Remote Hardware" mode
4.  Enter Raspberry Pi details:
    -   Hostname: raspberrypi.local (or IP address)
    -   Username: pi
    -   Password: (your password)
5.  Click "Connect"
6.  Open terminal tab to verify connection
7.  Run test commands:
    
    ```bash
    python3 raspberry_pi/get_gpio_status.py
    ```
    

* * *

## 🔨 Building macOS Application

Create a standalone macOS application bundle that can be distributed without Python installation.

### Prerequisites

1.  **macOS System**: macOS 10.15 or later
2.  **Python Environment**: Python 3.10 or 3.11 with all dependencies installed
3.  **PyInstaller**: Install separately:
    
    ```bash
    pip install pyinstaller>=6.0.0
    ```
    
4.  **Xcode Command Line Tools**:
    
    ```bash
    xcode-select --install
    ```
    

### Step 1: Prepare Environment

```bash
# Activate your main environment
conda activate firework_env

# Ensure all dependencies are installed
pip install -r requirements.txt

# Install PyInstaller
pip install pyinstaller

# Verify PyInstaller
pyinstaller --version
```

### Step 2: Fix Import Issues

The application uses absolute imports that need to be converted to relative imports for PyInstaller:

```bash
cd CueManagementSystem

# Run the import fixer script
python fix_imports.py

# This will:
# - Convert absolute imports to relative imports
# - Create backups of original files
# - Update all Python files in the project
```

### Step 3: Hardcode Spleeter Path

Since Spleeter runs in a separate environment, hardcode the path for the built app:

```bash
cd macos_app

# Find your spleeter path
conda activate spleeter_env
which spleeter
# Example output: /Users/username/.venvs/spleeter_env/bin/spleeter

# Run the hardcode script
chmod +x fix_spleeter_hardcode.sh
./fix_spleeter_hardcode.sh /Users/username/.venvs/spleeter_env/bin/spleeter

# This will:
# - Update spleeter_service.py with hardcoded path
# - Create backup of original file
# - Verify the change
```

### Step 4: Create Application Icon

```bash
# If you have a PNG icon (1024x1024 recommended)
cd macos_app

# Option 1: Using Python script
python create_icns.py /path/to/your/icon.png

# Option 2: Using alternative method
python create_icns_alternative.py /path/to/your/icon.png

# This creates CuePi.iconset directory and CuePi.icns file
```

### Step 5: Build the Application

```bash
cd macos_app

# Make build script executable
chmod +x build_macos_app.sh

# Run the build script
./build_macos_app.sh

# The script will:
# 1. Check prerequisites
# 2. Create .icns icon file
# 3. Clean previous builds
# 4. Run PyInstaller with CuePi.spec
# 5. Verify the build
# 6. Display build location

# Build output will be in: dist/CuePi.app
```

### Step 6: Test the Application

```bash
# Run the built application
open dist/CuePi.app

# Test all features:
# - Launch and welcome screen
# - Create new show
# - Load music file
# - Analyze waveform
# - Use Spleeter (if configured)
# - Save/load shows
# - Preview functionality
```

### Step 7: Create DMG Installer (Optional)

```bash
# Install create-dmg tool
brew install create-dmg

# Run DMG creation script
chmod +x create_dmg.sh
./create_dmg.sh

# This creates: CuePi-Installer.dmg
# Users can drag CuePi.app to Applications folder
```

### Troubleshooting Build Issues

**Issue: PyInstaller fails with import errors**

```bash
# Solution: Check hidden imports in CuePi.spec
# Add missing modules to hiddenimports list

# Example:
hiddenimports=[
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    'librosa',
    'madmom',
    # Add any missing modules here
]
```

**Issue: Application crashes on launch**

```bash
# Solution: Run from terminal to see error messages
cd dist
./CuePi.app/Contents/MacOS/CuePi

# Check for missing dependencies or path issues
```

**Issue: Spleeter not working in built app**

```bash
# Solution: Verify hardcoded path
# Check spleeter_service.py has correct path
# Ensure spleeter environment is accessible

# Test spleeter path:
/path/to/spleeter_env/bin/spleeter --help
```

**Issue: Large application size**

```bash
# Solution: Exclude unnecessary files in CuePi.spec
# Add to excludes list:

excludes=[
    'matplotlib.tests',
    'numpy.tests',
    'scipy.tests',
    'test',
    'tests',
]
```

### Build Configuration (CuePi.spec)

The `CuePi.spec` file controls the build process. Key sections:

```python
# Analysis: Specify entry point and dependencies
a = Analysis(
    ['../CueManagementSystem/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('../CueManagementSystem/resources', 'resources'),
        ('../CueManagementSystem/images', 'images'),
        # Add other data files/folders here
    ],
    hiddenimports=[
        # List all hidden imports
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # List modules to exclude
    ],
)

# EXE: Create executable
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
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='CuePi.icns',  # Application icon
)

# BUNDLE: Create macOS app bundle
app = BUNDLE(
    exe,
    name='CuePi.app',
    icon='CuePi.icns',
    bundle_identifier='com.cuepi.fireworks',
    info_plist={
        'NSPrincipalClass': 'NSApplication',
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '1.0.0',
        # Add other plist entries
    },
)
```

* * *

## 📖 Usage Guide

### Starting the Application

#### From Source

```bash
# 1. Activate your environment
conda activate firework_env  # or: source .venv/bin/activate

# 2. Navigate to application directory
cd CueManagementSystem/CueManagementSystem

# 3. Run the application
python main.py

# Alternative: Run from project root
cd CueManagementSystem
python -m CueManagementSystem.main
```

#### From Built Application (macOS)

```bash
# Double-click CuePi.app in Finder
# Or from terminal:
open /Applications/CuePi.app
```

### First Launch

1.  **Welcome Screen**: On first launch, you'll see the welcome screen with options:
    -   **Design Show**: Create a new show from scratch
    -   **Load Show**: Open an existing show file
    -   **Import Show**: Import show from CSV or other format
2.  **Mode Selection**: Choose your operating mode:
    -   **Simulation Mode**: Test shows without hardware
    -   **Local Hardware**: Control hardware directly connected to this computer
    -   **Remote Hardware**: Control Raspberry Pi via SSH

### Creating Your First Show

#### Method 1: Manual Cue Creation

1.  **Open Main Window**: Click "Design Show" from welcome screen
2.  **Add Music** (Optional but recommended):
    -   Click "Music Manager" button
    -   Click "Import Music"
    -   Select your audio file (WAV, MP3, etc.)
    -   Click "Load" to load the music
3.  **Create Cues Manually**:
    -   Click "Create Cue" button
    -   Fill in cue details:
        -   **Cue Number**: Unique identifier (auto-incremented)
        -   **Cue Type**: Select SHOT, DOUBLE\_SHOT, RUN, or DOUBLE\_RUN
        -   **Execution Time**: When to fire (in seconds)
        -   **Outputs**: Which firework outputs to trigger
        -   **Duration**: How long to hold outputs (for RUN types)
    -   Click "Create" to add cue
4.  **Edit Cues**:
    -   Double-click any cue in the table to edit
    -   Or right-click for context menu options
    -   Drag and drop to reorder cues
5.  **Save Show**:
    -   Click "Show Manager" button
    -   Click "Save Show"
    -   Enter show name and description
    -   Click "Save"

#### Method 2: Automatic Generation from Music

1.  **Load Music**:
    -   Click "Music Manager"
    -   Import and load your audio file
2.  **Analyze Waveform**:
    -   Click "Analyze Waveform" button
    -   Wait for analysis to complete (may take a minute)
    -   Waveform will display with detected beats
3.  **Optional: Use Spleeter for Better Results**:
    -   In waveform analysis dialog, check "Use Spleeter"
    -   Select stem model (4stems recommended)
    -   Click "Separate Audio"
    -   Wait for separation (may take several minutes)
    -   Re-analyze with isolated drum track
4.  **Generate Cues**:
    -   Click "Musical Generator" button
    -   Configure generation parameters:
        -   **Distribution Method**: Random or Sequential
        -   **Peak Type**: All peaks, drum hits only, or specific types
        -   **Time Offset**: Adjust timing relative to beats
        -   **Output Range**: Which outputs to use
    -   Click "Generate"
    -   Review generated cues
    -   Click "Add to Show" to add them
5.  **Fine-Tune**:
    -   Edit individual cues as needed
    -   Adjust timing offsets
    -   Add manual cues for specific moments
6.  **Save Show**:
    -   Save your show for future use

### Music Analysis Deep Dive

#### Waveform Analysis Dialog

**Opening the Dialog**:

-   Click "Analyze Waveform" button in main window
-   Or: Music Manager > Analyze

**Interface Components**:

1.  **Waveform Display**:
    -   Shows audio amplitude over time
    -   Detected beats marked with vertical lines
    -   Color-coded by beat type (kick, snare, etc.)
    -   Zoom controls for detailed view
2.  **Playback Controls**:
    -   Play/Pause button
    -   Timeline scrubber
    -   Volume control
    -   Loop region selection
3.  **Analysis Settings**:
    -   **Detection Method**: Choose algorithm
        -   Librosa: Fast, good for most music
        -   Madmom RNN: Slower, more accurate
        -   Onset Detection: For complex rhythms
    -   **Sensitivity**: Adjust detection threshold
    -   **Minimum Peak Distance**: Avoid duplicate detections
4.  **Spleeter Integration**:
    -   **Use Spleeter**: Enable audio separation
    -   **Stem Model**: Choose separation model
    -   **Analyze Drums Only**: Focus on drum track
    -   **Cache Results**: Save separated stems

**Workflow**:

1.  **Initial Analysis**:
    
    ```
    Load Audio → Analyze → Review Beats
    ```
    
2.  **With Spleeter** (Recommended for complex music):
    
    ```
    Load Audio → Enable Spleeter → Separate → Analyze Drums → Review Beats
    ```
    
3.  **Fine-Tuning**:
    
    ```
    Adjust Sensitivity → Re-analyze → Compare Results → Select Best
    ```
    

#### Beat Detection Methods

**Librosa Beat Tracking**:

-   **Pros**: Fast, works well for most music
-   **Cons**: May miss subtle beats
-   **Best For**: Pop, rock, electronic music with clear beats
-   **Settings**: Adjust hop\_length for precision

**Madmom RNN**:

-   **Pros**: Most accurate, handles complex rhythms
-   **Cons**: Slower processing
-   **Best For**: Jazz, classical, complex percussion
-   **Settings**: Adjust threshold for sensitivity

**Onset Detection**:

-   **Pros**: Detects all transients, not just beats
-   **Cons**: May detect too many events
-   **Best For**: Detailed synchronization, drum fills
-   **Settings**: Multiple onset functions available

#### Spleeter Stem Separation

**When to Use Spleeter**:

-   Music with vocals that interfere with beat detection
-   Complex arrangements with multiple instruments
-   When you need to focus on specific instruments
-   For professional-quality synchronization

**Stem Models**:

1.  **2stems** (vocals/accompaniment):
    -   Fastest processing
    -   Good for removing vocals
    -   Use when vocals are the main issue
2.  **4stems** (vocals/drums/bass/other):
    -   **Recommended for most cases**
    -   Isolates drums for beat detection
    -   Balanced speed and quality
3.  **5stems** (vocals/drums/bass/piano/other):
    -   Most detailed separation
    -   Slowest processing
    -   Use for complex classical or jazz

**Processing Time**:

-   2stems: ~30 seconds per minute of audio
-   4stems: ~45 seconds per minute of audio
-   5stems: ~60 seconds per minute of audio
-   (Times vary based on hardware)

**Caching**:

-   Separated stems are cached automatically
-   Cache location: `~/.cache/cuepi/spleeter/`
-   Reusing same audio file uses cached stems
-   Clear cache if you want to re-separate

### Musical Generator

The Musical Generator creates firework cues based on detected beats.

**Opening the Generator**:

-   After waveform analysis, click "Musical Generator"
-   Or: Main Window > Tools > Musical Generator

**Configuration Options**:

1.  **Distribution Method**:
    -   **Random**: Randomly assign outputs to beats
    -   **Sequential**: Use outputs in order
    -   **Grouped**: Group similar beats together
    -   **Custom Pattern**: Define your own pattern
2.  **Peak Selection**:
    -   **All Peaks**: Use every detected beat
    -   **Drum Hits Only**: Filter for drum sounds
    -   **Kick Drums**: Only bass drum hits
    -   **Snare Drums**: Only snare hits
    -   **Hi-Hats**: Only hi-hat hits
    -   **Custom Filter**: Define your own criteria
3.  **Timing Adjustment**:
    -   **Time Offset**: Shift all cues by fixed amount
    -   **Random Offset**: Add random variation
    -   **Quantize**: Snap to musical grid
    -   **Swing**: Add swing feel
4.  **Output Configuration**:
    -   **Output Range**: Which outputs to use (e.g., 1-32)
    -   **Cue Type**: SHOT, DOUBLE\_SHOT, RUN, DOUBLE\_RUN
    -   **Duration**: For RUN types, how long to hold
    -   **Exclude Outputs**: Skip specific outputs
5.  **Advanced Options**:
    -   **Intensity Mapping**: Map beat strength to output selection
    -   **Frequency Filtering**: Use only beats in certain frequency range
    -   **Minimum Spacing**: Ensure minimum time between cues
    -   **Maximum Cues**: Limit total number of generated cues

**Generation Process**:

1.  **Configure Settings**: Set all parameters as desired
2.  **Preview**: Click "Preview" to see what will be generated
3.  **Adjust**: Modify settings based on preview
4.  **Generate**: Click "Generate" to create cues
5.  **Review**: Check generated cues in preview table
6.  **Add to Show**: Click "Add to Show" to add them to your show

**Tips for Best Results**:

-   Start with "All Peaks" to see all detected beats
-   Filter to specific drum types for focused effects
-   Use Sequential distribution for predictable patterns
-   Use Random distribution for varied, exciting shows
-   Add time offset to compensate for ignition delay
-   Use intensity mapping for dynamic shows

### Show Preview

Before executing a show, preview it to verify timing and effects.

**Starting Preview**:

-   Click "Preview" button in main window
-   Or: Show > Preview Show

**Preview Interface**:

1.  **Timeline**:
    -   Shows entire show duration
    -   Cue markers indicate when cues fire
    -   Playhead shows current position
    -   Click timeline to jump to position
2.  **LED Panel**:
    -   Visual representation of outputs
    -   LEDs light up when outputs fire
    -   Color-coded by cue type
    -   Grouped or traditional view
3.  **Playback Controls**:
    -   Play/Pause
    -   Stop
    -   Speed control (0.5x to 2x)
    -   Loop mode
4.  **Music Synchronization**:
    -   If music is loaded, plays in sync
    -   Waveform display shows current position
    -   Volume control

**Preview Modes**:

1.  **Real-Time Preview**:
    -   Plays at actual speed
    -   Shows exact timing
    -   Use for final verification
2.  **Slow Motion**:
    -   Play at 0.5x or 0.25x speed
    -   Easier to see individual cues
    -   Good for detailed review
3.  **Fast Forward**:
    -   Play at 1.5x or 2x speed
    -   Quick overview of show
    -   Good for long shows

**Scrubbing**:

-   Drag playhead to any position
-   LEDs update instantly
-   Music follows playhead
-   Use for checking specific moments

### Show Execution

Execute your show on real hardware.

**Pre-Execution Checklist**:

1.  **Hardware Connection**:
    -   Verify Raspberry Pi is connected
    -   Check SSH connection status
    -   Ensure network is stable
2.  **Safety Checks**:
    -   Verify all personnel are at safe distance
    -   Check weather conditions
    -   Ensure fire safety equipment is available
    -   Verify emergency stop is accessible
3.  **System Checks**:
    -   Run pre-show checklist dialog
    -   Verify all outputs are functional
    -   Test arm/disarm system
    -   Check output enable status
4.  **Show Verification**:
    -   Preview show one final time
    -   Verify music is loaded (if using)
    -   Check cue count and timing
    -   Verify output assignments

**Execution Process**:

1.  **Arm System**:
    -   Click "Arm System" button
    -   Physical arm switch must be enabled
    -   Status indicator turns green
2.  **Enable Outputs**:
    -   Click "Enable Outputs" button
    -   Verify LED panel shows enabled state
    -   Check hardware status
3.  **Start Execution**:
    -   Click "Execute All" button
    -   Confirm execution in dialog
    -   Show begins immediately
4.  **Monitor Progress**:
    -   Watch LED panel for output status
    -   Monitor timeline progress
    -   Check connection status
    -   Be ready for emergency stop
5.  **Emergency Stop** (if needed):
    -   Click "Emergency Stop" button
    -   Or press hardware emergency stop
    -   All outputs immediately disabled
    -   System enters safe state
6.  **Post-Execution**:
    -   Wait for all cues to complete
    -   Disarm system
    -   Disable outputs
    -   Verify all outputs are off
    -   Disconnect from hardware

**Execution Modes**:

1.  **Execute All**:
    -   Runs entire show from start to finish
    -   Cannot be paused
    -   Use for final performance
2.  **Execute Selected**:
    -   Run only selected cues
    -   Good for testing specific sequences
    -   Can be paused/resumed
3.  **Step Through**:
    -   Execute one cue at a time
    -   Manual advancement
    -   Good for testing and troubleshooting

**Pause/Resume**:

-   Click "Pause" during execution
-   Show pauses at current position
-   Click "Resume" to continue
-   Music pauses/resumes in sync

### Saving and Loading Shows

**Save Show**:

1.  Click "Show Manager" button
2.  Click "Save Show"
3.  Enter show details:
    -   Name
    -   Description
    -   Tags (optional)
4.  Choose save location
5.  Click "Save"

**File Format**: JSON **File Extension**: `.cueshow` **File Contents**:

-   Cue list with all parameters
-   Music file reference
-   Show metadata
-   Configuration settings

**Load Show**:

1.  From welcome screen: Click "Load Show"
2.  Or from main window: Show Manager > Load Show
3.  Browse to show file
4.  Click "Open"
5.  Show loads into main window

**Import Show**:

-   Supports CSV format
-   Click "Import Show" from Show Manager
-   Select CSV file
-   Map columns to cue parameters
-   Click "Import"

**Export Show**:

-   Click "Export Show" from Show Manager
-   Choose format (CSV, JSON)
-   Select export location
-   Click "Export"

* * *

## 🚀 Advanced Features

### Custom Waveform Rendering

The application supports multiple waveform rendering modes for different visualization needs.

**Rendering Modes**:

1.  **Traditional Amplitude**:
    -   Standard waveform view
    -   Shows amplitude over time
    -   Fast rendering
    -   Good for general use
2.  **RMS Envelope**:
    -   Shows energy envelope
    -   Smoother than amplitude
    -   Better for beat visualization
    -   Recommended for music analysis
3.  **Spectral Color**:
    -   Color-coded by frequency content
    -   Blue = low frequencies
    -   Red = high frequencies
    -   Great for understanding music structure
4.  **Dual Layer**:
    -   Combines amplitude and RMS
    -   Shows both detail and energy
    -   Professional visualization
    -   Best for detailed analysis
5.  **Frequency Bands**:
    -   Separates into frequency ranges
    -   Bass, mids, treble visualization
    -   Good for EQ analysis
    -   Useful for complex music

**Color Schemes**:

-   Classic (blue/white)
-   Professional (gradient)
-   High Contrast (black/white)
-   Colorful (rainbow)
-   Custom (define your own)

**Configuring Rendering**:

1.  Open Waveform Analysis dialog
2.  Click "Rendering Settings"
3.  Select rendering mode
4.  Choose color scheme
5.  Adjust parameters
6.  Click "Apply"

### Performance Optimization

**For Large Audio Files**:

1.  **Reduce Sample Rate**:
    
    ```python
    # In waveform analyzer settings
    target_sr = 22050  # Instead of 44100
    ```
    
2.  **Use Caching**:
    -   Enable waveform caching
    -   Cache location: `~/.cache/cuepi/waveforms/`
    -   Reusing same file loads instantly
3.  **Limit Analysis Range**:
    -   Analyze only needed portion
    -   Set start/end time in analyzer
    -   Faster processing
4.  **Disable Real-Time Preview**:
    -   Turn off live waveform updates
    -   Render only when needed
    -   Improves responsiveness

**For Spleeter**:

1.  **Use GPU Acceleration**:
    -   Apple Silicon: Automatic with tensorflow-metal
    -   NVIDIA: Install CUDA-enabled TensorFlow
    -   Significant speedup (5-10x)
2.  **Cache Separated Stems**:
    -   Always enabled by default
    -   Reusing same audio is instant
    -   Clear cache if storage is limited
3.  **Use Lower Stem Count**:
    -   2stems is fastest
    -   4stems is good balance
    -   5stems only if needed

**For Show Execution**:

1.  **Optimize Cue Count**:
    -   Combine nearby cues if possible
    -   Remove redundant cues
    -   Fewer cues = more reliable timing
2.  **Use Wired Connection**:
    -   Ethernet preferred over WiFi
    -   More reliable for critical timing
    -   Lower latency
3.  **Minimize Background Processes**:
    -   Close unnecessary applications
    -   Disable system updates during show
    -   Dedicate system resources

### Database Management

Shows are stored in SQLite database for fast access.

**Database Location**:

-   macOS: `~/Library/Application Support/CuePi/shows.db`
-   Linux: `~/.local/share/CuePi/shows.db`
-   Windows: `%APPDATA%\CuePi\shows.db`

**Database Operations**:

1.  **Backup Database**:
    
    ```bash
    # Copy database file
    cp ~/Library/Application\ Support/CuePi/shows.db ~/Desktop/shows_backup.db
    ```
    
2.  **Restore Database**:
    
    ```bash
    # Replace with backup
    cp ~/Desktop/shows_backup.db ~/Library/Application\ Support/CuePi/shows.db
    ```
    
3.  **Export All Shows**:
    -   Show Manager > Export All
    -   Creates individual JSON files
    -   Good for version control
4.  **Import Multiple Shows**:
    -   Show Manager > Import Multiple
    -   Select folder with show files
    -   Batch import

**Database Maintenance**:

-   Automatic vacuum on startup
-   Automatic backup before major operations
-   Corruption detection and repair

### SSH Terminal Integration

Built-in SSH terminal for Raspberry Pi management.

**Opening Terminal**:

-   Mode Selector > Terminal tab
-   Or: Tools > SSH Terminal

**Features**:

-   Full terminal emulation
-   Command history
-   Tab completion
-   File transfer (SCP)
-   Multiple sessions

**Common Commands**:

```bash
# Check GPIO status
python3 raspberry_pi/get_gpio_status.py

# Test single output
python3 raspberry_pi/execute_cue.py '{"type":"SHOT","outputs":[1]}'

# Emergency stop
python3 raspberry_pi/emergency_stop.py

# Check system status
uptime
free -h
df -h

# View logs
tail -f /var/log/syslog

# Network status
python3 raspberry_pi/get_network_status.py
```

**File Transfer**:

1.  Click "Upload File" button
2.  Select local file
3.  Choose remote destination
4.  Click "Upload"

**Session Management**:

-   Sessions persist across disconnects
-   Automatic reconnection
-   Command history saved
-   Multiple concurrent sessions

### Custom Cue Types

Create custom cue types for special effects.

**Defining Custom Types**:

1.  Edit `show_enums.py`:
    
    ```python
    class CueType(Enum):
        SHOT = "SHOT"
        DOUBLE_SHOT = "DOUBLE_SHOT"
        RUN = "RUN"
        DOUBLE_RUN = "DOUBLE_RUN"
        CUSTOM_EFFECT = "CUSTOM_EFFECT"  # Add your type
    ```
    
2.  Implement execution logic in `execute_cue.py`:
    
    ```python
    elif cue_type == "CUSTOM_EFFECT":
        # Your custom logic here
        pass
    ```
    
3.  Update UI in `cue_creator_dialog.py`:
    
    ```python
    self.cue_type_combo.addItem("Custom Effect", "CUSTOM_EFFECT")
    ```
    

**Example Custom Types**:

-   Strobe effect
-   Chase sequence
-   Random pattern
-   Fade in/out
-   Synchronized groups

* * *

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Application Won't Start

**Symptom**: Application crashes immediately or shows error on launch

**Solutions**:

1.  **Check Python Version**:
    
    ```bash
    python --version
    # Should be 3.8 or higher
    ```
    
2.  **Verify Dependencies**:
    
    ```bash
    pip list | grep -E "PySide6|librosa|numpy"
    # All should be installed
    ```
    
3.  **Check for Conflicting Packages**:
    
    ```bash
    # Uninstall conflicting Qt packages
    pip uninstall PyQt5 PyQt6
    pip install --force-reinstall PySide6
    ```
    
4.  **Run with Debug Output**:
    
    ```bash
    python main.py --debug
    # Check error messages
    ```
    
5.  **Clear Cache**:
    
    ```bash
    # Remove cache files
    rm -rf ~/.cache/cuepi/
    rm -rf __pycache__
    find . -name "*.pyc" -delete
    ```
    

#### Audio Analysis Fails

**Symptom**: Waveform analysis crashes or produces no results

**Solutions**:

1.  **Check Audio File Format**:
    -   Convert to WAV if possible
    -   Ensure file is not corrupted
    -   Try with different audio file
2.  **Verify Librosa Installation**:
    
    ```bash
    python -c "import librosa; print(librosa.__version__)"
    ```
    
3.  **Check FFmpeg**:
    
    ```bash
    ffmpeg -version
    # Should show version info
    
    # If not installed:
    # macOS: brew install ffmpeg
    # Ubuntu: sudo apt-get install ffmpeg
    ```
    
4.  **Reduce File Size**:
    -   Large files may cause memory issues
    -   Try with shorter audio clip first
    -   Increase system RAM if possible
5.  **Check NumPy Version**:
    
    ```bash
    python -c "import numpy; print(numpy.__version__)"
    # Should be < 2.0 for madmom compatibility
    
    # If needed:
    pip install "numpy<2.0"
    ```
    

#### Spleeter Not Working

**Symptom**: Spleeter separation fails or command not found

**Solutions**:

1.  **Verify Spleeter Installation**:
    
    ```bash
    conda activate spleeter_env
    spleeter --help
    # Should show help text
    ```
    
2.  **Check TensorFlow**:
    
    ```bash
    python -c "import tensorflow as tf; print(tf.__version__)"
    # Should show version 2.5.x
    ```
    
3.  **Apple Silicon Issues**:
    
    ```bash
    # Ensure using arm64 environment
    conda activate spleeter_env
    python -c "import platform; print(platform.machine())"
    # Should show "arm64"
    
    # Reinstall with correct packages
    pip uninstall tensorflow spleeter
    pip install tensorflow-macos tensorflow-metal spleeter
    ```
    
4.  **Path Configuration**:
    -   Verify CUE\_SPLEETER\_PATH is set correctly
    -   Check path in application settings
    -   Use absolute path, not relative
5.  **Model Download Issues**:
    
    ```bash
    # Manually download models
    cd ~/.cache/spleeter/
    # Check if pretrained_models directory exists
    # If not, run:
    spleeter separate -p spleeter:4stems -o /tmp dummy.wav
    ```
    

#### Raspberry Pi Connection Issues

**Symptom**: Cannot connect to Raspberry Pi or connection drops

**Solutions**:

1.  **Verify Network Connection**:
    
    ```bash
    # Ping Raspberry Pi
    ping raspberrypi.local
    # Or use IP address
    ping 192.168.1.100
    ```
    
2.  **Check SSH Service**:
    
    ```bash
    # On Raspberry Pi
    sudo systemctl status ssh
    # Should show "active (running)"
    
    # If not:
    sudo systemctl start ssh
    sudo systemctl enable ssh
    ```
    
3.  **Verify Credentials**:
    -   Default username: pi
    -   Default password: raspberry (should be changed!)
    -   Check if password was changed
4.  **Check Firewall**:
    
    ```bash
    # On Raspberry Pi
    sudo ufw status
    # If active, allow SSH:
    sudo ufw allow ssh
    ```
    
5.  **Network Mode Issues**:
    
    ```bash
    # Check current mode
    python3 raspberry_pi/get_network_status.py
    
    # Switch modes if needed
    sudo ./wifi-mode.sh "SSID" "password"
    # Or
    sudo ./adhoc-mode.sh
    ```
    
6.  **SSH Key Issues**:
    
    ```bash
    # Remove old key
    ssh-keygen -R raspberrypi.local
    
    # Try connecting manually
    ssh pi@raspberrypi.local
    ```
    

#### GPIO Control Not Working

**Symptom**: Outputs don't fire or GPIO errors

**Solutions**:

1.  **Check GPIO Permissions**:
    
    ```bash
    # On Raspberry Pi
    sudo usermod -a -G gpio pi
    # Logout and login again
    ```
    
2.  **Verify Pin Configuration**:
    
    ```bash
    # Check current GPIO status
    python3 raspberry_pi/get_gpio_status.py
    ```
    
3.  **Test Individual Pins**:
    
    ```bash
    # Test GPIO functionality
    python3 raspberry_pi/test_gpio_pins.py
    ```
    
4.  **Check Wiring**:
    -   Verify shift register connections
    -   Check power supply
    -   Verify ground connections
    -   Check for loose wires
5.  **Library Conflicts**:
    
    ```bash
    # Ensure only one GPIO library is active
    pip list | grep -i gpio
    
    # If multiple, uninstall extras:
    pip uninstall gpiozero lgpio
    # Keep only RPi.GPIO
    ```
    

#### Performance Issues

**Symptom**: Application is slow or unresponsive

**Solutions**:

1.  **Check System Resources**:
    
    ```bash
    # Monitor CPU and memory
    top
    # Or
    htop
    ```
    
2.  **Close Background Applications**:
    -   Close unnecessary programs
    -   Disable system updates
    -   Free up RAM
3.  **Optimize Audio Files**:
    -   Convert to WAV format
    -   Reduce sample rate to 44.1kHz
    -   Trim unnecessary silence
4.  **Disable Real-Time Features**:
    -   Turn off live waveform updates
    -   Disable auto-save
    -   Reduce preview quality
5.  **Clear Cache**:
    
    ```bash
    # Remove old cache files
    rm -rf ~/.cache/cuepi/
    ```
    
6.  **Upgrade Hardware**:
    -   Add more RAM (16GB recommended)
    -   Use SSD instead of HDD
    -   Upgrade to faster CPU

#### macOS App Build Issues

**Symptom**: PyInstaller build fails or app won't run

**Solutions**:

1.  **Check PyInstaller Version**:
    
    ```bash
    pyinstaller --version
    # Should be 6.0.0 or higher
    
    pip install --upgrade pyinstaller
    ```
    
2.  **Fix Import Errors**:
    
    ```bash
    # Run import fixer
    python fix_imports.py
    
    # Check for remaining absolute imports
    grep -r "from CueManagementSystem" .
    ```
    
3.  **Add Hidden Imports**:
    -   Edit CuePi.spec
    -   Add missing modules to hiddenimports list
    -   Rebuild
4.  **Check Code Signing** (macOS):
    
    ```bash
    # Sign the app
    codesign --force --deep --sign - dist/CuePi.app
    
    # Verify signature
    codesign --verify --verbose dist/CuePi.app
    ```
    
5.  **Test from Terminal**:
    
    ```bash
    # Run built app from terminal to see errors
    ./dist/CuePi.app/Contents/MacOS/CuePi
    ```
    

### Error Messages

#### "ModuleNotFoundError: No module named 'X'"

**Cause**: Missing dependency

**Solution**:

```bash
pip install X
# Or reinstall all dependencies:
pip install -r requirements.txt
```

#### "ImportError: DLL load failed" (Windows)

**Cause**: Missing Visual C++ Redistributable

**Solution**:

-   Download and install Visual C++ Redistributable
-   From: [https://aka.ms/vs/17/release/vc\_redist.x64.exe](https://aka.ms/vs/17/release/vc_redist.x64.exe)

#### "OSError: \[Errno 48\] Address already in use"

**Cause**: Port already in use (usually for SSH or audio)

**Solution**:

```bash
# Find process using port
lsof -i :22  # For SSH
# Or
netstat -an | grep LISTEN

# Kill process if needed
kill -9 <PID>
```

#### "PermissionError: \[Errno 13\] Permission denied"

**Cause**: Insufficient permissions

**Solution**:

```bash
# For GPIO on Raspberry Pi:
sudo usermod -a -G gpio $USER

# For file access:
chmod +x script.py

# For directory access:
chmod -R 755 directory/
```

#### "RuntimeError: Failed to initialize libgpiod"

**Cause**: GPIO library initialization failed

**Solution**:

```bash
# On Raspberry Pi
sudo apt-get update
sudo apt-get install --reinstall python3-rpi.gpio

# Or use lgpio instead:
pip install lgpio
```

### Getting Help

If you encounter issues not covered here:

1.  **Check Logs**:
    
    ```bash
    # Application logs location:
    # macOS: ~/Library/Logs/CuePi/
    # Linux: ~/.local/share/CuePi/logs/
    # Windows: %APPDATA%\CuePi\logs\
    
    tail -f ~/Library/Logs/CuePi/cuepi.log
    ```
    
2.  **Enable Debug Mode**:
    
    ```bash
    python main.py --debug --verbose
    ```
    
3.  **Check GitHub Issues**:
    -   Visit: [https://github.com/mblyman89/CueManagementSystem/issues](https://github.com/mblyman89/CueManagementSystem/issues)
    -   Search for similar issues
    -   Create new issue if needed
4.  **Contact Developer**:
    -   Include error messages
    -   Include system information
    -   Include steps to reproduce
    -   Include log files

* * *

## 💡 Tips & Tricks

### Workflow Optimization

#### Keyboard Shortcuts

| Action | Shortcut | Description |
| --- | --- | --- |
| **File Operations** |   
 |   
 |
| New Show | `Cmd+N` (Mac) / `Ctrl+N` (Win) | Create new show |
| Open Show | `Cmd+O` / `Ctrl+O` | Open existing show |
| Save Show | `Cmd+S` / `Ctrl+S` | Save current show |
| Save As | `Cmd+Shift+S` / `Ctrl+Shift+S` | Save with new name |
| **Cue Operations** |   
 |   
 |
| Create Cue | `Cmd+K` / `Ctrl+K` | Open cue creator |
| Edit Cue | `Cmd+E` / `Ctrl+E` | Edit selected cue |
| Delete Cue | `Delete` / `Backspace` | Delete selected cue(s) |
| Duplicate Cue | `Cmd+D` / `Ctrl+D` | Duplicate selected cue |
| **Playback** |   
 |   
 |
| Play/Pause | `Space` | Toggle playback |
| Stop | `Cmd+.` / `Ctrl+.` | Stop playback |
| Preview | `Cmd+P` / `Ctrl+P` | Start preview mode |
| **View** |   
 |   
 |
| Zoom In | `Cmd++` / `Ctrl++` | Zoom in waveform |
| Zoom Out | `Cmd+-` / `Ctrl+-` | Zoom out waveform |
| Fit to Window | `Cmd+0` / `Ctrl+0` | Fit waveform to window |
| **Other** |   
 |   
 |
| Preferences | `Cmd+,` / `Ctrl+,` | Open preferences |
| Help | `F1` | Open help |
| Quit | `Cmd+Q` / `Ctrl+Q` | Quit application |

#### Quick Actions

1.  **Rapid Cue Creation**:
    -   Use Musical Generator for bulk creation
    -   Duplicate and modify existing cues
    -   Use templates for common patterns
2.  **Efficient Editing**:
    -   Multi-select cues (Shift+Click or Cmd+Click)
    -   Bulk edit selected cues
    -   Use find/replace for output numbers
3.  **Fast Navigation**:
    -   Click timeline to jump to position
    -   Use keyboard shortcuts for zoom
    -   Bookmark important positions

### Best Practices

#### Show Design

1.  **Start with Music**:
    -   Always load music first
    -   Analyze before creating cues
    -   Use Spleeter for complex music
2.  **Build Gradually**:
    -   Start with major beats
    -   Add details progressively
    -   Test frequently
3.  **Use Sections**:
    -   Divide show into acts/sections
    -   Different intensity for each section
    -   Build to climax
4.  **Timing Considerations**:
    -   Account for ignition delay (typically 50-100ms)
    -   Add time offset in Musical Generator
    -   Test timing with preview
5.  **Output Management**:
    -   Group similar effects together
    -   Reserve special outputs for climax
    -   Balance output usage

#### Music Analysis

1.  **Choose Right Method**:
    -   Librosa for simple music
    -   Madmom for complex rhythms
    -   Spleeter for vocal-heavy tracks
2.  **Optimize Settings**:
    -   Adjust sensitivity based on music
    -   Use appropriate peak distance
    -   Filter by beat type
3.  **Verify Results**:
    -   Always preview detected beats
    -   Listen while viewing waveform
    -   Adjust and re-analyze if needed
4.  **Use Spleeter Wisely**:
    -   Only when needed (vocals interfere)
    -   4stems is usually sufficient
    -   Cache results for reuse

#### Hardware Safety

1.  **Pre-Show Checklist**:
    -   Always run pre-show checklist
    -   Verify all safety systems
    -   Test emergency stop
2.  **Connection Reliability**:
    -   Use wired connection when possible
    -   Test connection before show
    -   Have backup plan
3.  **Monitoring**:
    -   Watch connection status during show
    -   Monitor output states
    -   Be ready for emergency stop
4.  **Post-Show**:
    -   Disarm system immediately
    -   Verify all outputs are off
    -   Disconnect safely

### Advanced Techniques

#### Custom Beat Detection

Create custom beat detection for specific music styles:

```python
# In waveform_analyzer.py, add custom method:

def detect_custom_beats(self, audio, sr):
    """Custom beat detection for specific music style"""
    # Your custom algorithm here
    # Example: Focus on specific frequency range
    
    # High-pass filter for hi-hats
    from scipy.signal import butter, filtfilt
    b, a = butter(4, 8000, btype='high', fs=sr)
    filtered = filtfilt(b, a, audio)
    
    # Detect peaks in filtered signal
    peaks = self.detect_peaks(filtered, threshold=0.3)
    
    return peaks
```

#### Batch Processing

Process multiple shows at once:

```python
# batch_process.py

import os
import json
from pathlib import Path

def batch_analyze_shows(show_directory):
    """Analyze all shows in directory"""
    for show_file in Path(show_directory).glob("*.cueshow"):
        with open(show_file) as f:
            show_data = json.load(f)
        
        # Analyze show
        print(f"Analyzing: {show_file.name}")
        # Your analysis code here
        
        # Save results
        results_file = show_file.with_suffix('.analysis.json')
        # Save analysis results

if __name__ == '__main__':
    batch_analyze_shows('/path/to/shows/')
```

#### Custom Visualizations

Create custom waveform visualizations:

```python
# In enhanced_waveform_renderer.py

def render_custom_visualization(self, audio, sr):
    """Custom visualization method"""
    import matplotlib.pyplot as plt
    
    # Your custom visualization
    # Example: Spectrogram with beat markers
    
    plt.figure(figsize=(12, 4))
    plt.specgram(audio, Fs=sr, cmap='viridis')
    
    # Add beat markers
    for beat_time in self.beat_times:
        plt.axvline(beat_time, color='red', alpha=0.5)
    
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.title('Custom Visualization')
    plt.tight_layout()
    
    return plt.gcf()
```

#### Automated Show Generation

Generate shows automatically based on rules:

```python
# auto_generate.py

def generate_show_from_rules(music_file, rules):
    """
    Generate show based on rule set
    
    Rules example:
    {
        'intro': {'duration': 30, 'intensity': 'low', 'outputs': [1-10]},
        'build': {'duration': 60, 'intensity': 'medium', 'outputs': [11-20]},
        'climax': {'duration': 30, 'intensity': 'high', 'outputs': [21-32]},
        'outro': {'duration': 20, 'intensity': 'low', 'outputs': [1-10]}
    }
    """
    # Analyze music
    beats = analyze_music(music_file)
    
    # Apply rules to generate cues
    cues = []
    current_time = 0
    
    for section, params in rules.items():
        section_beats = [b for b in beats 
                        if current_time <= b < current_time + params['duration']]
        
        # Generate cues for this section
        section_cues = generate_section_cues(
            section_beats,
            params['intensity'],
            params['outputs']
        )
        
        cues.extend(section_cues)
        current_time += params['duration']
    
    return cues
```

### Performance Tips

1.  **Audio File Optimization**:
    -   Use WAV format for best compatibility
    -   44.1kHz sample rate is sufficient
    -   Mono files process faster than stereo
    -   Trim silence from beginning/end
2.  **Memory Management**:
    -   Close unused shows
    -   Clear cache periodically
    -   Limit waveform zoom level
    -   Use preview mode sparingly
3.  **Network Optimization**:
    -   Use wired Ethernet when possible
    -   Minimize network traffic during show
    -   Close other network applications
    -   Use static IP for Raspberry Pi
4.  **Raspberry Pi Optimization**:
    -   Use Raspberry Pi 4 for best performance
    -   Overclock if needed (carefully!)
    -   Use quality SD card (Class 10 or better)
    -   Minimize background processes

### Troubleshooting Tips

1.  **When Analysis Fails**:
    -   Try different detection method
    -   Adjust sensitivity settings
    -   Use shorter audio clip for testing
    -   Check audio file integrity
2.  **When Timing is Off**:
    -   Measure actual ignition delay
    -   Add appropriate time offset
    -   Test with single cue first
    -   Adjust globally if needed
3.  **When Connection Drops**:
    -   Check network stability
    -   Use wired connection
    -   Reduce network traffic
    -   Enable watchdog timer
4.  **When Outputs Don't Fire**:
    -   Verify arm status
    -   Check output enable
    -   Test individual outputs
    -   Verify wiring

* * *

## 📁 Project Structure

### Directory Layout

```
CueManagementSystem/
│
├── CueManagementSystem/              # Main application package
│   │
│   ├── main.py                       # Application entry point
│   │   └── Initializes Qt application and event loop
│   │
│   ├── controllers/                  # Business logic layer
│   │   ├── __init__.py
│   │   ├── cue_controller.py         # Cue CRUD operations
│   │   ├── system_mode_controller.py # System mode management
│   │   ├── hardware_controller.py    # Hardware communication
│   │   ├── show_execution_manager.py # Show execution logic
│   │   ├── show_preview_controller.py # Preview management
│   │   ├── waveform_controller.py    # Waveform control logic
│   │   └── preview_state_manager.py  # Preview state sync
│   │
│   ├── models/                       # Data models layer
│   │   ├── __init__.py
│   │   ├── cue_model.py             # Cue data structure
│   │   ├── database_model.py        # Database interface
│   │   └── show_enums.py            # Enumerations
│   │
│   ├── views/                        # User interface layer
│   │   ├── __init__.py
│   │   ├── main_window.py           # Main application window
│   │   ├── welcome_page.py          # Welcome/splash screen
│   │   │
│   │   ├── # Dialogs
│   │   ├── cue_creator_dialog.py    # Create new cue
│   │   ├── cue_editor_dialog.py     # Edit existing cue
│   │   ├── mode_selector_dialog.py  # System mode selection
│   │   ├── music_file_dialog.py     # Music file management
│   │   ├── music_selection_dialog.py # Music selection
│   │   ├── music_analysis_dialog.py  # Music analysis interface
│   │   ├── waveform_analysis_dialog.py # Waveform analysis
│   │   ├── generate_show_dialog.py   # Show generation
│   │   ├── musical_generator.py      # Musical cue generator
│   │   ├── pre_show_checklist_dialog.py # Safety checklist
│   │   ├── led_selector_dialog.py    # LED view selector
│   │   │
│   │   ├── # Widgets
│   │   ├── cue_table.py             # Cue table view
│   │   ├── cue_table_widget.py      # Custom table widget
│   │   ├── led_grid.py              # Traditional LED grid
│   │   ├── led_grid_grouped.py      # Grouped LED grid
│   │   ├── led_widget.py            # Individual LED widget
│   │   ├── led_panel_manager.py     # LED panel management
│   │   ├── button_bar.py            # Action button bar
│   │   ├── button_widget.py         # Custom button widget
│   │   ├── waveform_widget.py       # Waveform display
│   │   ├── preview_timeline_widget.py # Preview timeline
│   │   ├── connection_status_widget.py # Connection status
│   │   ├── watchdog_status_widget_manager.py # Watchdog status
│   │   ├── custom_corner_widget.py  # Custom UI element
│   │   │
│   │   └── # Animations
│   │       ├── led_animations.py     # LED animation controller
│   │       ├── preview_led_animations.py # Preview animations
│   │       └── enhanced_drag_drop.py # Drag-drop manager
│   │
│   ├── utils/                        # Utility modules
│   │   ├── __init__.py
│   │   ├── json_utils.py            # JSON serialization
│   │   ├── spleeter_service.py      # Spleeter integration
│   │   ├── waveform_analyzer.py     # Audio analysis
│   │   ├── enhanced_waveform_renderer.py # Waveform rendering
│   │   ├── visual_validator.py      # Analysis validation
│   │   ├── music_manager.py         # Music file management
│   │   ├── show_manager.py          # Show file management
│   │   ├── show_generator.py        # Random show generation
│   │   ├── shift_register_formatter_manager.py # SR formatting
│   │   ├── gpio_controller.py       # GPIO control logic
│   │   ├── performance_monitor.py   # Performance tracking
│   │   ├── terminal_session_manager.py # SSH session management
│   │   ├── terminal_worker_manager.py # SSH workers
│   │   ├── terminal_commands_manager.py # Terminal commands
│   │   ├── file_editor_manager.py   # File editing
│   │   ├── watchdog_timer_manager.py # Connection watchdog
│   │   └── upload_scripts.py        # Script upload utility
│   │
│   ├── raspberry_pi/                 # Raspberry Pi scripts
│   │   ├── __init__.py
│   │   ├── execute_cue.py           # Execute single cue
│   │   ├── execute_show.py          # Execute full show
│   │   ├── toggle_outputs.py        # Enable/disable outputs
│   │   ├── emergency_stop.py        # Emergency shutdown
│   │   ├── set_arm_state.py         # Arm/disarm system
│   │   ├── get_gpio_status.py       # Query GPIO status
│   │   ├── get_network_status.py    # Query network status
│   │   ├── switch_wifi_mode.py      # Switch network mode
│   │   ├── test_gpio_pins.py        # GPIO testing
│   │   ├── shift_register_test.py   # Shift register testing
│   │   ├── adhoc-mode.sh            # Ad-hoc mode script
│   │   ├── wifi-mode.sh             # WiFi mode script
│   │   └── setup-network-switching.sh # Network setup
│   │
│   ├── macos_app/                    # macOS app building
│   │   ├── build_macos_app.sh       # Main build script
│   │   ├── fix_spleeter_hardcode.sh # Spleeter path fix
│   │   ├── create_dmg.sh            # DMG installer creation
│   │   ├── CuePi.spec               # PyInstaller spec file
│   │   ├── create_icns.py           # Icon creation
│   │   ├── create_icns_alternative.py # Alternative icon method
│   │   ├── fix_imports.py           # Import path fixer
│   │   ├── build_config.py          # Build configuration
│   │   └── clean_pyc.sh             # Clean Python cache
│   │
│   ├── config/                       # Configuration files
│   │   ├── settings.json            # Application settings
│   │   ├── gpio_config.json         # GPIO configuration
│   │   └── network_config.json      # Network configuration
│   │
│   ├── resources/                    # Application resources
│   │   ├── styles/                  # Qt stylesheets
│   │   ├── fonts/                   # Custom fonts
│   │   └── templates/               # Show templates
│   │
│   ├── images/                       # Image assets
│   │   ├── icons/                   # Application icons
│   │   ├── backgrounds/             # Background images
│   │   └── logos/                   # Logo files
│   │
│   ├── logs/                         # Application logs
│   │   └── cuepi.log               # Main log file
│   │
│   └── tests/                        # Unit tests
│       ├── __init__.py
│       ├── test_cue_model.py
│       ├── test_waveform_analyzer.py
│       └── test_show_generator.py
│
├── requirements.txt                  # Python dependencies
├── README.md                         # This file
├── .gitignore                        # Git ignore rules
└── LICENSE                           # License file
```

### Module Dependencies

```
main.py
├── views/
│   ├── welcome_page.py
│   └── main_window.py
│       ├── controllers/
│       │   ├── cue_controller.py
│       │   ├── system_mode_controller.py
│       │   └── show_execution_manager.py
│       ├── models/
│       │   ├── cue_model.py
│       │   └── database_model.py
│       ├── views/
│       │   ├── cue_table.py
│       │   ├── led_panel_manager.py
│       │   ├── button_bar.py
│       │   └── waveform_widget.py
│       └── utils/
│           ├── music_manager.py
│           ├── show_manager.py
│           └── waveform_analyzer.py
```

* * *

## 📚 API Documentation

### Core Classes

#### CueModel

Manages cue data and operations.

```python
from models.cue_model import Cue, CueModel

# Create cue model
cue_model = CueModel()

# Add cue
cue = Cue(
    cue_number=1,
    cue_type="SHOT",
    execution_time=5.0,
    outputs=[1, 2, 3],
    duration=0.0
)
cue_model.add_cue(cue)

# Get all cues
cues = cue_model.get_all_cues()

# Update cue
cue.execution_time = 6.0
cue_model.update_cue(cue)

# Delete cue
cue_model.delete_cue(cue.cue_number)

# Register observer
def on_cues_changed():
    print("Cues changed!")
cue_model.register_observer(on_cues_changed)
```

#### WaveformAnalyzer

Analyzes audio files for beat detection.

```python
from utils.waveform_analyzer import WaveformAnalyzer

# Create analyzer
analyzer = WaveformAnalyzer()

# Load audio
audio, sr = analyzer.load_audio('music.wav')

# Detect beats
beats = analyzer.detect_beats(audio, sr, method='madmom')

# Get beat times
beat_times = analyzer.get_beat_times(beats, sr)

# Classify drum hits
drum_hits = analyzer.classify_drum_hits(audio, sr, beat_times)

# Get analysis results
results = analyzer.get_analysis_results()
```

#### SpleeterService

Handles audio stem separation.

```python
from utils.spleeter_service import SpleeterService

# Create service
spleeter = SpleeterService()

# Separate audio
result = spleeter.separate_audio(
    input_file='music.wav',
    output_dir='output/',
    model='4stems'
)

# Check if successful
if result.success:
    print(f"Drums: {result.stems['drums']}")
    print(f"Vocals: {result.stems['vocals']}")
else:
    print(f"Error: {result.error}")
```

#### HardwareController

Controls Raspberry Pi hardware.

```python
from controllers.hardware_controller import HardwareController

# Create controller
hardware = HardwareController(
    host='raspberrypi.local',
    username='pi',
    password='raspberry'
)

# Connect
if hardware.connect():
    print("Connected!")
    
    # Execute cue
    hardware.execute_cue({
        'type': 'SHOT',
        'outputs': [1, 2, 3]
    })
    
    # Get GPIO status
    status = hardware.get_gpio_status()
    print(status)
    
    # Emergency stop
    hardware.emergency_stop()
    
    # Disconnect
    hardware.disconnect()
```

### Utility Functions

#### JSON Utilities

```python
from utils.json_utils import safe_json_dumps, safe_json_loads

# Serialize complex objects
data = {
    'numpy_array': np.array([1, 2, 3]),
    'datetime': datetime.now(),
    'custom_object': MyClass()
}
json_str = safe_json_dumps(data)

# Deserialize
loaded_data = safe_json_loads(json_str)
```

#### Show Management

```python
from utils.show_manager import ShowManager

# Create manager
show_manager = ShowManager(cue_model, led_panel)

# Save show
show_manager.save_show('my_show.cueshow')

# Load show
show_manager.load_show('my_show.cueshow')

# Export to CSV
show_manager.export_to_csv('my_show.csv')

# Import from CSV
show_manager.import_from_csv('my_show.csv')
```

### Signal/Slot Connections

The application uses Qt's signal/slot mechanism for communication:

```python
# Connect signals
cue_model.cues_changed.connect(self.on_cues_changed)
music_manager.playback_position_changed.connect(self.on_position_changed)
hardware_controller.connection_status_changed.connect(self.on_connection_changed)

# Emit signals
self.cue_created.emit(cue)
self.show_saved.emit(filename)
self.error_occurred.emit(error_message)
```

* * *

## 🤝 Contributing

This is a proprietary project. Contributions are not currently accepted.

* * *

## 📄 License

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

**Copyright © 2025 Michael Lyman. All rights reserved.**

* * *

## 🙏 Acknowledgments

### Open Source Libraries

This project would not be possible without these excellent open-source libraries:

-   **[PySide6](https://www.qt.io/qt-for-python)** - Qt for Python, providing the GUI framework
-   **[Librosa](https://librosa.org/)** - Audio analysis and feature extraction
-   **[Madmom](https://madmom.readthedocs.io/)** - State-of-the-art beat tracking and onset detection
-   **[Spleeter](https://github.com/deezer/spleeter)** - Audio source separation by Deezer
-   **[NumPy](https://numpy.org/)** - Fundamental package for numerical computing
-   **[SciPy](https://scipy.org/)** - Scientific computing library
-   **[Scikit-learn](https://scikit-learn.org/)** - Machine learning library
-   **[Matplotlib](https://matplotlib.org/)** - Plotting and visualization
-   **[Paramiko](https://www.paramiko.org/)** - SSH implementation
-   **[PyInstaller](https://pyinstaller.org/)** - Application bundling

### Special Thanks

-   The Qt Company for PySide6
-   The Librosa development team
-   The Madmom developers at Johannes Kepler University
-   Deezer Research for Spleeter
-   The Python community
-   All open-source contributors

### Inspiration

This project was inspired by professional pyrotechnic control systems and the desire to make sophisticated firework show design accessible to enthusiasts and professionals alike.

* * *

## 📞 Contact

For questions, support, or licensing inquiries:

-   **Email**: \[contact information\]
-   **GitHub**: [https://github.com/mblyman89/CueManagementSystem](https://github.com/mblyman89/CueManagementSystem)
-   **Website**: \[website if available\]

* * *

## 📝 Changelog

### Version 1.0.0 (Current)

-   Initial release
-   Full show design and management
-   Music analysis with Librosa and Madmom
-   Spleeter integration
-   Raspberry Pi hardware control
-   macOS application bundle
-   Comprehensive documentation

### Planned Features

-   Windows/Linux application bundles
-   Cloud show storage and sharing
-   Mobile app for remote control
-   Advanced effect sequencing
-   MIDI controller support
-   Multi-user collaboration
-   Show marketplace

* * *

**Made with ❤️ for the pyrotechnic community**

🎆 **CuePi - Professional Firework Show Management** 🎆