<template>
  <v-card>
    <v-card-title class="d-flex align-center">
      Vogel Details
      <v-spacer></v-spacer>
      <v-btn
        v-if="bird"
        icon
        variant="text"
        :to="`/birds/${bird.ring}`"
        v-tooltip="'Detailansicht öffnen'"
      >
        <v-icon>mdi-open-in-new</v-icon>
      </v-btn>
    </v-card-title>
    <v-card-text>
      <v-progress-circular
        v-if="!bird"
        indeterminate
        color="primary"
        class="ma-4"
      ></v-progress-circular>

      <template v-else>
        <v-list>
          <v-list-item>
            <v-list-item-title>Spezies</v-list-item-title>
            <v-list-item-subtitle>{{ bird.species }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Ring</v-list-item-title>
            <v-list-item-subtitle>{{ bird.ring }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Anzahl Sichtungen</v-list-item-title>
            <v-list-item-subtitle>{{ bird.sighting_count }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Erste Sichtung</v-list-item-title>
            <v-list-item-subtitle>{{ formatDate(bird.first_seen) }}</v-list-item-subtitle>
          </v-list-item>
          <v-list-item>
            <v-list-item-title>Letzte Sichtung</v-list-item-title>
            <v-list-item-subtitle>{{ formatDate(bird.last_seen) }}</v-list-item-subtitle>
          </v-list-item>
        </v-list>

        <v-divider class="my-4"></v-divider>

        <h3 class="text-h6 mb-2">Beringungsdaten</h3>
        
        <v-progress-circular
          v-if="isLoadingRinging"
          indeterminate
          color="primary"
          size="24"
          class="ma-2"
        ></v-progress-circular>

        <template v-else-if="ringingData">
          <v-list>
            <v-list-item>
              <v-list-item-title>Beringungsdatum</v-list-item-title>
              <v-list-item-subtitle>{{ formatDate(ringingData.date) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Beringungsort</v-list-item-title>
              <v-list-item-subtitle>{{ ringingData.place }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Beringer</v-list-item-title>
              <v-list-item-subtitle>{{ ringingData.ringer }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Ring Schema</v-list-item-title>
              <v-list-item-subtitle>{{ ringingData.ring_scheme }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Alter bei Beringung</v-list-item-title>
              <v-list-item-subtitle>{{ formatAge(ringingData.age) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Geschlecht</v-list-item-title>
              <v-list-item-subtitle>{{ formatSex(ringingData.sex) }}</v-list-item-subtitle>
            </v-list-item>
            <v-list-item>
              <v-list-item-title>Koordinaten</v-list-item-title>
              <v-list-item-subtitle>
                {{ formatCoordinates(ringingData.lat, ringingData.lon) }}
                <v-btn
                  icon="mdi-map-marker"
                  size="small"
                  variant="text"
                  density="compact"
                  :href="getGoogleMapsLink(ringingData.lat, ringingData.lon)"
                  target="_blank"
                  class="ms-2"
                  v-tooltip="'In Google Maps öffnen'"
                >
                </v-btn>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </template>
        <p v-else class="text-body-1 text-medium-emphasis">
          Keine Beringungsdaten verfügbar.
        </p>

        <v-divider class="my-4"></v-divider>

        <h3 class="text-h6 mb-2">Andere Artenbestimmungen</h3>
        <v-list v-if="Object.keys(bird.other_species_identifications).length > 0">
          <v-list-item v-for="(count, species) in bird.other_species_identifications" :key="species">
            <v-list-item-title>{{ species }}</v-list-item-title>
            <v-list-item-subtitle>{{ count }} mal</v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <p v-else class="text-body-1">Ausschließlich als {{ bird.species }} identifiziert.</p>
      </template>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue';
import { format } from 'date-fns';
import type { BirdMeta, Ringing } from '@/types';
import * as api from '@/api';

const props = defineProps<{
  bird: BirdMeta | null;
}>();

const ringingData = ref<Ringing | null>(null);
const isLoadingRinging = ref(false);

const loadRingingData = async (ring: string) => {
  isLoadingRinging.value = true;
  try {
    ringingData.value = await api.getRingingByRing(ring);
  } catch (error) {
    console.error('Error loading ringing data:', error);
  } finally {
    isLoadingRinging.value = false;
  }
};

watch(() => props.bird?.ring, (newRing) => {
  if (newRing) {
    loadRingingData(newRing);
  }
}, { immediate: true });

const formatDate = (date: string) => {
  return format(new Date(date), 'dd.MM.yyyy');
};

const formatAge = (age: number) => {
  // This is a simplified example - adjust based on your age coding system
  switch (age) {
    case 1: return 'Nestling (1)';
    case 2: return 'Flügge (2)';
    case 3: return 'Juvenil (3)';
    case 4: return 'Adult (4)';
    default: return `Code ${age}`;
  }
};

const formatSex = (sex: number) => {
  switch (sex) {
    case 1: return 'Männlich (1)';
    case 2: return 'Weiblich (2)';
    case 0: return 'Unbekannt (0)';
    default: return `Code ${sex}`;
  }
};

const formatCoordinates = (lat: number, lon: number) => {
  return `${lat.toFixed(6)}°, ${lon.toFixed(6)}°`;
};

const getGoogleMapsLink = (lat: number, lon: number) => {
  return `https://www.google.com/maps?q=${lat},${lon}`;
};
</script>

<style scoped>
.v-list-item-subtitle {
  display: flex;
  align-items: center;
}
</style>