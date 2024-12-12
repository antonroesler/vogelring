<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';

const props = defineProps<{
  latitude: number;
  longitude: number;
  radius?: number; // in meters
}>();

const emit = defineEmits<{
  'update:latitude': [value: number];
  'update:longitude': [value: number];
}>();

const mapContainer = ref<HTMLElement | null>(null);
const map = ref<L.Map | null>(null);
const marker = ref<L.Marker | null>(null);
const circle = ref<L.Circle | null>(null);

const updateCircle = (lat: number, lng: number, radius: number) => {
  if (!map.value) return;

  // Remove existing circle
  if (circle.value) {
    circle.value.remove();
  }

  // Add new circle
  circle.value = L.circle([lat, lng], {
    radius: radius,
    color: '#2196F3',
    fillColor: '#2196F3',
    fillOpacity: 0.1,
    weight: 2
  }).addTo(map.value);
};

const initMap = () => {
  if (!mapContainer.value || map.value) return;

  const initialLat = props.latitude || 50.1109;
  const initialLon = props.longitude || 8.6821;

  map.value = L.map(mapContainer.value).setView([initialLat, initialLon], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value);

  marker.value = L.marker([initialLat, initialLon], {
    draggable: true
  }).addTo(map.value);

  if (props.radius) {
    updateCircle(initialLat, initialLon, props.radius);
  }

  marker.value.on('dragend', (event) => {
    const latLng = event.target.getLatLng();
    emit('update:latitude', latLng.lat);
    emit('update:longitude', latLng.lng);
    map.value?.setView(latLng);
    if (props.radius) {
      updateCircle(latLng.lat, latLng.lng, props.radius);
    }
  });

  map.value.on('click', (event) => {
    const latLng = event.latlng;
    marker.value?.setLatLng(latLng);
    emit('update:latitude', latLng.lat);
    emit('update:longitude', latLng.lng);
    map.value?.setView(latLng);
    if (props.radius) {
      updateCircle(latLng.lat, latLng.lng, props.radius);
    }
  });

  // Force a resize after initialization
  setTimeout(() => {
    map.value?.invalidateSize();
  }, 100);
};

onMounted(() => {
  initMap();
});

watch([() => props.latitude, () => props.longitude], ([newLat, newLng]) => {
  if (marker.value && newLat && newLng) {
    marker.value.setLatLng([newLat, newLng]);
    map.value?.setView([newLat, newLng]);
    if (props.radius) {
      updateCircle(newLat, newLng, props.radius);
    }
  }
});

watch(() => props.radius, (newRadius) => {
  if (newRadius && props.latitude && props.longitude) {
    updateCircle(props.latitude, props.longitude, newRadius);
  }
});
</script>

<style scoped>
.map-container {
  height: 400px;
  width: 100%;
  position: relative;
  z-index: 0;
}
</style>