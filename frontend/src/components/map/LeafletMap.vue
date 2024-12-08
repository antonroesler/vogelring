<template>
  <div ref="mapContainer" style="height: 400px; width: 100%"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';

const props = defineProps<{
  latitude: number;
  longitude: number;
}>();

const emit = defineEmits<{
  'update:latitude': [value: number];
  'update:longitude': [value: number];
}>();

const mapContainer = ref<HTMLElement | null>(null);
const map = ref<L.Map | null>(null);
const marker = ref<L.Marker | null>(null);

onMounted(() => {
  if (!mapContainer.value) return;

  map.value = L.map(mapContainer.value).setView([50.1109, 8.6821], 13); // Frankfurt am Main

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value);

  marker.value = L.marker([props.latitude || 50.1109, props.longitude || 8.6821], {
    draggable: true
  }).addTo(map.value);

  marker.value.on('dragend', (event) => {
    const latLng = event.target.getLatLng();
    emit('update:latitude', latLng.lat);
    emit('update:longitude', latLng.lng);
  });

  map.value.on('click', (event) => {
    const latLng = event.latlng;
    marker.value?.setLatLng(latLng);
    emit('update:latitude', latLng.lat);
    emit('update:longitude', latLng.lng);
  });
});

watch([() => props.latitude, () => props.longitude], ([newLat, newLng]) => {
  if (marker.value && newLat && newLng) {
    marker.value.setLatLng([newLat, newLng]);
    map.value?.setView([newLat, newLng]);
  }
});
</script>