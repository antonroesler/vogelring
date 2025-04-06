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
          item-value="ring"
          return-object
          class="bird-search"
          density="compact"
          variant="solo"
          @update:search="debouncedSearch"
          @update:model-value="onBirdSelected"
          :filter="() => true"
          :custom-filter="() => true"
        >
          <template v-slot:item="{ item }">
            <div class="d-flex align-center py-1 px-2 suggestion-item" @click="navigateToBird(item.raw)">
              <v-icon icon="mdi-bird" color="primary" size="small" class="mr-2"></v-icon>
              <div class="flex-grow-1">
                <div><strong>{{ item.raw.ring }}</strong> - {{ item.raw.species }}</div>
                <div class="text-caption">
                  {{ item.raw.sighting_count }} 
                  Sichtung{{ item.raw.sighting_count !== 1 ? 'en' : '' }} | 
                  Letzte Sichtung: {{ formatDate(item.raw.last_seen) }}
                </div>
              </div>
              <v-btn
                icon
                size="small"
                variant="text"
                color="primary"
                @click.stop="navigateToBird(item.raw)"
                class="ml-2"
              >
                <v-icon>mdi-eye</v-icon>
                <v-tooltip activator="parent" location="bottom">
                  Details anzeigen
                </v-tooltip>
              </v-btn>
            </div>
          </template>

          <!-- Custom no-data slot to differentiate between loading and no results -->
          <template v-slot:no-data>
            <div class="pa-2">
              <div v-if="isLoading" class="d-flex align-center">
                <v-progress-circular
                  indeterminate
                  size="20"
                  width="2"
                  color="primary"
                  class="mr-2"
                ></v-progress-circular>
                <span>Suche läuft...</span>
              </div>
              <div v-else-if="noResults && searchQuery.length >= 2" class="text-center">
                <v-icon icon="mdi-alert-circle-outline" color="warning" class="mr-1"></v-icon>
                Keine Ergebnisse gefunden
              </div>
              <div v-else-if="searchQuery.length < 2" class="text-center text-medium-emphasis">
                Bitte mindestens 2 Zeichen eingeben
              </div>
            </div>
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
          to="/ringing" 
          variant="text"
          color="white"
        >Beringungen</v-btn>
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
import { SuggestionBird } from './types';

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

// Use the SuggestionBird type directly instead of redefining it
type BirdSuggestion = SuggestionBird;

const router = useRouter();
const version = ref<string>();
const searchQuery = ref('');
const suggestions = ref<BirdSuggestion[]>([]);
const isLoading = ref(false);
const selectedBird = ref<BirdSuggestion | null>(null);
const totalResults = ref(0);
const noResults = ref(false);
const latestRequestId = ref(0); // To track the latest request

// Updated computed property - no sorting needed, API provides sorted results
const sortedSuggestions = computed(() => {
  // Store total count
  totalResults.value = suggestions.value.length;
  
  // Return only first 50 results
  return suggestions.value.slice(0, 50);
});

// Format date helper function
const formatDate = (date: string | null) => {
  if (!date) return '';
  return new Date(date).toLocaleDateString('de-DE');
};

// Format the autocomplete item text for display
const formatBirdInfo = (item: SuggestionBird) => {
  return {
    title: `${item.ring} - ${item.species}`,
    subtitle: `${item.sighting_count} Sichtung${item.sighting_count !== 1 ? 'en' : ''} | Letzte Sichtung: ${formatDate(item.last_seen)}`
  };
};

// Debounced search function
const debouncedSearch = debounce(async (query: string) => {
  if (!query || query.length < 2) {
    suggestions.value = [];
    noResults.value = false;
    return;
  }

  isLoading.value = true;
  noResults.value = false;
  
  // Generate a unique request ID
  const currentRequestId = ++latestRequestId.value;
  
  try {
    console.log(`Sending request for query "${query}" (request ID: ${currentRequestId})`);
    const response = await api.get<BirdSuggestion[]>(`/birds/suggestions/${query}`);
    
    // Only update if this is still the latest request
    if (currentRequestId === latestRequestId.value) {
      console.log(`Received ${response.data.length} suggestions for query "${query}"`);
      suggestions.value = response.data;
      noResults.value = response.data.length === 0;
      
      // Debugging log to see the structure of the response data
      if (response.data.length > 0) {
        console.log('First suggestion:', JSON.stringify(response.data[0]));
      }
    } else {
      console.log(`Discarding stale response for query "${query}" (request ID: ${currentRequestId})`);
    }
  } catch (error) {
    // Only update if this is still the latest request
    if (currentRequestId === latestRequestId.value) {
      console.error('Failed to fetch suggestions:', error);
      suggestions.value = [];
      noResults.value = true;
    }
  } finally {
    // Only update if this is still the latest request
    if (currentRequestId === latestRequestId.value) {
      isLoading.value = false;
    }
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

// Navigate to bird details page
const navigateToBird = (bird: BirdSuggestion) => {
  router.push(`/birds/${bird.ring}`);
  selectedBird.value = null;
  searchQuery.value = '';
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

/* Styles for loading and no-results states */
.bird-search .v-autocomplete__no-data {
  padding: 8px;
  min-height: 48px;
}

.bird-search .v-autocomplete__no-data .v-progress-circular {
  margin-right: 8px;
}

.bird-search .v-autocomplete__no-data .text-center {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 32px;
}

/* Styles for suggestion items */
.suggestion-item {
  cursor: pointer;
  transition: background-color 0.2s ease;
  border-radius: 4px;
  margin: 2px 0;
}

.suggestion-item:hover {
  background-color: rgba(0, 67, 108, 0.05);
}

.suggestion-item .v-btn {
  opacity: 0.7;
}

.suggestion-item:hover .v-btn {
  opacity: 1;
}
</style>