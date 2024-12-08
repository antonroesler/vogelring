<template>
  <div ref="mapContainer" style="height: 400px; width: 100%"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';
import type { BirdMeta, AnalyticsBirdMeta } from '@/types';

const props = defineProps<{
  bird: BirdMeta;
  friends: AnalyticsBirdMeta[];
}>();

const mapContainer = ref<HTMLElement | null>(null);
const map = ref<L.Map | null>(null);
const markers = ref<L.Marker[]>([]);

const createMap = () => {
  if (!mapContainer.value) return;

  // Find first sighting with coordinates to center the map
  const firstSighting = props.bird.sightings.find(s => s.lat && s.lon);
  const center = firstSighting ? [firstSighting.lat!, firstSighting.lon!] : [50.1109, 8.6821];

  map.value = L.map(mapContainer.value).setView(center as [number, number], 13);

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

  // Add selected bird's sightings (red)
  props.bird.sightings.forEach(sighting => {
    if (sighting.lat && sighting.lon) {
      const marker = L.marker([sighting.lat, sighting.lon], {
        icon: L.divIcon({
          className: 'custom-div-icon',
          html: '<div style="background-color: red; width: 10px; height: 10px; border-radius: 50%;"></div>'
        })
      }).addTo(map.value!);
      markers.value.push(marker);
    }
  });

  // Add friend birds' sightings (blue)
  props.friends.forEach(friend => {
    friend.sightings.forEach(sighting => {
      if (sighting.lat && sighting.lon) {
        const marker = L.marker([sighting.lat, sighting.lon], {
          icon: L.divIcon({
            className: 'custom-div-icon',
            html: '<div style="background-color: blue; width: 10px; height: 10px; border-radius: 50%;"></div>'
          })
        }).addTo(map.value!);
        markers.value.push(marker);
      }
    });
  });

  // Fit bounds to include all markers
  if (markers.value.length > 0) {
    const group = L.featureGroup(markers.value);
    map.value.fitBounds(group.getBounds().pad(0.1));
  }
};

onMounted(createMap);

watch([() => props.bird, () => props.friends], () => {
  updateMarkers();
}, { deep: true });
</script>