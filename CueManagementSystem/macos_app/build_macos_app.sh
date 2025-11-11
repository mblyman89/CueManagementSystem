#!/bin/bash
# ============================================================================
# CuePi macOS App Builder
# ============================================================================
# This script builds the CuePi application into a standalone macOS app bundle
# 
# Prerequisites:
# - Python 3.10 environment with all dependencies installed
# - PyInstaller installed (pip install pyinstaller)
# - All project files in CueManagementSystem directory
# - Icon files prepared (CuePi.iconset directory)
#
# Usage:
#   chmod +x build_macos_app.sh
#   ./build_macos_app.sh
# ============================================================================

set -e  # Exit on error

echo "============================================================================"
echo "CuePi macOS App Builder"
echo "============================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Step 1: Check prerequisites
print_status "Checking prerequisites..."

if [ ! -d "CueManagementSystem/CueManagementSystem" ]; then
    print_error "CueManagementSystem directory not found!"
    exit 1
fi

if [ ! -f "CueManagementSystem/CueManagementSystem/main.py" ]; then
    print_error "main.py not found in CueManagementSystem/CueManagementSystem/"
    exit 1
fi

print_success "Project structure verified"

# Step 2: Check Python version
print_status "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
print_status "Python version: $PYTHON_VERSION"

# Step 3: Check PyInstaller
print_status "Checking PyInstaller installation..."
if ! command -v pyinstaller &> /dev/null; then
    print_warning "PyInstaller not found. Installing..."
    pip3 install pyinstaller
fi
PYINSTALLER_VERSION=$(pyinstaller --version 2>&1)
print_success "PyInstaller version: $PYINSTALLER_VERSION"

# Step 4: Create .icns file from iconset
print_status "Creating .icns icon file..."
if [ -d "CuePi.iconset" ]; then
    iconutil -c icns CuePi.iconset -o CuePi.icns
    print_success "Created CuePi.icns"
else
    print_warning "CuePi.iconset not found. Using PNG as fallback."
fi

# Step 5: Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build dist
print_success "Cleaned build directories"

# Step 6: Run PyInstaller
print_status "Building CuePi app bundle..."
echo ""
echo "This may take several minutes..."
echo ""

pyinstaller CuePi.spec

if [ $? -eq 0 ]; then
    print_success "Build completed successfully!"
else
    print_error "Build failed!"
    exit 1
fi

# Step 7: Verify the build
print_status "Verifying build..."

if [ -d "dist/CuePi.app" ]; then
    print_success "CuePi.app created successfully!"
    
    # Get app size
    APP_SIZE=$(du -sh dist/CuePi.app | awk '{print $1}')
    print_status "App bundle size: $APP_SIZE"
    
    # Check if icon is set
    if [ -f "CuePi.icns" ]; then
        print_status "Updating app icon..."
        # Copy icon to app bundle resources
        cp CuePi.icns dist/CuePi.app/Contents/Resources/
        print_success "Icon updated"
    fi
    
else
    print_error "CuePi.app not found in dist directory!"
    exit 1
fi

# Step 8: Test the app
print_status "Testing app launch..."
echo ""
print_warning "Attempting to launch CuePi.app..."
print_warning "If the app opens successfully, close it to continue."
echo ""

open dist/CuePi.app

sleep 3

# Step 9: Summary
echo ""
echo "============================================================================"
echo "Build Summary"
echo "============================================================================"
print_success "✓ CuePi.app created successfully"
print_status "Location: $(pwd)/dist/CuePi.app"
print_status "Size: $APP_SIZE"
echo ""
print_status "Next steps:"
echo "  1. Test the app by opening: dist/CuePi.app"
echo "  2. If it works, you can move it to /Applications"
echo "  3. Optional: Create a DMG installer with ./create_dmg.sh"
echo ""
echo "============================================================================"