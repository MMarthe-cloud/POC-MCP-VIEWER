"""
Commands that the LLM can send to control the map UI
These are the "actions" the model takes to show information
"""
from pydantic import BaseModel
from typing import Literal, Optional, Any


class HighlightFeaturesCommand(BaseModel):
    """Highlight specific features on the map"""
    command: Literal["highlight_features"] = "highlight_features"
    feature_ids: list[int]
    color: str = "#FF0000"
    label: Optional[str] = None


class ShowInfoBoxCommand(BaseModel):
    """Display an information box on the map"""
    command: Literal["show_info_box"] = "show_info_box"
    title: str
    content: dict  # Key-value pairs to display
    position: Optional[dict] = None  # If None, shows in corner


class ShowStatisticsCommand(BaseModel):
    """Display statistics overlay"""
    command: Literal["show_statistics"] = "show_statistics"
    title: str
    stats: dict  # e.g. {"Total": 50, "Damaged": 5}


class ClearHighlightsCommand(BaseModel):
    """Clear all highlights"""
    command: Literal["clear_highlights"] = "clear_highlights"


class ZoomToFeaturesCommand(BaseModel):
    """Zoom map to show specific features"""
    command: Literal["zoom_to_features"] = "zoom_to_features"
    feature_ids: list[int]


class ShowHeatmapCommand(BaseModel):
    """Show density heatmap"""
    command: Literal["show_heatmap"] = "show_heatmap"
    points: list[dict]  # [{"lon": ..., "lat": ..., "weight": ...}]
    property: str  # What this heatmap represents


class AddLabelsCommand(BaseModel):
    """Add text labels to features on the map"""
    command: Literal["add_labels"] = "add_labels"
    labels: list[dict]  # [{"feature_id": ..., "text": ..., "color": ...}]


class HighlightImageCommand(BaseModel):
    """Highlight specific image positions"""
    command: Literal["highlight_image"] = "highlight_image"
    image_ids: list[int]
    color: str = "#0000FF"
    label: Optional[str] = None


class DrawCircleCommand(BaseModel):
    """Draw a circle/radius around a point"""
    command: Literal["draw_circle"] = "draw_circle"
    center: dict  # {"lon": ..., "lat": ...}
    radius_m: float  # radius in meters
    color: str = "#FF0000"
    label: Optional[str] = None


# Union type for all commands
MapCommand = (
    HighlightFeaturesCommand |
    ShowInfoBoxCommand |
    ShowStatisticsCommand |
    ClearHighlightsCommand |
    ZoomToFeaturesCommand |
    ShowHeatmapCommand |
    AddLabelsCommand |
    HighlightImageCommand |
    DrawCircleCommand
)

