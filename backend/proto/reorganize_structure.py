"""
Reorganize mockup data folder structure
"""
from pathlib import Path
import shutil
import os

BASE_DIR = Path("/home/marco/Repos/cyclomedia/detekt-product/detekt-test/mockup_data/track_2020")

def reorganize_structure():
    """Reorganize folder structure to separate resources from generated data"""
    
    print("=" * 80)
    print("Reorganizing Folder Structure")
    print("=" * 80)
    
    # Define new structure
    resources_dir = BASE_DIR / "resources"
    reference_images_dir = resources_dir / "reference_images"
    data_dir = BASE_DIR / "data"
    data_images_dir = data_dir / "images"
    data_spherical_dir = data_images_dir / "spherical"
    
    # Create directories
    print("\n📁 Creating new directory structure...")
    resources_dir.mkdir(exist_ok=True)
    reference_images_dir.mkdir(exist_ok=True)
    data_dir.mkdir(exist_ok=True)
    data_images_dir.mkdir(exist_ok=True)
    data_spherical_dir.mkdir(exist_ok=True)
    print("  ✓ resources/reference_images/")
    print("  ✓ data/images/spherical/")
    
    # Move GeoPackage to resources
    print("\n📦 Moving source files to resources/...")
    gpkg_source = BASE_DIR / "US-SANB-201020.gpkg"
    gpkg_dest = resources_dir / "US-SANB-201020.gpkg"
    if gpkg_source.exists() and not gpkg_dest.exists():
        shutil.move(str(gpkg_source), str(gpkg_dest))
        print(f"  ✓ Moved {gpkg_source.name}")
    
    # Move reference images to resources/reference_images
    print("\n🖼️  Moving reference images...")
    images_source_dir = BASE_DIR / "images"
    for frame_img in images_source_dir.glob("frame*.png"):
        dest = reference_images_dir / frame_img.name
        if not dest.exists():
            shutil.move(str(frame_img), str(dest))
            print(f"  ✓ Moved {frame_img.name}")
    
    # Move metadata to data/
    print("\n📄 Moving metadata...")
    metadata_source = BASE_DIR / "image_metadata.json"
    metadata_dest = data_dir / "image_metadata.json"
    if metadata_source.exists() and not metadata_dest.exists():
        shutil.move(str(metadata_source), str(metadata_dest))
        print(f"  ✓ Moved image_metadata.json")
    
    # Remove old symlinks and recreate with correct paths
    print("\n🔗 Recreating symlinks with new structure...")
    old_spherical_dir = images_source_dir / "spherical"
    
    # Count old symlinks
    old_symlinks = list(old_spherical_dir.glob("*.jpg")) if old_spherical_dir.exists() else []
    print(f"  Found {len(old_symlinks)} old symlinks to recreate")
    
    # Get reference images
    reference_images = sorted(reference_images_dir.glob("frame*.png"))
    print(f"  Found {len(reference_images)} reference images")
    
    if not reference_images:
        print("  ❌ No reference images found!")
        return
    
    # Recreate symlinks
    created = 0
    for old_link in old_symlinks:
        # Get the ID from filename (e.g., "0.jpg" -> 0)
        file_id = int(old_link.stem)
        
        # Determine which reference image to use (cycle through)
        source_img = reference_images[file_id % len(reference_images)]
        
        # New symlink path
        new_link = data_spherical_dir / old_link.name
        
        # Remove old symlink
        if old_link.exists() or old_link.is_symlink():
            old_link.unlink()
        
        # Create new symlink with relative path
        relative_source = os.path.relpath(source_img, new_link.parent)
        os.symlink(relative_source, new_link)
        created += 1
        
        if created % 5000 == 0:
            print(f"  Progress: {created}/{len(old_symlinks)}...")
    
    print(f"  ✓ Recreated {created} symlinks")
    
    # Clean up old directories
    print("\n🧹 Cleaning up old structure...")
    if old_spherical_dir.exists() and not any(old_spherical_dir.iterdir()):
        old_spherical_dir.rmdir()
        print("  ✓ Removed empty spherical/ dir")
    if images_source_dir.exists() and not any(images_source_dir.iterdir()):
        images_source_dir.rmdir()
        print("  ✓ Removed empty images/ dir")
    
    # Show final structure
    print("\n📊 New Structure:")
    print("track_2020/")
    print("├── resources/")
    print("│   ├── US-SANB-201020.gpkg")
    print("│   └── reference_images/")
    for ref_img in reference_images:
        print(f"│       ├── {ref_img.name}")
    print("└── data/")
    print("    ├── image_metadata.json")
    print("    └── images/")
    print("        └── spherical/")
    print(f"            └── 0.jpg -> 29614.jpg ({created} symlinks)")
    
    print("\n✅ Reorganization complete!")

if __name__ == "__main__":
    reorganize_structure()

