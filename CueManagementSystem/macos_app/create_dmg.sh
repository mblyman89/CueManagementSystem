#!/bin/bash
# ============================================================================
# CuePi DMG Installer Creator
# ============================================================================
# This script creates a macOS Disk Image (.dmg) installer for CuePi
#
# Prerequisites:
# - CuePi.app must be built (run build_macos_app.sh first)
# - create-dmg tool installed (brew install create-dmg)
#
# Usage:
#   chmod +x create_dmg.sh
#   ./create_dmg.sh
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "CuePi DMG Installer Creator"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if CuePi.app exists
if [ ! -d "dist/CuePi.app" ]; then
    print_error "CuePi.app not found in dist directory!"
    print_error "Please run build_macos_app.sh first."
    exit 1
fi

# Check if create-dmg is installed
if ! command -v create-dmg &> /dev/null; then
    print_warning "create-dmg not found. Installing via Homebrew..."
    if command -v brew &> /dev/null; then
        brew install create-dmg
    else
        print_error "Homebrew not found. Please install create-dmg manually:"
        print_error "  brew install create-dmg"
        exit 1
    fi
fi

# Create a folder for DMG contents
print_status "Preparing DMG contents..."
mkdir -p dist/dmg
rm -rf dist/dmg/*

# Copy the app bundle to the dmg folder
cp -r "dist/CuePi.app" dist/dmg/
print_success "Copied CuePi.app to DMG folder"

# Remove old DMG if it exists
if [ -f "dist/CuePi.dmg" ]; then
    print_status "Removing old DMG..."
    rm "dist/CuePi.dmg"
fi

# Create the DMG
print_status "Creating DMG installer..."
echo ""

create-dmg \
  --volname "CuePi" \
  --volicon "CuePi.icns" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "CuePi.app" 175 190 \
  --hide-extension "CuePi.app" \
  --app-drop-link 425 190 \
  "dist/CuePi.dmg" \
  "dist/dmg/"

if [ $? -eq 0 ]; then
    print_success "DMG created successfully!"
    
    # Get DMG size
    DMG_SIZE=$(du -sh dist/CuePi.dmg | awk '{print $1}')
    
    echo ""
    echo "============================================================================"
    echo "DMG Creation Summary"
    echo "============================================================================"
    print_success "✓ CuePi.dmg created successfully"
    print_status "Location: $(pwd)/dist/CuePi.dmg"
    print_status "Size: $DMG_SIZE"
    echo ""
    print_status "To install:"
    echo "  1. Double-click CuePi.dmg"
    echo "  2. Drag CuePi.app to the Applications folder"
    echo "  3. Launch from Applications or Spotlight"
    echo ""
    echo "============================================================================"
else
    print_error "DMG creation failed!"
    exit 1
fi