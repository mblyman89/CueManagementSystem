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

# GitHub Authentication Instructions

To push your code to GitHub, you'll need to authenticate. Here's how to set up authentication using a Personal Access Token (PAT):

## Generate a Personal Access Token (PAT)

1. Go to your GitHub account settings: https://github.com/settings/profile
2. Click on "Developer settings" at the bottom of the left sidebar
3. Click on "Personal access tokens" and then "Tokens (classic)"
4. Click "Generate new token" and then "Generate new token (classic)"
5. Give your token a descriptive name (e.g., "CueManagementSystem access")
6. Select the scopes or permissions you need (at minimum, select "repo" for full repository access)
7. Click "Generate token"
8. **IMPORTANT**: Copy the token immediately! You won't be able to see it again.

## Use the Token for Authentication

### Method 1: Store credentials in Git credential manager

```bash
git config --global credential.helper store
git push origin main
```

When prompted, enter your GitHub username and use the PAT as your password.

### Method 2: Include the token in the remote URL

```bash
git remote set-url origin https://[YOUR_USERNAME]:[YOUR_TOKEN]@github.com/mblyman89/CueManagementSystem.git
git push origin main
```

Replace [YOUR_USERNAME] with your GitHub username and [YOUR_TOKEN] with the PAT you generated.

### Method 3: Use GitHub CLI

1. Install GitHub CLI: https://cli.github.com/
2. Authenticate with: `gh auth login`
3. Push with: `gh repo sync`

After setting up authentication, you can push your changes with:
```bash
git push origin main
```
