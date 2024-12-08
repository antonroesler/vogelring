<template>
  <v-dialog v-model="dialog" max-width="500px">
    <template v-slot:activator="{ props }">
      <v-btn
        color="primary"
        v-bind="props"
        :disabled="!reading || reading.length < 3"
      >
        Vorschläge
      </v-btn>
    </template>
    <v-card>
      <v-card-title>Vorschläge für "{{ reading }}"</v-card-title>
      <v-card-text>
        <v-list>
          <v-list-item
            v-for="suggestion in suggestions"
            :key="suggestion.ring"
            @click="selectSuggestion(suggestion)"
          >
            <v-list-item-title>
              {{ suggestion.ring }} - {{ suggestion.species }}
            </v-list-item-title>
            <v-list-item-subtitle>
              Letzte Sichtung: {{ formatDate(suggestion.last_seen) }}
            </v-list-item-subtitle>
          </v-list-item>
        </v-list>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
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

watch(() => props.reading, async (newReading) => {
  if (newReading && newReading.length >= 3) {
    try {
      suggestions.value = await getBirdSuggestions(newReading);
    } catch (error) {
      console.error('Error fetching suggestions:', error);
    }
  } else {
    suggestions.value = [];
  }
});

const selectSuggestion = (suggestion: BirdMeta) => {
  emit('select', suggestion);
  dialog.value = false;
};

const formatDate = (date: string) => {
  return format(new Date(date), 'dd.MM.yyyy');
};
</script>