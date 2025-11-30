"""
Quick test to verify data loading works
"""
from service import MappingService

def test_load():
    print("Testing data load...")
    campaign = MappingService.get_campaign()
    
    print(f"\n✅ Campaign: {campaign.name} ({campaign.id})")
    print(f"   - Features: {campaign.total_features}")
    print(f"   - Images: {campaign.total_images}")
    
    if campaign.features:
        print(f"\n📍 Sample feature:")
        feat = campaign.features[0]
        print(f"   - ID: {feat.id}")
        print(f"   - Type: {feat.type}")
        print(f"   - Condition: {feat.condition}")
        print(f"   - Position: {feat.geometry['coordinates']}")
    
    if campaign.images:
        print(f"\n📷 Sample image:")
        img = campaign.images[0]
        print(f"   - ID: {img.id}")
        print(f"   - Camera: {img.camera_id}")
        print(f"   - Timestamp: {img.timestamp}")
        print(f"   - Position: {img.geometry['coordinates']}")

if __name__ == "__main__":
    test_load()

