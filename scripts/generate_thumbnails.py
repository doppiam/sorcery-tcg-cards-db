#!/usr/bin/env python3
"""
Generate JPG thumbnails from PNG card images for the Sorcery TCG cards database.

This script:
- Recursively finds all PNG files in data/imgs/full/
- Creates corresponding JPG thumbnails in data/imgs/thumbs/
- Preserves the exact folder structure
- Maintains the filename (only changes extension: .png -> .jpg)
- Automatically handles any set name and product type
- Skips thumbnails that are already up-to-date
"""

import os
from pathlib import Path
from PIL import Image
import sys

# Configuration
FULL_DIR = Path('data/imgs/full')
THUMB_DIR = Path('data/imgs/thumbs')
THUMB_WIDTH = 300  # Width in pixels (height scales proportionally)
THUMB_QUALITY = 85  # JPEG quality (1-100)

def ensure_dir(path: Path):
    """Create directory if it doesn't exist."""
    path.mkdir(parents=True, exist_ok=True)

def is_thumbnail_outdated(source_png: Path, thumb_jpg: Path) -> bool:
    """
    Check if thumbnail needs to be regenerated.
    Returns True if thumbnail doesn't exist or is older than source.
    """
    if not thumb_jpg.exists():
        return True
    
    source_mtime = source_png.stat().st_mtime
    thumb_mtime = thumb_jpg.stat().st_mtime
    
    return source_mtime > thumb_mtime

def generate_thumbnail(source_png: Path, thumb_jpg: Path):
    """
    Generate a thumbnail from a PNG image.
    """
    try:
        # Open the source image
        with Image.open(source_png) as img:
            # Convert to RGB if necessary (PNG might have alpha channel)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create a white background
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Calculate new height maintaining aspect ratio
            width_percent = (THUMB_WIDTH / float(img.size[0]))
            new_height = int((float(img.size[1]) * float(width_percent)))
            
            # Resize image
            img_resized = img.resize((THUMB_WIDTH, new_height), Image.Resampling.LANCZOS)
            
            # Save as JPEG
            ensure_dir(thumb_jpg.parent)
            img_resized.save(thumb_jpg, 'JPEG', quality=THUMB_QUALITY, optimize=True)
            
        return True
        
    except Exception as e:
        print(f"❌ Error processing {source_png}: {e}", file=sys.stderr)
        return False

def main():
    """Main execution."""
    print("=" * 80)
    print("Sorcery TCG Thumbnail Generator")
    print("=" * 80)
    print()
    
    if not FULL_DIR.exists():
        print(f"❌ Error: Source directory not found: {FULL_DIR}")
        print(f"   Make sure you're running this from the repository root!")
        sys.exit(1)
    
    # Find all PNG files recursively
    png_files = list(FULL_DIR.rglob('*.png'))
    
    if not png_files:
        print(f"⚠️  No PNG files found in {FULL_DIR}")
        sys.exit(0)
    
    print(f"📁 Found {len(png_files)} PNG images")
    print(f"📏 Thumbnail size: {THUMB_WIDTH}px width")
    print(f"🎨 JPEG quality: {THUMB_QUALITY}%")
    print()
    
    stats = {
        'processed': 0,
        'skipped': 0,
        'errors': 0,
        'created': 0,
        'updated': 0,
    }
    
    for source_png in png_files:
        # Get relative path from full directory
        rel_path = source_png.relative_to(FULL_DIR)
        
        # Create corresponding thumbnail path (change extension to .jpg)
        thumb_jpg = THUMB_DIR / rel_path.with_suffix('.jpg')
        
        # Check if thumbnail needs updating
        if is_thumbnail_outdated(source_png, thumb_jpg):
            was_existing = thumb_jpg.exists()
            
            if generate_thumbnail(source_png, thumb_jpg):
                if was_existing:
                    stats['updated'] += 1
                    status = "🔄 Updated"
                else:
                    stats['created'] += 1
                    status = "✨ Created"
                
                stats['processed'] += 1
                
                # Show progress every 50 files
                if stats['processed'] % 50 == 0:
                    print(f"  {status} thumbnail {stats['processed']}/{len(png_files)}: {rel_path}")
            else:
                stats['errors'] += 1
        else:
            stats['skipped'] += 1
    
    print()
    print("=" * 80)
    print("Summary:")
    print("=" * 80)
    print(f"  ✅ Processed: {stats['processed']}")
    print(f"     - Created: {stats['created']}")
    print(f"     - Updated: {stats['updated']}")
    print(f"  ⏭️  Skipped (up-to-date): {stats['skipped']}")
    print(f"  ❌ Errors: {stats['errors']}")
    print(f"  📊 Total images: {len(png_files)}")
    print()
    
    if stats['errors'] > 0:
        print("⚠️  Some thumbnails failed to generate. Check errors above.")
        sys.exit(1)
    else:
        print("✅ All thumbnails generated successfully!")
        sys.exit(0)

if __name__ == "__main__":
    main()

