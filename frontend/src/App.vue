<template>
  <v-app>
    <v-app-bar flat color="primary">
      <!-- Left section -->
      <v-app-bar-title class="text-white">
        Vogelring 
        <span class="text-caption ms-2" v-if="version">v{{ version }}</span>
      </v-app-bar-title>

      <v-spacer></v-spacer>

      <!-- Center section with search -->
      <div class="search-container">
        <v-autocomplete
          v-model="selectedBird"
          v-model:search="searchQuery"
          :items="sortedSuggestions"
          :loading="isLoading"
          color="primary"
          hide-details
          :append-inner-icon="null"
          :no-data-append-icon="null"
          placeholder="Ring suchen..."
          item-title="ring"
          return-object
          class="bird-search"
          density="compact"
          variant="solo"
          @update:search="debouncedSearch"
          @update:model-value="onBirdSelected"
        >
          <template v-slot:item="{ props, item }">
            <v-list-item v-bind="props">
              <template v-slot:title>
                <strong>{{ item.raw.ring }}</strong> - {{ item.raw.species }}
              </template>
              <template v-slot:subtitle>
                {{ item.raw.sighting_count }} 
                Sichtung{{ item.raw.sighting_count !== 1 ? 'en' : '' }},
                zuletzt: {{ formatDate(item.raw.last_seen) }}
              </template>
            </v-list-item>
          </template>

          <!-- Add message for additional results -->
          <template v-slot:append-item v-if="totalResults > 50">
            <div class="pa-2 text-caption text-center text-medium-emphasis">
              {{ totalResults - 50 }} weitere Ergebnisse verfügbar
            </div>
          </template>
        </v-autocomplete>
      </div>

      <v-spacer></v-spacer>

      <!-- Right section -->
      <div class="navigation-buttons pe-4">
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
      </div>
    </v-app-bar>

    <v-main>
      <v-container class="px-6">
        <router-view :key="$route.fullPath"></router-view>
      </v-container>
    </v-main>
  </v-app>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { api } from './api';
import { useRouter } from 'vue-router';
import debounce from 'lodash/debounce';

interface Sighting {
  id: string;
  excel_id: number;
  species: string;
  ring: string;
  reading: string;
  date: string;
  place: string;
  group_size: number | null;
  comment: string | null;
  melder: string;
  melded: boolean;
  lat: number;
  lon: number;
  habitat: string;
}

interface BirdSuggestion {
  species: string;
  ring: string;
  sighting_count: number;
  last_seen: string;
  first_seen: string;
  other_species_identifications: Record<string, number>;
  sightings: Sighting[];
}

const router = useRouter();
const version = ref<string>();
const searchQuery = ref('');
const suggestions = ref<BirdSuggestion[]>([]);
const isLoading = ref(false);
const selectedBird = ref<BirdSuggestion | null>(null);
const totalResults = ref(0);

// Computed property for sorted and limited suggestions
const sortedSuggestions = computed(() => {
  const sorted = [...suggestions.value].sort((a, b) => {
    // First sort by sighting count (descending)
    const countDiff = b.sighting_count - a.sighting_count;
    if (countDiff !== 0) return countDiff;
    
    // Then by last seen date (descending)
    return new Date(b.last_seen).getTime() - new Date(a.last_seen).getTime();
  });
  
  // Store total count before limiting
  totalResults.value = sorted.length;
  
  // Return only first 50 results
  return sorted.slice(0, 50);
});

// Format date helper function
const formatDate = (date: string | null) => {
  if (!date) return '';
  return new Date(date).toLocaleDateString('de-DE');
};

// Debounced search function
const debouncedSearch = debounce(async (query: string) => {
  if (!query || query.length < 2) {
    suggestions.value = [];
    return;
  }

  isLoading.value = true;
  try {
    const response = await api.get<BirdSuggestion[]>(`/birds/suggestions/${query}`);
    suggestions.value = response.data;
  } catch (error) {
    console.error('Failed to fetch suggestions:', error);
    suggestions.value = [];
  } finally {
    isLoading.value = false;
  }
}, 900);

// Handle bird selection
const onBirdSelected = (bird: BirdSuggestion | null) => {
  if (bird) {
    router.push(`/birds/${bird.ring}`);
    selectedBird.value = null;
    searchQuery.value = '';
  }
};

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
  border: 1px solid #DED5CA !important;
  background-color: #FFFFFF !important;
  box-shadow: none !important;
}

.v-text-field .v-field {
  box-shadow: none !important;
  border: 1px solid #DED5CA !important;
  border-radius: 8px !important;
}

.v-text-field .v-field:hover {
  border-color: #228096 !important;
}

.v-text-field .v-field--focused {
  border-color: #00436C !important;
}

/* Remove underline from input fields */
.v-field__outline {
  --v-field-border-width: 0 !important;
}

/* Remove underline from select fields as well */
.v-select .v-field__outline {
  --v-field-border-width: 0 !important;
}

/* Updated search bar styles */
.search-container {
  width: 100%;
  max-width: 400px;
  margin: 0 24px;
}

.bird-search {
  width: 100%;
}

.bird-search .v-field {
  background-color: #FFFFFF !important;
  border: 1px solid rgba(0, 67, 108, 0.1) !important;
  border-radius: 4px !important;
  min-height: 34px !important;
  height: 34px !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
}

.bird-search .v-field input {
  color: #00436C !important;
  padding-top: 0 !important;
  padding-bottom: 0 !important;
  min-height: 34px !important;
  height: 34px !important;
  margin-top: 0 !important;
  margin-bottom: 0 !important;
  line-height: 34px !important;
}

.bird-search .v-field input::placeholder {
  color: rgba(0, 67, 108, 0.5) !important;
}

.bird-search .v-field__append-inner .v-icon {
  color: rgba(0, 0, 0, 0.6) !important;
}

/* Optional: Style the dropdown menu */
.bird-search .v-list {
  background-color: #FFFFFF;
  border: 1px solid #DED5CA;
  color: rgba(0, 0, 0, 0.87);
}

.bird-search .v-list-item:hover {
  background-color: #F7F4F1;
}

/* Navigation buttons container */
.navigation-buttons {
  display: flex;
  gap: 8px;
}

.bird-search .v-list-item__title strong {
  color: #00436C;
}

.bird-search .v-list-item__subtitle {
  color: #228096;
}

/* Add styles for the "more results" message */
.bird-search .v-autocomplete__append-item {
  border-top: 1px solid rgba(0, 0, 0, 0.12);
  background-color: #f5f5f5;
}

/* Force hide the dropdown icon */
.bird-search .v-field__append-inner {
  display: none !important;
}

/* Adjust the field input wrapper height */
.bird-search .v-field__input {
  min-height: 34px !important;
  padding: 0 12px !important;
}

/* Optional: Add a subtle hover effect */
.bird-search .v-field:hover {
  background-color: rgba(255, 255, 255, 0.95) !important;
  border-color: rgba(255, 255, 255, 0.3) !important;
}

/* Add new styles for better contrast and readability */
.v-app-bar.v-app-bar--flat {
  background-color: #00436C !important;
}

.navigation-buttons .v-btn {
  color: #FFFFFF !important;
  opacity: 0.9;
}

.navigation-buttons .v-btn:hover {
  opacity: 1;
  background-color: rgba(255, 255, 255, 0.1) !important;
}
</style>