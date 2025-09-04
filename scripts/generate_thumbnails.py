#!/usr/bin/env python3
"""
Generate thumbnails for Sorcery TCG card images (including subdirectories)
"""

import os
import sys
from pathlib import Path

# Check for PIL/Pillow first
try:
    from PIL import Image
except ImportError:
    print("Error: PIL (Pillow) not installed!")
    print("Install it with: pip install Pillow")
    sys.exit(1)

def print_progress_bar(current, total, bar_length=40):
    """Print a progress bar to stdout"""
    progress = current / total
    filled_length = int(bar_length * progress)
    bar = '█' * filled_length + '░' * (bar_length - filled_length)
    percent = progress * 100
    sys.stdout.write(f'\rProgress: [{bar}] {current}/{total} ({percent:.1f}%)')
    sys.stdout.flush()

def generate_thumbnails():
    # Get the script's directory and find project root
    script_dir = Path(__file__).parent.absolute()
    
    # If script is in 'scripts' or 'tools' folder, go up one level
    if script_dir.name in ['scripts', 'tools']:
        project_root = script_dir.parent
    else:
        project_root = script_dir

    # Use pathlib throughout for consistency
    full_dir = project_root / 'data' / 'imgs' / 'full'
    thumb_dir = project_root / 'data' / 'imgs' / 'thumbs'
    thumbnail_size = (200, 280)
    
    print(f"Project root: {project_root}")
    print(f"Looking for images in: {full_dir}")
    print(f"Thumbnails will be saved to: {thumb_dir}")
    
    # Create thumbnails directory
    thumb_dir.mkdir(parents=True, exist_ok=True)
    
    if not full_dir.exists():
        print(f"Source directory not found: {full_dir}")
        print("Make sure your images are in 'data/imgs/full/' folder")
        return False
    
    processed = 0
    skipped = 0
    errors = 0
    
    image_extensions = ('.jpg', '.jpeg', '.png', '.webp', '.bmp', '.tiff')
    
    # Find all images recursively using pathlib
    print("Scanning for images...")
    image_files = []
    
    for image_path in full_dir.rglob('*'):
        if image_path.is_file() and image_path.suffix.lower() in image_extensions:
            # Get relative path from full_dir
            rel_path = image_path.relative_to(full_dir)
            image_files.append(rel_path)
    
    if not image_files:
        print("No images found in the source directory")
        return False
    
    print(f"Found {len(image_files)} images to process")
    print("Starting thumbnail generation...\n")
    
    # Process each image with progress tracking
    for i, rel_file_path in enumerate(image_files, 1):
        full_path = full_dir / rel_file_path
        
        # Update progress bar
        print_progress_bar(i, len(image_files))

        # Create subdirectory structure in thumbs folder
        rel_dir = rel_file_path.parent
        if rel_dir != Path('.'):  # Not in root
            thumb_subdir = thumb_dir / rel_dir
            thumb_subdir.mkdir(parents=True, exist_ok=True)
        
        # Generate thumbnail path (always save as .jpg)
        thumb_filename = rel_file_path.with_suffix('.jpg')
        thumb_path = thumb_dir / thumb_filename
        
        # Skip if thumbnail exists and is newer than source
        if (thumb_path.exists() and 
            thumb_path.stat().st_mtime > full_path.stat().st_mtime):
            skipped += 1
            continue
        
        try:
            with Image.open(full_path) as img:
                # Convert to RGB if needed (handles transparency)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    
                    if img.mode == 'RGBA':
                        # Paste with alpha channel as mask
                        background.paste(img, mask=img.split()[-1])
                    else:
                        background.paste(img)
                    
                    img = background
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save optimized thumbnail
                img.save(
                    thumb_path, 
                    'JPEG', 
                    optimize=True, 
                    quality=85, 
                    progressive=True
                )
                
                processed += 1
                
        except Exception as e:
            errors += 1
            print(f"\nError processing {rel_file_path}: {e}")
    
    # Final summary
    print()
    print(f"\nThumbnail generation complete!")
    print(f"   Generated: {processed}")
    print(f"   Skipped: {skipped} (already up-to-date)")
    print(f"   Errors: {errors}")
    
    if errors > 0:
        print(f"\n{errors} files had errors - check the output above for details")
    
    return processed > 0

if __name__ == '__main__':
    print("Sorcery TCG Thumbnail Generator")
    print("=" * 50)
    
    try:
        success = generate_thumbnails()
        
        if success:
            print("\nAll done! Your thumbnails are ready.")
            sys.exit(0)
        else:
            print("\nNo thumbnails were generated.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)