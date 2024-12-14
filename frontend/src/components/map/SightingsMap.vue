<template>
  <div>
    <div ref="mapContainer" style="height: 400px;"></div>
    <div class="map-controls">
      <v-btn-group density="compact" variant="outlined">
        <v-btn
          v-for="(map, key) in baseMaps"
          :key="key"
          :active="currentBaseMap === key"
          @click="switchBaseMap(key)"
          size="small"
        >
          {{ map.name }}
        </v-btn>
      </v-btn-group>
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
        <div v-if="props.ringingData" class="legend-item">
          <div class="legend-marker ringing"></div>
          <span>Beringungsort</span>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue';
import L from 'leaflet';
import type { Sighting, Ringing } from '@/types';

const props = defineProps<{
  currentSighting?: Sighting;
  otherSightings?: Sighting[];
  ringingData?: Ringing | null;
  timelineMode?: boolean;
}>();

const mapContainer = ref<HTMLElement | null>(null);
const map = ref<L.Map | null>(null);
const currentBaseMap = ref('osm');
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

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  });
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
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>`,
    className: 'custom-div-icon',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
};

// Define custom icons
const currentIcon = L.divIcon({
  html: '<div style="background-color: #FF4444; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white;"></div>',
  className: 'custom-div-icon',
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

const otherIcon = L.divIcon({
  html: '<div style="background-color: #FFB300; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white;"></div>',
  className: 'custom-div-icon',
  iconSize: [16, 16],
  iconAnchor: [8, 8]
});

const ringingIcon = L.divIcon({
  html: '<div style="background-color: #4CAF50; width: 16px; height: 16px; border-radius: 50%; border: 2px solid white;"></div>',
  className: 'custom-div-icon',
  iconSize: [20, 20],
  iconAnchor: [10, 10]
});

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

  updateMarkers();
};

const updateMarkers = () => {
  if (!map.value) return;

  // Clear existing markers
  map.value.eachLayer((layer) => {
    if (layer instanceof L.Marker) {
      map.value?.removeLayer(layer);
    }
  });

  // Helper function to check if coordinates are valid
  const hasValidCoordinates = (lat: number | null | undefined, lon: number | null | undefined): boolean => {
    return lat != null && lon != null && !isNaN(lat) && !isNaN(lon);
  };

  if (timelineMode.value && props.otherSightings) {
    // Add timeline markers
    props.otherSightings.forEach(sighting => {
      if (hasValidCoordinates(sighting.lat, sighting.lon) && sighting.date) {
        L.marker(
          [sighting.lat!, sighting.lon!],
          { 
            icon: createTimelineIcon(sighting.date),
            zIndexOffset: 0
          }
        )
          .addTo(map.value!)
          .bindPopup(`Sichtung am ${formatDate(sighting.date)}`);
      }
    });
  } else {
    if (props.otherSightings) {
      props.otherSightings
        .filter(sighting => !props.currentSighting || sighting.id !== props.currentSighting.id)
        .forEach(sighting => {
          if (hasValidCoordinates(sighting.lat, sighting.lon)) {
            L.marker(
              [sighting.lat!, sighting.lon!],
              { 
                icon: otherIcon,
                zIndexOffset: 0
              }
            )
              .addTo(map.value!)
              .bindPopup(`Sichtung am ${formatDate(sighting.date)}`);
          }
        });
    }

    // Add current sighting marker last (on top)
    if (props.currentSighting && hasValidCoordinates(props.currentSighting.lat, props.currentSighting.lon)) {
      L.marker(
        [props.currentSighting.lat!, props.currentSighting.lon!],
        { 
          icon: currentIcon,
          zIndexOffset: 1000
        }
      )
        .addTo(map.value)
        .bindPopup(`Aktuelle Sichtung (${formatDate(props.currentSighting.date)})`);
    }
  }

  // Always add ringing marker if available (on top of everything)
  if (props.ringingData && hasValidCoordinates(props.ringingData.lat, props.ringingData.lon)) {
    L.marker(
      [props.ringingData.lat!, props.ringingData.lon!],
      { 
        icon: ringingIcon,
        zIndexOffset: 2000
      }
    )
      .addTo(map.value)
      .bindPopup(`Beringungsort (${formatDate(props.ringingData.date)})`);
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

// Watch for changes in sightings
watch(
  () => [props.currentSighting, props.otherSightings, props.ringingData],
  () => {
    if (map.value) {
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

.map-controls {
  position: absolute;
  top: 10px;
  right: 10px;
  z-index: 1000;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
</style>