Quick Rebuild and DMG Creation Commands
Prerequisites
Make sure you're in the correct directory and virtual environment is activated.

Step 1: Navigate to Project Directory
cd ~/Desktop/"Cue Management System"/CuePi-Build
Step 2: Activate Virtual Environment
source /Users/michaellyman/.venvs/cueaudio/bin/activate
Step 3: Clean Previous Build (Optional but Recommended)
rm -rf build dist
rm -rf ~/.pyinstaller_cache
Step 4: Rebuild the App
pyinstaller --clean CuePi.spec
This will take 3-5 minutes. You'll see the build progress in the terminal.

Step 5: Copy App to Applications Folder
cp -r dist/CuePi.app /Applications/
Step 6: Remove Quarantine Attributes
xattr -cr /Applications/CuePi.app
Step 7: Create DMG (Optional - for distribution)
./create_dmg.sh
The DMG will be created as CuePi-1.0.0.dmg in the current directory.

All-in-One Script
Copy and paste this entire block to do everything at once:

# Navigate to project
cd ~/Desktop/"Cue Management System"/CuePi-Build

# Activate virtual environment
source /Users/michaellyman/.venvs/cueaudio/bin/activate

# Clean previous build
echo "Cleaning previous build..."
rm -rf build dist
rm -rf ~/.pyinstaller_cache

# Rebuild app
echo "Building app (this takes 3-5 minutes)..."
pyinstaller --clean CuePi.spec

# Copy to Applications
echo "Copying to Applications folder..."
cp -r dist/CuePi.app /Applications/

# Remove quarantine
echo "Removing quarantine attributes..."
xattr -cr /Applications/CuePi.app

echo "✅ Build complete! App is ready in /Applications/CuePi.app"
echo ""
echo "To create DMG for distribution, run: ./create_dmg.sh"
Quick Test After Build
Launch the app from terminal to see any error messages:

/Applications/CuePi.app/Contents/MacOS/CuePi
Or launch normally from Applications folder or Dock.

Troubleshooting
If build fails:

# Check Python version
python --version  # Should be 3.10.11

# Check virtual environment
which python  # Should point to /Users/michaellyman/.venvs/cueaudio/bin/python

# Reinstall PyInstaller
pip install --upgrade pyinstaller
If app won't launch:

# Check for errors
/Applications/CuePi.app/Contents/MacOS/CuePi

# Remove and rebuild
rm -rf /Applications/CuePi.app
pyinstaller --clean CuePi.spec
cp -r dist/CuePi.app /Applications/
xattr -cr /Applications/CuePi.app
Build Times
Clean build: 3-5 minutes
Incremental build: 1-2 minutes (without --clean flag)
DMG creation: 30-60 seconds
File Sizes
CuePi.app: ~413 MB
CuePi-1.0.0.dmg: ~450 MB