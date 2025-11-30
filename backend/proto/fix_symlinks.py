#!/usr/bin/env python3
"""Fix symlinks: rename .jpg to .png"""
from pathlib import Path

spherical_dir = Path(__file__).parent.parent.parent / "mockup_data" / "track_2020" / "data" / "images" / "spherical"

print(f"Fixing symlinks in: {spherical_dir}")

jpg_links = list(spherical_dir.glob("*.jpg"))
print(f"Found {len(jpg_links)} .jpg symlinks")

for i, jpg_link in enumerate(jpg_links):
    if i % 1000 == 0:
        print(f"  Progress: {i}/{len(jpg_links)}")
    
    target = jpg_link.readlink()
    png_link = jpg_link.with_suffix(".png")
    
    if png_link.exists():
        png_link.unlink()
    
    png_link.symlink_to(target)
    jpg_link.unlink()

print(f"✅ Done! Renamed {len(jpg_links)} symlinks from .jpg to .png")

