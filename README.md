# CueManagementSystem
Firework Show Manager

## Cue Management System Architecture

This document explains the proposed 3-layer architecture for the Cue Management System.

## 1. Models Layer (`models/cue_model.py`)

The Models Layer is responsible for data management and business logic. Moving cue data management to `models/cue_model.py` achieves:

- **Data Encapsulation**: All cue-related data structures and operations are defined in one place
- **Business Logic Isolation**: Validation rules, data transformations, and business rules are kept separate from UI
- **Reusability**: Data models can be reused across different views and controllers
- **Single Source of Truth**: All components access cue data through the model, avoiding inconsistencies

Current implementation has cue data scattered across multiple files (main_window.py, cue_table.py, etc.). Moving this to a dedicated model class creates a central place for managing all cue-related data.

## Audio Analysis Features

The Cue Management System includes advanced audio analysis features powered by librosa. These features enable automatic detection of beats, onsets, and other musical elements to help create synchronized light shows.

### Librosa Integration

Librosa is now properly integrated with the system, with the following enhancements:

- Automatic detection of librosa in Anaconda environments
- Fallback mechanism to use librosa from a dedicated virtual environment (librosa_env)
- Updated requirements.txt with proper dependencies

For detailed setup instructions, see the README.md file in the librosa_env directory.

### Waveform Visualization Enhancements

The waveform visualization has been enhanced with the following features:

- Improved peak marker visualization with color coding based on amplitude
- Visual effects for selected peaks (glow, larger markers)
- Simplified peak markers visible at lower zoom levels
- Enhanced peak selection with improved click detection
- Amplitude indicators for selected peaks

These enhancements make it easier to identify and select peaks in the audio waveform, improving the workflow for creating cue points.
