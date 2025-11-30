"""
Core domain models for mobile mapping data
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class Feature(BaseModel):
    """A detected object in the campaign (sign, marking, guardrail, etc.)"""
    id: int
    type: Literal[
        # Horizontal features
        "pavement_damage", "road_marking", "manhole_cover", "drainage_grate", "pavement_patch",
        # Vertical features  
        "traffic_sign", "street_light", "utility_pole", "trash_bin", "fire_hydrant", 
        "traffic_light", "vegetation"
    ]
    condition: Literal["good", "fair", "poor", "damaged"]
    confidence: float = 0.85  # Detection confidence (0-1)
    geometry: dict  # GeoJSON point
    attributes: dict  # Type-specific attributes
    image_ids: list[int]  # Images where this feature appears
    
    @property
    def display_name(self) -> str:
        return f"{self.type.replace('_', ' ').title()} #{self.id}"


class ImagePosition(BaseModel):
    """A camera position in the campaign"""
    id: int
    timestamp: datetime
    camera_id: str
    geometry: dict  # GeoJSON point (lon, lat)
    heading: float  # degrees
    feature_ids: list[int]  # Visible features from this position


class Campaign(BaseModel):
    """A mobile mapping campaign"""
    id: str
    name: str
    features: list[Feature]
    images: list[ImagePosition]
    
    @property
    def total_features(self) -> int:
        return len(self.features)
    
    @property
    def total_images(self) -> int:
        return len(self.images)

