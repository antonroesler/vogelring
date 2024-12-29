<template>
  <v-app>
    <v-app-bar flat color="primary">
      <v-app-bar-title class="text-white">
        Vogelring 
        <span class="text-caption ms-2" v-if="version">v{{ version }}</span>
      </v-app-bar-title>
      <v-spacer></v-spacer>
      <v-btn 
        to="/new-entry" 
        variant="text"
        color="white"
      >Neuer Eintrag</v-btn>
      <v-btn 
        to="/entries" 
        variant="text"
        color="white"
      >Eintragliste</v-btn>
      <v-btn 
        to="/statistics" 
        variant="text"
        color="white"
      >Statistiken</v-btn>
    </v-app-bar>

    <v-main>
      <v-container class="px-6">
        <router-view :key="$route.fullPath"></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { api } from './api';

const version = ref<string>();

onMounted(async () => {
  try {
    const response = await api.get('/health');
    version.value = response.data.version;
  } catch (error) {
    console.error('Failed to fetch version:', error);
  }
});
</script>

<style>
.v-btn {
  margin-left: 8px;
  text-transform: none;
  font-weight: 400;
  box-shadow: none !important;
}

/* Style for disabled buttons */
.v-btn.v-btn--disabled {
  background-color: #E0E0E0 !important;
  color: #FFFFFF !important;
  opacity: 1 !important;
}

.v-card {
  border: 1px solid #E0E0E0 !important;
  box-shadow: none !important;
}

.v-text-field .v-field {
  box-shadow: none !important;
  border: 1px solid #E0E0E0 !important;
  border-radius: 8px !important;
}

.v-text-field .v-field:hover {
  border-color: #BDBDBD !important;
}

.v-text-field .v-field--focused {
  border-color: var(--v-primary-base) !important;
}

/* Remove underline from input fields */
.v-field__outline {
  --v-field-border-width: 0 !important;
}

/* Remove underline from select fields as well */
.v-select .v-field__outline {
  --v-field-border-width: 0 !important;
}
</style>