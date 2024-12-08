<template>
  <div ref="mapContainer" style="height: 400px; width: 100%"></div>
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
const markers = ref<L.Marker[]>([]);

const createMap = () => {
  if (!mapContainer.value || !props.currentSighting.lat || !props.currentSighting.lon) return;

  map.value = L.map(mapContainer.value).setView([props.currentSighting.lat, props.currentSighting.lon], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value);

  updateMarkers();
};

const updateMarkers = () => {
  if (!map.value) return;

  // Clear existing markers
  markers.value.forEach(marker => marker.remove());
  markers.value = [];

  // Add current sighting marker (red)
  if (props.currentSighting.lat && props.currentSighting.lon) {
    const currentMarker = L.marker([props.currentSighting.lat, props.currentSighting.lon], {
      icon: L.divIcon({
        className: 'custom-div-icon',
        html: '<div style="background-color: red; width: 10px; height: 10px; border-radius: 50%;"></div>'
      })
    }).addTo(map.value);
    markers.value.push(currentMarker);
  }

  // Add other sightings markers (blue)
  props.otherSightings?.forEach(sighting => {
    if (sighting.lat && sighting.lon) {
      const marker = L.marker([sighting.lat, sighting.lon], {
        icon: L.divIcon({
          className: 'custom-div-icon',
          html: '<div style="background-color: blue; width: 10px; height: 10px; border-radius: 50%;"></div>'
        })
      }).addTo(map.value);
      markers.value.push(marker);
    }
  });
};

onMounted(createMap);

watch([() => props.currentSighting, () => props.otherSightings], () => {
  updateMarkers();
}, { deep: true });
</script>