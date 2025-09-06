# Firework Cue Management System

A comprehensive application for designing, synchronizing, and executing professional firework shows with musical integration.

## Overview

The Firework Cue Management System is a powerful desktop application that enables users to design and execute professional-grade firework shows synchronized with music. The system features advanced audio analysis capabilities that can detect beats, particularly drum hits, in music tracks and automatically generate firework cues that synchronize with these beats.

## Key Features

### Show Design and Management
- Create, edit, and manage firework cue sequences
- Design shows from scratch or generate them automatically based on music
- Save, load, and import show configurations
- Preview shows before execution

### Music Integration and Analysis
- Advanced audio waveform visualization and analysis
- Automatic beat detection with drum hit classification
- Audio stem separation using Spleeter to isolate drums for better beat detection
- Manual and automatic peak selection for precise cue placement
- Synchronize fireworks with specific musical elements

### Firework Control
- Support for various firework types and effects
- Sequential or random distribution of fireworks
- Precise timing control with millisecond accuracy
- Multiple output channels for complex choreography

### Hardware Integration
- Control fireworks via Raspberry Pi GPIO
- Remote execution via SSH connection
- Hardware status monitoring and diagnostics
- Safety features including arm/disarm controls

### User Interface
- Intuitive graphical interface with cue table
- Real-time waveform visualization
- LED panel visualization for show preview
- Comprehensive status monitoring

## System Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux
- **Python**: Version 3.8 or higher
- **RAM**: 8GB minimum, 16GB recommended for larger audio files
- **Storage**: 2GB for application and dependencies
- **Additional Hardware** (optional): Raspberry Pi for physical firework control

## Installation Guide

### Setting Up the Environment

#### Option 1: Using Conda (Recommended)

1. **Install Miniconda or Anaconda**:
   - Download and install from [Anaconda's website](https://www.anaconda.com/products/distribution)

2. **Create a new Conda environment**:
   ```bash
   conda create -n firework_env python=3.12
   conda activate firework_env
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

#### Option 2: Using Virtual Environment

1. **Create a virtual environment**:
   ```bash
   python -m venv .venv
   ```

2. **Activate the environment**:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Setting Up Spleeter for Audio Stem Separation

The application uses Spleeter for separating drums from music tracks. This requires a separate environment:

1. **Create a Spleeter environment**:
   ```bash
   conda create -n spleeter_env python=3.8
   conda activate spleeter_env
   pip install spleeter
   ```

2. **Download pre-trained models**:
   ```bash
   # While in spleeter_env
   spleeter separate -p spleeter:4stems -o output_folder dummy.wav
   ```
   This will download the necessary models. You can cancel the process after the models are downloaded.

## PyCharm Setup Guide

For users who prefer PyCharm as their IDE, follow these steps for optimal setup:

1. **Install PyCharm**:
   - Download and install [PyCharm Community or Professional](https://www.jetbrains.com/pycharm/download/)

2. **Open the Project**:
   - Open PyCharm
   - Select "Open" and navigate to the CueManagementSystem directory
   - Click "Open"

3. **Configure Python Interpreter**:
   - Go to File > Settings (Windows/Linux) or PyCharm > Preferences (macOS)
   - Navigate to Project: CueManagementSystem > Python Interpreter
   - Click the gear icon and select "Add..."
   - Choose "Conda Environment" or "Virtual Environment" based on your setup
   - Select "Existing environment" and point to your firework_env

4. **Configure Spleeter Environment** (if using PyCharm Professional):
   - Go to File > Settings (Windows/Linux) or PyCharm > Preferences (macOS)
   - Navigate to Project: CueManagementSystem > Python Interpreter
   - Click the gear icon and select "Add..."
   - Choose "Conda Environment"
   - Select "Existing environment" and point to your spleeter_env
   - This creates an additional interpreter that you can switch to when working with Spleeter code

5. **Run Configuration**:
   - Click on "Add Configuration" in the top-right corner
   - Click the "+" button and select "Python"
   - Set the script path to the main.py file
   - Set the Python interpreter to your firework_env
   - Click "Apply" and "OK"

## Usage Guide

### Starting the Application

1. Activate your environment:
   ```bash
   conda activate firework_env
   ```

2. Navigate to the application directory:
   ```bash
   cd CueManagementSystem
   ```

3. Run the application:
   ```bash
   python main.py
   ```

### Creating a New Show

1. From the welcome screen, select "Design Show"
2. Use the cue creator to add individual cues or use the music analysis feature for automatic cue generation

### Music Analysis and Synchronization

1. Click on "Music Manager" in the main window
2. Select a music file to analyze
3. Choose whether to use Spleeter for drum separation (recommended for better beat detection)
4. After analysis, the waveform will display with detected beats
5. Use the Musical Generator to create cues based on the detected beats
6. Adjust distribution methods, time offsets, and other parameters as needed
7. Generate and add the cues to your show

### Previewing and Executing Shows

1. Use the "Preview" button to simulate the show with music
2. For hardware execution, select the appropriate system mode (Simulation, Local Hardware, or Remote Hardware)
3. If using hardware, ensure outputs are enabled and armed before execution
4. Use the execution controls (Execute All, Pause, Resume, Stop) to manage the show

### Saving and Loading Shows

1. Use the Show Manager to save your current show
2. Previously saved shows can be loaded from the welcome screen or via the Show Manager

## Troubleshooting

### Common Issues

1. **Audio Analysis Fails**:
   - Ensure your audio file is in a supported format (WAV recommended)
   - Try using a different audio file
   - Check if Spleeter is properly installed

2. **Hardware Connection Issues**:
   - Verify SSH credentials for remote connections
   - Check network connectivity
   - Ensure Raspberry Pi is powered and running

3. **Performance Issues**:
   - Large audio files may require more processing time
   - Close other resource-intensive applications
   - Consider upgrading RAM if processing is consistently slow

### Getting Help

For additional assistance, check the documentation in the CueManagementSystem directory or contact the developer.

## License

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

## Acknowledgments

- Librosa for audio analysis capabilities
- Spleeter for audio source separation
- PySide6 for the graphical user interface
- The open-source community for various tools and libraries that made this project possible