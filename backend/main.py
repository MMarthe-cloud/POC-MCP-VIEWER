"""
FastAPI backend for mobile mapping viewer
"""
import os
import math
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from typing import List, Optional
from agent_service import MappingAgent
from service import MappingService
from rio_tiler.io import Reader
from rio_tiler.models import ImageData
import numpy as np

# Load .env from project root
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Mobile Mapping Viewer API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent (in production, would be per-session)
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY environment variable not set")

agent = MappingAgent(GROQ_API_KEY)

# COG file path (use symlinked version from mockup data)
COG_PATH = Path(__file__).parent.parent / "mockup_data" / "track_2020" / "data" / "images" / "ortho" / "san_bernardino_201020.tif"

class AskRequest(BaseModel):
    question: str


@app.get("/")
def read_root():
    return {"status": "ok", "service": "mobile-mapping-viewer"}


@app.get("/campaign")
def get_campaign():
    """Get the current campaign data"""
    campaign = MappingService.get_campaign()
    return campaign.model_dump()


@app.post("/ask")
def ask_question(request: AskRequest):
    """
    Ask a question to the AI agent
    Returns: answer text + map commands to execute
    """
    try:
        result = agent.ask(request.question)
        return result
    except Exception as e:
        import traceback
        print(f"Error in ask_question: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
def clear_conversation():
    """Clear conversation history"""
    agent.clear_history()
    return {"status": "cleared"}


@app.get("/cog/info")
def get_cog_info():
    """Get COG metadata (bounds, center, etc.)"""
    if not COG_PATH.exists():
        raise HTTPException(status_code=404, detail=f"COG file not found: {COG_PATH}")
    
    try:
        with Reader(str(COG_PATH)) as cog:
            info = cog.info()
            
            # Get geographic bounds (WGS84) using the reader's dataset
            # cog.bounds returns native CRS, we need to transform to EPSG:4326
            from rasterio.warp import transform_bounds
            
            # Get bounds in native CRS
            native_bounds = cog.dataset.bounds
            native_crs = cog.dataset.crs
            
            # Transform to WGS84 (EPSG:4326)
            wgs84_bounds = transform_bounds(
                native_crs,
                'EPSG:4326',
                native_bounds.left,
                native_bounds.bottom,
                native_bounds.right,
                native_bounds.top
            )
            
            # Calculate center
            center = [(wgs84_bounds[0] + wgs84_bounds[2]) / 2, (wgs84_bounds[1] + wgs84_bounds[3]) / 2]
            
            return {
                "bounds": list(wgs84_bounds),  # [minx, miny, maxx, maxy] in WGS84
                "center": center,  # [lon, lat]
                "width": info.width,
                "height": info.height,
                "minzoom": 0,
                "maxzoom": 22,
                "band_count": info.count
            }
    except Exception as e:
        import traceback
        print(f"Error reading COG: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error reading COG: {str(e)}")


@app.get("/cog/tiles/{z}/{x}/{y}.png")
def get_cog_tile(z: int, x: int, y: int):
    """Serve COG tiles in XYZ format"""
    if not COG_PATH.exists():
        raise HTTPException(status_code=404, detail="COG file not found")
    
    try:
        with Reader(str(COG_PATH)) as cog:
            # Read the tile
            img = cog.tile(x, y, z)
            
            # Convert to PNG
            png_data = img.render(img_format="PNG")
            
            return Response(content=png_data, media_type="image/png")
    except Exception as e:
        # Return transparent tile if error (tile might be outside bounds)
        # Create a 256x256 transparent PNG
        from io import BytesIO
        from PIL import Image
        img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
        buf = BytesIO()
        img.save(buf, format='PNG')
        return Response(content=buf.getvalue(), media_type="image/png")


@app.get("/images/{image_id}")
def get_image(image_id: int):
    """Serve 360° spherical images"""
    image_path = Path(__file__).parent.parent / "mockup_data" / "track_2020" / "data" / "images" / "spherical" / f"{image_id}.png"
    
    if not image_path.exists():
        raise HTTPException(status_code=404, detail=f"Image not found: {image_id}")
    
    # Detect actual image type by checking magic bytes (file could be PNG despite .jpg extension)
    with open(image_path, 'rb') as f:
        header = f.read(8)
        if header.startswith(b'\x89PNG'):
            mime_type = "image/png"
        elif header.startswith(b'\xff\xd8\xff'):
            mime_type = "image/jpeg"
        else:
            mime_type = "application/octet-stream"
    
    return FileResponse(
        image_path, 
        media_type=mime_type,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )


@app.get("/krpano/pano.xml")
def get_krpano_xml(image_url: str):
    """Generate Krpano XML configuration for a spherical image"""
    from fastapi.responses import Response
    
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<krpano version="1.23.3">
    <image type="sphere">
        <sphere url="{image_url}" />
    </image>
    
    <view hlookat="0" vlookat="0" fovtype="VFOV" fov="90" fovmin="30" fovmax="150" />
    
    <control mouse="drag" mousespeed="8.0" />
    
    <display tessmode="auto" />
</krpano>
"""
    
    return Response(
        content=xml_content,
        media_type="text/xml",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )


@app.get("/nearby/images")
def get_nearby_images(
    image_id: int,
    max_distance: float = Query(50.0, description="Maximum distance in meters")
):
    """
    Get nearby images within a specified distance from the given image.
    Returns image metadata with bearing and distance.
    """
    try:
        campaign = agent.campaign
        
        # Find the source image
        source_image = None
        for img in campaign.images:
            if img.id == image_id:
                source_image = img
                break
        
        if not source_image:
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
        
        # Source camera position
        src_coords = source_image.geometry['coordinates']
        src_lon = src_coords[0]
        src_lat = src_coords[1]
        
        nearby = []
        
        for img in campaign.images:
            if img.id == image_id:
                continue  # Skip self
            
            # Target camera position
            tgt_coords = img.geometry['coordinates']
            tgt_lon = tgt_coords[0]
            tgt_lat = tgt_coords[1]
            
            # Calculate bearing and distance
            dlon = math.radians(tgt_lon - src_lon)
            lat1 = math.radians(src_lat)
            lat2 = math.radians(tgt_lat)
            
            y = math.sin(dlon) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
            bearing = math.degrees(math.atan2(y, x))
            bearing = (bearing + 360) % 360
            
            # Distance (haversine)
            dlat = lat2 - lat1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = 6371000 * c
            
            if distance <= max_distance and distance > 0:
                nearby.append({
                    "image_id": img.id,
                    "bearing": bearing,
                    "distance": round(distance, 2),
                    "timestamp": img.timestamp.isoformat()
                })
        
        # Sort by distance
        nearby.sort(key=lambda x: x['distance'])
        
        return {"nearby_images": nearby}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding nearby images: {str(e)}")


@app.get("/project/features")
def project_features(
    image_id: int,
    feature_ids: str = Query("", description="Comma-separated feature IDs")
):
    """
    Project features onto a 360° image sphere based on camera position.
    Returns hotspot data (azimuth, elevation) for each feature.
    """
    try:
        campaign = agent.campaign
        
        # Find the image
        image = None
        for img in campaign.images:
            if img.id == image_id:
                image = img
                break
        
        if not image:
            raise HTTPException(status_code=404, detail=f"Image {image_id} not found")
        
        # Parse feature IDs
        if not feature_ids:
            return {"hotspots": []}
        
        feature_id_list = [int(fid.strip()) for fid in feature_ids.split(",") if fid.strip()]
        
        # Camera position (WGS84)
        cam_coords = image.geometry['coordinates']
        cam_lon = cam_coords[0]
        cam_lat = cam_coords[1]
        cam_elev = cam_coords[2] if len(cam_coords) > 2 else 0
        
        hotspots = []
        
        # Find requested features
        for feature in campaign.features:
            if feature.id not in feature_id_list:
                continue
            
            # Feature position (WGS84)
            feat_coords = feature.geometry['coordinates']
            feat_lon = feat_coords[0]
            feat_lat = feat_coords[1]
            feat_elev = feat_coords[2] if len(feat_coords) > 2 else 0
            
            # Calculate bearing (azimuth) from camera to feature
            dlon = math.radians(feat_lon - cam_lon)
            lat1 = math.radians(cam_lat)
            lat2 = math.radians(feat_lat)
            
            y = math.sin(dlon) * math.cos(lat2)
            x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
            azimuth = math.degrees(math.atan2(y, x))
            
            # Normalize azimuth to 0-360
            azimuth = (azimuth + 360) % 360
            
            # Calculate distance (haversine formula)
            dlat = lat2 - lat1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            c = 2 * math.asin(math.sqrt(a))
            distance = 6371000 * c  # Earth radius in meters
            
            # Calculate elevation angle with feature-type adjustments
            delev = feat_elev - cam_elev
            base_elevation_angle = math.degrees(math.atan2(delev, distance))
            
            # Adjust elevation based on feature type (camera is ~1.5m high)
            # Horizontal features: on the ground, look down
            # Vertical features: at various heights, look straight or up
            if feature.type in ['pavement_damage', 'pavement_patch', 'road_marking', 
                                'crosswalk', 'manhole_cover', 'drainage_grate']:
                # Horizontal features: assume on ground, look down (-10 to -30 degrees)
                elevation_angle = base_elevation_angle - 15  # Look down at ground
            elif feature.type in ['traffic_sign', 'stop_sign', 'speed_limit']:
                # Signs: typically 2-3m high, slight upward angle
                elevation_angle = base_elevation_angle + 5
            elif feature.type in ['traffic_light', 'street_light']:
                # Lights: high up, look up more
                elevation_angle = base_elevation_angle + 15
            elif feature.type in ['utility_pole', 'fire_hydrant', 'trash_bin']:
                # Mid-height objects, roughly eye level
                elevation_angle = base_elevation_angle
            else:
                # Default: use calculated angle
                elevation_angle = base_elevation_angle
            
            # Skip if feature is too far (e.g., > 100m)
            if distance > 100:
                continue
            
            hotspots.append({
                "feature_id": feature.id,
                "feature_type": feature.type,
                "hlookat": azimuth,  # Krpano horizontal angle (0-360)
                "vlookat": elevation_angle,  # Krpano vertical angle (-90 to 90)
                "distance": round(distance, 2),
                "confidence": feature.confidence,
                "condition": feature.condition
            })
        
        return {"hotspots": hotspots}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error projecting features: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

