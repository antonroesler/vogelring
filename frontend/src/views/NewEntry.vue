<template>
  <v-card class="mb-4">
    <v-card-title class="d-flex align-center">
      <span>Neuer Eintrag</span>
      <v-spacer></v-spacer>
      <clear-fields-settings
        v-model:settings="clearFieldsSettings"
      />
    </v-card-title>
    <v-card-text>
      <sighting-form
        :sighting="sighting"
        :loading="loading"
        :is-new-entry="true"
        :show-bird-suggestions="true"
        :show-place-suggestions="true"
        :show-coordinates="true"
        :clear-fields-settings="clearFieldsSettings"
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
import ClearFieldsSettings from '@/components/settings/ClearFieldsSettings.vue';

const store = useSightingsStore();
const loading = ref(false);
const showSuccessSnackbar = ref(false);
const showErrorSnackbar = ref(false);
const errorMessage = ref('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
const clearFieldsSettings = ref<Record<string, boolean>>({});

const sighting = ref<Partial<Sighting>>({
  date: new Date().toISOString().split('T')[0],
  melded: false,
  is_exact_location: false
});

const saveSighting = async (newSighting: Partial<Sighting>) => {
  loading.value = true;
  try {
    await store.createSighting(newSighting);
    showSuccessSnackbar.value = true;
    
    // Create new sighting object with preserved fields
    const preservedSighting: Partial<Sighting> = {};
    
    // Preserve fields based on settings
    Object.keys(newSighting).forEach(key => {
      if (!clearFieldsSettings.value[key]) {
        preservedSighting[key as keyof Sighting] = newSighting[key as keyof Sighting];
      }
    });

    // Handle coordinates together
    if (clearFieldsSettings.value.lat || clearFieldsSettings.value.lon) {
      preservedSighting.lat = null;
      preservedSighting.lon = null;
      preservedSighting.is_exact_location = false;
    } else {
      preservedSighting.lat = newSighting.lat;
      preservedSighting.lon = newSighting.lon;
      preservedSighting.is_exact_location = newSighting.is_exact_location;
    }

    preservedSighting.melded = false;
    sighting.value = preservedSighting;
  } catch (error) {
    console.error('Error saving sighting:', error);
    showErrorSnackbar.value = true;
  } finally {
    loading.value = false;
  }
};
</script>