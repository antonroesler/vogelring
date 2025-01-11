<template>
  <div ref="mapContainer" style="height: 400px; width: 100%"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';
import type { BirdMeta, AnalyticsBirdMeta } from '@/types';

const props = defineProps<{
  bird: BirdMeta;
  friends: AnalyticsBirdMeta[];
  friendColors?: Record<string, string>;
}>();

const mapContainer = ref<HTMLElement | null>(null);
const map = ref<L.Map | null>(null);
const markerClusterGroup = ref<L.MarkerClusterGroup | null>(null);

const createMarkerIcon = (color: string, isExact: boolean = true, size: number = 10) => {
  const border = isExact ? 'solid' : 'dashed';
  return L.divIcon({
    className: 'custom-div-icon',
    html: `<div style="
      background-color: ${color}; 
      opacity: 0.85; 
      width: ${size}px; 
      height: ${size}px; 
      border-radius: 50%; 
      border: 2px ${border} rgba(255,255,255,0.9);
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

  map.value = L.map(mapContainer.value).setView(center as [number, number], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value);

  // Initialize marker cluster group
  markerClusterGroup.value = L.markerClusterGroup({
    maxClusterRadius: 30,
    spiderfyOnMaxZoom: false,
    showCoverageOnHover: false,
    zoomToBoundsOnClick: true,
    disableClusteringAtZoom: 16
  });

  // Override the default cluster click behavior
  markerClusterGroup.value.on('clusterclick', (event) => {
    const cluster = event.layer;
    const map = event.target._map;
    const clusterLatLng = cluster.getLatLng();
    
    // Prevent the default zoom behavior
    event.originalEvent.preventDefault();
    
    // Close all tooltips before zooming
    map.eachLayer((layer) => {
      if (layer.getTooltip) {
        const tooltip = layer.getTooltip();
        if (tooltip) {
          layer.closeTooltip();
        }
      }
    });
    
    // Zoom to the cluster position at zoom level 16
    map.setView(clusterLatLng, 16);
  });

  map.value.addLayer(markerClusterGroup.value);

  // Add zoom start handler to close tooltips
  map.value.on('zoomstart', () => {
    map.value?.eachLayer((layer) => {
      if (layer.getTooltip) {
        const tooltip = layer.getTooltip();
        if (tooltip) {
          layer.closeTooltip();
        }
      }
    });
  });

  updateMarkers();
};

const updateMarkers = () => {
  if (!map.value || !markerClusterGroup.value) return;

  // Clear existing markers
  markerClusterGroup.value.clearLayers();

  // Helper function to create tooltip
  const createTooltip = (content: string) => {
    return L.tooltip({
      permanent: false,
      direction: 'top',
      offset: [0, -8],
      opacity: 0.9,
    }).setContent(content);
  };

  // Add friend birds' sightings first (so they'll be below)
  props.friends.forEach(friend => {
    const color = props.friendColors?.[friend.ring] || 'blue';
    friend.sightings.forEach(sighting => {
      if (sighting.lat && sighting.lon) {
        const marker = L.marker([sighting.lat, sighting.lon], {
          icon: createMarkerIcon(color, sighting.is_exact_location ?? false, 10),
          zIndexOffset: 100
        })
          .bindTooltip(createTooltip(friend.ring))
          markerClusterGroup.value.addLayer(marker);
      }
    });
  });

  // Add selected bird's sightings last (so they'll be on top)
  props.bird.sightings.forEach(sighting => {
    if (sighting.lat && sighting.lon) {
      const marker = L.marker([sighting.lat, sighting.lon], {
        icon: createMarkerIcon('#FF0000', sighting.is_exact_location ?? false, 10),
        zIndexOffset: 1000
      })
        .bindTooltip(createTooltip(props.bird.ring))
        markerClusterGroup.value.addLayer(marker);
    }
  });

  // Fit bounds to include all markers
  if (markerClusterGroup.value.getLayers().length > 0) {
    map.value.fitBounds(markerClusterGroup.value.getBounds().pad(0.1));
  }
};

onMounted(createMap);

watch([() => props.bird, () => props.friends], () => {
  updateMarkers();
}, { deep: true });
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
</style>