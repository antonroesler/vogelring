<template>
  <v-card class="mb-4">
    <v-card-title>Neuer Eintrag</v-card-title>
    <v-card-text>
      <v-form @submit.prevent="saveSighting">
        <v-row>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="sighting.reading"
              label="Ablesung"
              hint="Nutze ... oder * als Platzhalter"
              persistent-hint
            ></v-text-field>
            <bird-suggestions
              :reading="sighting.reading || ''"
              @select="handleSuggestionSelect"
              class="mt-2"
            ></bird-suggestions>
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="sighting.ring"
              label="Ring"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="sighting.date"
              label="Datum"
              type="date"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="sighting.species"
              label="Spezies"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="sighting.place"
              label="Ort"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="sighting.group_size"
              label="Gruppengröße"
              type="number"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="6">
            <v-text-field
              v-model="sighting.melder"
              label="Melder"
            ></v-text-field>
          </v-col>
          <v-col cols="12" md="6">
            <v-checkbox
              v-model="sighting.melded"
              label="Gemeldet"
            ></v-checkbox>
          </v-col>
          <v-col cols="12">
            <v-textarea
              v-model="sighting.comment"
              label="Kommentare"
            ></v-textarea>
          </v-col>
          <v-col cols="12">
            <leaflet-map
              v-model:latitude="sighting.lat"
              v-model:longitude="sighting.lon"
            ></leaflet-map>
            <v-row class="mt-2">
              <v-col cols="6">
                <v-text-field
                  v-model="sighting.lat"
                  label="Breitengrad"
                  readonly
                  density="compact"
                ></v-text-field>
              </v-col>
              <v-col cols="6">
                <v-text-field
                  v-model="sighting.lon"
                  label="Längengrad"
                  readonly
                  density="compact"
                ></v-text-field>
              </v-col>
            </v-row>
          </v-col>
        </v-row>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            type="submit"
            :loading="loading"
            size="large"
            prepend-icon="mdi-content-save"
          >
            Speichern
          </v-btn>
        </v-card-actions>
      </v-form>
    </v-card-text>
  </v-card>
  <v-snackbar v-model="showSnackbar" color="success">
    Eintrag erfolgreich gespeichert
  </v-snackbar>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useSightingsStore } from '@/stores/sightings';
import type { Sighting, BirdMeta } from '@/types';
import LeafletMap from '@/components/map/LeafletMap.vue';
import BirdSuggestions from '@/components/birds/BirdSuggestions.vue';

const store = useSightingsStore();
const loading = ref(false);
const showSnackbar = ref(false);

const sighting = ref<Partial<Sighting>>({
  date: new Date().toISOString().split('T')[0],
  lat: 50.1109,
  lon: 8.6821,
  melded: false
});

const handleSuggestionSelect = (suggestion: BirdMeta) => {
  sighting.value.ring = suggestion.ring;
  sighting.value.species = suggestion.species;
};

const saveSighting = async () => {
  loading.value = true;
  try {
    await store.createSighting(sighting.value);
    showSnackbar.value = true;
    
    // Reset form except for place, date, and coordinates
    const { place, date, lat, lon } = sighting.value;
    
    sighting.value = {
      place,
      date,
      lat,
      lon,
      melded: false
    };
  } catch (error) {
    console.error('Error saving sighting:', error);
  } finally {
    loading.value = false;
  }
};
</script>