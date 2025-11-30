# Changes Summary

## Data Structure Created

### Mockup Data Location
`mockup_data/track_2020/`

```
track_2020/
├── resources/                          # Source data (immutable)
│   ├── US-SANB-201020.gpkg            # Original GeoPackage (29,615 positions)
│   └── reference_images/               # 4 reference frames (261MB)
│
└── data/                               # Generated/processed data
    ├── image_metadata.json             # 29,615 image positions (18MB)
    ├── features/
    │   ├── horizontal/                 # 590 ground features
    │   │   ├── pavement_damage.json    # 150 features
    │   │   ├── road_marking.json       # 200 features
    │   │   ├── manhole_cover.json      # 80 features
    │   │   ├── drainage_grate.json     # 60 features
    │   │   └── pavement_patch.json     # 100 features
    │   └── vertical/                   # 700 above-ground features
    │       ├── traffic_sign.json       # 180 features
    │       ├── street_light.json       # 120 features
    │       ├── utility_pole.json       # 150 features
    │       ├── trash_bin.json          # 70 features
    │       ├── fire_hydrant.json       # 40 features
    │       ├── traffic_light.json      # 50 features
    │       └── vegetation.json         # 90 features
    └── images/
        ├── ortho/
        │   └── san_bernardino_201020.tif  # COG symlink
        └── spherical/                      # 29,615 image symlinks
```

## Backend Changes

### Files Updated
- `backend/service.py` - Now loads real data from JSON files
  - Loads 1,290 features (horizontal + vertical)
  - Loads 297 image positions (subsampled from 29,615)
  - Maps feature types to existing model

- `backend/main.py` - Updated COG tile serving
  - Fixed COG info endpoint (bounds API)
  - Updated COG path to use symlinked file

### Utility Scripts Moved to `backend/proto/`
- `explore_gpkg.py` - GeoPackage exploration
- `convert_gpkg_to_json.py` - GeoPackage to JSON converter
- `generate_mock_features.py` - Feature generator
- `reorganize_structure.py` - Folder restructuring
- `recreate_symlinks.py` - Symlink recreation
- `test_load_data.py` - Data loading test

## Frontend Changes

### Map Styles Updated
Map styles now in order:
1. **Dark** 🌙 (default) - Dark basemap
2. **Satellite** 🛰️ - Satellite imagery
3. **Orthophoto** 🚗 - COG orthophoto (mobile mapping car icon)
4. **Streets** 🗺️ - Street map

### Default Location
- Changed from Vienna to San Bernardino, CA
- Center: -117.491325, 34.108351
- Zoom: 13

### Bug Fixes
- Fixed map style switching - proper cleanup of sources/layers
- Fixed COG tile loading

## Campaign Data

**San Bernardino 2020-10 Campaign**
- Location: San Bernardino, California
- Bounds: (-117.52°, 34.07°) to (-117.46°, 34.15°)
- 1,290 detected features
- 29,615 image positions (297 shown on map for performance)
- Ladybug 8 360° spherical camera
- Date: September 4, 2020

## Space Savings
- Using symlinks for images: **~260GB saved**
- Only 4 reference images (261MB) vs 29,615 full images

## Icon System Update (Latest)

### Visual Representation

#### Camera Positions (Images)
- **Unselected**: White circle with blue border (⚪🔵)
  - Radius: 7px
  - Clickable (cursor changes to pointer)
  - TODO: Opens image viewer on click

- **Selected**: Gold circle with white border (🟡⚪)
  - Radius: 14px
  - Color: Gold (#FFD700)
  - More prominent when highlighted

#### Features
- **Unselected**: Gray circle (general feature icon)
  - Color: #666666
  - Radius: 5px
  - Subtle presence on map

- **Selected/Highlighted**: Smart icon system
  - Radius: 12px (larger)
  - White border for contrast
  - **Smart Coloring** - Automatic color by type:
    - Pavement damage: Red (#E74C3C)
    - Road marking: Orange (#F39C12)
    - Manhole cover: Gray (#7F8C8D)
    - Drainage grate: Blue (#3498DB)
    - Traffic sign: Orange (#E67E22)
    - Traffic light: Green (#27AE60)
    - Street light: Yellow (#F1C40F)
    - Utility pole: Purple (#8E44AD)
    - Fire hydrant: Dark red (#C0392B)
    - Vegetation: Bright green (#2ECC71)
    - ... and more!

### Updated Help Panel

**New Feature Types Listed:**
- **Horizontal (Ground)**: pavement damage, road markings, manhole covers, drainage grates, pavement patches
- **Vertical (Above Ground)**: traffic signs, traffic lights, street lights, utility poles, trash bins, fire hydrants, vegetation

**Example Questions Updated:**
- "show me all traffic signs"
- "find damaged pavement"
- "show all manhole covers"
- "show images containing traffic signs"

### Map Legend Added
Small legend in top-right shows:
- Camera Position icon (white circle)
- Feature (unselected) icon (gray circle)
- Selected/Highlighted icon (colored circle)

### Agent Service Updated
- System prompt now mentions San Bernardino, California
- Lists all horizontal and vertical feature types
- Better context for the AI to understand available features


## Actual Icon System (Emoji Symbols)

### Now Using Real Icons!

Instead of just colored circles, highlighted features now show **emoji icons** that represent their type:

#### Feature Type Icons:
- 🔴 **Pavement Damage** - Red circle
- 🟠 **Road Marking** - Orange circle
- ⚫ **Manhole Cover** - Black circle
- 🔵 **Drainage Grate** - Blue circle
- ⬜ **Pavement Patch** - White square
- 🛑 **Traffic Sign** - Stop sign
- 🚦 **Traffic Light** - Traffic light
- 💡 **Street Light** - Light bulb
- 📍 **Utility Pole** - Pin
- 🗑️ **Trash Bin** - Trash can
- 🚒 **Fire Hydrant** - Fire truck
- 🌳 **Vegetation** - Tree

### How It Works:
1. **Unselected features**: Small gray circles (minimal, clean)
2. **Selected features**: 
   - White circle background (18px)
   - Colored border matching feature type
   - **Emoji icon on top** (20px font size)
   - MapLibre GL `symbol` layer with `text-field`

### Technical Implementation:
- Uses MapLibre GL's **symbol layer** with emoji text
- `text-allow-overlap: true` - icons don't hide each other
- `text-ignore-placement: true` - always visible
- Two-layer system: circle background + emoji symbol
- Data-driven styling with `match` expressions

### Benefits:
- ✅ Immediate visual recognition of feature types
- ✅ No external image files needed (emojis are Unicode)
- ✅ Cross-platform compatible
- ✅ Easy to customize/extend
- ✅ Accessible (emojis have semantic meaning)

### Future Options:
- Could replace emojis with custom SVG icons
- Could add image sprites for professional look
- Could animate icons on hover/selection
- Could scale icons based on zoom level

