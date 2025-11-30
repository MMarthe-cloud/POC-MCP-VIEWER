<script>
  import { onMount, onDestroy } from 'svelte';
  
  export let imageId = null;
  export let imagePath = '';
  export let visible = false;
  export let highlightedFeatures = [];
  export let onClose = () => {};
  
  let viewerContainer;
  let krpano = null;
  let hotspots = [];
  let nearbyImages = [];
  let hoverInfo = null;
  let mousePosition = { x: 0, y: 0 };
  
  onMount(() => {
    loadKrpanoScript();
  });
  
  function loadKrpanoScript() {
    if (window.embedpano) {
      return;
    }
    
    const script = document.createElement('script');
    script.src = '/krpano/krpano.js';
    script.onload = () => {
      console.log('✅ Krpano loaded');
    };
    document.head.appendChild(script);
  }
  
  $: if (visible && imagePath && window.embedpano && viewerContainer) {
    console.log('🎬 Initializing Krpano for image:', imagePath);
    initViewer();
  }
  
  // Watch for changes in highlighted features and update hotspots
  $: if (krpano && highlightedFeatures) {
    console.log('🔄 Highlighted features changed, updating hotspots...');
    updateHotspots();
  }
  
  async function fetchHotspots() {
    if (!imageId || !highlightedFeatures || highlightedFeatures.length === 0) {
      hotspots = [];
      return;
    }
    
    try {
      const featureIdsParam = highlightedFeatures.join(',');
      const response = await fetch(
        `http://localhost:8000/project/features?image_id=${imageId}&feature_ids=${featureIdsParam}`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      hotspots = data.hotspots || [];
      console.log('📍 Fetched hotspots:', hotspots.length);
    } catch (error) {
      console.error('❌ Error fetching hotspots:', error);
      hotspots = [];
    }
  }
  
  async function fetchNearbyImages() {
    if (!imageId) {
      nearbyImages = [];
      return;
    }
    
    try {
      const response = await fetch(
        `http://localhost:8000/nearby/images?image_id=${imageId}&max_distance=50`
      );
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      nearbyImages = data.nearby_images || [];
      console.log('📷 Fetched nearby images:', nearbyImages.length);
    } catch (error) {
      console.error('❌ Error fetching nearby images:', error);
      nearbyImages = [];
    }
  }
  
  function navigateToImage(targetImageId) {
    console.log('🚀 Navigating to image:', targetImageId);
    
    // Close current viewer and reopen with new image
    if (krpano) {
      viewerContainer.innerHTML = '';
      krpano = null;
    }
    
    // Update the parent component's selected image
    // We'll need to emit an event for this
    const event = new CustomEvent('navigate', { detail: { imageId: targetImageId } });
    window.dispatchEvent(event);
  }
  
  function getIconForFeatureType(type) {
    // All highlighted features use the same red pin icon
    return '/icons/highlighted-icon.svg';
  }
  
  function removeFeatureHotspots() {
    if (!krpano || !hotspots || hotspots.length === 0) {
      return;
    }
    
    // Remove all feature hotspots from Krpano
    hotspots.forEach((hotspot) => {
      const hotspotName = `feature_${hotspot.feature_id}`;
      if (krpano.get(`hotspot[${hotspotName}]`)) {
        krpano.call(`removehotspot(${hotspotName})`);
      }
    });
    console.log('🗑️ Removed', hotspots.length, 'old feature hotspots');
  }
  
  async function updateHotspots() {
    if (!krpano || !imageId) {
      return;
    }
    
    // Remove old feature hotspots
    removeFeatureHotspots();
    
    // Fetch new hotspots
    await fetchHotspots();
    
    // Add new hotspots
    addHotspots();
  }
  
  function showHotspotInfo(featureId) {
    const hotspot = hotspots.find(h => h.feature_id === featureId);
    if (hotspot) {
      hoverInfo = {
        feature_id: hotspot.feature_id,
        feature_type: hotspot.feature_type,
        distance: hotspot.distance,
        confidence: hotspot.confidence,
        condition: hotspot.condition
      };
    }
  }
  
  function hideHotspotInfo() {
    hoverInfo = null;
  }
  
  function addHotspots() {
    if (!krpano || !hotspots || hotspots.length === 0) {
      return;
    }
    
    console.log('🎯 Adding', hotspots.length, 'feature hotspots to Krpano');
    
    hotspots.forEach((hotspot, index) => {
      const hotspotName = `feature_${hotspot.feature_id}`;
      const iconUrl = getIconForFeatureType(hotspot.feature_type);
      
      // Add hotspot using Krpano API
      krpano.call(`addhotspot(${hotspotName})`);
      
      // Set hotspot properties
      krpano.set(`hotspot[${hotspotName}].ath`, hotspot.hlookat);
      krpano.set(`hotspot[${hotspotName}].atv`, hotspot.vlookat);
      krpano.set(`hotspot[${hotspotName}].url`, iconUrl);
      krpano.set(`hotspot[${hotspotName}].scale`, 0.8);
      krpano.set(`hotspot[${hotspotName}].distorted`, true);
      krpano.set(`hotspot[${hotspotName}].zoom`, true);
      krpano.set(`hotspot[${hotspotName}].alpha`, 0.9);
      krpano.set(`hotspot[${hotspotName}].zorder`, 100);
      
      // Add hover handlers - store feature ID as property and use jscall
      krpano.set(`hotspot[${hotspotName}].feature_id`, hotspot.feature_id);
      krpano.set(`hotspot[${hotspotName}].onhover`, () => {
        showHotspotInfo(hotspot.feature_id);
      });
      krpano.set(`hotspot[${hotspotName}].onout`, () => {
        hideHotspotInfo();
      });
      
      console.log(`  ✓ Added feature hotspot: ${hotspot.feature_type} at h=${hotspot.hlookat}° v=${hotspot.vlookat}° (${hotspot.distance}m)`);
    });
  }
  
  function addCameraHotspots() {
    if (!krpano || !nearbyImages || nearbyImages.length === 0) {
      return;
    }
    
    console.log('📷 Adding', nearbyImages.length, 'camera hotspots to Krpano');
    
    nearbyImages.forEach((nearbyImg) => {
      const hotspotName = `camera_${nearbyImg.image_id}`;
      
      // Add camera hotspot
      krpano.call(`addhotspot(${hotspotName})`);
      
      // Set hotspot properties - camera icon
      krpano.set(`hotspot[${hotspotName}].ath`, nearbyImg.bearing);
      krpano.set(`hotspot[${hotspotName}].atv`, 0);  // Horizontal level
      krpano.set(`hotspot[${hotspotName}].url`, '/icons/camera-capture-icon.svg');
      krpano.set(`hotspot[${hotspotName}].scale`, 0.6);
      krpano.set(`hotspot[${hotspotName}].distorted`, true);
      krpano.set(`hotspot[${hotspotName}].alpha`, 0.8);
      krpano.set(`hotspot[${hotspotName}].zorder`, 50);  // Behind features
      
      // Make clickable
      krpano.set(`hotspot[${hotspotName}].onclick`, () => {
        navigateToImage(nearbyImg.image_id);
      });
      
      // Hover effect
      krpano.set(`hotspot[${hotspotName}].onhover`, () => {
        krpano.set(`hotspot[${hotspotName}].scale`, 0.8);
      });
      krpano.set(`hotspot[${hotspotName}].onout`, () => {
        krpano.set(`hotspot[${hotspotName}].scale`, 0.6);
      });
      
      console.log(`  ✓ Added camera hotspot: Image ${nearbyImg.image_id} at bearing ${nearbyImg.bearing}° (${nearbyImg.distance}m)`);
    });
  }
  
  async function initViewer() {
    viewerContainer.innerHTML = '';
    
    // Fetch both feature hotspots and nearby camera positions
    await Promise.all([
      fetchHotspots(),
      fetchNearbyImages()
    ]);
    
    // Generate XML URL with image path as parameter
    const xmlUrl = `http://localhost:8000/krpano/pano.xml?image_url=${encodeURIComponent(imagePath)}`;
    
    console.log('📄 Loading Krpano with XML URL:', xmlUrl);
    
    window.embedpano({
      xml: xmlUrl,
      target: viewerContainer,
      html5: 'only',
      mobilescale: 1.0,
      passQueryParameters: false,
      consolelog: true,
      onready: function(krpanoInterface) {
        krpano = krpanoInterface;
        console.log('✅ Krpano initialized!');
        
        // Add both feature and camera hotspots after Krpano is ready
        setTimeout(() => {
          addHotspots();
          addCameraHotspots();
        }, 500);
      }
    });
  }
  
  function handleClose() {
    if (krpano) {
      viewerContainer.innerHTML = '';
      krpano = null;
    }
    hoverInfo = null;
    onClose();
  }
  
  function handleMouseMove(event) {
    mousePosition = { x: event.clientX, y: event.clientY };
  }
  
  onDestroy(() => {
    if (krpano) {
      viewerContainer.innerHTML = '';
    }
  });
</script>

{#if visible}
  <div class="image-viewer-overlay" on:mousemove={handleMouseMove}>
    <div class="viewer-header">
      <div class="viewer-title">
        360° Image {#if imageId !== null}#{imageId}{/if}
        {#if hotspots.length > 0}
          <span class="hotspot-badge">📍 {hotspots.length} feature{hotspots.length !== 1 ? 's' : ''}</span>
        {/if}
        {#if nearbyImages.length > 0}
          <span class="camera-badge">📷 {nearbyImages.length} camera{nearbyImages.length !== 1 ? 's' : ''}</span>
        {/if}
      </div>
      <button class="close-btn" on:click={handleClose}>
        ✕
      </button>
    </div>
    
    <div class="viewer-container" bind:this={viewerContainer}></div>
    
    <!-- Hover Inspector for Features -->
    {#if hoverInfo}
    <div 
      class="hotspot-inspector"
      style="left: {mousePosition.x + 15}px; top: {mousePosition.y + 15}px;"
    >
      <div class="inspector-header">
        <img src={getIconForFeatureType(hoverInfo.feature_type)} alt="icon" class="inspector-icon" />
        Feature #{hoverInfo.feature_id}
      </div>
      <div class="inspector-content">
        <div class="inspector-row">
          <span class="inspector-label">Type:</span>
          <span class="inspector-value">{hoverInfo.feature_type.replace('_', ' ')}</span>
        </div>
        <div class="inspector-row">
          <span class="inspector-label">Distance:</span>
          <span class="inspector-value">{hoverInfo.distance}m</span>
        </div>
        <div class="inspector-row">
          <span class="inspector-label">Condition:</span>
          <span class="inspector-value">{hoverInfo.condition}</span>
        </div>
        <div class="inspector-row">
          <span class="inspector-label">Confidence:</span>
          <span class="inspector-value">{Math.round(hoverInfo.confidence * 100)}%</span>
        </div>
      </div>
    </div>
    {/if}
  </div>
{/if}

<style>
  .image-viewer-overlay {
    position: fixed;
    top: 80px;
    left: 0;
    right: 0;
    bottom: 0;
    background: #000;
    z-index: 10000;
    display: flex;
    flex-direction: column;
  }
  
  .viewer-header {
    background: #1a1a1a;
    padding: 15px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 2px solid #333;
    z-index: 10001;
  }
  
  .viewer-title {
    color: white;
    font-size: 16px;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .hotspot-badge {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 500;
  }
  
  .camera-badge {
    background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
    padding: 4px 12px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: 500;
  }
  
  .close-btn {
    background: #ff4444;
    color: white;
    border: none;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    font-size: 24px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: background 0.2s;
    padding: 0;
    line-height: 1;
  }
  
  .close-btn:hover {
    background: #ff0000;
  }
  
  .viewer-container {
    flex: 1;
    position: relative;
    width: 100%;
    background: #000;
  }
  
  .hotspot-inspector {
    position: fixed;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    padding: 0;
    z-index: 10002;
    pointer-events: none;
    min-width: 220px;
    font-size: 12px;
  }
  
  .inspector-header {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 8px 12px;
    border-radius: 8px 8px 0 0;
    font-weight: 600;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .inspector-icon {
    width: 24px;
    height: 24px;
    flex-shrink: 0;
  }
  
  .inspector-content {
    padding: 10px 12px;
  }
  
  .inspector-row {
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    gap: 12px;
  }
  
  .inspector-label {
    color: #666;
    font-weight: 500;
  }
  
  .inspector-value {
    color: #333;
    font-weight: 600;
    text-align: right;
    text-transform: capitalize;
  }
</style>
