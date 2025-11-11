# CuePi Quick Reference Guide

A condensed reference for common tasks and commands.

* * *

## 🚀 Quick Start

### Installation (5 Minutes)

```bash
# 1. Clone repository
git clone https://github.com/mblyman89/CueManagementSystem.git
cd CueManagementSystem

# 2. Create environment
conda create -n firework_env python=3.11
conda activate firework_env

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
cd CueManagementSystem
python main.py
```

### Spleeter Setup (10 Minutes)

```bash
# 1. Create separate environment
conda create -n spleeter_env python=3.8
conda activate spleeter_env

# 2. Install Spleeter
# For Intel/AMD:
pip install spleeter

# For Apple Silicon:
pip install tensorflow-macos tensorflow-metal spleeter

# 3. Download models
spleeter separate -p spleeter:4stems -o /tmp dummy.wav
# (Cancel after models download)

# 4. Get spleeter path
which spleeter
# Set this path in app settings or CUE_SPLEETER_PATH environment variable
```

* * *

## 📋 Common Commands

### Environment Management

```bash
# Activate main environment
conda activate firework_env

# Activate Spleeter environment
conda activate spleeter_env

# Deactivate environment
conda deactivate

# List environments
conda env list

# Update dependencies
pip install --upgrade -r requirements.txt
```

### Running the Application

```bash
# Normal mode
python main.py

# Debug mode
python main.py --debug

# Verbose mode
python main.py --debug --verbose

# From project root
python -m CueManagementSystem.main
```

### Raspberry Pi Commands

```bash
# SSH into Raspberry Pi
ssh pi@raspberrypi.local

# Check GPIO status
python3 raspberry_pi/get_gpio_status.py

# Test single output
python3 raspberry_pi/execute_cue.py '{"type":"SHOT","outputs":[1]}'

# Emergency stop
python3 raspberry_pi/emergency_stop.py

# Switch to WiFi mode
sudo ./wifi-mode.sh "SSID" "password"

# Switch to Ad-Hoc mode
sudo ./adhoc-mode.sh

# Check network status
python3 raspberry_pi/get_network_status.py
```

* * *

## ⌨️ Keyboard Shortcuts

| Action | macOS | Windows/Linux |
| --- | --- | --- |
| New Show | `Cmd+N` | `Ctrl+N` |
| Open Show | `Cmd+O` | `Ctrl+O` |
| Save Show | `Cmd+S` | `Ctrl+S` |
| Create Cue | `Cmd+K` | `Ctrl+K` |
| Edit Cue | `Cmd+E` | `Ctrl+E` |
| Delete Cue | `Delete` | `Delete` |
| Play/Pause | `Space` | `Space` |
| Preview | `Cmd+P` | `Ctrl+P` |
| Zoom In | `Cmd++` | `Ctrl++` |
| Zoom Out | `Cmd+-` | `Ctrl+-` |
| Preferences | `Cmd+,` | `Ctrl+,` |
| Quit | `Cmd+Q` | `Ctrl+Q` |

* * *

## 🎵 Music Analysis Workflow

### Basic Analysis

```
1. Music Manager → Import Music
2. Select audio file
3. Click "Analyze Waveform"
4. Wait for analysis
5. Review detected beats
6. Musical Generator → Configure → Generate
7. Add to Show
```

### With Spleeter (Better Results)

```
1. Music Manager → Import Music
2. Select audio file
3. Click "Analyze Waveform"
4. Check "Use Spleeter"
5. Select "4stems" model
6. Click "Separate Audio" (wait 2-5 minutes)
7. Click "Analyze Drums"
8. Review detected beats
9. Musical Generator → Configure → Generate
10. Add to Show
```

* * *

## 🔧 Troubleshooting Quick Fixes

### Application Won't Start

```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Clear cache
rm -rf ~/.cache/cuepi/
find . -name "*.pyc" -delete
```

### Audio Analysis Fails

```bash
# Check FFmpeg
ffmpeg -version

# Install FFmpeg
# macOS:
brew install ffmpeg

# Ubuntu:
sudo apt-get install ffmpeg

# Check NumPy version
python -c "import numpy; print(numpy.__version__)"
# Should be < 2.0

# Fix if needed:
pip install "numpy<2.0"
```

### Spleeter Not Working

```bash
# Verify installation
conda activate spleeter_env
spleeter --help

# Check TensorFlow
python -c "import tensorflow as tf; print(tf.__version__)"

# Reinstall (Apple Silicon)
pip uninstall tensorflow spleeter
pip install tensorflow-macos tensorflow-metal spleeter

# Check path
which spleeter
# Set in app: Settings → Spleeter Path
```

### Raspberry Pi Connection Issues

```bash
# Test connection
ping raspberrypi.local

# Test SSH
ssh pi@raspberrypi.local

# Check SSH service (on Pi)
sudo systemctl status ssh
sudo systemctl start ssh

# Remove old SSH key
ssh-keygen -R raspberrypi.local
```

* * *

## 🏗️ Building macOS App

### Quick Build

```bash
cd CueManagementSystem/macos_app

# 1. Fix imports
cd ..
python fix_imports.py

# 2. Hardcode Spleeter path
cd macos_app
./fix_spleeter_hardcode.sh /path/to/spleeter_env/bin/spleeter

# 3. Build app
./build_macos_app.sh

# 4. Test app
open dist/CuePi.app

# 5. Create DMG (optional)
./create_dmg.sh
```

* * *

## 📁 Important File Locations

### macOS

```
Application Support: ~/Library/Application Support/CuePi/
Logs: ~/Library/Logs/CuePi/
Cache: ~/.cache/cuepi/
Spleeter Models: ~/.cache/spleeter/
```

### Linux

```
Application Support: ~/.local/share/CuePi/
Logs: ~/.local/share/CuePi/logs/
Cache: ~/.cache/cuepi/
Spleeter Models: ~/.cache/spleeter/
```

### Windows

```
Application Support: %APPDATA%\CuePi\
Logs: %APPDATA%\CuePi\logs\
Cache: %LOCALAPPDATA%\cuepi\
Spleeter Models: %USERPROFILE%\.cache\spleeter\
```

* * *

## 🔍 Useful Commands

### Check Dependencies

```bash
# List installed packages
pip list

# Check specific package
pip show PySide6

# Verify imports
python -c "import PySide6; print('OK')"
python -c "import librosa; print('OK')"
python -c "import madmom; print('OK')"
```

### Database Management

```bash
# Backup database
cp ~/Library/Application\ Support/CuePi/shows.db ~/Desktop/backup.db

# Restore database
cp ~/Desktop/backup.db ~/Library/Application\ Support/CuePi/shows.db
```

### Log Analysis

```bash
# View logs
tail -f ~/Library/Logs/CuePi/cuepi.log

# Search for errors
grep -i error ~/Library/Logs/CuePi/cuepi.log

# Clear logs
rm ~/Library/Logs/CuePi/*.log
```

### Performance Monitoring

```bash
# Monitor CPU/Memory
top -pid $(pgrep -f "python.*main.py")

# Check disk usage
du -sh ~/.cache/cuepi/
du -sh ~/.cache/spleeter/
```

* * *

## 🎯 Best Practices

### Show Design

1.  ✅ Always load music first
2.  ✅ Use Spleeter for vocal-heavy tracks
3.  ✅ Preview before execution
4.  ✅ Save frequently
5.  ✅ Test timing with single cues first

### Music Analysis

1.  ✅ Use WAV format when possible
2.  ✅ Start with Librosa, use Madmom for complex music
3.  ✅ Adjust sensitivity based on results
4.  ✅ Use Spleeter for better drum detection
5.  ✅ Verify beats by listening

### Hardware Safety

1.  ✅ Always run pre-show checklist
2.  ✅ Test connection before show
3.  ✅ Use wired connection when possible
4.  ✅ Have emergency stop ready
5.  ✅ Verify all outputs are off after show

### Performance

1.  ✅ Close unnecessary applications
2.  ✅ Use 44.1kHz audio files
3.  ✅ Clear cache periodically
4.  ✅ Limit waveform zoom level
5.  ✅ Use static IP for Raspberry Pi

* * *

## 📞 Quick Help

### Error Messages

| Error | Quick Fix |
| --- | --- |
| ModuleNotFoundError | `pip install <module>` |
| ImportError DLL | Install Visual C++ Redistributable |
| Address already in use | `kill -9 <PID>` |
| Permission denied | `chmod +x` or `sudo` |
| GPIO initialization failed | `sudo usermod -a -G gpio $USER` |

### Common Issues

| Issue | Solution |
| --- | --- |
| App won't start | Check Python version, reinstall deps |
| Analysis fails | Check FFmpeg, try different file |
| Spleeter fails | Verify installation, check path |
| Can't connect to Pi | Check network, test SSH |
| Outputs don't fire | Check arm status, verify wiring |

* * *

## 🔗 Useful Links

-   **GitHub**: [https://github.com/mblyman89/CueManagementSystem](https://github.com/mblyman89/CueManagementSystem)
-   **Librosa Docs**: [https://librosa.org/doc/latest/](https://librosa.org/doc/latest/)
-   **Madmom Docs**: [https://madmom.readthedocs.io/](https://madmom.readthedocs.io/)
-   **Spleeter Docs**: [https://github.com/deezer/spleeter](https://github.com/deezer/spleeter)
-   **PySide6 Docs**: [https://doc.qt.io/qtforpython/](https://doc.qt.io/qtforpython/)
-   **Raspberry Pi Docs**: [https://www.raspberrypi.com/documentation/](https://www.raspberrypi.com/documentation/)

* * *

## 📝 Quick Notes

### Version Requirements

-   Python: 3.8 - 3.12 (3.10+ recommended)
-   Spleeter: Python 3.8 only
-   NumPy: < 2.0 (for madmom compatibility)
-   PySide6: >= 6.5.0

### System Requirements

-   RAM: 8GB minimum, 16GB recommended
-   Storage: 2GB for app, 5GB with Spleeter
-   OS: macOS 10.15+, Windows 10+, Ubuntu 20.04+

### Raspberry Pi

-   Model: Pi 3B+, 4, or Zero W2
-   OS: Raspberry Pi OS (32-bit or 64-bit)
-   Power: 5V 3A (Pi 4) or 5V 2.5A (Pi 3)
-   Network: WiFi or Ethernet

* * *

**For detailed information, see the full README.md**