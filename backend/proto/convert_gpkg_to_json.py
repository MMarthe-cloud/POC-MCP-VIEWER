"""
Convert GeoPackage imagery positions to JSON metadata
and create symlinks for images
"""
import json
import geopandas as gpd
from pathlib import Path
from datetime import datetime
import os

GPKG_PATH = Path("/home/marco/Repos/cyclomedia/detekt-product/detekt-test/mockup_data/track_2020/US-SANB-201020.gpkg")
OUTPUT_JSON = Path("/home/marco/Repos/cyclomedia/detekt-product/detekt-test/mockup_data/track_2020/image_metadata.json")
IMAGES_DIR = Path("/home/marco/Repos/cyclomedia/detekt-product/detekt-test/mockup_data/track_2020/images")
SPHERICAL_DIR = IMAGES_DIR / "spherical"

# Source images to cycle through
SOURCE_IMAGES = [
    IMAGES_DIR / "frame1.png",
    IMAGES_DIR / "frame2.png",
    IMAGES_DIR / "frame3.png",
    IMAGES_DIR / "frame4.png"
]

def convert_geopackage_to_json():
    """Convert GeoPackage to JSON metadata for image positions"""
    
    print("=" * 80)
    print("Converting GeoPackage to JSON Metadata")
    print("=" * 80)
    
    # Read the GeoPackage
    print(f"\n📦 Reading GeoPackage: {GPKG_PATH}")
    gdf = gpd.read_file(GPKG_PATH, layer='imagery_positions')
    print(f"✓ Loaded {len(gdf)} image positions")
    
    # Convert from UTM (EPSG:32611) to WGS84 (EPSG:4326) for lat/lon
    print(f"\n🌍 Converting coordinates from {gdf.crs} to EPSG:4326 (WGS84)")
    gdf_wgs84 = gdf.to_crs('EPSG:4326')
    print(f"✓ Converted to lat/lon coordinates")
    
    # Create output structure
    image_positions = []
    
    print(f"\n🔄 Processing {len(gdf_wgs84)} positions...")
    for idx, row in gdf_wgs84.iterrows():
        # Get lon, lat from geometry
        lon = row.geometry.x
        lat = row.geometry.y
        elevation = row['z']
        
        # Convert timestamp from milliseconds to ISO format
        timestamp_ms = row['timestamp']
        timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
        
        # Create image position object
        position = {
            "id": int(idx),
            "image_path": row['image_path'],
            "frame": int(row['frame']),
            "timestamp": timestamp_dt.isoformat(),
            "timestamp_ms": int(timestamp_ms),
            
            # Position (WGS84)
            "longitude": float(lon),
            "latitude": float(lat),
            "elevation": float(elevation),
            
            # Camera info
            "camera_name": row['camera_name'],
            "camera_model": row['camera_model'],
            "camera_type": "360_spherical",  # Ladybug 8 is 360° camera
            
            # Image properties
            "width": int(row['width']),
            "height": int(row['height']),
            
            # Recording info
            "track_name": row['track_name'],
            "dataset_name": row['dataset_name'],
            
            # UTM coordinates (keep for reference)
            "utm_x": float(row['x']),
            "utm_y": float(row['y']),
            "utm_zone": "11N",
            "crs": "EPSG:32611"
        }
        
        image_positions.append(position)
        
        if (idx + 1) % 5000 == 0:
            print(f"  Processed {idx + 1}/{len(gdf_wgs84)}...")
    
    # Create metadata structure
    metadata = {
        "campaign": {
            "id": "US-SANB-201020",
            "name": "San Bernardino 2020-10",
            "description": "Mobile mapping campaign in San Bernardino, California",
            "location": "San Bernardino, CA, USA",
            "date": "2020-10-20",
            "track_name": gdf.iloc[0]['track_name'],
            "dataset_name": gdf.iloc[0]['dataset_name']
        },
        "bounds": {
            "min_lon": float(gdf_wgs84.total_bounds[0]),
            "min_lat": float(gdf_wgs84.total_bounds[1]),
            "max_lon": float(gdf_wgs84.total_bounds[2]),
            "max_lat": float(gdf_wgs84.total_bounds[3]),
            "center_lon": float((gdf_wgs84.total_bounds[0] + gdf_wgs84.total_bounds[2]) / 2),
            "center_lat": float((gdf_wgs84.total_bounds[1] + gdf_wgs84.total_bounds[3]) / 2)
        },
        "camera": {
            "model": gdf.iloc[0]['camera_model'],
            "type": "360_spherical",
            "width": int(gdf.iloc[0]['width']),
            "height": int(gdf.iloc[0]['height'])
        },
        "total_images": len(image_positions),
        "image_positions": image_positions
    }
    
    # Save to JSON
    print(f"\n💾 Saving metadata to: {OUTPUT_JSON}")
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Metadata saved! ({len(image_positions)} positions)")
    
    # Print summary
    print(f"\n📊 Summary:")
    print(f"  - Campaign: {metadata['campaign']['name']}")
    print(f"  - Total Images: {metadata['total_images']}")
    print(f"  - Bounds: ({metadata['bounds']['min_lon']:.6f}, {metadata['bounds']['min_lat']:.6f}) to ({metadata['bounds']['max_lon']:.6f}, {metadata['bounds']['max_lat']:.6f})")
    print(f"  - Center: ({metadata['bounds']['center_lon']:.6f}, {metadata['bounds']['center_lat']:.6f})")
    
    return metadata


def create_image_symlinks(metadata):
    """Create symlinks for images, cycling through the 4 source images"""
    
    print("\n" + "=" * 80)
    print("Creating Image Symlinks")
    print("=" * 80)
    
    # Verify source images exist
    print(f"\n🔍 Checking source images...")
    available_sources = []
    for img in SOURCE_IMAGES:
        if img.exists():
            print(f"  ✓ {img.name} exists")
            available_sources.append(img)
        else:
            print(f"  ✗ {img.name} NOT FOUND")
    
    if not available_sources:
        print("❌ No source images found! Cannot create symlinks.")
        return
    
    print(f"\n✓ Found {len(available_sources)} source images to cycle through")
    
    # Create spherical directory
    SPHERICAL_DIR.mkdir(parents=True, exist_ok=True)
    print(f"\n📁 Created directory: {SPHERICAL_DIR}")
    
    # Create symlinks
    print(f"\n🔗 Creating symlinks for {metadata['total_images']} images...")
    created = 0
    skipped = 0
    
    for position in metadata['image_positions']:
        # Target symlink path (e.g., images/spherical/0.jpg)
        target_path = IMAGES_DIR / position['image_path']
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Cycle through source images
        source_image = available_sources[position['id'] % len(available_sources)]
        
        # Create symlink
        if target_path.exists() or target_path.is_symlink():
            skipped += 1
        else:
            # Create relative symlink
            relative_source = os.path.relpath(source_image, target_path.parent)
            os.symlink(relative_source, target_path)
            created += 1
        
        if (created + skipped) % 5000 == 0:
            print(f"  Progress: {created + skipped}/{metadata['total_images']}...")
    
    print(f"\n✅ Symlinks created!")
    print(f"  - Created: {created}")
    print(f"  - Skipped (already exist): {skipped}")
    print(f"  - Total: {created + skipped}")


if __name__ == "__main__":
    # Convert GeoPackage to JSON
    metadata = convert_geopackage_to_json()
    
    # Create symlinks
    create_image_symlinks(metadata)
    
    print("\n" + "=" * 80)
    print("✅ COMPLETE!")
    print("=" * 80)

