<template>
  <v-card class="mb-4">
    <v-card-title>Neuer Eintrag</v-card-title>
    <v-card-text>
      <sighting-form
        :sighting="sighting"
        :loading="loading"
        :is-new-entry="true"
        :show-bird-suggestions="true"
        :show-place-suggestions="true"
        :show-coordinates="true"
        @submit="saveSighting"
      />
    </v-card-text>
  </v-card>
  <v-snackbar v-model="showSnackbar" color="success">
    Eintrag erfolgreich gespeichert
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useSightingsStore } from '@/stores/sightings';
import type { Sighting } from '@/types';
import SightingForm from '@/components/sightings/SightingForm.vue';

const store = useSightingsStore();
const loading = ref(false);
const showSnackbar = ref(false);

const sighting = ref<Partial<Sighting>>({
  date: new Date().toISOString().split('T')[0],
  lat: 50.1109,
  lon: 8.6821,
  melded: false
});

const saveSighting = async (newSighting: Partial<Sighting>) => {
  loading.value = true;
  try {
    await store.createSighting(newSighting);
    showSnackbar.value = true;
    
    // Reset form except for place, date, and coordinates
    const { place, date, lat, lon } = newSighting;
    sighting.value = {
      place,
      date,
      lat,
      lon,
      melded: false
    };
  } catch (error) {
    console.error('Error saving sighting:', error);
  } finally {
    loading.value = false;
  }
};
</script>