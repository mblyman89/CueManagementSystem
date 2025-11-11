#!/bin/bash
# Script to hardcode Spleeter path in CuePi

set -e

echo "======================================"
echo "Hardcoding Spleeter Path"
echo "======================================"
echo ""

cd ~/Desktop/"Cue Management System"/CuePi-Build/CueManagementSystem

# Backup the original file
echo "Creating backup of spleeter_service.py..."
cp ./CueManagementSystem/utils/audio/spleeter_service.py ./CueManagementSystem/utils/audio/spleeter_service.py.backup

# Replace the spleeter_command line to use hardcoded path
echo "Updating spleeter_command to use hardcoded path..."
sed -i '' "s|'spleeter_command': os.environ.get('CUE_SPLEETER_PATH') or 'spleeter'|'spleeter_command': '/Users/michaellyman/.venvs/cueaudio/bin/spleeter'|g" ./CueManagementSystem/utils/audio/spleeter_service.py

# Also update the fallback in _resolve_spleeter_path
sed -i '' "s|return self.config.get('spleeter_command') or 'spleeter'|return self.config.get('spleeter_command') or '/Users/michaellyman/.venvs/cueaudio/bin/spleeter'|g" ./CueManagementSystem/utils/audio/spleeter_service.py

echo "✓ Spleeter path updated!"
echo ""
echo "Changes made:"
echo "  - Hardcoded path: /Users/michaellyman/.venvs/cueaudio/bin/spleeter"
echo "  - Backup saved: spleeter_service.py.backup"
echo ""
echo "Next steps:"
echo "  1. Rebuild the app: cd ~/Desktop/&quot;Cue Management System&quot;/CuePi-Build && ./build_macos_app.sh"
echo "  2. Install: cp -r dist/CuePi.app /Applications/ && xattr -cr /Applications/CuePi.app"
echo "  3. Test: open /Applications/CuePi.app"
echo ""