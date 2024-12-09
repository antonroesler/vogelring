<template>
  <div>
    <h1 class="text-h4 mb-4">Eintrag Details</h1>

    <v-row>
      <v-col cols="12" md="8">
        <v-card class="mb-4">
          <v-card-title>Sichtung bearbeiten</v-card-title>
          <v-card-text>
            <sighting-form
              :sighting="sighting"
              :loading="loading"
              @submit="updateSighting"
            ></sighting-form>
          </v-card-text>
        </v-card>
      </v-col>

      <v-col cols="12" md="4">
        <bird-details
          v-if="birdDetails"
          :bird="birdDetails"
          class="mb-4"
        ></bird-details>
      </v-col>

      <v-col cols="12">
        <v-card class="mb-4">
          <v-card-title>Sichtungen Karte</v-card-title>
          <v-card-text>
            <sightings-map
              v-if="sighting"
              :current-sighting="sighting"
              :other-sightings="birdDetails?.sightings"
            ></sightings-map>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-snackbar
      v-model="showSnackbar"
      color="success"
    >
      Eintrag erfolgreich gespeichert
    </v-snackbar>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import type { Sighting, BirdMeta } from '@/types';
import * as api from '@/api';
import SightingForm from '@/components/sightings/SightingForm.vue';
import BirdDetails from '@/components/birds/BirdDetails.vue';
import SightingsMap from '@/components/map/SightingsMap.vue';
import { useSightingsStore } from '@/stores/sightings';

const route = useRoute();
const sighting = ref<Sighting | null>(null);
const birdDetails = ref<BirdMeta | null>(null);
const loading = ref(false);
const showSnackbar = ref(false);
const store = useSightingsStore();

const loadSighting = async () => {
  const id = route.params.id as string;
  try {
    sighting.value = await api.getSightingById(id);
    if (sighting.value?.ring) {
      birdDetails.value = await api.getBirdByRing(sighting.value.ring);
    }
  } catch (error) {
    console.error('Error loading sighting:', error);
  }
};

const updateSighting = async (updatedSighting: Partial<Sighting>) => {
  loading.value = true;
  try {
    await store.updateSighting(updatedSighting);
    showSnackbar.value = true;
    await loadSighting(); // Reload the current sighting details
  } catch (error) {
    console.error('Error updating sighting:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(loadSighting);
</script>