"""
Generate mock features (horizontal and vertical) for the San Bernardino campaign
"""
import json
import random
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path("/home/marco/Repos/cyclomedia/detekt-product/detekt-test/mockup_data/track_2020")
METADATA_FILE = BASE_DIR / "data" / "image_metadata.json"
FEATURES_DIR = BASE_DIR / "data" / "features"
HORIZONTAL_DIR = FEATURES_DIR / "horizontal"
VERTICAL_DIR = FEATURES_DIR / "vertical"

# Feature type definitions
HORIZONTAL_TYPES = {
    "pavement_damage": {
        "subtypes": ["crack", "pothole", "spalling", "rutting"],
        "severity": ["minor", "moderate", "severe"],
        "count": 150
    },
    "road_marking": {
        "subtypes": ["crosswalk", "lane_line", "stop_line", "arrow", "text"],
        "condition": ["good", "faded", "worn", "missing"],
        "count": 200
    },
    "manhole_cover": {
        "material": ["cast_iron", "concrete", "composite"],
        "condition": ["good", "damaged", "missing"],
        "count": 80
    },
    "drainage_grate": {
        "type": ["linear", "circular", "square"],
        "condition": ["good", "damaged", "clogged"],
        "count": 60
    },
    "pavement_patch": {
        "material": ["asphalt", "concrete"],
        "age": ["recent", "aged", "deteriorated"],
        "count": 100
    }
}

VERTICAL_TYPES = {
    "traffic_sign": {
        "subtypes": ["stop_sign", "yield_sign", "speed_limit", "warning", "regulatory", "guide"],
        "condition": ["good", "faded", "damaged", "missing"],
        "count": 180
    },
    "street_light": {
        "type": ["led", "sodium", "halogen"],
        "condition": ["working", "flickering", "not_working"],
        "count": 120
    },
    "utility_pole": {
        "material": ["wood", "metal", "concrete"],
        "condition": ["good", "leaning", "damaged"],
        "count": 150
    },
    "trash_bin": {
        "type": ["public", "residential", "recycling"],
        "condition": ["good", "damaged", "overflowing"],
        "count": 70
    },
    "fire_hydrant": {
        "condition": ["good", "damaged", "obstructed"],
        "last_inspection": None,  # Will generate dates
        "count": 40
    },
    "traffic_light": {
        "type": ["standard", "pedestrian", "arrow"],
        "condition": ["working", "damaged", "not_working"],
        "count": 50
    },
    "vegetation": {
        "type": ["tree", "shrub", "overgrowth"],
        "obstruction_level": ["none", "minor", "major"],
        "count": 90
    }
}


def load_campaign_bounds():
    """Load campaign metadata to get bounds"""
    print(f"📄 Loading campaign bounds from: {METADATA_FILE}")
    with open(METADATA_FILE, 'r') as f:
        metadata = json.load(f)
    
    bounds = metadata['bounds']
    print(f"✓ Campaign bounds: ({bounds['min_lon']:.6f}, {bounds['min_lat']:.6f}) to ({bounds['max_lon']:.6f}, {bounds['max_lat']:.6f})")
    
    return bounds, metadata['image_positions']


def generate_random_point(bounds):
    """Generate a random point within bounds"""
    lon = random.uniform(bounds['min_lon'], bounds['max_lon'])
    lat = random.uniform(bounds['min_lat'], bounds['max_lat'])
    elevation = random.uniform(280, 300)  # Approximate elevation for San Bernardino
    return lon, lat, elevation


def find_nearby_images(lon, lat, image_positions, max_distance=0.0005):
    """Find images within distance of a point (rough distance in degrees)"""
    nearby = []
    for img in image_positions:
        dist = ((img['longitude'] - lon)**2 + (img['latitude'] - lat)**2)**0.5
        if dist < max_distance:
            nearby.append(img['id'])
    return nearby[:10]  # Max 10 images per feature


def generate_horizontal_features(bounds, image_positions):
    """Generate horizontal (ground-level) features"""
    print("\n" + "="*80)
    print("Generating Horizontal Features")
    print("="*80)
    
    HORIZONTAL_DIR.mkdir(parents=True, exist_ok=True)
    
    all_features = []
    feature_id = 0
    
    for feature_type, config in HORIZONTAL_TYPES.items():
        print(f"\n🔧 Generating {config['count']} {feature_type} features...")
        features = []
        
        for i in range(config['count']):
            lon, lat, elevation = generate_random_point(bounds)
            
            # Base feature data
            feature = {
                "id": feature_id,
                "feature_type": feature_type,
                "detection_type": "horizontal",
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat, elevation]
                },
                "confidence": round(random.uniform(0.75, 0.99), 3),
                "detected_by": random.choice(["AI_VISION_v2.1", "AI_VISION_v2.0", "MANUAL"]),
                "visible_in_images": find_nearby_images(lon, lat, image_positions)
            }
            
            # Add type-specific attributes
            attributes = {}
            for key, values in config.items():
                if key != 'count' and isinstance(values, list):
                    attributes[key] = random.choice(values)
            
            # Add common attributes
            if feature_type == "pavement_damage":
                attributes["area_m2"] = round(random.uniform(0.1, 2.5), 2)
                attributes["requires_repair"] = attributes.get("severity", "minor") in ["moderate", "severe"]
            
            elif feature_type == "road_marking":
                attributes["width_cm"] = random.choice([10, 15, 20, 30])
                attributes["color"] = random.choice(["white", "yellow"])
            
            elif feature_type == "manhole_cover":
                attributes["diameter_cm"] = random.choice([60, 80, 100])
                attributes["utility_type"] = random.choice(["sewer", "storm_drain", "telecom", "electric"])
            
            elif feature_type == "drainage_grate":
                attributes["width_cm"] = random.randint(30, 60)
                attributes["length_cm"] = random.randint(60, 120)
            
            elif feature_type == "pavement_patch":
                attributes["area_m2"] = round(random.uniform(1.0, 10.0), 2)
            
            feature["attributes"] = attributes
            features.append(feature)
            all_features.append(feature)
            feature_id += 1
        
        # Save to JSON file
        output_file = HORIZONTAL_DIR / f"{feature_type}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "feature_type": feature_type,
                "detection_type": "horizontal",
                "total_features": len(features),
                "features": features
            }, f, indent=2)
        
        print(f"  ✓ Saved {len(features)} features to {output_file.name}")
    
    return all_features


def generate_vertical_features(bounds, image_positions):
    """Generate vertical (above-ground) features"""
    print("\n" + "="*80)
    print("Generating Vertical Features")
    print("="*80)
    
    VERTICAL_DIR.mkdir(parents=True, exist_ok=True)
    
    all_features = []
    feature_id = 10000  # Start vertical features at 10000
    
    for feature_type, config in VERTICAL_TYPES.items():
        print(f"\n🔧 Generating {config['count']} {feature_type} features...")
        features = []
        
        for i in range(config['count']):
            lon, lat, elevation = generate_random_point(bounds)
            
            # Base feature data
            feature = {
                "id": feature_id,
                "feature_type": feature_type,
                "detection_type": "vertical",
                "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat, elevation]
                },
                "confidence": round(random.uniform(0.80, 0.99), 3),
                "detected_by": random.choice(["AI_VISION_v2.1", "AI_LIDAR_v1.5", "MANUAL"]),
                "visible_in_images": find_nearby_images(lon, lat, image_positions)
            }
            
            # Add type-specific attributes
            attributes = {}
            for key, values in config.items():
                if key != 'count' and isinstance(values, list):
                    attributes[key] = random.choice(values)
            
            # Add common attributes
            attributes["height_m"] = round(random.uniform(1.5, 8.0), 2)
            
            if feature_type == "traffic_sign":
                if attributes.get("subtypes") == "speed_limit":
                    attributes["speed_limit_mph"] = random.choice([25, 35, 45, 55, 65])
                attributes["retroreflectivity"] = round(random.uniform(50, 300), 1)
            
            elif feature_type == "street_light":
                attributes["power_watts"] = random.choice([100, 150, 250, 400])
                attributes["last_maintenance"] = (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
            
            elif feature_type == "utility_pole":
                attributes["pole_number"] = f"P{random.randint(1000, 9999)}"
                attributes["has_transformer"] = random.choice([True, False])
            
            elif feature_type == "fire_hydrant":
                attributes["last_inspection"] = (datetime.now() - timedelta(days=random.randint(90, 730))).isoformat()
                attributes["flow_gpm"] = random.choice([1000, 1500, 2000, 2500])
                attributes["color"] = random.choice(["red", "yellow", "orange"])
            
            elif feature_type == "traffic_light":
                attributes["num_heads"] = random.choice([1, 2, 3, 4])
                attributes["has_camera"] = random.choice([True, False])
            
            elif feature_type == "vegetation":
                attributes["requires_trimming"] = attributes.get("obstruction_level") in ["minor", "major"]
            
            feature["attributes"] = attributes
            features.append(feature)
            all_features.append(feature)
            feature_id += 1
        
        # Save to JSON file
        output_file = VERTICAL_DIR / f"{feature_type}.json"
        with open(output_file, 'w') as f:
            json.dump({
                "feature_type": feature_type,
                "detection_type": "vertical",
                "total_features": len(features),
                "features": features
            }, f, indent=2)
        
        print(f"  ✓ Saved {len(features)} features to {output_file.name}")
    
    return all_features


def create_summary(horizontal_features, vertical_features):
    """Create a summary of all features"""
    print("\n" + "="*80)
    print("Creating Feature Summary")
    print("="*80)
    
    summary = {
        "campaign_id": "US-SANB-201020",
        "generated_at": datetime.now().isoformat(),
        "total_features": len(horizontal_features) + len(vertical_features),
        "horizontal_features": {
            "total": len(horizontal_features),
            "by_type": {}
        },
        "vertical_features": {
            "total": len(vertical_features),
            "by_type": {}
        }
    }
    
    # Count by type
    for feature in horizontal_features:
        ftype = feature['feature_type']
        summary['horizontal_features']['by_type'][ftype] = summary['horizontal_features']['by_type'].get(ftype, 0) + 1
    
    for feature in vertical_features:
        ftype = feature['feature_type']
        summary['vertical_features']['by_type'][ftype] = summary['vertical_features']['by_type'].get(ftype, 0) + 1
    
    # Save summary
    summary_file = FEATURES_DIR / "features_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n✓ Summary saved to: {summary_file}")
    print(f"\n📊 Feature Statistics:")
    print(f"  Horizontal Features: {summary['horizontal_features']['total']}")
    for ftype, count in summary['horizontal_features']['by_type'].items():
        print(f"    - {ftype}: {count}")
    print(f"\n  Vertical Features: {summary['vertical_features']['total']}")
    for ftype, count in summary['vertical_features']['by_type'].items():
        print(f"    - {ftype}: {count}")
    print(f"\n  Total Features: {summary['total_features']}")


def main():
    """Generate all mock features"""
    random.seed(42)  # For reproducibility
    
    print("="*80)
    print("Mock Feature Generator")
    print("="*80)
    
    # Load campaign bounds
    bounds, image_positions = load_campaign_bounds()
    
    # Sample image positions for faster processing (use every 10th)
    sampled_images = image_positions[::10]
    print(f"✓ Using {len(sampled_images)} sampled image positions for visibility checks")
    
    # Generate features
    horizontal_features = generate_horizontal_features(bounds, sampled_images)
    vertical_features = generate_vertical_features(bounds, sampled_images)
    
    # Create summary
    create_summary(horizontal_features, vertical_features)
    
    print("\n" + "="*80)
    print("✅ Feature Generation Complete!")
    print("="*80)


if __name__ == "__main__":
    main()

