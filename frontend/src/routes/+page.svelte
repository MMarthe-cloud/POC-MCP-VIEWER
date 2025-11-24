<script>
  import { onMount } from 'svelte';
  import maplibregl from 'maplibre-gl';
  import 'maplibre-gl/dist/maplibre-gl.css';
  
  const API_BASE = 'http://localhost:8000';
  
  let mapContainer;
  let map;
  let question = '';
  let isLoading = false;
  let currentAnswer = '';
  let conversationHistory = [];
  let toolExecutions = [];
  let statsBox = null;
  let showHistory = false;
  let showTools = false;
  let showHelp = false;
  let currentMapStyle = 'dark';
  let campaignData = null; // Cache campaign data
  let isChangingStyle = false; // Prevent rapid style changes
  
  // Available map styles
  const mapStyles = {
    streets: {
      name: 'Streets',
      url: 'https://demotiles.maplibre.org/style.json',
      icon: '🗺️'
    },
    satellite: {
      name: 'Satellite',
      url: {
        "version": 8,
        "sources": {
          "satellite": {
            "type": "raster",
            "tiles": [
              "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            ],
            "tileSize": 256,
            "attribution": "© ESRI"
          }
        },
        "layers": [{
          "id": "satellite",
          "type": "raster",
          "source": "satellite"
        }]
      },
      icon: '🛰️'
    },
    topo: {
      name: 'Topographic',
      url: {
        "version": 8,
        "sources": {
          "topo": {
            "type": "raster",
            "tiles": ["https://tile.opentopomap.org/{z}/{x}/{y}.png"],
            "tileSize": 256,
            "attribution": "© OpenTopoMap"
          }
        },
        "layers": [{
          "id": "topo",
          "type": "raster",
          "source": "topo"
        }]
      },
      icon: '⛰️'
    },
    dark: {
      name: 'Dark',
      url: {
        "version": 8,
        "sources": {
          "dark": {
            "type": "raster",
            "tiles": ["https://a.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png"],
            "tileSize": 256,
            "attribution": "© CARTO"
          }
        },
        "layers": [{
          "id": "dark",
          "type": "raster",
          "source": "dark"
        }]
      },
      icon: '🌙'
    }
  };
  
  // Initialize map
  onMount(async () => {
    // Fetch and cache campaign data
    const campaignRes = await fetch(`${API_BASE}/campaign`);
    campaignData = await campaignRes.json();
    
    // Initialize map (Vienna center)
    map = new maplibregl.Map({
      container: mapContainer,
      style: mapStyles[currentMapStyle].url,
      center: [16.3738, 48.2082],
      zoom: 12
    });
    
    map.on('load', () => {
      console.log('✓ Initial map load complete');
      addCampaignLayers(false);
    });
  });
  
  function addCampaignLayers(skipCleanup = false) {
    if (!map || !campaignData) {
      console.log('❌ Cannot add layers - map or data missing');
      return;
    }
    
    console.log('✓ Adding campaign layers...', {
      styleLoaded: map.isStyleLoaded(),
      features: campaignData.features.length,
      images: campaignData.images.length
    });
    
    // Remove existing layers if they exist (but only if not skipping cleanup)
    if (!skipCleanup) {
      ['highlighted-layer', 'highlighted-images-layer', 'features-layer', 'images-layer'].forEach(layerId => {
        if (map.getLayer(layerId)) {
          try {
            map.removeLayer(layerId);
            console.log('✓ Removed layer:', layerId);
          } catch (e) {
            console.log('⚠️ Could not remove layer:', layerId, e.message);
          }
        }
      });
      
      // Remove existing sources if they exist
      ['highlighted', 'highlighted-images', 'features', 'images'].forEach(sourceId => {
        if (map.getSource(sourceId)) {
          try {
            map.removeSource(sourceId);
            console.log('✓ Removed source:', sourceId);
          } catch (e) {
            console.log('⚠️ Could not remove source:', sourceId, e.message);
          }
        }
      });
    }
    
    // Now add everything fresh
    try {
      // Add features as a source
      map.addSource('features', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: campaignData.features.map(f => ({
            type: 'Feature',
            id: f.id,
            geometry: f.geometry,
            properties: {
              type: f.type,
              condition: f.condition,
              ...f.attributes
            }
          }))
        }
      });
      
      // Add default feature markers (small gray dots)
      map.addLayer({
        id: 'features-layer',
        type: 'circle',
        source: 'features',
        paint: {
          'circle-radius': 4,
          'circle-color': '#888',
          'circle-opacity': 0.6
        }
      });
      
      // Add image positions
      map.addSource('images', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: campaignData.images.map(img => ({
            type: 'Feature',
            id: img.id,
            geometry: img.geometry,
            properties: {
              camera_id: img.camera_id,
              timestamp: img.timestamp
            }
          }))
        }
      });
      
      map.addLayer({
        id: 'images-layer',
        type: 'circle',
        source: 'images',
        paint: {
          'circle-radius': 6,
          'circle-color': '#3887be',
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff'
        }
      });
      
      console.log('✅ Campaign layers added successfully! Features:', campaignData.features.length);
    } catch (error) {
      console.error('❌ Error adding campaign layers:', error);
      console.error('Error details:', error.message, error.stack);
    }
  }
  
  // Execute map commands from the model
  function executeMapCommands(commands) {
    commands.forEach(cmd => {
      if (cmd.command === 'highlight_features') {
        highlightFeatures(cmd.feature_ids, cmd.color, cmd.label);
      } else if (cmd.command === 'show_statistics') {
        showStatistics(cmd.title, cmd.stats);
      } else if (cmd.command === 'clear_highlights') {
        clearHighlights();
      } else if (cmd.command === 'highlight_image') {
        highlightImages(cmd.image_ids, cmd.color, cmd.label);
      } else if (cmd.command === 'show_heatmap') {
        showHeatmap(cmd.points, cmd.property);
      }
    });
  }
  
  function highlightFeatures(featureIds, color = '#FF0000', label = null) {
    // Remove old highlights
    clearHighlights();
    
    // Skip if no features to highlight
    if (!featureIds || featureIds.length === 0) {
      console.log('No features to highlight');
      return;
    }
    
    // Add new highlight layer
    const sourceData = map.getSource('features')._data;
    const highlightedData = {
      type: 'FeatureCollection',
      features: sourceData.features.filter(f => featureIds.includes(f.id))
    };
    
    if (map.getSource('highlighted')) {
      map.getSource('highlighted').setData(highlightedData);
    } else {
      map.addSource('highlighted', {
        type: 'geojson',
        data: highlightedData
      });
      
      map.addLayer({
        id: 'highlighted-layer',
        type: 'circle',
        source: 'highlighted',
        paint: {
          'circle-radius': 10,
          'circle-color': color,
          'circle-opacity': 0.8,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#fff'
        }
      });
    }
    
    // Zoom to highlighted features
    if (highlightedData.features.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      highlightedData.features.forEach(f => {
        bounds.extend(f.geometry.coordinates);
      });
      map.fitBounds(bounds, { padding: 50 });
    }
  }
  
  function showStatistics(title, stats) {
    statsBox = { title, stats };
  }
  
  function highlightImages(imageIds, color = '#0000FF', label = null) {
    // Highlight specific image positions
    const sourceData = map.getSource('images')._data;
    const highlightedData = {
      type: 'FeatureCollection',
      features: sourceData.features.filter(f => imageIds.includes(f.id))
    };
    
    if (map.getSource('highlighted-images')) {
      map.getSource('highlighted-images').setData(highlightedData);
    } else {
      map.addSource('highlighted-images', {
        type: 'geojson',
        data: highlightedData
      });
      
      map.addLayer({
        id: 'highlighted-images-layer',
        type: 'circle',
        source: 'highlighted-images',
        paint: {
          'circle-radius': 12,
          'circle-color': color,
          'circle-opacity': 0.9,
          'circle-stroke-width': 3,
          'circle-stroke-color': '#fff'
        }
      });
    }
    
    // Zoom to highlighted images
    if (highlightedData.features.length > 0) {
      const bounds = new maplibregl.LngLatBounds();
      highlightedData.features.forEach(f => {
        bounds.extend(f.geometry.coordinates);
      });
      map.fitBounds(bounds, { padding: 50 });
    }
  }
  
  function showHeatmap(points, property) {
    // Simple heatmap using circle sizes (real heatmap would need heatmap layer)
    console.log('Heatmap requested:', property, points);
    // For now, just show as regular markers - proper heatmap needs MapLibre GL heatmap layer
  }
  
  function clearHighlights() {
    if (map.getLayer('highlighted-layer')) {
      map.removeLayer('highlighted-layer');
    }
    if (map.getSource('highlighted')) {
      map.removeSource('highlighted');
    }
    if (map.getLayer('highlighted-images-layer')) {
      map.removeLayer('highlighted-images-layer');
    }
    if (map.getSource('highlighted-images')) {
      map.removeSource('highlighted-images');
    }
    statsBox = null;
  }
  
  function clearConversation() {
    conversationHistory = [];
    currentAnswer = '';
    toolExecutions = [];
    statsBox = null;
    clearHighlights();
    
    // Clear backend history too
    fetch(`${API_BASE}/clear`, { method: 'POST' }).catch(console.error);
  }
  
  function useExampleQuestion(exampleQuestion) {
    question = exampleQuestion;
    showHelp = false;
    // Auto-submit after short delay
    setTimeout(() => askQuestion(), 100);
  }
  
  function changeMapStyle(styleKey) {
    if (!map || isChangingStyle) {
      console.log('⚠️ Cannot change style - already changing or map not ready');
      return;
    }
    
    if (styleKey === currentMapStyle) {
      console.log('⚠️ Already on this style');
      return;
    }
    
    isChangingStyle = true;
    const style = mapStyles[styleKey];
    
    console.log('🔄 Changing map style to:', styleKey);
    
    // Save highlighted features data safely
    let highlightedData = null;
    let highlightedImagesData = null;
    let highlightedColor = '#FF0000';
    let highlightedImagesColor = '#0000FF';
    
    try {
      const highlightedSource = map.getSource('highlighted');
      if (highlightedSource && highlightedSource._data) {
        highlightedData = JSON.parse(JSON.stringify(highlightedSource._data)); // Deep clone
        console.log('✓ Saved highlighted data:', highlightedData.features?.length, 'features');
        if (map.getLayer('highlighted-layer')) {
          highlightedColor = map.getPaintProperty('highlighted-layer', 'circle-color') || '#FF0000';
        }
      }
    } catch (e) {
      console.log('⚠️ No highlighted data to save:', e.message);
    }
    
    try {
      const highlightedImagesSource = map.getSource('highlighted-images');
      if (highlightedImagesSource && highlightedImagesSource._data) {
        highlightedImagesData = JSON.parse(JSON.stringify(highlightedImagesSource._data)); // Deep clone
        console.log('✓ Saved highlighted images:', highlightedImagesData.features?.length, 'images');
        if (map.getLayer('highlighted-images-layer')) {
          highlightedImagesColor = map.getPaintProperty('highlighted-images-layer', 'circle-color') || '#0000FF';
        }
      }
    } catch (e) {
      console.log('⚠️ No highlighted images to save:', e.message);
    }
    
    // Change style
    try {
      map.setStyle(style.url);
      currentMapStyle = styleKey;
    } catch (e) {
      console.error('❌ Error setting style:', e);
      isChangingStyle = false;
      return;
    }
    
    // Restore everything after style loads
    let styleLoadTimeout;
    let restorationDone = false;
    
    const restoreLayers = () => {
      if (restorationDone) {
        console.log('⚠️ Restoration already done, skipping');
        return;
      }
      restorationDone = true;
      
      console.log('✓ New style loaded:', styleKey);
      
      // Clear any existing timeout
      if (styleLoadTimeout) clearTimeout(styleLoadTimeout);
      
      // Wait a bit for the style to fully initialize, then restore
      styleLoadTimeout = setTimeout(() => {
        console.log('✓ Starting layer restoration...');
        
        try {
          // Re-add all campaign layers using cached data
          addCampaignLayers(true); // Skip cleanup since we just changed styles
          
          // Small delay before adding highlights
          setTimeout(() => {
            // Restore highlighted features if they existed
            if (highlightedData && highlightedData.features && highlightedData.features.length > 0) {
              console.log('✓ Restoring', highlightedData.features.length, 'highlighted features');
              try {
                map.addSource('highlighted', {
                  type: 'geojson',
                  data: highlightedData
                });
                
                map.addLayer({
                  id: 'highlighted-layer',
                  type: 'circle',
                  source: 'highlighted',
                  paint: {
                    'circle-radius': 10,
                    'circle-color': highlightedColor,
                    'circle-opacity': 0.8,
                    'circle-stroke-width': 2,
                    'circle-stroke-color': '#fff'
                  }
                });
                console.log('✅ Highlighted features restored');
              } catch (e) {
                console.error('❌ Error restoring highlights:', e.message);
              }
            }
            
            // Restore highlighted images if they existed
            if (highlightedImagesData && highlightedImagesData.features && highlightedImagesData.features.length > 0) {
              console.log('✓ Restoring', highlightedImagesData.features.length, 'highlighted images');
              try {
                map.addSource('highlighted-images', {
                  type: 'geojson',
                  data: highlightedImagesData
                });
                
                map.addLayer({
                  id: 'highlighted-images-layer',
                  type: 'circle',
                  source: 'highlighted-images',
                  paint: {
                    'circle-radius': 12,
                    'circle-color': highlightedImagesColor,
                    'circle-opacity': 0.9,
                    'circle-stroke-width': 3,
                    'circle-stroke-color': '#fff'
                  }
                });
                console.log('✅ Highlighted images restored');
              } catch (e) {
                console.error('❌ Error restoring image highlights:', e.message);
              }
            }
            
            console.log('✅ Map style switch complete!');
            
            // Re-enable style switching
            setTimeout(() => {
              isChangingStyle = false;
            }, 500);
          }, 100);
        } catch (e) {
          console.error('❌ Error during restoration:', e);
          isChangingStyle = false;
        }
      }, 200); // Wait 200ms after style loads
    };
    
    // Try multiple events since different map types behave differently
    map.once('style.load', restoreLayers);
    map.once('styledata', restoreLayers);
    map.once('idle', restoreLayers);
    
    // Fallback timeout in case events don't fire
    setTimeout(() => {
      if (!restorationDone) {
        console.log('⚠️ Style events not firing, using fallback restoration');
        restoreLayers();
      }
    }, 2000);
  }
  
  async function askQuestion() {
    if (!question.trim() || isLoading) return;
    
    const userQuestion = question;
    question = '';
    isLoading = true;
    currentAnswer = '';
    toolExecutions = [];
    
    try {
      const res = await fetch(`${API_BASE}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQuestion })
      });
      
      const data = await res.json();
      
      // Clean up the answer (remove function call syntax)
      let cleanAnswer = data.answer || 'Done.';
      cleanAnswer = cleanAnswer.replace(/<function=.*?<\/function>/g, '').trim();
      
      currentAnswer = cleanAnswer;
      
      // Add to conversation history
      conversationHistory = [
        ...conversationHistory,
        { type: 'question', text: userQuestion },
        { type: 'answer', text: cleanAnswer }
      ];
      
      // Store tool executions
      if (data.tool_uses && data.tool_uses.length > 0) {
        toolExecutions = data.tool_uses.map(t => ({
          tool: t.tool,
          input: t.input,
          result: t.result
        }));
      }
      
      // Execute map commands
      if (data.map_commands && data.map_commands.length > 0) {
        executeMapCommands(data.map_commands);
      }
    } catch (error) {
      currentAnswer = 'Error: ' + error.message;
    } finally {
      isLoading = false;
    }
  }
  
  function handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  }
</script>

<div class="container">
  <!-- Ask Bar -->
  <div class="ask-bar">
    <button class="help-btn" on:click={() => showHelp = !showHelp} title="Show help">
      ?
    </button>
    <input
      type="text"
      bind:value={question}
      on:keypress={handleKeyPress}
      placeholder="Ask me anything about the campaign..."
      disabled={isLoading}
    />
    <button on:click={askQuestion} disabled={isLoading || !question.trim()}>
      {isLoading ? 'Thinking...' : 'Ask'}
    </button>
    {#if conversationHistory.length > 0}
      <button class="clear-btn-top" on:click={clearConversation}>
        Clear
      </button>
    {/if}
  </div>
  
  <!-- Help Panel -->
  {#if showHelp}
    <div class="help-panel">
      <div class="help-header">
        <h3>💡 What can I ask?</h3>
        <button class="close-btn" on:click={() => showHelp = false}>×</button>
      </div>
      <div class="help-content">
        <div class="help-section">
          <h4>🔍 Finding Features</h4>
          <ul>
            <li on:click={() => useExampleQuestion("show me all stop signs")}>show me all stop signs</li>
            <li on:click={() => useExampleQuestion("find damaged guardrails")}>find damaged guardrails</li>
            <li on:click={() => useExampleQuestion("show crosswalks in poor condition")}>show crosswalks in poor condition</li>
            <li on:click={() => useExampleQuestion("highlight all poles")}>highlight all poles</li>
          </ul>
        </div>
        
        <div class="help-section">
          <h4>📷 Image Questions</h4>
          <ul>
            <li on:click={() => useExampleQuestion("which image has the most features?")}>which image has the most features?</li>
            <li on:click={() => useExampleQuestion("show images containing stop signs")}>show images containing stop signs</li>
            <li on:click={() => useExampleQuestion("which image has the most damaged features?")}>which image has the most damaged features?</li>
            <li on:click={() => useExampleQuestion("images with guardrails")}>images with guardrails</li>
          </ul>
        </div>
        
        <div class="help-section">
          <h4>💬 Follow-up Questions</h4>
          <ul>
            <li on:click={() => question = "which ones are damaged?"}>which ones are damaged? <span style="opacity: 0.6; font-size: 11px;">(after showing features)</span></li>
          </ul>
        </div>
        
        <div class="help-section">
          <h4>📊 Feature Types</h4>
          <div class="feature-tags">
            <span class="tag">stop signs</span>
            <span class="tag">speed limits</span>
            <span class="tag">crosswalks</span>
            <span class="tag">guardrails</span>
            <span class="tag">poles</span>
          </div>
        </div>
        
        <div class="help-section">
          <h4>🎨 Conditions</h4>
          <div class="feature-tags">
            <span class="tag condition-good">good</span>
            <span class="tag condition-fair">fair</span>
            <span class="tag condition-poor">poor</span>
            <span class="tag condition-damaged">damaged</span>
          </div>
        </div>
      </div>
    </div>
  {/if}
  
  <!-- Current Answer -->
  {#if currentAnswer}
    <div class="answer-box">
      <div class="answer-header">
        <span>Answer</span>
        <button class="close-btn" on:click={() => currentAnswer = ''}>×</button>
      </div>
      <div class="answer-content">{currentAnswer}</div>
    </div>
  {/if}
  
  <!-- Tool Executions Panel -->
  {#if toolExecutions.length > 0}
    <div class="tools-panel" class:collapsed={!showTools}>
      <div class="panel-header" on:click={() => showTools = !showTools}>
        <span>🔧 Model Actions ({toolExecutions.length})</span>
        <span class="toggle">{showTools ? '▼' : '▶'}</span>
      </div>
      {#if showTools}
        <div class="panel-content">
          {#each toolExecutions as tool}
            <div class="tool-item">
              <div class="tool-name">{tool.tool}</div>
              <div class="tool-input">
                {#each Object.entries(tool.input) as [key, value]}
                  <span class="param">{key}: {JSON.stringify(value).substring(0, 50)}</span>
                {/each}
              </div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
  
  <!-- Conversation History Panel -->
  {#if conversationHistory.length > 0}
    <div class="history-panel" class:collapsed={!showHistory}>
      <div class="panel-header" on:click={() => showHistory = !showHistory}>
        <span>💬 History ({conversationHistory.length / 2})</span>
        <span class="toggle">{showHistory ? '▼' : '▶'}</span>
      </div>
      {#if showHistory}
        <div class="panel-content">
          {#each conversationHistory as msg}
            <div class="history-item {msg.type}">
              <div class="history-label">{msg.type === 'question' ? 'You' : 'AI'}</div>
              <div class="history-text">{msg.text}</div>
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {/if}
  
  <!-- Statistics Box -->
  {#if statsBox}
    <div class="stats-box">
      <h3>{statsBox.title}</h3>
      {#each Object.entries(statsBox.stats) as [key, value]}
        <div class="stat-row">
          <span class="stat-label">{key}:</span>
          <span class="stat-value">{value}</span>
        </div>
      {/each}
    </div>
  {/if}
  
  <!-- Map Style Switcher -->
  <div class="map-style-switcher">
    {#each Object.entries(mapStyles) as [key, style]}
      <button 
        class="style-btn" 
        class:active={currentMapStyle === key}
        class:disabled={isChangingStyle}
        on:click={() => changeMapStyle(key)}
        title={style.name}
        disabled={isChangingStyle}
      >
        {style.icon}
      </button>
    {/each}
  </div>
  
  <!-- Map -->
  <div class="map-container" bind:this={mapContainer}></div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  
  .container {
    width: 100vw;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }
  
  .ask-bar {
    display: flex;
    gap: 12px;
    padding: 20px;
    background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    z-index: 1000;
  }
  
  .ask-bar input {
    flex: 1;
    padding: 14px 20px;
    font-size: 16px;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    outline: none;
    transition: border-color 0.2s;
  }
  
  .ask-bar input:focus {
    border-color: #3887be;
  }
  
  .ask-bar input:disabled {
    background: #f5f5f5;
  }
  
  .ask-bar button {
    padding: 14px 32px;
    font-size: 16px;
    font-weight: 600;
    background: #3887be;
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    transition: background 0.2s;
  }
  
  .ask-bar button:hover:not(:disabled) {
    background: #2c6a9e;
  }
  
  .ask-bar button:disabled {
    background: #ccc;
    cursor: not-allowed;
  }
  
  .clear-btn-top {
    padding: 14px 24px !important;
    background: #dc3545 !important;
  }
  
  .clear-btn-top:hover:not(:disabled) {
    background: #c82333 !important;
  }
  
  .help-btn {
    width: 40px !important;
    height: 40px;
    padding: 0 !important;
    font-size: 20px;
    font-weight: bold;
    background: #f8f9fa !important;
    color: #666 !important;
    border: 2px solid #e0e0e0 !important;
    border-radius: 50% !important;
    cursor: pointer;
    transition: all 0.2s;
    margin-right: 12px;
  }
  
  .help-btn:hover {
    background: #3887be !important;
    color: white !important;
    border-color: #3887be !important;
  }
  
  .help-panel {
    position: absolute;
    top: 80px;
    left: 50%;
    transform: translateX(-50%);
    width: 90%;
    max-width: 700px;
    background: white;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.2);
    z-index: 1001;
    max-height: 80vh;
    overflow-y: auto;
  }
  
  .help-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px 12px 0 0;
    color: white;
  }
  
  .help-header h3 {
    margin: 0;
    font-size: 20px;
    font-weight: 600;
  }
  
  .help-header .close-btn {
    color: white !important;
  }
  
  .help-content {
    padding: 24px;
  }
  
  .help-section {
    margin-bottom: 24px;
  }
  
  .help-section:last-child {
    margin-bottom: 0;
  }
  
  .help-section h4 {
    margin: 0 0 12px 0;
    font-size: 15px;
    font-weight: 600;
    color: #333;
  }
  
  .help-section ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  .help-section li {
    padding: 8px 12px;
    margin: 4px 0;
    background: #f8f9fa;
    border-radius: 6px;
    font-size: 13px;
    color: #555;
    font-family: 'Courier New', monospace;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .help-section li:hover {
    background: #e3f2fd;
    color: #1976d2;
    transform: translateX(4px);
  }
  
  .feature-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .tag {
    padding: 6px 12px;
    background: #e0e0e0;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 500;
    color: #555;
  }
  
  .tag.condition-good {
    background: #c8e6c9;
    color: #2e7d32;
  }
  
  .tag.condition-fair {
    background: #fff9c4;
    color: #f57f17;
  }
  
  .tag.condition-poor {
    background: #ffccbc;
    color: #d84315;
  }
  
  .tag.condition-damaged {
    background: #ffcdd2;
    color: #c62828;
  }
  
  .map-style-switcher {
    position: absolute;
    top: 100px;
    right: 20px;
    display: flex;
    flex-direction: column;
    gap: 8px;
    z-index: 999;
  }
  
  .style-btn {
    width: 44px;
    height: 44px;
    background: white;
    border: 2px solid #e0e0e0;
    border-radius: 8px;
    font-size: 20px;
    cursor: pointer;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
    transition: all 0.2s;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  
  .style-btn:hover {
    border-color: #3887be;
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  }
  
  .style-btn.active {
    border-color: #3887be;
    background: #e3f2fd;
    box-shadow: 0 0 0 2px #3887be;
  }
  
  .style-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  .answer-box {
    position: absolute;
    top: 100px;
    left: 20px;
    max-width: 400px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 999;
  }
  
  .answer-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: #f8f9fa;
    border-bottom: 1px solid #e0e0e0;
    border-radius: 8px 8px 0 0;
    font-weight: 600;
    font-size: 13px;
    color: #555;
  }
  
  .answer-content {
    padding: 16px 20px;
    font-size: 14px;
    line-height: 1.6;
    color: #333;
  }
  
  .close-btn {
    background: none;
    border: none;
    font-size: 24px;
    cursor: pointer;
    color: #999;
    padding: 0;
    width: 24px;
    height: 24px;
    line-height: 20px;
  }
  
  .close-btn:hover {
    color: #333;
  }
  
  .tools-panel,
  .history-panel {
    position: absolute;
    left: 20px;
    max-width: 400px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 998;
  }
  
  .tools-panel {
    bottom: 20px;
  }
  
  .history-panel {
    bottom: 80px;
  }
  
  .tools-panel.collapsed,
  .history-panel.collapsed {
    max-width: 200px;
  }
  
  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 16px;
    background: #f8f9fa;
    border-radius: 8px;
    cursor: pointer;
    user-select: none;
    font-size: 13px;
    font-weight: 600;
    color: #555;
  }
  
  .panel-header:hover {
    background: #e9ecef;
  }
  
  .toggle {
    font-size: 10px;
    color: #999;
  }
  
  .panel-content {
    max-height: 300px;
    overflow-y: auto;
    padding: 8px;
  }
  
  .tool-item {
    padding: 8px 12px;
    margin: 4px 0;
    background: #f8f9fa;
    border-radius: 6px;
    font-size: 12px;
  }
  
  .tool-name {
    font-weight: 600;
    color: #3887be;
    margin-bottom: 4px;
  }
  
  .tool-input {
    font-size: 11px;
    color: #666;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }
  
  .param {
    font-family: monospace;
  }
  
  .history-item {
    padding: 8px 12px;
    margin: 4px 0;
    border-radius: 6px;
    font-size: 13px;
  }
  
  .history-item.question {
    background: #e3f2fd;
  }
  
  .history-item.answer {
    background: #f1f8e9;
  }
  
  .history-label {
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    color: #666;
    margin-bottom: 4px;
  }
  
  .history-text {
    color: #333;
    line-height: 1.5;
  }
  
  .stats-box {
    position: absolute;
    top: 100px;
    right: 20px;
    min-width: 250px;
    padding: 16px 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    z-index: 999;
  }
  
  .stats-box h3 {
    margin: 0 0 12px 0;
    font-size: 16px;
    font-weight: 600;
    color: #333;
  }
  
  .stat-row {
    display: flex;
    justify-content: space-between;
    padding: 6px 0;
    border-bottom: 1px solid #f0f0f0;
  }
  
  .stat-row:last-child {
    border-bottom: none;
  }
  
  .stat-label {
    font-size: 14px;
    color: #666;
  }
  
  .stat-value {
    font-size: 14px;
    font-weight: 600;
    color: #333;
  }
  
  .map-container {
    flex: 1;
    position: relative;
  }
</style>

