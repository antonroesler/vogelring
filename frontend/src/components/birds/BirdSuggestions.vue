<template>
  <v-dialog v-model="dialog" max-width="500" width="90%">
    <template v-slot:activator="{ props }">
      <v-btn
        variant="text"
        color="primary"
        v-bind="props"
        :disabled="!reading || reading.length < 3"
        icon
        size="small"
      >
        <v-icon>mdi-magnify</v-icon>
      </v-btn>
    </template>
    <v-card>
      <v-card-title class="d-flex align-center">
        <span>Vorschläge für "{{ reading }}"</span>
        <v-spacer></v-spacer>
        <v-progress-circular
          v-if="isLoading"
          indeterminate
          size="20"
          width="2"
          color="primary"
          class="mr-2"
        ></v-progress-circular>
      </v-card-title>
      <v-card-text>
        <v-list v-if="suggestions.length > 0">
          <v-list-item
            v-for="suggestion in suggestions"
            :key="suggestion.ring || ''"
            @click="selectSuggestion(suggestion)"
            class="suggestion-item"
          >
            <template v-slot:prepend>
              <v-icon icon="mdi-bird" color="primary" size="small" class="mr-2"></v-icon>
            </template>
            <v-list-item-title>
              <strong>{{ suggestion.ring }}</strong> - {{ suggestion.species }}
            </v-list-item-title>
            <v-list-item-subtitle>
              {{ suggestion.sighting_count }} 
              Sichtung{{ suggestion.sighting_count !== 1 ? 'en' : '' }} | 
              Letzte Sichtung: {{ formatDate(suggestion.last_seen) }}
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
        <div v-else-if="isLoading" class="d-flex align-center justify-center pa-4">
          <span>Suche läuft...</span>
        </div>
        <div v-else-if="noResults && reading.length >= 3" class="text-center pa-4">
          <v-icon icon="mdi-alert-circle-outline" color="warning" class="mr-1"></v-icon>
          Keine Ergebnisse gefunden
        </div>
        <div v-else class="text-center pa-4 text-medium-emphasis">
          Bitte mindestens 3 Zeichen eingeben
        </div>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue';
import { format } from 'date-fns';
import { getBirdSuggestions } from '@/api';
import type { SuggestionBird } from '@/types';

const props = defineProps<{
  reading: string;
}>();

const emit = defineEmits<{
  'select': [suggestion: SuggestionBird];
}>();

const dialog = ref(false);
const suggestions = ref<SuggestionBird[]>([]);
const isLoading = ref(false);
const noResults = ref(false);
const latestRequestId = ref(0); // To track the latest request
let debounceTimeout: number | null = null;

// Debounced function to fetch suggestions
const fetchSuggestions = async (reading: string) => {
  if (reading && reading.length >= 3) {
    isLoading.value = true;
    noResults.value = false;
    
    // Generate a unique request ID
    const currentRequestId = ++latestRequestId.value;
    
    try {
      const result = await getBirdSuggestions(reading);
      
      // Only update if this is still the latest request
      if (currentRequestId === latestRequestId.value) {
        // Use all suggestions from the server without any client-side filtering
        suggestions.value = result;
        noResults.value = result.length === 0;
        
        // Log the number of suggestions for debugging
        console.log(`Received ${result.length} suggestions for reading "${reading}"`);
      } else {
        console.log(`Discarding stale response for reading "${reading}" (request ID: ${currentRequestId})`);
      }
    } catch (error) {
      // Only update if this is still the latest request
      if (currentRequestId === latestRequestId.value) {
        console.error('Error fetching suggestions:', error);
        suggestions.value = [];
        noResults.value = true;
      }
    } finally {
      // Only update if this is still the latest request
      if (currentRequestId === latestRequestId.value) {
        isLoading.value = false;
      }
    }
  } else {
    suggestions.value = [];
    noResults.value = false;
  }
};

// Watch with debounce
watch(() => props.reading, (newReading) => {
  // Clear any existing timeout
  if (debounceTimeout) {
    window.clearTimeout(debounceTimeout);
  }

  // Set new timeout
  debounceTimeout = window.setTimeout(() => {
    fetchSuggestions(newReading);
  }, 900);
}, { immediate: true });

// Clean up the timeout when component is unmounted
onBeforeUnmount(() => {
  if (debounceTimeout) {
    window.clearTimeout(debounceTimeout);
  }
});

const selectSuggestion = (suggestion: SuggestionBird) => {
  emit('select', suggestion);
  dialog.value = false;
};

const formatDate = (date: string | null) => {
  if (!date) return '';
  return format(new Date(date), 'dd.MM.yyyy');
};
</script>

<style scoped>
.suggestion-item {
  transition: background-color 0.2s ease;
  border-radius: 4px;
  margin: 2px 0;
}

.suggestion-item:hover {
  background-color: rgba(0, 67, 108, 0.05);
}

.v-list-item-title strong {
  color: #00436C;
}

.v-list-item-subtitle {
  color: #228096;
}
</style>