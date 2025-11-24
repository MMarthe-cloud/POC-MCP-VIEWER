"""
Data service - provides mock campaign data
In production, this would fetch from database/files
"""
import random
from datetime import datetime, timedelta
from models.domain import Feature, ImagePosition, Campaign


class MappingService:
    """Mock data service for testing"""
    
    # Vienna center
    BASE_LAT = 48.2082
    BASE_LON = 16.3738
    
    # Cache the campaign
    _cached_campaign = None
    
    @staticmethod
    def generate_mock_campaign() -> Campaign:
        """Generate a mock campaign with random features and images"""
        
        # Generate features
        features = []
        feature_types = ["stop_sign", "speed_limit", "crosswalk", "guardrail", "pole"]
        conditions = ["good", "fair", "poor", "damaged"]
        
        for i in range(50):
            # Random position near Vienna
            lat = MappingService.BASE_LAT + random.uniform(-0.05, 0.05)
            lon = MappingService.BASE_LON + random.uniform(-0.05, 0.05)
            
            feature_type = random.choice(feature_types)
            
            # Type-specific attributes
            attributes = {}
            if feature_type == "speed_limit":
                attributes["speed"] = random.choice([30, 50, 70, 100])
            elif feature_type == "crosswalk":
                attributes["width_m"] = round(random.uniform(2.5, 4.0), 2)
            
            features.append(Feature(
                id=i,
                type=feature_type,
                condition=random.choice(conditions),
                geometry={"type": "Point", "coordinates": [lon, lat]},
                attributes=attributes,
                image_ids=[]  # Will be filled later
            ))
        
        # Generate image positions
        images = []
        base_time = datetime.now() - timedelta(days=30)
        
        for i in range(20):
            lat = MappingService.BASE_LAT + random.uniform(-0.05, 0.05)
            lon = MappingService.BASE_LON + random.uniform(-0.05, 0.05)
            
            # Find nearby features (within ~500m)
            nearby_feature_ids = [
                f.id for f in features
                if abs(f.geometry["coordinates"][0] - lon) < 0.005
                and abs(f.geometry["coordinates"][1] - lat) < 0.005
            ]
            
            images.append(ImagePosition(
                id=i,
                timestamp=base_time + timedelta(minutes=i * 10),
                camera_id=f"CAM_{i % 3 + 1}",
                geometry={"type": "Point", "coordinates": [lon, lat]},
                heading=random.uniform(0, 360),
                feature_ids=nearby_feature_ids
            ))
        
        # Link features to images
        for img in images:
            for feature_id in img.feature_ids:
                if feature_id < len(features):
                    features[feature_id].image_ids.append(img.id)
        
        return Campaign(
            id="vienna_2024",
            name="Vienna Campaign 2024",
            features=features,
            images=images
        )
    
    @staticmethod
    def get_campaign() -> Campaign:
        """Get the mock campaign (cached so data is consistent)"""
        if MappingService._cached_campaign is None:
            # Use fixed seed for consistent data
            random.seed(42)
            MappingService._cached_campaign = MappingService.generate_mock_campaign()
        return MappingService._cached_campaign

