<template>
  <div>
    <v-card v-if="selectedBirds" class="mb-4">
      <v-card-text>
        <div class="bird-list">
          <div class="location-header" v-if="selectedBirds.length > 1">
            <v-icon icon="mdi-map-marker" color="primary" size="small" class="me-1" />
            {{ selectedBirds.length }} Vögel an diesem Ort
          </div>
          <div 
            v-for="bird in selectedBirds" 
            :key="bird.ring"
            class="bird-info"
            :class="{ 'with-current-bird': bird.seenWithCurrentBird }"
          >
            <div class="d-flex align-center justify-space-between w-100">
              <div>
                <div class="d-flex align-center">
                  <span :style="{ color: bird.color }" class="bird-ring">{{ bird.ring }}</span>
                  <v-chip 
                    size="x-small" 
                    :color="getStatusColor(bird.seenStatus)"
                    class="ms-2"
                  >
                    {{ getStatusLabel(bird.seenStatus) }}
                  </v-chip>
                </div>
                <div class="bird-details text-medium-emphasis">
                  <span>{{ bird.species }}</span>
                  <span v-if="bird.lastSeen" class="bullet-separator">•</span>
                  <span v-if="bird.lastSeen">Zuletzt: {{ formatDate(bird.lastSeen) }}</span>
                  <span class="bullet-separator">•</span>
                  <span>{{ bird.sightingCount }} Sichtung{{ bird.sightingCount !== 1 ? 'en' : '' }}</span>
                </div>
              </div>
              <v-btn
                variant="text"
                color="primary"
                size="small"
                :to="`/birds/${bird.ring}`"
                target="_blank"
              >
                Details
                <v-icon size="small" class="ms-1">mdi-open-in-new</v-icon>
              </v-btn>
            </div>
          </div>
        </div>
        <v-btn
          variant="text"
          color="grey"
          @click="selectedBirds = null"
          size="small"
          class="close-button"
        >
          <v-icon size="small">mdi-close</v-icon>
        </v-btn>
      </v-card-text>
    </v-card>
    <div ref="mapContainer" style="height: 400px; width: 100%"></div>
    <div class="map-legend">
      <div class="legend-item">
        <div class="legend-marker" style="border-color: #FF0000"></div>
        <span>Untersuchter Vogel</span>
      </div>
      <div class="legend-item">
        <div class="legend-marker" style="border-color: #424242"></div>
        <span>Zusammen gesehen</span>
      </div>
      <div class="legend-item">
        <div class="legend-marker" style="border-color: #FFFFFF; box-shadow: 0 0 4px rgba(0,0,0,0.4)"></div>
        <span>Nicht zusammen gesehen</span>
      </div>
      <div class="legend-item">
        <div class="legend-marker approximate"></div>
        <span>Ungefähre Position</span>
      </div>
    </div>
    <div class="map-footer">
      <div class="switch-container">
        <span class="switch-label" :class="{ 'active': !showOnlyJointSightings }">
          Alle Sichtungen
        </span>
        <v-switch
          v-model="showOnlyJointSightings"
          color="success"
          density="comfortable"
          hide-details
          inset
        />
        <span class="switch-label" :class="{ 'active': showOnlyJointSightings }">
          Nur zusammen gesehen
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import '@/utils/leaflet-extensions';
import { BirdMeta, AnalyticsBirdMeta, SeenStatus } from '@/types';
import { format } from 'date-fns';

interface SelectedBird {
  ring: string;
  color: string;
  species: string;
  lastSeen: string;
  sightingCount: number;
  seenStatus: SeenStatus;
}

const props = defineProps<{
  bird: BirdMeta;
  friends: AnalyticsBirdMeta[];
  friendColors?: Record<string, string>;
  seenStatus: Record<string, SeenStatus>;
}>();

const mapContainer = ref<HTMLElement | null>(null);
const map = ref<L.Map | null>(null);
const markerClusterGroup = ref<L.MarkerClusterGroup | null>(null);
const selectedBirds = ref<SelectedBird[] | null>(null);
const showOnlyJointSightings = ref(false);

const formatDate = (date: string) => {
  return format(new Date(date), 'dd.MM.yyyy');
};

const createMarkerIcon = (seenStatus: SeenStatus, isExact: boolean = true, size: number = 10, color: string) => {
  const border = isExact ? 'solid' : 'dashed';
  let borderColor;
  switch (seenStatus) {
    case SeenStatus.CURRENT_BIRD:
      borderColor = '#FF0000';
      break;
    case SeenStatus.SEEN_TOGETHER:
      borderColor = '#424242';  // Dark grey
      break;
    case SeenStatus.SEEN_SEPARATE:
      borderColor = '#FFFFFF';
      break;
  }

  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      background-color: ${color}; 
      opacity: 0.85; 
      width: ${size}px; 
      height: ${size}px; 
      border-radius: 50%; 
      border: 2px ${border} ${borderColor};
      box-shadow: 0 0 3px rgba(0,0,0,0.3);
    "></div>`,
    iconSize: [size + 4, size + 4],
    iconAnchor: [(size + 4)/2, (size + 4)/2]
  });
};

const createMap = () => {
  if (!mapContainer.value) return;

  // Find first sighting with coordinates to center the map
  const firstSighting = props.bird.sightings.find(s => s.lat && s.lon);
  const center = firstSighting ? [firstSighting.lat!, firstSighting.lon!] : [50.1109, 8.6821];

  map.value = L.map(mapContainer.value, {
    // Disable animations at high zoom levels to prevent rendering issues
    zoomAnimation: true,
    markerZoomAnimation: false,
    fadeAnimation: true
  }).setView(center as [number, number], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value);

  // Initialize marker cluster group
  markerClusterGroup.value = L.markerClusterGroup({
    maxClusterRadius: 30,
    spiderfyOnMaxZoom: false,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true,
    disableClusteringAtZoom: 16,
    animate: false  // Disable cluster animations
  });

  // Override the default cluster click behavior
  markerClusterGroup.value.on('clusterclick', (event) => {
    const cluster = event.layer;
    const map = event.target._map;
    const clusterLatLng = cluster.getLatLng();
    
    // Prevent the default zoom behavior
    event.originalEvent.preventDefault();
    
    // Zoom to the cluster position at zoom level 16
    map.setView(clusterLatLng, 16, {
      animate: false  // Disable animation for manual zoom
    });
  });

  map.value.addLayer(markerClusterGroup.value);

  // Handle zoom levels
  map.value.on('zoomend', () => {
    const currentZoom = map.value?.getZoom();
    if (map.value) {
      // Toggle animations based on zoom level
      map.value.options.zoomAnimation = !(currentZoom && currentZoom >= 16);
    }
  });

  updateMarkers();
};

const updateMarkers = () => {
  if (!map.value || !markerClusterGroup.value) return;

  // Clear existing markers
  markerClusterGroup.value.clearLayers();

  // Create a map to group sightings by coordinates
  const coordMap = new Map<string, { ring: string; color: string; isExact: boolean; sightingId: string; seenStatus: SeenStatus }[]>();

  // Helper function to get coordinate key
  const getCoordKey = (lat: number, lon: number) => `${lat},${lon}`;

  // First, group all friend sightings by coordinates
  props.friends.forEach(friend => {
    const color = props.friendColors?.[friend.ring] || 'blue';
    friend.sightings.forEach(sighting => {
      if (sighting.lat && sighting.lon) {
        // Skip if we're only showing joint sightings and this sighting wasn't together
        if (showOnlyJointSightings.value && 
            (!sighting.id || props.seenStatus[sighting.id] !== SeenStatus.SEEN_TOGETHER)) {
          return;
        }

        const key = getCoordKey(sighting.lat, sighting.lon);
        if (!coordMap.has(key)) {
          coordMap.set(key, []);
        }
        const seenStatus = sighting.id && props.seenStatus[sighting.id] 
          ? props.seenStatus[sighting.id] 
          : SeenStatus.SEEN_SEPARATE;
        
        coordMap.get(key)?.push({
          ring: friend.ring,
          color,
          isExact: sighting.is_exact_location ?? false,
          sightingId: sighting.id || '',
          seenStatus
        });
      }
    });
  });

  // Add the current bird's sightings to the coordinate map
  props.bird.sightings.forEach(sighting => {
    if (sighting.lat && sighting.lon) {
      const key = getCoordKey(sighting.lat, sighting.lon);
      if (!coordMap.has(key)) {
        coordMap.set(key, []);
      }
      coordMap.get(key)?.push({
        ring: props.bird.ring,
        color: '#FF0000',
        isExact: sighting.is_exact_location ?? false,
        sightingId: sighting.id || '',
        seenStatus: SeenStatus.CURRENT_BIRD
      });
    }
  });

  // Create markers for each unique coordinate
  coordMap.forEach((birds, coordKey) => {
    const [lat, lon] = coordKey.split(',').map(Number);
    
    // Use the first bird's exact/inexact status for the marker style
    const isExact = birds[0].isExact;
    
    // Create tooltip content showing all birds at this location
    const tooltipContent = birds.length > 1
      ? `<div style="text-align: center;">
          <strong>${birds.length} Vögel an diesem Ort:</strong><br>
          ${birds.map(b => 
            `<span style="color: ${b.color};">${b.ring}</span>`
          ).join('<br>')}
        </div>`
      : birds[0].ring;

    // Create marker with the appropriate style
    const marker = L.marker([lat, lon], {
      icon: createMarkerIcon(
        birds[0].seenStatus || SeenStatus.SEEN_SEPARATE,
        isExact,
        birds.length > 1 ? 14 : 10,
        birds.length > 1 ? '#9C27B0' : birds[0].color
      ),
      zIndexOffset: birds.some(b => b.ring === props.bird.ring) ? 1000 : 100
    }).on('click', () => {
      selectedBirds.value = birds.map(b => {
        const friendData = props.friends.find(f => f.ring === b.ring) || 
          (b.ring === props.bird.ring ? props.bird : null);
        
        return {
          ring: b.ring,
          color: b.color,
          species: friendData?.species || 'Unbekannt',
          lastSeen: friendData?.last_seen || '',
          sightingCount: friendData?.sighting_count || 0,
          seenStatus: b.seenStatus
        };
      });
    });

    markerClusterGroup.value?.addLayer(marker);
  });

  // Fit bounds with animation disabled at high zoom
  if (markerClusterGroup.value.getLayers().length > 0) {
    const zoom = map.value?.getZoom() || 0;
    map.value?.fitBounds(markerClusterGroup.value.getBounds().pad(0.1), {
      animate: zoom < 16
    });
  }
};

onMounted(createMap);

watch([() => props.bird, () => props.friends], () => {
  updateMarkers();
}, { deep: true });

// Watch for changes in the filter switch
watch(showOnlyJointSightings, () => {
  updateMarkers();
});

const getStatusColor = (status: SeenStatus) => {
  switch (status) {
    case SeenStatus.CURRENT_BIRD:
      return 'error';  // red
    case SeenStatus.SEEN_TOGETHER:
      return 'success';  // green
    case SeenStatus.SEEN_SEPARATE:
      return 'grey';  // grey
    default:
      return 'grey';
  }
};

const getStatusLabel = (status: SeenStatus) => {
  switch (status) {
    case SeenStatus.CURRENT_BIRD:
      return 'Untersuchter Vogel';
    case SeenStatus.SEEN_TOGETHER:
      return 'Zusammen gesehen';
    case SeenStatus.SEEN_SEPARATE:
      return 'Nicht zusammen gesehen';
    default:
      return 'Unbekannt';
  }
};
</script>

<style scoped>
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

.custom-div-icon {
  background: none !important;
  border: none !important;
}

:deep(.multi-bird-tooltip) {
  .leaflet-tooltip-content {
    font-size: 0.9em;
    line-height: 1.3;
  }
}

.bird-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
  padding-right: 40px; /* Space for close button */
}

.bird-ring {
  font-family: monospace;
  font-weight: 500;
  font-size: 1.1em;
}

.bird-info {
  padding: 8px 12px;
  border-radius: 4px;
  background-color: rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(0, 0, 0, 0.08);
}

.bird-details {
  font-size: 0.9em;
  margin-top: 2px;
}

.bullet-separator {
  margin: 0 6px;
  opacity: 0.5;
}

.location-header {
  font-size: 0.9em;
  color: rgba(0, 0, 0, 0.6);
  margin-bottom: 4px;
  display: flex;
  align-items: center;
}

.close-button {
  position: absolute;
  top: 8px;
  right: 8px;
}

.v-card-text {
  padding: 12px 16px !important;
}

.map-footer {
  margin-top: 12px;
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

:deep(.v-switch) {
  margin: 0;
}

:deep(.v-switch .v-label) {
  opacity: 0.8;
}

:deep(.v-switch--selected .v-label) {
  opacity: 1;
}

.map-legend {
  background: white;
  padding: 8px 12px;
  border-radius: 4px;
  margin: 12px 0;
  display: flex;
  gap: 16px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.9em;
}

.legend-marker {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid;
  background-color: #BBBBBB;  /* neutral color for legend markers */
  box-shadow: 0 0 3px rgba(0,0,0,0.3);
}

.legend-marker.approximate {
  border: 2px dashed white !important;
  background-color: #FFB300;
}

.bird-info.with-current-bird {
  background-color: rgba(255, 0, 0, 0.05);
  border-color: rgba(255, 0, 0, 0.2);
}

.switch-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.switch-label {
  font-size: 0.9rem;
  color: rgba(0, 0, 0, 0.6);
  transition: color 0.2s ease;
}

.switch-label.active {
  color: rgba(0, 0, 0, 0.87);
  font-weight: 500;
}

:deep(.v-switch) {
  margin: 0;
  flex-shrink: 0;
}

:deep(.v-switch--inset .v-switch__track) {
  opacity: 0.2;
}

:deep(.v-switch--inset.v-switch--selected .v-switch__track) {
  opacity: 0.3;
}
</style>