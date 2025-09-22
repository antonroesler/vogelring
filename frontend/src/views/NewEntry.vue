<template>
  <v-card class="mb-4 new-entry-card">
    <v-card-title class="d-flex align-center">
      <v-icon icon="mdi-plus-circle" class="me-2" color="primary"></v-icon>
      <span class="card-title-text">Neuer Eintrag</span>
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
  <v-snackbar 
    v-model="showSuccessSnackbar" 
    color="success"
    class="success-snackbar"
  >
    <v-icon icon="mdi-check-circle" class="me-2"></v-icon>
    Eintrag erfolgreich gespeichert
  </v-snackbar>
  <v-snackbar 
    v-model="showErrorSnackbar" 
    color="error"
    class="error-snackbar"
  >
    <v-icon icon="mdi-alert-circle" class="me-2"></v-icon>
    {{ errorMessage }}
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useSightingsStore } from '@/stores/sightings';
import type { Sighting } from '@/types';
import SightingForm from '@/components/sightings/SightingForm.vue';
import ClearFieldsSettings from '@/components/settings/ClearFieldsSettings.vue';
import { createClearedSighting, createDefaultSighting } from '@/utils/fieldClearingUtils';

const store = useSightingsStore();
const loading = ref(false);
const showSuccessSnackbar = ref(false);
const showErrorSnackbar = ref(false);
const errorMessage = ref('Ein Fehler ist aufgetreten. Bitte versuchen Sie es erneut.');
const clearFieldsSettings = ref<Record<string, boolean>>({});

const sighting = ref<Partial<Sighting>>(createDefaultSighting());

const saveSighting = async (newSighting: Partial<Sighting>) => {
  loading.value = true;
  try {
    await store.createSighting(newSighting);
    showSuccessSnackbar.value = true;
    
    // Create new sighting object with fields cleared according to user settings
    sighting.value = createClearedSighting(newSighting, clearFieldsSettings.value);
  } catch (error) {
    console.error('Error saving sighting:', error);
    showErrorSnackbar.value = true;
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.new-entry-card {
  border-radius: 16px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
  border: 1px solid rgba(0, 67, 108, 0.1) !important;
  transition: all 0.3s ease;
}

.new-entry-card:hover {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12) !important;
  transform: translateY(-2px);
}

.card-title-text {
  font-size: 1.25rem;
  font-weight: 600;
  color: #00436C;
}

.success-snackbar :deep(.v-snackbar__wrapper) {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(76, 175, 80, 0.3);
}

.error-snackbar :deep(.v-snackbar__wrapper) {
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(244, 67, 54, 0.3);
}
</style>
