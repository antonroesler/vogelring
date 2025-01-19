<template>
  <div ref="mapContainer" class="map-container"></div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix marker icons
import icon from 'leaflet/dist/images/marker-icon.png';
import iconShadow from 'leaflet/dist/images/marker-shadow.png';

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41]
});

L.Marker.prototype.options.icon = DefaultIcon;

const props = defineProps<{
  latitude?: number | null;
  longitude?: number | null;
  showDefaultMarker?: boolean;
  radius?: number; // in meters
}>();

const emit = defineEmits<{
  'update:latitude': [value: number | null];
  'update:longitude': [value: number | null];
  'marker-placed': [];
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

const handleMapClick = (e: L.LeafletMouseEvent) => {
  // Remove existing marker if any
  if (marker.value) {
    map.value?.removeLayer(marker.value);
  }

  // Create new marker at clicked location
  marker.value = L.marker([e.latlng.lat, e.latlng.lng], {
    draggable: true
  }).addTo(map.value!);

  // Add dragend event listener to new marker
  marker.value.on('dragend', (event) => {
    const latLng = event.target.getLatLng();
    emit('update:latitude', latLng.lat);
    emit('update:longitude', latLng.lng);
    map.value?.setView(latLng);
    if (props.radius) {
      updateCircle(latLng.lat, latLng.lng, props.radius);
    }
  });

  // Update circle if radius is set
  if (props.radius) {
    updateCircle(e.latlng.lat, e.latlng.lng, props.radius);
  }

  // Emit the new coordinates
  emit('update:latitude', e.latlng.lat);
  emit('update:longitude', e.latlng.lng);
  emit('marker-placed');
};

const updateMarker = () => {
  if (marker.value) {
    map.value.removeLayer(marker.value);
    marker.value = null;
  }

  if (props.latitude && props.longitude) {
    marker.value = L.marker([props.latitude, props.longitude]).addTo(map.value);
  }
};

const initMap = () => {
  if (!mapContainer.value || map.value) return;

  // Center map on Frankfurt by default
  const initialLat = 50.1109;
  const initialLon = 8.6821;

  map.value = L.map(mapContainer.value).setView([initialLat, initialLon], 13);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors'
  }).addTo(map.value);

  // Only create marker if showDefaultMarker is true or if we have initial coordinates
  if ((props.showDefaultMarker && !props.latitude && !props.longitude) || 
      (props.latitude && props.longitude)) {
    const markerLat = props.latitude || initialLat;
    const markerLon = props.longitude || initialLon;
    
    marker.value = L.marker([markerLat, markerLon], {
      draggable: true
    }).addTo(map.value);

    marker.value.on('dragend', (event) => {
      const latLng = event.target.getLatLng();
      emit('update:latitude', latLng.lat);
      emit('update:longitude', latLng.lng);
      map.value?.setView(latLng);
      if (props.radius) {
        updateCircle(latLng.lat, latLng.lng, props.radius);
      }
    });

    if (props.radius) {
      updateCircle(markerLat, markerLon, props.radius);
    }
  }

  map.value.on('click', handleMapClick);

  // Force a resize after initialization
  setTimeout(() => {
    map.value?.invalidateSize();
  }, 100);
};

onMounted(() => {
  initMap();
});

watch([() => props.latitude, () => props.longitude], ([newLat, newLng]) => {
  if (marker.value) {
    map.value?.removeLayer(marker.value);
    marker.value = null;
  }

  if (newLat && newLng) {
    marker.value = L.marker([newLat, newLng], {
      draggable: true
    }).addTo(map.value!);

    marker.value.on('dragend', (event) => {
      const latLng = event.target.getLatLng();
      emit('update:latitude', latLng.lat);
      emit('update:longitude', latLng.lng);
      map.value?.setView(latLng);
      if (props.radius) {
        updateCircle(latLng.lat, latLng.lng, props.radius);
      }
    });

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