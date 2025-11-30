"""
Recreate symlinks in the new structure
"""
import json
import os
from pathlib import Path

BASE_DIR = Path("/home/marco/Repos/cyclomedia/detekt-product/detekt-test/mockup_data/track_2020")
METADATA_FILE = BASE_DIR / "data" / "image_metadata.json"
REFERENCE_DIR = BASE_DIR / "resources" / "reference_images"
SPHERICAL_DIR = BASE_DIR / "data" / "images" / "spherical"

def recreate_symlinks():
    """Recreate all symlinks from metadata"""
    
    print("=" * 80)
    print("Recreating Image Symlinks")
    print("=" * 80)
    
    # Load metadata
    print(f"\n📄 Loading metadata from: {METADATA_FILE}")
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    print(f"✓ Loaded {metadata['total_images']} image positions")
    
    # Get reference images
    reference_images = sorted(REFERENCE_DIR.glob("frame*.png"))
    print(f"\n🖼️  Found {len(reference_images)} reference images:")
    for img in reference_images:
        print(f"  - {img.name}")
    
    if not reference_images:
        print("❌ No reference images found!")
        return
    
    # Create spherical directory
    SPHERICAL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Target directory: {SPHERICAL_DIR}")
    
    # Create symlinks
    print(f"\n🔗 Creating {metadata['total_images']} symlinks...")
    created = 0
    
    for position in metadata['image_positions']:
        # Target path (e.g., data/images/spherical/0.jpg)
        target_filename = position['image_path'].split('/')[-1]  # Get just the filename
        target_path = SPHERICAL_DIR / target_filename
        
        # Cycle through reference images
        source_img = reference_images[position['id'] % len(reference_images)]
        
        # Create relative symlink
        # From: data/images/spherical/0.jpg
        # To: resources/reference_images/frame1.png
        # Relative: ../../../resources/reference_images/frame1.png
        relative_source = os.path.relpath(source_img, target_path.parent)
        
        # Remove if exists
        if target_path.exists() or target_path.is_symlink():
            target_path.unlink()
        
        # Create symlink
        os.symlink(relative_source, target_path)
        created += 1
        
        if created % 5000 == 0:
            print(f"  Progress: {created}/{metadata['total_images']}...")
    
    print(f"\n✅ Created {created} symlinks!")
    
    # Verify a few symlinks
    print(f"\n🔍 Verifying symlinks...")
    for i in range(min(5, len(metadata['image_positions']))):
        target_filename = metadata['image_positions'][i]['image_path'].split('/')[-1]
        link_path = SPHERICAL_DIR / target_filename
        if link_path.is_symlink():
            target = os.readlink(link_path)
            print(f"  ✓ {link_path.name} -> {target}")
        else:
            print(f"  ✗ {link_path.name} is not a symlink!")

if __name__ == "__main__":
    recreate_symlinks()

