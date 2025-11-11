"""
Script to convert PNG to macOS .icns format
"""
from PIL import Image
import os
import subprocess

def create_iconset(png_path, output_name="CuePi"):
    """
    Create macOS .icns file from PNG
    """
    # Load the image
    img = Image.open(png_path)
    
    # Create iconset directory
    iconset_dir = f"{output_name}.iconset"
    os.makedirs(iconset_dir, exist_ok=True)
    
    # Define required icon sizes for macOS
    sizes = [
        (16, 'icon_16x16.png'),
        (32, 'icon_16x16@2x.png'),
        (32, 'icon_32x32.png'),
        (64, 'icon_32x32@2x.png'),
        (128, 'icon_128x128.png'),
        (256, 'icon_128x128@2x.png'),
        (256, 'icon_256x256.png'),
        (512, 'icon_256x256@2x.png'),
        (512, 'icon_512x512.png'),
        (1024, 'icon_512x512@2x.png'),
    ]
    
    # Generate all required sizes
    for size, filename in sizes:
        resized = img.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(os.path.join(iconset_dir, filename))
        print(f"Created {filename}")
    
    # Convert iconset to icns using macOS iconutil
    try:
        subprocess.run(['iconutil', '-c', 'icns', iconset_dir, '-o', f'{output_name}.icns'], check=True)
        print(f"\n✅ Successfully created {output_name}.icns")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error creating .icns file: {e}")
        print("Note: iconutil is only available on macOS")
        return False
    except FileNotFoundError:
        print("❌ iconutil not found - this script must run on macOS")
        return False

if __name__ == "__main__":
    png_path = "CueManagementSystem/CueManagementSystem/images/CuePiShifter_APP_Logo.png"
    create_iconset(png_path, "CuePi")