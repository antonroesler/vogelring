<template>
  <v-dialog v-model="dialog" max-width="500px">
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
      <v-card-title>Vorschläge für "{{ reading }}"</v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item
            v-for="suggestion in [...suggestions].sort((a, b) => 
              (b.sightings?.length || 0) - (a.sightings?.length || 0)
            )"
            :key="suggestion.ring || ''"
            @click="selectSuggestion(suggestion)"
          >
            <v-list-item-title>
              {{ suggestion.ring }} - {{ suggestion.species }}
            </v-list-item-title>
            <v-list-item-subtitle>
              {{ suggestion.sightings?.length || 0 }} 
              Sichtung{{ (suggestion.sightings?.length || 0) !== 1 ? 'en' : '' }} |
              Letzte Sichtung: {{ formatDate(suggestion.last_seen) }} 
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue';
import { format } from 'date-fns';
import { getBirdSuggestions } from '@/api';
import type { BirdMeta } from '@/types';

const props = defineProps<{
  reading: string;
}>();

const emit = defineEmits<{
  'select': [suggestion: BirdMeta];
}>();

const dialog = ref(false);
const suggestions = ref<BirdMeta[]>([]);
let debounceTimeout: number | null = null;

// Debounced function to fetch suggestions
const fetchSuggestions = async (reading: string) => {
  if (reading && reading.length >= 3) {
    try {
      suggestions.value = await getBirdSuggestions(reading);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  } else {
    suggestions.value = [];
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
  }, 1000); // 1 second delay
}, { immediate: true });

// Clean up the timeout when component is unmounted
onBeforeUnmount(() => {
  if (debounceTimeout) {
    window.clearTimeout(debounceTimeout);
  }
});

const selectSuggestion = (suggestion: BirdMeta) => {
  emit('select', suggestion);
  dialog.value = false;
};

const formatDate = (date: string | null) => {
  if (!date) return '';
  return format(new Date(date), 'dd.MM.yyyy');
};
</script>