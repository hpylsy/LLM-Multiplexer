#!/usr/bin/env python3
"""Generate favicon files from team-logo.png.

Usage:
    python scripts/generate_favicon.py

Requires: Pillow (pip install Pillow)
"""
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Error: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent.parent
BRAND_DIR = BASE_DIR / "static" / "brand"
LOGO_PATH = BRAND_DIR / "team-logo.png"

if not LOGO_PATH.exists():
    print(f"Error: {LOGO_PATH} not found. Please add your team logo first.")
    sys.exit(1)

img = Image.open(LOGO_PATH)

# Generate favicon.ico (32x32)
img_32 = img.resize((32, 32), Image.LANCZOS)
ico_path = BASE_DIR / "static" / "favicon.ico"
img_32.save(ico_path, format="ICO", sizes=[(32, 32)])
print(f"Created: {ico_path}")

# Generate favicon-32x32.png
png32_path = BRAND_DIR / "favicon-32x32.png"
img_32.save(png32_path, format="PNG")
print(f"Created: {png32_path}")

# Generate apple-touch-icon.png (180x180)
img_180 = img.resize((180, 180), Image.LANCZOS)
apple_path = BRAND_DIR / "apple-touch-icon.png"
img_180.save(apple_path, format="PNG")
print(f"Created: {apple_path}")

print("\nDone! Run 'python manage.py collectstatic' to update served files.")
