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
  const coordMap = new Map<string, { ring: string; color: string; isExact: boolean }[]>();

  // Helper function to get coordinate key
  const getCoordKey = (lat: number, lon: number) => `${lat},${lon}`;

  // First, group all friend sightings by coordinates
  props.friends.forEach(friend => {
    const color = props.friendColors?.[friend.ring] || 'blue';
    friend.sightings.forEach(sighting => {
      if (sighting.lat && sighting.lon) {
        const key = getCoordKey(sighting.lat, sighting.lon);
        if (!coordMap.has(key)) {
          coordMap.set(key, []);
        }
        coordMap.get(key)?.push({
          ring: friend.ring,
          color,
          isExact: sighting.is_exact_location ?? false
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
        isExact: sighting.is_exact_location ?? false
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
        birds.length > 1 ? '#9C27B0' : birds[0].color,  // Use purple for multiple birds
        isExact,
        birds.length > 1 ? 14 : 10  // Larger marker for multiple birds
      ),
      zIndexOffset: birds.some(b => b.ring === props.bird.ring) ? 1000 : 100
    })
    .bindTooltip(L.tooltip({
      permanent: false,
      direction: 'top',
      offset: [0, birds.length > 1 ? -12 : -8],
      opacity: 0.9,
      className: 'multi-bird-tooltip'
    }).setContent(tooltipContent));

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
</style>