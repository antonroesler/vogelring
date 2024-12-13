<template>
  <div ref="mapContainer" style="height: 400px;"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';
import type { Sighting } from '@/types';

const props = defineProps<{
  currentSighting: Sighting;
  otherSightings?: Sighting[];
}>();

const mapContainer = ref<HTMLElement | null>(null);
const map = ref<L.Map | null>(null);

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('de-DE', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
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

const initMap = () => {
  if (!mapContainer.value) return;

  // Initialize map
  map.value = L.map(mapContainer.value).setView(
    [props.currentSighting.lat, props.currentSighting.lon],
    13
  );

  // Add tile layer
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
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

  // Add current sighting marker
  L.marker(
    [props.currentSighting.lat, props.currentSighting.lon],
    { icon: currentIcon }
  )
    .addTo(map.value)
    .bindPopup(`Aktuelle Sichtung (${formatDate(props.currentSighting.date)})`);

  // Add other sightings markers
  if (props.otherSightings) {
    props.otherSightings
      .filter(sighting => sighting.id !== props.currentSighting.id)
      .forEach(sighting => {
        if (sighting.lat && sighting.lon) {
          L.marker(
            [sighting.lat, sighting.lon],
            { icon: otherIcon }
          )
            .addTo(map.value!)
            .bindPopup(`Sichtung am ${formatDate(sighting.date)}`);
        }
      });
  }
};

// Watch for changes in sightings
watch(
  () => [props.currentSighting, props.otherSightings],
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
.custom-div-icon {
  background: none !important;
  border: none !important;
}
.custom-div-icon div {
  box-shadow: 0 0 3px rgba(0,0,0,0.3);
}
</style>