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
          :loading="!suggestions.places.length"
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
        <v-autocomplete
          v-model="localSighting.habitat"
          :items="filteredHabitats"
          label="Habitat"
          @update:search="filterHabitats"
          :loading="!suggestions.habitats.length"
          hide-no-data
          autocomplete="off"
          clearable
          :filter="() => true"
          :return-object="false"
          density="comfortable"
        ></v-autocomplete>
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
        >
          <template v-if="showBirdSuggestions" v-slot:append-inner>
            <bird-suggestions
              :reading="localSighting.reading || ''"
              @select="handleSuggestionSelect"
            ></bird-suggestions>
          </template>
        </v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.ring"
          label="Ring"
          density="comfortable"
        ></v-text-field>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-autocomplete
          v-model="localSighting.species"
          :items="filteredSpecies"
          label="Spezies"
          @update:search="filterSpecies"
          :loading="!suggestions.species.length"
          hide-no-data
          autocomplete="off"
          clearable
          :filter="() => true"
          :return-object="false"
          density="comfortable"
        ></v-autocomplete>
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
        <v-autocomplete
          v-model="localSighting.melder"
          :items="filteredMelders"
          label="Melder"
          @update:search="filterMelders"
          :loading="!suggestions.melders.length"
          hide-no-data
          autocomplete="off"
          clearable
          :filter="() => true"
          :return-object="false"
          density="comfortable"
        ></v-autocomplete>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-checkbox
          v-model="localSighting.melded"
          label="Gemeldet"
          density="comfortable"
        ></v-checkbox>
      </v-col>
      <v-col cols="12" sm="4" md="4">
        <v-text-field
          v-model="localSighting.partner"
          label="Partner"
          density="comfortable"
        >
          <template v-if="showBirdSuggestions" v-slot:append-inner>
            <bird-suggestions
              :reading="localSighting.partner || ''"
              @select="handlePartnerSelect"
            ></bird-suggestions>
          </template>
        </v-text-field>
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
const suggestions = ref<{
  places: string[];
  species: string[];
  habitats: string[];
  melders: string[];
}>({
  places: [],
  species: [],
  habitats: [],
  melders: []
});

const filteredPlaces = ref<string[]>([]);
const filteredSpecies = ref<string[]>([]);
const filteredHabitats = ref<string[]>([]);
const filteredMelders = ref<string[]>([]);

onMounted(async () => {
  try {
    const response = await api.get('/suggestions');
    suggestions.value = response.data;
    filteredPlaces.value = suggestions.value.places;
    filteredSpecies.value = suggestions.value.species;
    filteredHabitats.value = suggestions.value.habitats;
    filteredMelders.value = suggestions.value.melders;
  } catch (error) {
    console.error('Error fetching suggestions:', error);
  }
});

watch(() => props.sighting, (newSighting) => {
  localSighting.value = { ...newSighting };
}, { deep: true });

const createFilter = (field: keyof typeof suggestions.value) => {
  return (input: string) => {
    const targetRef = computed(() => {
      switch(field) {
        case 'places': return filteredPlaces;
        case 'species': return filteredSpecies;
        case 'habitats': return filteredHabitats;
        case 'melders': return filteredMelders;
      }
    });

    if (!input) {
      targetRef.value.value = suggestions.value[field] || [];
      return;
    }
    
    const searchTerm = input.toLowerCase();
    const filtered = (suggestions.value[field] || [])
      .filter(item => item.toLowerCase().includes(searchTerm))
      .slice(0, 5);
    
    if (input && !filtered.includes(input)) {
      filtered.unshift(input);
    }
    
    targetRef.value.value = filtered;
  };
};

const filterPlaces = createFilter('places');
const filterSpecies = createFilter('species');
const filterHabitats = createFilter('habitats');
const filterMelders = createFilter('melders');

const handleSuggestionSelect = (suggestion: BirdMeta) => {
  localSighting.value.ring = suggestion.ring;
  localSighting.value.species = suggestion.species;
};

const handlePartnerSelect = (suggestion: BirdMeta) => {
  localSighting.value.partner = suggestion.ring;
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