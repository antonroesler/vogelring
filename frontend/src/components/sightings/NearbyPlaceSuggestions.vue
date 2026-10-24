<template>
  <div v-if="hasCoordinates" class="nearby-places mt-3">
    <!-- Non-blocking plausibility hint: place name vs. marker position -->
    <v-alert
      v-if="check?.warning && check.message"
      type="warning"
      variant="tonal"
      density="compact"
      icon="mdi-map-marker-alert"
      class="mb-3 nearby-places__warning"
    >
      {{ check.message }}
    </v-alert>

    <div class="d-flex align-center mb-1">
      <v-icon icon="mdi-map-marker-radius" size="small" color="secondary" class="me-1"></v-icon>
      <span class="text-caption text-medium-emphasis">Bekannte Orte in der Nähe</span>
      <v-progress-circular
        v-if="loading"
        indeterminate
        size="14"
        width="2"
        color="secondary"
        class="ms-2"
      ></v-progress-circular>
    </div>

    <v-list
      v-if="suggestions.length"
      density="compact"
      rounded
      border
      class="nearby-places__list py-0"
    >
      <v-list-item
        v-for="suggestion in suggestions"
        :key="`${suggestion.place}|${suggestion.area ?? ''}`"
        :active="isCurrent(suggestion)"
        :title="titleFor(suggestion)"
        :subtitle="detailsFor(suggestion)"
        color="primary"
        @click="emit('select', suggestion)"
      >
        <template #prepend>
          <v-icon icon="mdi-map-marker" size="small"></v-icon>
        </template>
        <template #append>
          <v-icon v-if="isCurrent(suggestion)" icon="mdi-check" size="small"></v-icon>
        </template>
      </v-list-item>
    </v-list>
    <div v-else-if="!loading && loaded" class="text-caption text-disabled">
      Keine bekannten Orte in der Nähe
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue';
import type { NearbyPlace, PlaceCheck } from '@/types';
import { checkPlacePosition, getNearbyPlaces } from '@/api';

const props = defineProps<{
  latitude?: number | null;
  longitude?: number | null;
  place?: string | null;
  /** Maximum number of suggestions shown (default 6). */
  limit?: number;
}>();

const emit = defineEmits<{
  /** The user picked a suggestion; the parent fills place/area and keeps the marker. */
  select: [suggestion: NearbyPlace];
}>();

const NEARBY_DEBOUNCE_MS = 300;
const CHECK_DEBOUNCE_MS = 400;

const suggestions = ref<NearbyPlace[]>([]);
const loading = ref(false);
const loaded = ref(false);
const check = ref<PlaceCheck | null>(null);

const hasCoordinates = computed(
  () =>
    typeof props.latitude === 'number' &&
    typeof props.longitude === 'number' &&
    !isNaN(props.latitude) &&
    !isNaN(props.longitude)
);

const trimmedPlace = computed(() => (props.place ?? '').trim());

const isCurrent = (suggestion: NearbyPlace) =>
  trimmedPlace.value.toLowerCase() === suggestion.place.toLowerCase();

const formatDistance = (meters: number) => {
  if (meters < 1000) {
    return `${Math.max(10, Math.round(meters / 10) * 10)} m`;
  }
  const km = meters / 1000;
  return `${km.toLocaleString('de-DE', { maximumFractionDigits: km < 10 ? 1 : 0 })} km`;
};

const titleFor = (s: NearbyPlace) => (s.area ? `${s.place} · Kleinfläche: ${s.area}` : s.place);

const detailsFor = (s: NearbyPlace) => {
  const parts = [formatDistance(s.distance_m), s.count === 1 ? '1 Eintrag' : `${s.count} Einträge`];
  if (s.last_date) {
    parts.push(`zuletzt ${s.last_date.slice(0, 4)}`);
  }
  return parts.join(' · ');
};

// Debounced, sequence-guarded fetches so a stale response never overwrites a newer one.
let nearbyTimer: ReturnType<typeof setTimeout> | undefined;
let checkTimer: ReturnType<typeof setTimeout> | undefined;
let nearbySeq = 0;
let checkSeq = 0;

const fetchNearby = async (lat: number, lon: number) => {
  const seq = ++nearbySeq;
  loading.value = true;
  try {
    const result = await getNearbyPlaces(lat, lon, { limit: props.limit ?? 6 });
    if (seq === nearbySeq) {
      suggestions.value = result;
      loaded.value = true;
    }
  } catch (error) {
    console.warn('Nearby places unavailable:', error);
    if (seq === nearbySeq) {
      suggestions.value = [];
      loaded.value = true;
    }
  } finally {
    if (seq === nearbySeq) loading.value = false;
  }
};

const fetchCheck = async (place: string, lat: number, lon: number) => {
  const seq = ++checkSeq;
  try {
    const result = await checkPlacePosition(place, lat, lon);
    if (seq === checkSeq) check.value = result;
  } catch (error) {
    console.warn('Place check unavailable:', error);
    if (seq === checkSeq) check.value = null;
  }
};

watch(
  [() => props.latitude, () => props.longitude],
  ([lat, lon]) => {
    clearTimeout(nearbyTimer);
    if (!hasCoordinates.value) {
      nearbySeq++;
      suggestions.value = [];
      loaded.value = false;
      loading.value = false;
      return;
    }
    nearbyTimer = setTimeout(() => fetchNearby(lat as number, lon as number), NEARBY_DEBOUNCE_MS);
  },
  { immediate: true }
);

// Works in both orders: marker first then place, or place typed first then marker placed.
watch(
  [trimmedPlace, () => props.latitude, () => props.longitude],
  ([place, lat, lon]) => {
    clearTimeout(checkTimer);
    if (!place || !hasCoordinates.value) {
      checkSeq++;
      check.value = null;
      return;
    }
    checkTimer = setTimeout(() => fetchCheck(place, lat as number, lon as number), CHECK_DEBOUNCE_MS);
  },
  { immediate: true }
);

onBeforeUnmount(() => {
  clearTimeout(nearbyTimer);
  clearTimeout(checkTimer);
});
</script>

<style scoped>
.nearby-places__list {
  background: rgba(0, 67, 108, 0.02);
}

.nearby-places__list :deep(.v-list-item-title) {
  font-size: 0.9rem;
  white-space: normal;
}

.nearby-places__list :deep(.v-list-item-subtitle) {
  font-size: 0.78rem;
}

.nearby-places__warning :deep(.v-alert__content) {
  font-size: 0.9rem;
}
</style>
