<template>
  <v-form @submit.prevent="saveSighting">
    <!-- Group 1: Date and Place -->
    <v-card-subtitle class="px-0">Datum und Ort</v-card-subtitle>
    <v-row dense>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.date"
          label="Datum"
          type="date"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-autocomplete
          v-if="showPlaceSuggestions"
          v-model="localSighting.place"
          :items="filteredPlaces"
          label="Ort"
          @update:search="filterPlaces"
          :loading="!places.length"
          hide-no-data
          autocomplete="off"
          clearable
          :filter="() => true"
          :return-object="false"
          density="comfortable"
        ></v-autocomplete>
        <v-text-field
          v-else
          v-model="localSighting.place"
          label="Ort"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.habitat"
          label="Habitat"
          density="comfortable"
        ></v-text-field>
      </v-col>
    </v-row>

    <!-- Group 2: Bird Identification -->
    <v-card-subtitle class="px-0 mt-4">Vogelidentifikation</v-card-subtitle>
    <v-row dense>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.reading"
          label="Ablesung"
          :hint="showBirdSuggestions ? 'Nutze ... oder * als Platzhalter' : undefined"
          :persistent-hint="showBirdSuggestions"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.ring"
          label="Ring"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.species"
          label="Spezies"
          density="comfortable"
        ></v-text-field>
      </v-col>
    </v-row>
    <v-row v-if="showBirdSuggestions">
      <v-col cols="12" class="pt-0">
        <bird-suggestions
          :reading="localSighting.reading || ''"
          @select="handleSuggestionSelect"
        ></bird-suggestions>
      </v-col>
    </v-row>

    <!-- Group 3: Additional Information -->
    <v-card-subtitle class="px-0 mt-4">Zusätzliche Informationen</v-card-subtitle>
    <v-row dense>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.group_size"
          label="Gruppengröße"
          type="number"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.melder"
          label="Melder"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-checkbox
          v-model="localSighting.melded"
          label="Gemeldet"
          density="comfortable"
        ></v-checkbox>
      </v-col>
    </v-row>

    <!-- Comments -->
    <v-card-subtitle class="px-0 mt-4">Kommentar</v-card-subtitle>
    <v-row>
      <v-col cols="12">
        <v-textarea
          v-model="localSighting.comment"
          label="Kommentare"
          density="comfortable"
        ></v-textarea>
      </v-col>
    </v-row>

    <!-- Map -->
    <v-card-subtitle class="px-0 mt-4">Standort</v-card-subtitle>
    <v-row>
      <v-col cols="12">
        <leaflet-map
          v-model:latitude="latitude"
          v-model:longitude="longitude"
        ></leaflet-map>
        <v-row v-if="showCoordinates" class="mt-2" dense>
          <v-col cols="6">
            <v-text-field
              v-model="latitude"
              label="Breitengrad"
              readonly
              density="compact"
            ></v-text-field>
          </v-col>
          <v-col cols="6">
            <v-text-field
              v-model="longitude"
              label="Längengrad"
              readonly
              density="compact"
            ></v-text-field>
          </v-col>
        </v-row>
      </v-col>
    </v-row>

    <v-card-actions class="mt-4">
      <v-spacer></v-spacer>
      <v-btn
        color="primary"
        type="submit"
        :loading="loading"
        size="large"
        variant="elevated"
        class="px-8"
        :prepend-icon="isNewEntry ? 'mdi-content-save' : undefined"
      >
        Speichern
      </v-btn>
    </v-card-actions>
  </v-form>
</template>

<script setup lang="ts">
import { ref, watch, computed, onMounted } from 'vue';
import type { Sighting, BirdMeta } from '@/types';
import LeafletMap from '@/components/map/LeafletMap.vue';
import BirdSuggestions from '@/components/birds/BirdSuggestions.vue';
import { api } from '@/api';

const props = defineProps<{
  sighting: Partial<Sighting>;
  loading?: boolean;
  isNewEntry?: boolean;
  showBirdSuggestions?: boolean;
  showPlaceSuggestions?: boolean;
  showCoordinates?: boolean;
}>();

const emit = defineEmits<{
  'submit': [sighting: Partial<Sighting>];
}>();

const localSighting = ref<Partial<Sighting>>({ ...props.sighting });
const places = ref<string[]>([]);
const filteredPlaces = ref<string[]>([]);

// Load places if needed
onMounted(async () => {
  if (props.showPlaceSuggestions) {
    try {
      const response = await api.get('/places');
      places.value = response.data;
    } catch (error) {
      console.error('Error fetching places:', error);
      places.value = [];
    }
  }
});

watch(() => props.sighting, (newSighting) => {
  localSighting.value = { ...newSighting };
}, { deep: true });

const filterPlaces = (input: string) => {
  if (!input) {
    filteredPlaces.value = places.value || [];
    return;
  }
  const searchTerm = input.toLowerCase();
  const filtered = places.value
    .filter(place => place.toLowerCase().includes(searchTerm))
    .slice(0, 5); // Only show top 5 suggestions
  
  // Add the current input as an option if it's not in the filtered list
  if (!filtered.includes(input)) {
    filtered.unshift(input);
  }
  
  filteredPlaces.value = filtered;
};

const handleSuggestionSelect = (suggestion: BirdMeta) => {
  localSighting.value.ring = suggestion.ring;
  localSighting.value.species = suggestion.species;
};

const saveSighting = () => {
  emit('submit', localSighting.value);
};

const latitude = computed({
  get: () => localSighting.value.lat ?? 50.1109,
  set: (val) => localSighting.value.lat = val
});

const longitude = computed({
  get: () => localSighting.value.lon ?? 8.6821,
  set: (val) => localSighting.value.lon = val
});
</script>