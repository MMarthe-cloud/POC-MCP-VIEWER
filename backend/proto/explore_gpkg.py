"""
Explore GeoPackage to understand its structure
"""
import geopandas as gpd
import fiona
from pathlib import Path

GPKG_PATH = Path("/home/marco/Repos/cyclomedia/detekt-product/detekt-test/mockup_data/track_2020/US-SANB-201020.gpkg")

def explore_geopackage():
    """Read and explore the GeoPackage structure"""
    
    print("=" * 80)
    print(f"Exploring GeoPackage: {GPKG_PATH}")
    print("=" * 80)
    
    # List all layers in the GeoPackage
    print("\n📦 LAYERS IN GEOPACKAGE:")
    layers = fiona.listlayers(str(GPKG_PATH))
    for i, layer in enumerate(layers, 1):
        print(f"  {i}. {layer}")
    
    # Read each layer and show info
    for layer_name in layers:
        print(f"\n{'='*80}")
        print(f"LAYER: {layer_name}")
        print('='*80)
        
        gdf = gpd.read_file(GPKG_PATH, layer=layer_name)
        
        print(f"\n📊 Basic Info:")
        print(f"  - Total records: {len(gdf)}")
        print(f"  - Geometry type: {gdf.geometry.type.unique()}")
        print(f"  - CRS: {gdf.crs}")
        
        print(f"\n📋 Columns ({len(gdf.columns)}):")
        for col in gdf.columns:
            dtype = gdf[col].dtype
            non_null = gdf[col].notna().sum()
            print(f"  - {col}: {dtype} ({non_null}/{len(gdf)} non-null)")
        
        print(f"\n🔍 Sample Data (first 3 rows):")
        # Show first few rows without geometry (geometry is usually long)
        sample_cols = [col for col in gdf.columns if col != 'geometry']
        print(gdf[sample_cols].head(3).to_string())
        
        print(f"\n📍 Geometry Bounds:")
        bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
        center_x = (bounds[0] + bounds[2]) / 2
        center_y = (bounds[1] + bounds[3]) / 2
        print(f"  - Min X: {bounds[0]:.6f}")
        print(f"  - Min Y: {bounds[1]:.6f}")
        print(f"  - Max X: {bounds[2]:.6f}")
        print(f"  - Max Y: {bounds[3]:.6f}")
        print(f"  - Center: ({center_x:.6f}, {center_y:.6f})")
        
        # Show unique values for interesting columns
        interesting_cols = ['camera_id', 'camera_type', 'recording_id', 'session_id', 'type', 'feature_type']
        for col in interesting_cols:
            if col in gdf.columns:
                unique_vals = gdf[col].unique()
                print(f"\n🔑 Unique values in '{col}': {len(unique_vals)}")
                if len(unique_vals) <= 10:
                    print(f"    Values: {list(unique_vals)}")
                else:
                    print(f"    Sample: {list(unique_vals[:10])}...")

if __name__ == "__main__":
    explore_geopackage()

