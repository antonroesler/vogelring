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
  <v-snackbar v-model="showSuccessSnackbar" color="success">
    Eintrag erfolgreich gespeichert
  </v-snackbar>
  <v-snackbar v-model="showErrorSnackbar" color="error">
    {{ errorMessage }}
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useSightingsStore } from '@/stores/sightings';
import type { Sighting } from '@/types';
import SightingForm from '@/components/sightings/SightingForm.vue';

const store = useSightingsStore();
const loading = ref(false);
const showSuccessSnackbar = ref(false);
const showErrorSnackbar = ref(false);
const errorMessage = ref('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');

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
    showSuccessSnackbar.value = true;
    
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
    showErrorSnackbar.value = true;
  } finally {
    loading.value = false;
  }
};
</script>