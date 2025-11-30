import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List
from models.domain import Feature, ImagePosition, Campaign


class MappingService:
    
    MOCKUP_BASE: Path = Path(__file__).parent.parent / "mockup_data" / "track_2020" / "data"
    IMAGE_METADATA: Path = MOCKUP_BASE / "image_metadata.json"
    FEATURES_DIR: Path = MOCKUP_BASE / "features"
    
    _cached_campaign: Optional[Campaign] = None
    
    @staticmethod
    def load_real_campaign() -> Campaign:
        
        print(f"📦 Loading campaign data from: {MappingService.MOCKUP_BASE}")
        
        print(f"  Loading images from: {MappingService.IMAGE_METADATA}")
        with open(MappingService.IMAGE_METADATA, 'r') as f:
            image_data: Dict[str, Any] = json.load(f)
        
        images: List[ImagePosition] = []
        for img_pos in image_data['image_positions'][::100]:
            images.append(ImagePosition(
                id=img_pos['id'],
                timestamp=datetime.fromisoformat(img_pos['timestamp']),
                camera_id=img_pos['camera_name'],
                geometry={
                    "type": "Point",
                    "coordinates": [img_pos['longitude'], img_pos['latitude']]
                },
                heading=0.0,
                feature_ids=img_pos.get('visible_in_images', [])
            ))
        
        print(f"  ✓ Loaded {len(images)} image positions (subsampled from {len(image_data['image_positions'])})")
        
        features: List[Feature] = []
        
        horizontal_dir: Path = MappingService.FEATURES_DIR / "horizontal"
        if horizontal_dir.exists():
            for feature_file in horizontal_dir.glob("*.json"):
                if feature_file.name == "features_summary.json":
                    continue
                
                with open(feature_file, 'r') as f:
                    feature_data: Dict[str, Any] = json.load(f)
                
                for feat in feature_data['features']:
                    feature_type: str = feat['feature_type']
                    condition: str = _map_condition(feat)
                    
                    features.append(Feature(
                        id=feat['id'],
                        type=feature_type,
                        condition=condition,
                        confidence=feat.get('confidence', 0.85),
                        geometry=feat['geometry'],
                        attributes=feat.get('attributes', {}),
                        image_ids=feat.get('visible_in_images', [])
                    ))
                
                print(f"  ✓ Loaded {len(feature_data['features'])} {feature_data['feature_type']} features")
        
        vertical_dir: Path = MappingService.FEATURES_DIR / "vertical"
        if vertical_dir.exists():
            for feature_file in vertical_dir.glob("*.json"):
                if feature_file.name == "features_summary.json":
                    continue
                
                with open(feature_file, 'r') as f:
                    feature_data: Dict[str, Any] = json.load(f)
                
                for feat in feature_data['features']:
                    feature_type: str = feat['feature_type']
                    condition: str = _map_condition(feat)
                    
                    features.append(Feature(
                        id=feat['id'],
                        type=feature_type,
                        condition=condition,
                        confidence=feat.get('confidence', 0.85),
                        geometry=feat['geometry'],
                        attributes=feat.get('attributes', {}),
                        image_ids=feat.get('visible_in_images', [])
                    ))
                
                print(f"  ✓ Loaded {len(feature_data['features'])} {feature_data['feature_type']} features")
        
        print(f"  ✓ Total features loaded: {len(features)}")
        
        campaign: Campaign = Campaign(
            id=image_data['campaign']['id'],
            name=image_data['campaign']['name'],
            features=features,
            images=images
        )
        
        print(f"✅ Campaign loaded: {campaign.name}")
        print(f"   - {campaign.total_features} features")
        print(f"   - {campaign.total_images} image positions")
        
        return campaign
    
    @staticmethod
    def get_campaign() -> Campaign:
        if MappingService._cached_campaign is None:
            MappingService._cached_campaign = MappingService.load_real_campaign()
        return MappingService._cached_campaign


def _map_condition(feature: Dict[str, Any]) -> str:
    attributes: Dict[str, Any] = feature.get('attributes', {})
    
    if 'condition' in attributes:
        cond: str = attributes['condition'].lower()
        if cond in ['good', 'fair', 'poor', 'damaged']:
            return cond
    
    if 'severity' in attributes:
        severity_map: Dict[str, str] = {"minor": "fair", "moderate": "poor", "severe": "damaged"}
        return severity_map.get(attributes['severity'], "fair")
    
    confidence: float = feature.get('confidence', 0.9)
    if confidence > 0.95:
        return "good"
    elif confidence > 0.85:
        return "fair"
    else:
        return "poor"
