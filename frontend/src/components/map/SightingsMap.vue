<template>
  <div>
    <v-card v-if="selectedSighting" class="mb-4">
      <v-card-text class="d-flex align-center justify-space-between">
        <div>
          <span class="font-weight-medium">{{ formatDate(selectedSighting.date) }}</span>
          <span class="mx-2">•</span>
          <span>{{ selectedSighting.place || 'Kein Ort' }}</span>
          <span v-if="selectedSighting.area" class="text-medium-emphasis">
            ({{ selectedSighting.area }})
          </span>
        </div>
        <div class="d-flex align-center">
          <v-btn
            variant="text"
            color="primary"
            :to="`/entries/${selectedSighting.id}`"
            target="_blank"
            size="small"
          >
            Details öffnen
            <v-icon size="small" class="ml-1">mdi-open-in-new</v-icon>
          </v-btn>
          <v-btn
            variant="text"
            color="grey"
            @click="selectedSighting = null"
            size="small"
          >
            <v-icon size="small">mdi-close</v-icon>
          </v-btn>
        </div>
      </v-card-text>
    </v-card>

    <div class="map-wrapper">
      <div ref="mapContainer" style="height: 400px;"></div>
      <div class="map-controls">
        <button
          v-for="(mapStyle, key) in baseMaps"
          :key="key"
          :class="['map-control-btn', { active: currentBaseMap === key }]"
          @click="switchBaseMap(key)"
        >
          {{ mapStyle.name }}
        </button>
      </div>
    </div>
    <div class="map-legend">
      <template v-if="timelineMode">
        <div class="legend-item">
          <div class="legend-gradient"></div>
          <div class="legend-labels-horizontal">
            <span>Ältere</span>
            <span class="arrow">→</span>
            <span>Neuere</span>
            <span>Sichtungen</span>
          </div>
        </div>
        <div v-if="props.ringingData" class="legend-item">
          <div class="legend-marker ringing"></div>
          <span>Beringungsort</span>
        </div>
      </template>
      <template v-else>
        <div class="legend-item">
          <div class="legend-marker current"></div>
          <span>Aktuelle Sichtung</span>
        </div>
        <div class="legend-item">
          <div class="legend-marker other"></div>
          <span>Frühere Sichtungen</span>
        </div>
        <div class="legend-item">
          <div class="legend-marker approximate"></div>
          <span>Ungefähre Position</span>
        </div>
        <div v-if="props.ringingData" class="legend-item">
          <div class="legend-marker ringing"></div>
          <span>Beringungsort</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed, onUnmounted } from 'vue';
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import '@/utils/leaflet-extensions';
import type { Sighting, Ringing } from '@/types';
import { format } from 'date-fns';

const props = defineProps<{
  currentSighting?: Sighting;
  otherSightings?: Sighting[];
  ringingData?: Ringing | null;
  timelineMode?: boolean;
}>();

const mapContainer = ref<HTMLElement | null>(null);
const map = ref<L.Map | null>(null);
const currentBaseMap = ref('cartoLight');
const baseMapLayer = ref<L.TileLayer | null>(null);

const baseMaps = {
  osm: {
    name: 'Standard',
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© OpenStreetMap contributors'
  },
  cartoLight: {
    name: 'Hell',
    url: 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png',
    attribution: '© OpenStreetMap contributors, © CARTO'
  },
  cartoDark: {
    name: 'Dunkel',
    url: 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
    attribution: '© OpenStreetMap contributors, © CARTO'
  }
};

const formatDate = (date: string | undefined | null) => {
  if (!date) return '';
  return format(new Date(date), 'dd.MM.yyyy');
};

const timelineMode = computed(() => props.timelineMode);

const getTimelineColor = (date: string) => {
  const sightingDate = new Date(date);
  const now = new Date();
  const oldestDate = new Date(Math.min(...props.otherSightings!.map(s => new Date(s.date!).getTime())));
  
  const totalDays = (now.getTime() - oldestDate.getTime()) / (1000 * 60 * 60 * 24);
  const daysSince = (now.getTime() - sightingDate.getTime()) / (1000 * 60 * 60 * 24);
  
  const hue = Math.round(60 * (daysSince / totalDays));
  const saturation = 100;
  const lightness = 50;
  
  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
};

const createTimelineIcon = (date: string) => {
  const color = getTimelineColor(date);
  return L.divIcon({
    html: `<div style="
      background-color: ${color}; 
      width: 12px; 
      height: 12px; 
      border-radius: 50%; 
      border: 2px solid white;
    "></div>`,
    className: 'custom-div-icon',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
};

const createTimelineIconWithExactLocation = (date: string, isExact: boolean = true) => {
  const color = getTimelineColor(date);
  const border = isExact ? 'solid' : 'dashed';
  return L.divIcon({
    html: `<div style="
      background-color: ${color}; 
      width: 12px; 
      height: 12px; 
      border-radius: 50%; 
      border: 2px ${border} white;
    "></div>`,
    className: 'custom-div-icon',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
};

// Create marker cluster groups
const markerClusterGroup = ref<L.MarkerClusterGroup | null>(null);

// Define custom icons with approximate location variants
const createMarkerIcon = (color: string, isExact: boolean = true, size: number = 16) => {
  const border = isExact ? 'solid' : 'dashed';
  return L.divIcon({
    html: `<div style="
      background-color: ${color}; 
      width: ${size}px; 
      height: ${size}px; 
      border-radius: 50%; 
      border: 2px ${border} white;
    "></div>`,
    className: 'custom-div-icon',
    iconSize: [size, size],
    iconAnchor: [size/2, size/2]
  });
};

const currentIcon = (isExact: boolean) => createMarkerIcon('#FF4444', isExact, 16);
const otherIcon = (isExact: boolean) => createMarkerIcon('#FFB300', isExact, 12);
const ringingIcon = createMarkerIcon('#4CAF50', true, 16);

const initMap = () => {
  if (!mapContainer.value) return;

  // Default to a central point (e.g., center of Germany)
  const defaultCenter: [number, number] = [51.1657, 10.4515];

  // Find initial center from available coordinates
  let initialCenter = defaultCenter;
  if (props.currentSighting?.lat && props.currentSighting?.lon) {
    initialCenter = [props.currentSighting.lat, props.currentSighting.lon];
  } else if (props.otherSightings?.[0]?.lat && props.otherSightings[0]?.lon) {
    initialCenter = [props.otherSightings[0].lat, props.otherSightings[0].lon];
  } else if (props.ringingData?.lat && props.ringingData?.lon) {
    initialCenter = [props.ringingData.lat, props.ringingData.lon];
  }

  // Initialize map
  map.value = L.map(mapContainer.value).setView(initialCenter, 13);

  // Add initial base map
  const initialMap = baseMaps[currentBaseMap.value];
  baseMapLayer.value = L.tileLayer(initialMap.url, {
    attribution: initialMap.attribution
  }).addTo(map.value);

  // Add CSS for markers
  const style = document.createElement('style');
  style.textContent = `
    .custom-div-icon {
      background: none !important;
      border: none !important;
    }
    .custom-div-icon div {
      box-shadow: 0 0 3px rgba(0,0,0,0.3);
    }
  `;
  document.head.appendChild(style);

  // Initialize marker cluster group
  markerClusterGroup.value = L.markerClusterGroup({
    maxClusterRadius: 30,
    spiderfyOnMaxZoom: true,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true,
    disableClusteringAtZoom: 16
  });

  map.value.addLayer(markerClusterGroup.value);

  updateMarkers();
};

// Add cleanup function
const cleanup = () => {
  if (map.value) {
    map.value.remove();
    map.value = null;
  }
  if (markerClusterGroup.value) {
    markerClusterGroup.value.clearLayers();
    markerClusterGroup.value = null;
  }
  if (baseMapLayer.value) {
    baseMapLayer.value = null;
  }
};

const selectedSighting = ref<Sighting | null>(null);

const updateMarkers = () => {
  if (!map.value || !markerClusterGroup.value) return;

  // Clear existing markers
  markerClusterGroup.value.clearLayers();

  // Helper function to check if coordinates are valid
  const hasValidCoordinates = (lat: number | null | undefined, lon: number | null | undefined): boolean => {
    return lat != null && lon != null && !isNaN(lat) && !isNaN(lon);
  };

  if (timelineMode.value && props.otherSightings) {
    // Add timeline markers
    props.otherSightings.forEach(sighting => {
      if (hasValidCoordinates(sighting.lat, sighting.lon) && sighting.date) {
        const marker = L.marker(
          [sighting.lat!, sighting.lon!],
          { 
            icon: createTimelineIconWithExactLocation(sighting.date, sighting.is_exact_location ?? false),
            zIndexOffset: 0
          }
        ).on('click', () => {
          selectedSighting.value = sighting;
        });
        
        markerClusterGroup.value?.addLayer(marker);
      }
    });
  } else {
    // Add other sightings markers
    if (props.otherSightings) {
      props.otherSightings
        .filter(sighting => !props.currentSighting || sighting.id !== props.currentSighting.id)
        .forEach(sighting => {
          if (hasValidCoordinates(sighting.lat, sighting.lon)) {
            const marker = L.marker(
              [sighting.lat!, sighting.lon!],
              { 
                icon: otherIcon(sighting.is_exact_location ?? false),
                zIndexOffset: 0
              }
            ).on('click', () => {
              selectedSighting.value = sighting;
            });
            
            markerClusterGroup.value?.addLayer(marker);
          }
        });
    }

    // Add current sighting marker
    if (props.currentSighting && hasValidCoordinates(props.currentSighting.lat, props.currentSighting.lon)) {
      const currentMarker = L.marker(
        [props.currentSighting.lat!, props.currentSighting.lon!],
        { 
          icon: currentIcon(props.currentSighting.is_exact_location ?? false),
          zIndexOffset: 1000
        }
      ).on('click', () => {
        selectedSighting.value = props.currentSighting!;
      });
      
      map.value.addLayer(currentMarker);
    }
  }

  // Add ringing marker if available
  if (props.ringingData && hasValidCoordinates(props.ringingData.lat, props.ringingData.lon)) {
    const ringingMarker = L.marker(
      [props.ringingData.lat!, props.ringingData.lon!],
      { 
        icon: ringingIcon,
        zIndexOffset: 2000
      }
    ).on('click', () => {
      // For ringing data, we could show a different kind of info or disable click
    });
    
    map.value.addLayer(ringingMarker);
  }

  // Adjust bounds
  const bounds = L.latLngBounds([]);
  let hasPoints = false;
  
  if (props.currentSighting && hasValidCoordinates(props.currentSighting.lat, props.currentSighting.lon)) {
    bounds.extend([props.currentSighting.lat!, props.currentSighting.lon!]);
    hasPoints = true;
  }
  if (props.ringingData && hasValidCoordinates(props.ringingData.lat, props.ringingData.lon)) {
    bounds.extend([props.ringingData.lat!, props.ringingData.lon!]);
    hasPoints = true;
  }
  props.otherSightings?.forEach(s => {
    if (hasValidCoordinates(s.lat, s.lon)) {
      bounds.extend([s.lat!, s.lon!]);
      hasPoints = true;
    }
  });
  if (hasPoints) {
    map.value.fitBounds(bounds, { padding: [50, 50] });
  }
};

const switchBaseMap = (mapKey: string) => {
  if (!map.value || !baseMapLayer.value) return;
  
  currentBaseMap.value = mapKey;
  const newMap = baseMaps[mapKey];
  
  // Remove current base layer
  baseMapLayer.value.remove();
  
  // Add new base layer
  baseMapLayer.value = L.tileLayer(newMap.url, {
    attribution: newMap.attribution
  }).addTo(map.value);
};

// Add onUnmounted lifecycle hook
onUnmounted(() => {
  cleanup();
});

// Modify the watch to handle cleanup
watch(
  () => [props.currentSighting, props.otherSightings, props.ringingData],
  () => {
    if (map.value) {
      map.value.closePopup(); // Close any open popups before updating
      updateMarkers();
    }
  },
  { deep: true }
);

onMounted(() => {
  initMap();
});
</script>

<style scoped>
.map-legend {
  background: white;
  padding: 8px 12px;
  border-radius: 4px;
  margin-top: 8px;
  display: flex;
  gap: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-marker {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 0 3px rgba(0,0,0,0.3);
}

.legend-marker.current {
  background-color: #FF4444;
}

.legend-marker.other {
  background-color: #FFB300;
  width: 12px;
  height: 12px;
}

.legend-marker.ringing {
  background-color: #4CAF50;
}

.legend-marker.approximate {
  border: 2px dashed white !important;
  background-color: #FFB300;
  width: 12px;
  height: 12px;
}

.custom-div-icon {
  background: none !important;
  border: none !important;
}

.custom-div-icon div {
  box-shadow: 0 0 3px rgba(0,0,0,0.3);
}

.legend-gradient {
  width: 100px;
  height: 16px;
  background: linear-gradient(to right, hsl(60, 100%, 50%), hsl(0, 100%, 50%));
  border-radius: 4px;
}

.legend-labels-horizontal {
  display: flex;
  align-items: center;
  margin-left: 8px;
  font-size: 0.8rem;
  gap: 4px;
}

.legend-labels-horizontal .arrow {
  color: #666;
  font-weight: bold;
}

.legend-labels-horizontal span:last-child {
  margin-left: 4px;
}

.map-wrapper {
  position: relative;
}

.map-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  display: flex;
  background: white;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  overflow: hidden;
}

.map-control-btn {
  padding: 6px 12px;
  border: none;
  background: white;
  color: rgba(0, 0, 0, 0.7);
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.15s ease;
  border-right: 1px solid rgba(0, 0, 0, 0.08);
}

.map-control-btn:last-child {
  border-right: none;
}

.map-control-btn:hover {
  background: rgba(0, 0, 0, 0.04);
}

.map-control-btn.active {
  background: rgb(var(--v-theme-primary));
  color: white;
}

/* Override marker cluster default styles */
:deep(.marker-cluster) {
  background-color: rgba(255, 255, 255, 0.8);
  border: 2px solid #fff;
  box-shadow: 0 0 3px rgba(0,0,0,0.3);
  width: 30px !important;
  height: 30px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  margin-left: -15px !important;
  margin-top: -15px !important;
}

:deep(.marker-cluster div) {
  background-color: rgba(34, 128, 150, 0.8);
  color: white;
  width: 26px;
  height: 26px;
  margin: 0 !important;
  text-align: center;
  border-radius: 13px;
  font-size: 12px;
  line-height: 26px;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

.v-card-text {
  padding: 12px 16px !important;
}
</style>