"""
Alternative script to create .icns file using png2icns
"""
import os
import subprocess
from PIL import Image

def create_icns_with_sips(png_path, output_name="CuePi"):
    """
    Create .icns using sips (macOS built-in tool)
    This will be run on the user's Mac
    """
    # Create a temporary 1024x1024 version
    img = Image.open(png_path)
    img_1024 = img.resize((1024, 1024), Image.Resampling.LANCZOS)
    temp_png = f"{output_name}_1024.png"
    img_1024.save(temp_png)
    
    # Create the iconset directory structure
    iconset_dir = f"{output_name}.iconset"
    os.makedirs(iconset_dir, exist_ok=True)
    
    # Define required icon sizes
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
    
    print(f"✅ Created iconset directory: {iconset_dir}")
    print(f"✅ Created temporary 1024x1024 PNG: {temp_png}")
    print("\n📝 To complete the .icns creation on macOS, run:")
    print(f"   iconutil -c icns {iconset_dir} -o {output_name}.icns")
    
    return iconset_dir, temp_png

if __name__ == "__main__":
    png_path = "CueManagementSystem/CueManagementSystem/images/CuePiShifter_APP_Logo.png"
    create_icns_with_sips(png_path, "CuePi")